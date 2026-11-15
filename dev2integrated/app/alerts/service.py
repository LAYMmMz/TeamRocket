from datetime import datetime, timezone
import math
from operator import eq, ge, gt, le, lt
from uuid import NAMESPACE_URL, uuid5

from app.alerts.models import Rule, RuleMode
from app.incidents.service import link_alert

_OPERATORS = {"gt": gt, "ge": ge, "lt": lt, "le": le, "eq": eq}

def _parse(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

def evaluate_measurement(
    payload, store, settings, actor_id, *, now=None
):
    now = now or datetime.now(timezone.utc)
    found = []

    for historical in store.list(
        "health_alert", mission_id=payload["mission_id"]
    ):
        if (
            historical.get("evidence_event_id") != payload["event_id"]
            or historical.get("kind") != "RULE_MATCH"
        ):
            continue
        snapshot = historical.get("rule_snapshot")
        if snapshot:
            link_alert(historical, snapshot, store, actor_id)
            found.append(historical)

    known_ids = {alert["event_id"] for alert in found}
    versions = [
        Rule.model_validate(row)
        for row in store.list(
            "alert_rule", mission_id=payload["mission_id"]
        )
    ]
    latest = {}
    for version in versions:
        if (
            version.rule_id not in latest
            or version.version > latest[version.rule_id].version
        ):
            latest[version.rule_id] = version

    for rule in latest.values():
        if payload.get("metric") != rule.metric:
            continue

        block = None
        measured = _parse(payload["measured_at"])

        if not rule.valid_from <= now < rule.valid_until:
            block = "rule_outside_validity"
        elif not rule.valid_from <= measured < rule.valid_until:
            block = "evidence_outside_rule_validity"
        elif rule.mode == RuleMode.RESEARCH:
            block = "research_only"
        elif rule.mode == RuleMode.OPERATIONAL and (
            rule.verification != "VERIFIED"
            or rule.approval != "APPROVED"
        ):
            block = "rule_not_approved_and_verified"
        elif rule.mode == RuleMode.DEMO and (
            settings.environment not in {"development", "test"}
            or not settings.allow_demo_rules
        ):
            block = "demo_disabled"
        elif rule.mode == RuleMode.DEMO and (
            payload.get("source_type") != "SIMULATED"
            or payload.get("is_synthetic") is not True
        ):
            block = "demo_requires_synthetic_evidence"
        elif payload.get("source_type") == "RESEARCH":
            block = "research_evidence"
        elif (
            rule.operator != "unavailable"
            and payload.get("quality") != "VALID"
        ):
            block = "evidence_quality_unavailable"
        elif (
            rule.mode == RuleMode.OPERATIONAL
            and payload.get("verification") != "VERIFIED"
        ):
            block = "evidence_unverified"
        elif (
            rule.operator != "unavailable"
            and (now - measured).total_seconds()
            > rule.max_evidence_age_seconds
        ):
            block = "evidence_stale"
        elif measured > now:
            block = "evidence_in_future"

        metadata = payload.get("metadata") or {}
        if block is None and any(
            metadata.get(key) != value
            for key, value in rule.required_context.items()
        ):
            block = "context_not_applicable"

        if (
            block is None
            and rule.operator != "unavailable"
            and rule.averaging_window_seconds is not None
        ):
            if (
                metadata.get("averaging_window_seconds")
                != rule.averaging_window_seconds
                or metadata.get("aggregation")
                not in {"mean", "time_weighted_mean"}
            ):
                block = "averaging_window_not_applicable"

        value = payload.get("normalized_value")
        unit = payload.get("normalized_unit")
        if value is None:
            value = payload.get("value")
            unit = payload.get("unit")

        if (
            block is None
            and rule.operator != "unavailable"
            and unit != rule.unit
        ):
            block = "units_not_comparable"
        if (
            block is None
            and rule.operator != "unavailable"
            and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            )
        ):
            block = "value_unavailable"

        if block:
            store.audit(
                "rule_evaluation_blocked", actor_id,
                mission_id=payload["mission_id"],
                record_id=payload["event_id"],
                details={
                    "rule_id": rule.rule_id,
                    "version": rule.version,
                    "reason": block,
                },
            )
            continue

        if rule.operator == "unavailable":
            unavailable = (
                payload.get("quality") in {"MISSING", "STALE", "INVALID"}
                or value is None
                or (now - measured).total_seconds()
                > rule.max_evidence_age_seconds
            )
            if not unavailable:
                continue
        elif not _OPERATORS[rule.operator](value, rule.threshold):
            continue

        alert_id = str(uuid5(
            NAMESPACE_URL,
            f"rule-alert:{rule.storage_id}:{payload['event_id']}"
        ))
        alert = store.get("health_alert", alert_id)
        if alert is None:
            synthetic = payload.get("is_synthetic") is True
            alert = {
                "event_id": alert_id,
                "evidence_event_id": payload["event_id"],
                "mission_id": payload["mission_id"],
                "astronaut_id": payload.get("astronaut_id"),
                "severity": rule.severity,
                "kind": "RULE_MATCH",
                "mode": rule.mode.value,
                "operational": (
                    rule.mode == RuleMode.OPERATIONAL
                    and not synthetic
                ),
                "label": (
                    "SIMULATED" if synthetic
                    else "APPROVED RULE REVIEW"
                ),
                "message": (
                    "Evidence meets a configured review rule. "
                    "Human review is required."
                ),
                "rule_snapshot": rule.model_dump(mode="json"),
                "evidence_snapshot": payload,
                **{
                    key: payload[key] for key in [
                        "source_type", "is_synthetic",
                        "measured_at", "received_at",
                        "quality", "verification"
                    ]
                },
            }
            store.put(
                "health_alert", alert_id, alert,
                mission_id=payload["mission_id"],
                actor_id=actor_id,
                priority=0 if rule.severity == "critical" else 25,
            )

        link_alert(
            alert, rule.model_dump(mode="json"), store, actor_id
        )
        if alert["event_id"] not in known_ids:
            found.append(alert)
            known_ids.add(alert["event_id"])

    return found

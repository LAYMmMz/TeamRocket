"""Public, read-only RocketPulse synthetic demo API.

This adapter reads ONLY public.rocketpulse_public_demo_samples from Supabase
using the publishable key as the anonymous PostgREST role. It does not query
health_logs, astronauts, the privileged sync RPC, or local clinical SQLite.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import math
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.dependencies import get_settings

router = APIRouter(prefix="/api/v1/public", tags=["Public synthetic demo"])
MISSION = "DEMO-01"
CREW = ("CREW-01", "CREW-02", "CREW-03", "CREW-04")
DOMAINS = frozenset((
    "cardiorespiratory", "vascular", "radiation", "gravity", "fitness",
    "bone", "vision", "immune", "sleep", "cabin",
    "microbiology", "medicalops",
))
METRICS = frozenset((
    "HR", "SpO2", "RR", "BP_SYS", "VASCULAR_INDEX", "DOSE_MSV",
    "GRAVITY_G", "EXERCISE_MIN", "BONE_INDEX", "OCT_INDEX",
    "IMMUNE_INDEX", "SLEEP_H", "CO2_PPM", "CULTURE_INDEX",
    "CHECKIN_COUNT",
))
# Legacy display indices lack the method-specific evidence required by MasterDocs.
UNSUPPORTED_METRICS = frozenset(("VASCULAR_INDEX", "BONE_INDEX", "OCT_INDEX", "IMMUNE_INDEX", "CULTURE_INDEX"))
METRIC_CONTRACTS = {
    "HR": ("cardiorespiratory", "bpm"), "SpO2": ("cardiorespiratory", "%"),
    "RR": ("cardiorespiratory", "breaths/min"), "BP_SYS": ("cardiorespiratory", "mmHg"),
    "DOSE_MSV": ("radiation", "mSv"), "GRAVITY_G": ("gravity", "g"),
    "EXERCISE_MIN": ("fitness", "min"), "SLEEP_H": ("sleep", "h"),
    "CO2_PPM": ("cabin", "ppm"), "CHECKIN_COUNT": ("medicalops", "count"),
}
VISIBLE_COLUMNS = (
    "event_id,mission_id,astronaut_code,domain,metric_code,value,"
    "unit,measured_at,quality,verification,source_type,is_synthetic,"
    "approved_for_public"
)
# The display-only crew names are generated locally; no identifiable
# astronaut profile is read from the private astronauts table.
PUBLIC_CREW = [{
    "id": code,
    "crew_code": code,
    "display_name": "Synthetic Crew Member " + code[-2:],
    "role": "simulated",
    "status": "synthetic",
} for code in CREW]


def _read_approved(settings, *, crew: str, domain: str | None = None):
    url = settings.supabase_url.rstrip("/")
    key = settings.supabase_anon_key
    if not url.startswith("https://") or not key:
        raise HTTPException(503, "Public synthetic database feed is not configured")
    # Fixed server-controlled table, columns, predicates and row limit.
    # Never use a service_role key for this endpoint; anonymous RLS must apply.
    params = {
        "select": VISIBLE_COLUMNS,
        "mission_id": "eq.DEMO-01",
        "astronaut_code": "eq." + crew,
        "approved_for_public": "eq.true",
        "is_synthetic": "eq.true",
        "source_type": "eq.SIMULATED",
        "order": "measured_at.desc,event_id.desc",
        "limit": "200",
    }
    if domain:
        params["domain"] = "eq." + domain
    try:
        with httpx.Client(
            timeout=httpx.Timeout(8.0, connect=3.0),
            follow_redirects=False,
        ) as client:
            response = client.get(
                url + "/rest/v1/rocketpulse_public_demo_samples",
                params=params,
                headers={
                    "apikey": key,
                    "Accept": "application/json",
                },
            )
        response.raise_for_status()
        records = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        # Fail closed; no credentials or upstream body included in public errors.
        raise HTTPException(503, "Approved synthetic Supabase feed unavailable") from exc
    if not isinstance(records, list):
        raise HTTPException(503, "Unexpected synthetic feed response")

    # Independently validate all returned rows, even though PostgREST RLS
    # and strict table constraints should enforce the same invariants.
    approved = []
    for r in records:
        if not isinstance(r, dict) or not (
            r.get("mission_id") == MISSION
            and r.get("astronaut_code") == crew
            and r.get("approved_for_public") is True
            and r.get("is_synthetic") is True
            and r.get("source_type") == "SIMULATED"
            and r.get("quality") == "VALID"
            and r.get("verification") == "UNVERIFIED"
            and r.get("domain") in DOMAINS
            and r.get("metric_code") in METRICS
            and isinstance(r.get("event_id"), str)
            and r["event_id"].startswith("RP-PUBLIC-")
        ):
            raise HTTPException(503, "Synthetic feed failed data validation")
        try:
            numeric = float(r["value"])
            when = datetime.fromisoformat(r["measured_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            raise HTTPException(503, "Invalid synthetic feed data") from exc
        if not math.isfinite(numeric) or not 0 <= numeric <= 10000 or when.tzinfo is None:
            raise HTTPException(503, "Invalid synthetic feed range")
        if domain is not None and r["domain"] != domain:
            raise HTTPException(503, "Synthetic feed domain mismatch")
        if r["metric_code"] in UNSUPPORTED_METRICS:
            continue
        expected_domain, expected_unit = METRIC_CONTRACTS[r["metric_code"]]
        if (r["domain"], r["unit"]) != (expected_domain, expected_unit):
            raise HTTPException(503, "Synthetic measurement contract mismatch")
        approved.append({
            "event_id": r["event_id"], "mission_id": MISSION,
            "astronaut_id": crew, "metric_code": r["metric_code"],
            "domain": r["domain"], "value": numeric, "unit": str(r["unit"])[:24],
            "measured_at": when.isoformat(), "is_synthetic": True,
        })
    return approved


def _vital(row):
    return {
        "id": row["event_id"], "event_id": row["event_id"],
        "astronaut_id": row["astronaut_id"],
        "metric_code": row["metric_code"], "value": row["value"],
        "unit": row["unit"], "baseline": None, "source_type": "synthetic",
        "is_synthetic": True, "measured_at": row["measured_at"],
        "received_at": row["measured_at"], "source_device_id": None,
        "quality": "VALID", "verification": "UNVERIFIED",
    }


def _cache(response: Response):
    response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=30"
    response.headers["X-RocketPulse-Data-Source"] = "supabase-approved-synthetic"


@router.get("/missions/{mission_id}/command")
def public_command(
    mission_id: str, response: Response,
    astronaut_id: Literal["CREW-01", "CREW-02", "CREW-03", "CREW-04"],
    settings=Depends(get_settings),
):
    if mission_id != MISSION:
        raise HTTPException(404, "Public demo mission not found")
    rows = _read_approved(settings, crew=astronaut_id)
    if not rows:
        raise HTTPException(503, "Public synthetic feed has not been seeded")
    latest = {}
    for row in rows:
        if row["domain"] == "cardiorespiratory":
            latest.setdefault(row["metric_code"], row)
    _cache(response)
    return {
        "mission_id": MISSION, "mission_phase": "SYNTHETIC / PUBLIC",
        "mission_day": 0, "timestamp": max(x["measured_at"] for x in rows),
        "crew": PUBLIC_CREW,
        "vitals": [_vital(row) for row in latest.values()],
        "alerts": [], "exam_backlog": 0,
        "sync_state": "connected",
        "devices_online": 0, "devices_total": 0,
        "is_synthetic": True, "data_source": "supabase-approved-synthetic",
    }


@router.get("/measurements/trends")
def public_trends(
    response: Response,
    astronaut_id: Literal["CREW-01", "CREW-02", "CREW-03", "CREW-04"],
    mission_id: Literal["DEMO-01"] = MISSION,
    hours: int = Query(24, ge=1, le=720),
    settings=Depends(get_settings),
):
    rows = _read_approved(settings, crew=astronaut_id, domain="cardiorespiratory")
    if not rows:
        raise HTTPException(503, "Public synthetic feed has not been seeded")
    # Historical timestamps are preserved exactly; do not fabricate live data.
    latest = max(datetime.fromisoformat(r["measured_at"]) for r in rows)
    from datetime import timedelta
    boundary = latest - timedelta(hours=hours)
    points = {}
    for row in rows:
        metric = row["metric_code"]
        if metric not in {"HR", "SpO2", "RR"}:
            continue
        ts = row["measured_at"]
        if datetime.fromisoformat(ts) < boundary:
            continue
        point = points.setdefault(ts, {
            "timestamp": ts, "label": ts[11:16],
            "HR": None, "SpO2": None, "RR": None,
        })
        point[metric] = row["value"]
    _cache(response)
    return sorted(points.values(), key=lambda x: x["timestamp"])[-240:]


@router.get("/reports/domains/{domain_id}")
def public_domain(
    domain_id: str, response: Response,
    astronaut_id: Literal["CREW-01", "CREW-02", "CREW-03", "CREW-04"],
    settings=Depends(get_settings),
):
    if domain_id not in DOMAINS:
        raise HTTPException(404, "Unknown synthetic monitoring domain")
    rows = _read_approved(settings, crew=astronaut_id, domain=domain_id)
    _cache(response)
    return [{
        "id": r["event_id"], "label": r["metric_code"],
        "value": str(r["value"]), "unit": r["unit"],
        "measured_at": r["measured_at"], "source": "SIMULATED",
        "quality": "VALID / UNVERIFIED",
        "details": "Approved synthetic Supabase sample; not a clinical observation",
        "record_table": "rocketpulse_public_demo_samples",
        "is_synthetic": True,
    } for r in rows[:40]]

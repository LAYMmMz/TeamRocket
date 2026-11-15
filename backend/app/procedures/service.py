from datetime import datetime, timezone
from app.core.errors import AppError
from app.procedures.models import Procedure

def key(procedure_id, version):
    return f"{procedure_id}:v{version}"

def check_access(
    procedure, settings, *,
    operational=True, now=None, store=None
):
    now = now or datetime.now(timezone.utc)
    if isinstance(procedure, dict):
        procedure = Procedure.model_validate(procedure)

    if not procedure.valid_from <= now < procedure.expires_at:
        raise AppError(
            409, "procedure_expired", "Procedure outside validity"
        )

    if operational:
        if store is not None:
            versions = [
                row["version"]
                for row in store.list(
                    "procedure", mission_id=procedure.mission_id
                )
                if row["procedure_id"] == procedure.procedure_id
            ]
            if versions and procedure.version != max(versions):
                raise AppError(
                    409, "procedure_superseded",
                    "Procedure superseded"
                )

        provenance = procedure.provenance
        if (
            procedure.mode != "OPERATIONAL"
            or procedure.approval_state != "approved"
            or not all([
                provenance.verified_by,
                provenance.verified_at,
                provenance.approved_by,
                provenance.approved_at,
            ])
            or provenance.verified_at > now
            or provenance.approved_at > now
            or provenance.approved_at < provenance.verified_at
        ):
            raise AppError(
                409, "procedure_not_approved",
                "Procedure not approved"
            )

    elif procedure.mode == "DEMO" and (
        settings.environment not in {"development", "test"}
        or not settings.allow_demo_rules
    ):
        raise AppError(403, "demo_disabled", "Demo disabled")

    return procedure

def save_procedure(procedure, store, settings, actor_id):
    if procedure.mode == "DEMO" and (
        settings.environment not in {"development", "test"}
        or not settings.allow_demo_rules
    ):
        raise AppError(403, "demo_disabled", "Demo disabled")
    return store.put(
        "procedure",
        key(procedure.procedure_id, procedure.version),
        procedure.model_dump(mode="json"),
        mission_id=procedure.mission_id,
        actor_id=actor_id,
    )

def get_procedure(store, procedure_id, version):
    row = store.get("procedure", key(procedure_id, version))
    if row is None:
        raise AppError(
            404, "procedure_not_found", "Procedure not found"
        )
    return Procedure.model_validate(row)

def acknowledge(
    procedure, acknowledgment, store, settings, actor_id
):
    if (
        procedure.is_synthetic
        and settings.environment not in {"development", "test"}
    ):
        raise AppError(403, "demo_disabled", "Demo disabled")

    pkey = key(procedure.procedure_id, procedure.version)
    record_id = (
        f"{pkey}:{acknowledgment.execution_id}:"
        f"{acknowledgment.step_order}"
    )
    body = acknowledgment.model_dump(mode="json") | {
        "procedure_id": procedure.procedure_id,
        "version": procedure.version,
        "mission_id": procedure.mission_id,
        "actor_id": actor_id,
        "source_type": procedure.source_type,
        "is_synthetic": procedure.is_synthetic,
        "label": (
            "SIMULATED" if procedure.is_synthetic
            else procedure.mode
        ),
    }

    if store.get("procedure_acknowledgment", record_id) is not None:
        return store.put(
            "procedure_acknowledgment", record_id, body,
            mission_id=procedure.mission_id, actor_id=actor_id
        )

    check_access(
        procedure, settings,
        operational=acknowledgment.operational, store=store
    )
    if not acknowledgment.operational and procedure.mode != "DEMO":
        raise AppError(
            409, "procedure_not_executable",
            "Procedure not executable"
        )

    previous = [
        row for row in store.list(
            "procedure_acknowledgment",
            mission_id=procedure.mission_id
        )
        if row["procedure_id"] == procedure.procedure_id
        and row["version"] == procedure.version
        and row["execution_id"] == acknowledgment.execution_id
    ]
    if previous and any(
        row["actor_id"] != actor_id for row in previous
    ):
        raise AppError(
            403, "execution_owner", "Execution belongs to another user"
        )

    expected = 1
    if previous:
        latest_time = max(
            datetime.fromisoformat(
                row["acknowledged_at"].replace("Z", "+00:00")
            )
            for row in previous
        )
        if acknowledgment.acknowledged_at < latest_time:
            raise AppError(
                422, "acknowledgment_order",
                "Acknowledgment time is out of order"
            )

        last = max(previous, key=lambda row: row["step_order"])
        prior_step = procedure.steps[last["step_order"] - 1]
        if prior_step.branches:
            branch = next(
                (
                    branch for branch in prior_step.branches
                    if branch.option_id == last["selected_option_id"]
                ),
                None,
            )
            if branch is None:
                raise AppError(
                    409, "branch_required",
                    "Manual branch selection required"
                )
            expected = branch.next_step_order
        else:
            expected = last["step_order"] + 1

    if (
        acknowledgment.step_order != expected
        or expected > len(procedure.steps)
    ):
        raise AppError(
            409, "step_order", "Incorrect next step",
            {"expected_step": expected}
        )

    step = procedure.steps[acknowledgment.step_order - 1]
    options = {branch.option_id for branch in step.branches}
    if (
        options and acknowledgment.selected_option_id not in options
    ) or (
        not options and acknowledgment.selected_option_id is not None
    ):
        raise AppError(422, "invalid_branch", "Invalid manual branch")

    if acknowledgment.acknowledged_at > datetime.now(timezone.utc):
        raise AppError(
            422, "future_acknowledgment",
            "Acknowledgment cannot be in the future"
        )

    return store.put(
        "procedure_acknowledgment", record_id, body,
        mission_id=procedure.mission_id, actor_id=actor_id
    )

def neutral_guidance():
    return {
        "mode": "DEMO",
        "source_type": "SIMULATED",
        "is_synthetic": True,
        "label": "SIMULATED — generic contact guidance",
        "operational": False,
        "guidance": (
            "Contact the designated clinician or mission medical "
            "contact for review. Follow an applicable approved "
            "procedure when one is available."
        ),
        "treatment_instructions": False,
    }

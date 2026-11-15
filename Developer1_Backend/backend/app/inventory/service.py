from datetime import datetime, timezone
from app.core.errors import AppError
from app.inventory.models import InventoryLot

def guard_source(is_synthetic, settings):
    if is_synthetic and settings.environment not in {"development", "test"}:
        raise AppError(
            403, "synthetic_disabled", "Synthetic medical data disabled"
        )

def import_catalog(body, store, settings, actor_id):
    now = datetime.now(timezone.utc)
    for entry in body.entries:
        guard_source(entry.is_synthetic, settings)
        if entry.verified_at and entry.verified_at > now:
            raise AppError(
                422, "future_verification",
                "Verification cannot be in the future"
            )
    with store.transaction():
        return [
            store.put(
                "condition_catalog",
                f"{entry.catalog_id}:v{entry.version}:{entry.code}",
                entry.model_dump(mode="json") | {
                    "label": (
                        "SIMULATED" if entry.is_synthetic
                        else "VERIFIED_SOURCE"
                    )
                },
                actor_id=actor_id,
            )
            for entry in body.entries
        ]

def search_catalog(store, query="", official_only=False):
    query = query.casefold()
    all_rows = store.list("condition_catalog")
    rows = [
        row for row in all_rows
        if (not official_only or not row["is_synthetic"])
        and query in (
            row["code"] + " " + row["title"]
            + " " + row["description"]
        ).casefold()
    ]
    return {
        "items": rows,
        "official_catalog_available": any(
            not row["is_synthetic"] for row in all_rows
        ),
        "automated_diagnosis": False,
    }

def save_lot(lot, store, settings, actor_id):
    guard_source(lot.is_synthetic, settings)
    return store.put(
        "inventory_lot", lot.lot_id,
        lot.model_dump(mode="json"),
        mission_id=lot.mission_id, actor_id=actor_id
    )

def availability(
    store, mission_id, item_id, quantity=1, now=None
):
    now = now or datetime.now(timezone.utc)
    rows = []
    for row in store.list("inventory_lot", mission_id=mission_id):
        if row["item_id"] != item_id:
            continue
        lot = InventoryLot.model_validate(row)
        rows.append(row | {
            "expired": lot.expires_at <= now,
            "available": (
                lot.expires_at > now and lot.quantity >= quantity
            ),
        })
    return {
        "mission_id": mission_id,
        "clinician_selected_item_id": item_id,
        "requested_quantity": quantity,
        "available": any(row["available"] for row in rows),
        "lots": rows,
        "automated_selection": False,
    }

def administer(body, store, settings, actor_id):
    guard_source(body.is_synthetic, settings)
    payload = body.model_dump(mode="json") | {
        "actor_id": actor_id,
        "label": (
            "SIMULATED" if body.is_synthetic
            else "RECORDED_ADMINISTRATION"
        ),
    }
    with store.transaction():
        existing = store.get(
            "medication_administration", body.event_id
        )
        if existing is None:
            row = store.get("inventory_lot", body.lot_id)
            if row is None:
                raise AppError(
                    404, "lot_not_found", "Inventory lot not found"
                )
            lot = InventoryLot.model_validate(row)
            if lot.mission_id != body.mission_id:
                raise AppError(
                    403, "lot_mission", "Lot mission mismatch"
                )
            if lot.category not in {"medication", "antimicrobial"}:
                raise AppError(
                    422, "not_medication", "Lot is not medication"
                )
            if lot.item_id != body.clinician_selected_item_id:
                raise AppError(
                    422, "item_mismatch", "Selected item mismatch"
                )
            if (
                lot.unit != body.unit
                or lot.is_synthetic != body.is_synthetic
            ):
                raise AppError(
                    422, "lot_contract", "Lot source or unit mismatch"
                )
            now = datetime.now(timezone.utc)
            if body.measured_at > now or body.received_at > now:
                raise AppError(
                    422, "future_administration",
                    "Administration cannot be in the future"
                )
            if lot.expires_at <= now or lot.expires_at <= body.measured_at:
                raise AppError(
                    409, "lot_expired", "Inventory lot expired"
                )
            if body.quantity > lot.quantity:
                raise AppError(
                    409, "insufficient_stock", "Insufficient stock"
                )

            updated = lot.model_dump(mode="json") | {
                "quantity": lot.quantity - body.quantity
            }
            store.put(
                "inventory_lot", lot.lot_id, updated,
                mission_id=lot.mission_id,
                actor_id=actor_id, immutable=False,
            )
            return store.put(
                "medication_administration", body.event_id, payload,
                mission_id=body.mission_id,
                actor_id=actor_id, priority=10,
            )

    return store.put(
        "medication_administration", body.event_id, payload,
        mission_id=body.mission_id,
        actor_id=actor_id, priority=10,
    )

def record_countermeasure(body, store, settings, actor_id):
    guard_source(body.is_synthetic, settings)
    payload = body.model_dump(mode="json") | {
        "actor_id": actor_id,
        "label": (
            "SIMULATED" if body.is_synthetic
            else "RECORDED_COUNTERMEASURE"
        ),
    }
    if store.get("countermeasure", body.event_id) is not None:
        return store.put(
            "countermeasure", body.event_id, payload,
            mission_id=body.mission_id, actor_id=actor_id
        )

    now = datetime.now(timezone.utc)
    if body.measured_at > now or body.received_at > now:
        raise AppError(
            422, "future_countermeasure",
            "Countermeasure cannot be in the future"
        )

    if body.inventory_lot_id:
        lot = store.get("inventory_lot", body.inventory_lot_id)
        if (
            lot is None
            or lot["mission_id"] != body.mission_id
            or lot["is_synthetic"] != body.is_synthetic
            or InventoryLot.model_validate(lot).expires_at <= now
            or lot["quantity"] < 1
        ):
            raise AppError(
                409, "countermeasure_inventory",
                "Linked inventory unavailable or incompatible"
            )

    for event_id in body.measured_observation_ids:
        measurement = store.get("measurement", event_id)
        if (
            measurement is None
            or measurement["mission_id"] != body.mission_id
            or measurement.get("astronaut_id") != body.astronaut_id
            or measurement["is_synthetic"] != body.is_synthetic
        ):
            raise AppError(
                422, "observation_link", "Invalid observation link"
            )

    if body.administration_event_id:
        administration = store.get(
            "medication_administration",
            body.administration_event_id
        )
        if (
            administration is None
            or administration["mission_id"] != body.mission_id
            or administration["astronaut_id"] != body.astronaut_id
            or administration["is_synthetic"] != body.is_synthetic
        ):
            raise AppError(
                422, "administration_link",
                "Invalid administration link"
            )

    return store.put(
        "countermeasure", body.event_id, payload,
        mission_id=body.mission_id, actor_id=actor_id
    )

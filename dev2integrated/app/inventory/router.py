from fastapi import APIRouter, Depends, Query
from app.auth.dependencies import Principal, require
from app.core.dependencies import get_settings, get_store
from app.inventory.models import (
    Administration, CatalogImport, Countermeasure, InventoryLot
)
from app.inventory.service import (
    administer, availability, import_catalog,
    record_countermeasure, save_lot, search_catalog
)

router = APIRouter(tags=["inventory", "catalog"])

@router.get("/conditions")
def conditions(
    q: str = "",
    official_only: bool = False,
    principal: Principal = Depends(require("inventory:read")),
    store=Depends(get_store),
):
    return search_catalog(store, q, official_only)

@router.post("/conditions/import", status_code=201)
def catalog_import(
    body: CatalogImport,
    principal: Principal = Depends(require("inventory:manage")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    if principal.offline and any(
        not entry.is_synthetic for entry in body.entries
    ):
        principal.deny("catalog:offline_verification")
    return {
        "items": import_catalog(
            body, store, settings, principal.user_id
        )
    }

@router.post("/inventory/lots", status_code=201)
def lot_create(
    body: InventoryLot,
    principal: Principal = Depends(require("inventory:manage")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(body.mission_id)
    return save_lot(body, store, settings, principal.user_id)

@router.get("/inventory/lots")
def lots(
    mission_id: str,
    principal: Principal = Depends(require("inventory:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {
        "items": store.list("inventory_lot", mission_id=mission_id)
    }

@router.get("/inventory/availability")
def stock(
    mission_id: str,
    item_id: str,
    quantity: int = Query(1, gt=0),
    principal: Principal = Depends(require("inventory:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return availability(store, mission_id, item_id, quantity)

@router.post("/inventory/administrations", status_code=201)
def administration(
    body: Administration,
    principal: Principal = Depends(require("inventory:manage")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(body.mission_id)
    return administer(body, store, settings, principal.user_id)

@router.get("/inventory/administrations")
def administrations(
    mission_id: str,
    principal: Principal = Depends(require("inventory:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {
        "items": store.list(
            "medication_administration", mission_id=mission_id
        )
    }

@router.post("/countermeasures", status_code=201)
def countermeasure(
    body: Countermeasure,
    principal: Principal = Depends(require("inventory:manage")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(body.mission_id)
    return record_countermeasure(
        body, store, settings, principal.user_id
    )

@router.get("/countermeasures")
def countermeasures(
    mission_id: str,
    principal: Principal = Depends(require("inventory:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {
        "items": store.list("countermeasure", mission_id=mission_id)
    }

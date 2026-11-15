"""Source-safe aggregated reports for developer demonstrations, never patient diagnosis."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import require
from app.core.dependencies import get_store
from app.domain2.contracts import DOMAIN_FIELDS, PRIVATE_DOMAINS
router=APIRouter(prefix="/reports",tags=["Developer 2 reporting prototype"])

@router.get("/summary")
def summary(mission_id:str,principal=Depends(require("foundation:read")),store=Depends(get_store)):
    principal.require_mission(mission_id)
    counts={}
    for domain in DOMAIN_FIELDS:
        if domain in PRIVATE_DOMAINS and not any(r in principal.roles for r in ("admin","flight_surgeon")):
            counts[domain]={"access":"restricted"}
            continue
        items=store.list("dev2_"+domain,mission_id=mission_id)
        counts[domain]={"count":len(items),"simulated":sum(x.get("is_synthetic") is True for x in items),"invalid_or_missing":sum(x.get("quality") in ("INVALID","MISSING","STALE") for x in items)}
    return {"mission_id":mission_id,"domains":counts,"data_classification":"simulated_prototype","clinical_interpretation":False}

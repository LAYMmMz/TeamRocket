from __future__ import annotations

import inspect
import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dev1_bridge import ActorContext, get_actor_context
from app.seed.scenarios import run_scenario
from app.seed.seed_demo import run_seed

router = APIRouter(prefix="/api/simulation", tags=["deterministic simulation"])


class SimulationStartRequest(BaseModel):
    seed: int = 20261115
    profile: str = "baseline"


class ScenarioTriggerRequest(BaseModel):
    scenario_id: str


def _guard_demo_environment(request: Request) -> None:
    settings = getattr(request.app.state, "settings", None)
    raw_env = getattr(
        settings,
        "environment",
        os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "development",
    )
    env = str(raw_env).strip().lower()
    if env not in {"development", "dev", "test", "testing"}:
        raise HTTPException(
            status_code=403,
            detail="Simulation endpoints are strictly disabled outside development/test environments.",
        )


def _invoke_run_scenario(db: Session, scenario_id: str, store: Any) -> Any:
    params = inspect.signature(run_scenario).parameters
    if "shared_store" in params:
        return run_scenario(db, scenario_id, shared_store=store)
    return run_scenario(db, scenario_id)


@router.post("/start")
def simulation_start(
    body: SimulationStartRequest,
    request: Request,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    _guard_demo_environment(request)
    store = getattr(request.app.state, "store", None)
    db.commit()
    manifest = run_seed(db, seed=body.seed, reset=True, profile=body.profile, shared_store=store)
    db.commit()
    return {"status": "started", "manifest": manifest}


@router.post("/scenario")
def simulation_scenario(
    body: ScenarioTriggerRequest,
    request: Request,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    _guard_demo_environment(request)
    store = getattr(request.app.state, "store", None)
    try:
        result = _invoke_run_scenario(db, body.scenario_id.strip().upper(), store)
        db.commit()
        return result
    except (ValueError, KeyError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise


@router.post("/reset")
def simulation_reset(
    request: Request,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    _guard_demo_environment(request)
    store = getattr(request.app.state, "store", None)
    db.commit()
    manifest = run_seed(db, seed=20261115, reset=True, profile="baseline", shared_store=store)
    db.commit()
    return {"status": "reset_complete", "manifest": manifest}
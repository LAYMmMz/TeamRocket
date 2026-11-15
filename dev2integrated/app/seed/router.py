from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.schemas.dev2_schemas import ScenarioRunRequest
from app.seed.scenarios import execute_scenario
from app.seed.seed_demo import seed_baseline_dataset

router = APIRouter(tags=["Deterministic Simulation & Seeding (DEMO-Only)"])


def _guard_demo_environment() -> None:
    if not get_settings().is_demo_or_test_env:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Simulation and reset endpoints are disabled outside development/demo/test environments.",
        )


@router.post("/api/simulation/start")
def simulation_start(
    seed: int = 20261115,
    at_timestamp: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    _guard_demo_environment()
    return seed_baseline_dataset(db=db, seed=seed, reset=True, at_timestamp=at_timestamp)


@router.post("/api/simulation/reset")
def simulation_reset(seed: int = 20261115, db: Session = Depends(get_db)):
    _guard_demo_environment()
    return seed_baseline_dataset(db=db, seed=seed, reset=True)


@router.post("/api/simulation/scenario")
def simulation_scenario(payload: ScenarioRunRequest, db: Session = Depends(get_db)):
    _guard_demo_environment()
    return execute_scenario(
        db=db,
        scenario_id=payload.scenario_id,
        seed=payload.seed,
        at_timestamp=payload.at_timestamp,
    )
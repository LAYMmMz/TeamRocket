from __future__ import annotations

from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development")
    app_name: str = Field(default="NASA Astronaut Health Monitoring API")
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

    # Local offline SQLite database (primary onboard write target)
    sqlite_db_path: str = Field(default="./offline_runtime.db")

    # Cloud Supabase PostgreSQL database (secondary sync target)
    supabase_db_url: str = Field(default="")
    supabase_url: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    supabase_storage_bucket: str = Field(default="medical-artifacts")

    # Deterministic simulation settings
    default_demo_seed: int = Field(default=20261115)

    # Configurable prototype / research-only parameters (T15, T16, T17)
    # Never treated as autonomous flight clearance or universal operational limits without approval.
    gravity_adaptation_window_hours: int = Field(default=72)
    gravity_symptom_cutoff: float = Field(default=3.0)
    gravity_reaction_time_cutoff_ms: float = Field(default=500.0)

    co2_averaging_window_minutes: int = Field(default=60)
    co2_demo_threshold_mmhg: float = Field(default=3.0)

    radiation_career_ref_msv: float = Field(default=600.0)
    radiation_spe_ref_msv: float = Field(default=250.0)
    dosimeter_stale_after_hours: int = Field(default=6)

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_demo_or_test_env(self) -> bool:
        return self.app_env.lower() in {"development", "demo", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
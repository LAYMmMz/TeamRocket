from dataclasses import dataclass, field
import os
from pathlib import Path

def option(name, default="", parser=None):
    def read():
        value = os.getenv(name, default)
        return parser(value) if parser else value
    return field(default_factory=read)

@dataclass
class Settings:
    environment: str = option("APP_ENV", "development")
    sqlite_path: str = option("SQLITE_PATH", "./data/offline.db")
    encryption_key: str | None = option("LOCAL_ENCRYPTION_KEY", None)
    cors_origins: list[str] = option(
        "CORS_ORIGINS", "http://localhost:5173",
        lambda x: [v.strip() for v in x.split(",") if v.strip()]
    )
    auth_issuer: str = option("AUTH_ISSUER")
    auth_audience: str = option("AUTH_AUDIENCE", "authenticated")
    auth_jwks_url: str = option("AUTH_JWKS_URL")
    dev_auth_secret: str = option("DEV_AUTH_SECRET")
    offline_grant_secret: str = option("OFFLINE_GRANT_SECRET")
    offline_grant_max_hours: int = option(
        "OFFLINE_GRANT_MAX_HOURS", "8", int
    )
    allow_demo_rules: bool = option(
        "ALLOW_DEMO_RULES", "false",
        lambda x: x.lower() in {"true", "1", "yes"}
    )
    sync_rpc_url: str = option("SYNC_RPC_URL")
    supabase_url: str = option("SUPABASE_URL")
    supabase_anon_key: str = option("SUPABASE_ANON_KEY")
    sync_access_token: str = option("SYNC_ACCESS_TOKEN")
    sync_max_attempts: int = option("SYNC_MAX_ATTEMPTS", "5", int)
    sync_batch_size: int = option("SYNC_BATCH_SIZE", "50", int)
    sync_interval_seconds: float = option(
        "SYNC_INTERVAL_SECONDS", "5", float
    )
    schema_manifest_path: str = option(
        "SCHEMA_MANIFEST_PATH", "../docs/schema-handoff.json"
    )
    attachments_root: str = option(
        "ATTACHMENTS_ROOT", "./data/attachments"
    )
    max_attachment_bytes: int = 10 * 1024 * 1024

    def validate(self):
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("Invalid APP_ENV")
        if "*" in self.cors_origins:
            raise ValueError("CORS requires explicit origins")
        secrets = [self.dev_auth_secret, self.offline_grant_secret]
        if any(s and len(s) < 32 for s in secrets):
            raise ValueError("Signing secrets require 32+ characters")
        if (
            self.sync_max_attempts < 1
            or not 1 <= self.sync_batch_size <= 500
            or self.sync_interval_seconds <= 0
        ):
            raise ValueError("Invalid sync configuration")
        if not 1 <= self.offline_grant_max_hours <= 24:
            raise ValueError("Offline grant limit must be 1..24 hours")
        if self.environment == "production":
            if not self.encryption_key or not self.offline_grant_secret:
                raise ValueError(
                    "Production requires external encryption and grant keys"
                )
            if self.allow_demo_rules or self.dev_auth_secret:
                raise ValueError(
                    "Development authentication and demo rules "
                    "are disabled in production"
                )
            if (
                not self.auth_issuer.startswith("https://")
                or not self.auth_jwks_url.startswith("https://")
            ):
                raise ValueError("Production requires HTTPS Auth URLs")
            if any(
                not origin.startswith("https://")
                for origin in self.cors_origins
            ):
                raise ValueError("Production CORS requires HTTPS")
        Path(self.sqlite_path).parent.mkdir(
            parents=True, exist_ok=True, mode=0o700
        )

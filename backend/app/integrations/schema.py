import hashlib
import json
from pathlib import Path

FOUNDATION_TABLES = {
    "astronauts", "missions", "mission_crew", "users",
    "roles", "user_role_assignments", "devices", "device_assignments"
}

def inspect_handoff(path):
    file = Path(path)
    if not file.is_file():
        return {
            "ready": False,
            "checks": {"manifest_present": False},
            "blockers": ["Database Team schema handoff not supplied"],
            "live_database_verified": False,
        }
    try:
        manifest = json.loads(file.read_text(encoding="utf-8"))
        tables = manifest.get("tables", [])
        names = [
            table.get("name") for table in tables
            if isinstance(table, dict)
        ]
        migration_hash = manifest.get("migration_sha256", "")
        checks = {
            "schema_version": bool(manifest.get("schema_version")),
            "migration_hash": (
                isinstance(migration_hash, str)
                and len(migration_hash) == 64
                and all(
                    character in "0123456789abcdef"
                    for character in migration_hash
                )
            ),
            "57_unique_cloud_tables": (
                len(names) == 57 and len(set(names)) == 57
            ),
            "foundation_names": FOUNDATION_TABLES.issubset(set(names)),
            "column_dictionary": bool(tables) and all(
                isinstance(table, dict)
                and table.get("columns")
                and table.get("primary_key")
                and "foreign_keys" in table
                for table in tables
            ),
            "rls_evidence": (
                manifest.get("rls_test_status") == "PASS"
                and bool(manifest.get("rls_evidence_reference"))
            ),
            "sqlite_review": (
                manifest.get("sqlite_review_status") == "APPROVED"
            ),
            "receipt_contract": (
                manifest.get("receipt_contract_version") == "1"
            ),
            "reviewer": bool(manifest.get("reviewed_by")),
        }
        return {
            "ready": all(checks.values()),
            "checks": checks,
            "blockers": [
                key for key, value in checks.items() if not value
            ],
            "schema_version": manifest.get("schema_version"),
            "manifest_sha256": hashlib.sha256(
                file.read_bytes()
            ).hexdigest(),
            "live_database_verified": False,
        }
    except (OSError, ValueError, TypeError, AttributeError):
        return {
            "ready": False,
            "checks": {"manifest_valid": False},
            "blockers": ["Invalid Database Team manifest"],
            "live_database_verified": False,
        }

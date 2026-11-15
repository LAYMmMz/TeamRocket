import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

from database import BASE_DIR, get_db

load_dotenv(BASE_DIR / ".env")


def sync_pending_records(batch_size: int = 100):
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        return {
            "connected": False,
            "error": "SUPABASE_URL or SUPABASE_SECRET_KEY missing in backend/.env",
            "synced": 0,
            "failed": 0,
        }

    try:
        client = create_client(url, key)
    except Exception as exc:
        return {
            "connected": False,
            "error": f"Client init failed: {exc}",
            "synced": 0,
            "failed": 0,
        }

    with get_db() as db:
        pending = [
            dict(row)
            for row in db.execute(
                """
                SELECT event_id, target_table, record_id, payload_json, attempts
                FROM sync_outbox
                WHERE state IN ('pending', 'retry')
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (batch_size,),
            ).fetchall()
        ]

    synced = 0
    failed = 0

    for item in pending:
        payload = json.loads(item["payload_json"])
        target_table = item["target_table"]

        try:
            client.table(target_table).upsert(payload, on_conflict="id").execute()

            with get_db() as db:
                db.execute(
                    """
                    UPDATE sync_outbox
                    SET state = 'synced',
                        synced_at = ?,
                        last_error = NULL
                    WHERE event_id = ?
                    """,
                    (datetime.now(timezone.utc).isoformat(), item["event_id"]),
                )
            synced += 1

        except Exception as error:
            next_state = "failed" if item["attempts"] + 1 >= 10 else "retry"
            with get_db() as db:
                db.execute(
                    """
                    UPDATE sync_outbox
                    SET state = ?,
                        attempts = attempts + 1,
                        last_error = ?
                    WHERE event_id = ?
                    """,
                    (next_state, str(error)[:500], item["event_id"]),
                )
            failed += 1

    with get_db() as db:
        remaining = db.execute(
            "SELECT COUNT(*) FROM sync_outbox WHERE state IN ('pending', 'retry')"
        ).fetchone()[0]

    return {
        "connected": failed == 0,
        "synced": synced,
        "failed": failed,
        "pending_remaining": remaining,
    }
import hashlib
from typing import Protocol
import httpx
from app.core.errors import AppError
from app.offline.store import canonical

class ReceiptTransport(Protocol):
    def send(self, event: dict) -> dict:
        ...

class HTTPReceiptTransport:
    def __init__(self, settings):
        self.url = settings.sync_rpc_url
        self.anon_key = settings.supabase_anon_key
        self.access_token = settings.sync_access_token
        if self.url and not self.url.startswith("https://"):
            raise AppError(
                503, "unsafe_cloud_url", "Cloud sync requires HTTPS"
            )

    def send(self, event):
        if not self.url or not self.access_token:
            raise AppError(
                503, "cloud_not_configured", "Cloud not configured"
            )
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if self.anon_key:
            headers["apikey"] = self.anon_key
        with httpx.Client(
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=False
        ) as client:
            response = client.post(
                self.url, json={"p_event": event}, headers=headers
            )
            response.raise_for_status()
            result = response.json()
        if isinstance(result, list) and len(result) == 1:
            result = result[0]
        return result

class SyncWorker:
    def __init__(
        self, store, transport, max_attempts=5, batch_size=50
    ):
        self.store = store
        self.transport = transport
        self.max_attempts = max(1, min(int(max_attempts), 20))
        self.batch_size = max(1, min(int(batch_size), 1000))

    def run_once(self, mission_ids=None):
        delivered = failed = 0
        for _ in range(self.batch_size):
            items = self.store.claim_batch(
                1, mission_ids=mission_ids,
                max_attempts=self.max_attempts
            )
            if not items:
                break
            item = items[0]
            event = {
                "event_id": item["remote_event_id"],
                "kind": item["kind"],
                "record_id": item["record_id"],
                "mission_id": item["mission_id"],
                "payload_hash": item["payload_hash"],
                "payload": item["payload"],
                "audit_event": item["audit_event"],
                "immutable": item["immutable"],
                "previous_hash": item["previous_hash"],
            }
            try:
                receipt = self.transport.send(event)
                if not isinstance(receipt, dict) or (
                    receipt.get("event_id") != event["event_id"]
                    or receipt.get("payload_hash")
                    != event["payload_hash"]
                    or not receipt.get("receipt_id")
                ):
                    raise ValueError("Receipt does not match evidence")
                self.store.mark_synced(
                    item["queue_id"], receipt,
                    expected_attempt=item["attempts"]
                )
                delivered += 1
            except Exception:
                self.store.mark_failed(
                    item["queue_id"], self.max_attempts,
                    "delivery_or_receipt_failed",
                    expected_attempt=item["attempts"],
                )
                failed += 1
        return {
            "delivered": delivered,
            "failed": failed,
            "queue": self.store.queue_status(mission_ids),
        }

class MemoryReceiptTransport:
    def __init__(self):
        self.events = {}
        self.calls = []

    def send(self, event):
        self.calls.append(event["event_id"])
        previous = self.events.get(event["event_id"])
        if previous:
            if previous["payload_hash"] != event["payload_hash"]:
                raise ValueError("Remote event conflict")
            return previous
        receipt = {
            "event_id": event["event_id"],
            "payload_hash": event["payload_hash"],
            "receipt_id": hashlib.sha256(canonical([
                event["event_id"], event["payload_hash"]
            ])).hexdigest(),
        }
        self.events[event["event_id"]] = receipt
        return receipt

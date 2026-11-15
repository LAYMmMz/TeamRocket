# Developer 1 backend

Requires Python 3.12.

From the backend directory:

    python -m pip install -r requirements.txt
    python dev.py

Open http://127.0.0.1:8000/docs.
Use Authorize with the development token printed in the terminal.

Create a fictional mission using POST /api/missions:

    {
      "mission_id": "DEMO-01",
      "name": "Fictional development mission",
      "source_type": "SIMULATED",
      "is_synthetic": true,
      "verification": "UNVERIFIED"
    }

Local encrypted SQLite storage works without Supabase.
No clinical thresholds, approved medical procedures or official catalogs
are supplied.

Supabase configuration belongs in backend/.env when ready:

    SUPABASE_URL=https://YOUR_PROJECT.supabase.co
    SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_ANON_KEY
    AUTH_ISSUER=https://YOUR_PROJECT.supabase.co/auth/v1
    AUTH_JWKS_URL=https://YOUR_PROJECT.supabase.co/auth/v1/.well-known/jwks.json
    AUTH_AUDIENCE=authenticated

Production Auth uses asymmetric RS256/ES256 signing keys.
Never put a service-role key in React.

Cloud sync also requires the Database Team's atomic receipt RPC:

    SYNC_RPC_URL=https://YOUR_PROJECT.supabase.co/rest/v1/YOUR_RECEIPT_RPC
    SYNC_ACCESS_TOKEN=SCOPED_AUTHENTICATED_JWT

The RPC receives {"p_event": {...}} and must atomically authorize the
mission, validate the payload, preserve immutable evidence, write its
audit, and return matching event_id, payload_hash and stable receipt_id.
Identical retries must return the original receipt.
Mutable revisions include a previous_hash and unique transport event ID.
A remote conflict must preserve earlier evidence.

The local queue alone cannot guarantee an exactly-once cloud outcome.

The Database Team owns all 57 cloud tables, migrations and RLS.
The schema handoff manifest deliberately reports not ready until reviewed.
SQLite migrations also require Database Team review.

For production, configure externally managed LOCAL_ENCRYPTION_KEY and
OFFLINE_GRANT_SECRET, HTTPS Auth/CORS, and an encrypted persistent volume.
Remove DEV_AUTH_SECRET and leave ALLOW_DEMO_RULES=false.
Payload encryption alone does not hide SQLite routing metadata.

This paste contains the runnable application source and migrations.
The separate full test suite and Developer 2 domain/scenario implementation
are not included in this generated folder.

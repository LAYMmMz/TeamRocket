"""Static safety assertions for the new clinical migration. Not a live DB test."""
from pathlib import Path
s=(Path(__file__).resolve().parents[1]/'supabase/20261116_03_clinical_sync_records.sql').read_text()
for term in ['ENABLE ROW LEVEL SECURITY','mission_members','auth.uid()','ingest_clinical_sync_event',"'conflict'","'duplicate_ok'",'CONFLICT_REJECTED',"'behavioral_checkins'"]:
 assert term in s,term
for unsafe in ['DROP TABLE','TRUNCATE','CASCADE','SERVICE_ROLE_KEY']:
 assert unsafe not in s,unsafe
print('PASS: SQL static safeguards (NOT live Supabase execution)')

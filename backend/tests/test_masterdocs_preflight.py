"""Schema/feature inventory static check: not a deployed cloud migration test."""
from pathlib import Path
import json
import unittest

class MasterdocsPreflightContract(unittest.TestCase):
    def test_full_canonical_inventory_is_in_read_only_query(self):
        root=Path(__file__).resolve().parents[2]
        spec=json.loads((root/"frontend/src/data/masterdocs.json").read_text(encoding="utf-8"))
        query=(root/"supabase/queries/masterdocs_57_table_preflight.sql").read_text(encoding="utf-8")
        self.assertEqual(len(spec["tables"]),57)
        self.assertEqual(len(spec["scenarios"]),12)
        self.assertEqual(len(spec["features"]),47)
        for table in spec["tables"]:
            self.assertIn("'"+table["name"]+"'",query)
            for column in table["columns"]:
                self.assertIn("'"+column+"'",query)
        self.assertIn("rls_enabled",query)
        self.assertIn("missing_starter_columns",query)
        # SELECT only — no schema changes or data mutations.
        upper=query.upper()
        for keyword in ["CREATE TABLE", "DROP TABLE", "ALTER TABLE",
                        "INSERT INTO", "DELETE FROM", "TRUNCATE", "GRANT "]:
            self.assertNotIn(keyword,upper)

    def test_fresh_schema_draft_has_all_names_rls_and_candidate_fks(self):
        root=Path(__file__).resolve().parents[2]
        spec=json.loads((root/"frontend/src/data/masterdocs.json").read_text(encoding="utf-8"))
        draft=(root/"supabase/manual/20261117_fresh_schema_57_table_DRAFT.sql").read_text(encoding="utf-8")
        self.assertIn("DO NOT APPLY TO TEAMROCKET PRODUCTION",draft)
        self.assertEqual(draft.count("CREATE TABLE IF NOT EXISTS public."),57)
        for table in spec["tables"]:
            self.assertIn('CREATE TABLE IF NOT EXISTS public."'+table["name"]+'"',draft)
            self.assertIn('ALTER TABLE public."'+table["name"]+'" ENABLE ROW LEVEL SECURITY;',draft)
        self.assertGreaterEqual(draft.count('ADD CONSTRAINT "fk_'),45)

    def test_local_scenario_report_does_not_claim_live_acceptance(self):
        root=Path(__file__).resolve().parents[2]
        source=(root/"backend/scripts/masterdocs_scenario_report.py").read_text(encoding="utf-8")
        self.assertIn("LOCAL_TEST_PASSED_CLOUD_UNVERIFIED",source)
        self.assertIn('"live_supabase_verified": False',source)
        self.assertIn('"all_deployed_scenarios_verified": False',source)


if __name__=="__main__":
    unittest.main()

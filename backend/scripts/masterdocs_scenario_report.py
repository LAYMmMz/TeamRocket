"""Scenario evidence matrix: run existing local API tests without implying cloud acceptance.

Run: cd backend && python -m scripts.masterdocs_scenario_report
Generated summary is deliberately a LOCAL-TEST report, not live Supabase evidence.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

SCENARIOS = {f"S{i:02d}": f"test_s{i:02d}_" for i in range(1, 13)}
SCENARIO_CLASS = "AcceptanceTests"


def walk(suite):
    for case in suite:
        if isinstance(case, unittest.TestSuite):
            yield from walk(case)
        else:
            yield case


class Results(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.completed = set()
        self.skipped_ids = set()
        self.failed_ids = set()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.completed.add(test.id())

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.skipped_ids.add(test.id())

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.failed_ids.add(test.id())

    def addError(self, test, err):
        super().addError(test, err)
        self.failed_ids.add(test.id())


def run():
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "tests.test_teamrocket_acceptance"
    )
    ids = [case.id() for case in walk(suite)]
    run_result = unittest.TextTestRunner(
        stream=sys.stderr, verbosity=1, resultclass=Results
    ).run(suite)
    matrix = []
    for scenario, prefix in SCENARIOS.items():
        matches = [testid for testid in ids if testid.split(".")[-1].startswith(prefix)]
        if not matches:
            status = "MISSING_TEST"
        elif any(t in run_result.failed_ids for t in matches):
            status = "FAILED_LOCAL_TEST"
        elif any(t in run_result.skipped_ids for t in matches):
            status = "SKIPPED_LOCAL_TEST"
        elif all(t in run_result.completed for t in matches):
            status = "LOCAL_TEST_PASSED_CLOUD_UNVERIFIED"
        else:
            status = "UNVERIFIED"
        matrix.append({"scenario": scenario, "status": status,
                       "test_ids": matches})
    result = {
        "kind": "LOCAL_UNIT_TEST_EVIDENCE_ONLY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_scenarios": len(matrix),
        "live_supabase_verified": False,
        "actual_cloud_receipts_verified": False,
        "all_deployed_scenarios_verified": False,
        "test_suite_passed": run_result.wasSuccessful(),
        "scenarios": matrix,
    }
    print(json.dumps(result, indent=2))
    return 0 if run_result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run())

"""One-command TeamRocket test runner; writes a readable JSON report.
Run from Developer1_Backend/backend: python run_teamrocket_tests.py
"""
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

class Reporter(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = []

    def _add(self, test, status, details=""):
        self.results.append({"test": str(test), "status": status, "details": details})

    def addSuccess(self, test):
        super().addSuccess(test)
        self._add(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._add(test, "FAIL", self._exc_info_to_string(err, test)[-1500:])

    def addError(self, test, err):
        super().addError(test, err)
        self._add(test, "ERROR", self._exc_info_to_string(err, test)[-1500:])

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._add(test, "BLOCKED", reason)


def main():
    tests = unittest.defaultTestLoader.discover(
        start_dir=str(BASE / "tests"),
        pattern="test_*.py",
        top_level_dir=str(BASE),
    )
    runner = unittest.TextTestRunner(verbosity=2, resultclass=Reporter)
    result = runner.run(tests)
    entries = result.results
    counts = {s: sum(x["status"] == s for x in entries)
              for s in ("PASS", "FAIL", "ERROR", "BLOCKED")}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite": "TeamRocket local backend verification (no live Supabase)",
        "counts": counts,
        "passed": result.wasSuccessful(),
        "complete_acceptance": False,
        "limitations": [
            "Scenario fixture presence is not equivalent to full scenario execution.",
            "S04 and S05 are explicitly blocked by missing workflow implementations.",
            "Other S01-S12 checks are partial behaviors, not end-to-end clinical acceptance.",
            "In-memory transport is not a real Supabase sync or RLS test.",
            "Tests do not verify app deployment, real device ingestion, or browser/UI behavior.",
            "Tests use a disposable encrypted SQLite file; existing data is untouched.",
        ],
        "tests": entries,
    }
    output = BASE / "teamrocket_test_report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nReport saved:", output)
    print("Summary:", counts)
    if result.wasSuccessful():
        print("All executable checks passed; see BLOCKED and limitations before claiming completion.")
    else:
        print("Some executable checks failed. Review the test names and report.")
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())

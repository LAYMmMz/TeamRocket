"""One command: python run_dev2_tests.py. Results saved in dev2_test_report.json.
The HTTP tests use temporary encrypted DBs; no live Supabase or production data.
"""
from pathlib import Path
import unittest,json,sys
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
class CapturingResult(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.entries=[]
    def addSuccess(self,t):super().addSuccess(t);self.entries.append({'test':str(t),'status':'PASS'})
    def addFailure(self,t,e):super().addFailure(t,e);self.entries.append({'test':str(t),'status':'FAIL','details':self._exc_info_to_string(e,t)[-1500:]})
    def addError(self,t,e):super().addError(t,e);self.entries.append({'test':str(t),'status':'ERROR','details':self._exc_info_to_string(e,t)[-1500:]})
    def addSkip(self,t,r):super().addSkip(t,r);self.entries.append({'test':str(t),'status':'BLOCKED','details':r})

def main():
    test_dir=BASE/'tests'
    if not test_dir.is_dir():
        print('ERROR: missing backend/tests folder; copy the whole tests folder from ZIP.');return 2
    (test_dir/'__init__.py').touch(exist_ok=True)
    suite=unittest.defaultTestLoader.discover(start_dir=str(test_dir),pattern='test_dev2_*.py',top_level_dir=str(BASE))
    if suite.countTestCases()==0:
        print('ERROR: no tests found. Check copy location.');return 2
    result=unittest.TextTestRunner(verbosity=2,resultclass=CapturingResult).run(suite)
    counts={s:sum(x['status']==s for x in result.entries) for s in ('PASS','FAIL','ERROR','BLOCKED')}
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'counts':counts,'tests':result.entries,
            'clinical_operational_acceptance':False,'live_supabase_verified':False,
            'notes':['Logic tests run here; API tests run only when installed in existing backend.',
                     'Scenario descriptors/fixtures do not imply S01-S12 are end-to-end verified.',
                     'No claims of operational medical approvals or diagnosis.']}
    (BASE/'dev2_test_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('Saved:',BASE/'dev2_test_report.json')
    return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())

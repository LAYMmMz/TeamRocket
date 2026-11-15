import csv,json,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.schema_audit import audit

def test_audit_detects_missing_contract():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'sample.csv'
        with p.open('w',newline='',encoding='utf8') as f:
            w=csv.writer(f);w.writerow(['table_name','columns']);w.writerow(['missions',json.dumps([{'column':'id','type':'uuid'}])])
        report=audit(p)
        assert report['table_count']==1
        assert any('Receipt contract' in x for x in report['warnings'])
        assert any('DEMO-02' in x for x in report['warnings'])

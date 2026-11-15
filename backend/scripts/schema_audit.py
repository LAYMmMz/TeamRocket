"""Read-only Supabase metadata audit for TeamRocket CSV. No credentials required."""
import argparse,csv,json,sys
from pathlib import Path

EXPECT={
 'missions':{'id':'uuid'},
 'astronauts':{'id':'uuid'},
 'vital_signs':{'id':'bigint','event_id':'text'},
 'health_logs':{'mission_id':'text'},
 'symptom_reports':{'severity':'integer'},
 'alert_rules':{'version':'text','condition_definition':'text'},
 'sync_receipts':{'event_id':'uuid'},
}

def audit(path):
    with open(path,encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if not {'table_name','columns'}.issubset(rows[0] if rows else {}):
        raise ValueError('Expected columns table_name,columns')
    tables={}
    for row in rows:
        cols=json.loads(row['columns'])
        tables[row['table_name']]={c['column']:c for c in cols}
    warnings=[]
    for name,req in EXPECT.items():
        if name not in tables:
            warnings.append(f'MISSING TABLE: {name}')
            continue
        for col,datatype in req.items():
            got=tables[name].get(col,{}).get('type')
            if got!=datatype:
                warnings.append(f'Unexpected {name}.{col}: {got!r}; example CSV had {datatype!r}')
    if len(tables)!=57:warnings.append(f'{len(tables)} exported tables vs PDF 57 logical tables; requires DB-team reconciliation')
    if 'payload_hash' not in tables.get('sync_receipts',{}):warnings.append('Receipt contract missing payload_hash in sync_receipts table; RPC could supply it separately, verify')
    if tables.get('missions',{}).get('id',{}).get('type')=='uuid':warnings.append('Demo mission IDs like DEMO-02 cannot be passed to missions.id uuid without explicit mapping')
    return {'table_count':len(tables),'column_count':sum(map(len,tables.values())),'warnings':warnings,'tables':sorted(tables)}

def main():
    p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    res=audit(a.csv);text=json.dumps(res,indent=2)
    print(text)
    if a.out:a.out.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()

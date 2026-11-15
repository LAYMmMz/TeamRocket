import fs from 'node:fs';
import path from 'node:path';
const base=path.resolve(import.meta.dirname,'..');
const spec=JSON.parse(fs.readFileSync(path.join(base,'src/data/masterdocs.json'),'utf8'));
const requirements={features:47,views:7,domains:12,tables:57,offline_tables:6,scenarios:12,hazards:5};
let problems=0;
for(const [name,count] of Object.entries(requirements)){
 const got=spec[name].length;
 console.log(`${got===count?'PASS':'FAIL'} ${name}: ${got}/${count}`);
 if(got!==count)problems++;
}
for(const [name,items] of Object.entries({features:spec.features,scenarios:spec.scenarios,tables:spec.tables})){
 const key=name==='tables'?'name':'id';const vals=items.map(x=>x[key]);
 if(new Set(vals).size!==vals.length){console.error('FAIL duplicate '+name);problems++}
}
const tableNames=new Set(spec.tables.map(t=>t.name));
for(const d of spec.domains){for(const t of d.tables){if(!tableNames.has(t)){console.error('FAIL unknown canonical table',d.id,t);problems++}}for(const f of d.feature_ids){if(!spec.features.some(x=>x.id===f)){console.error('FAIL unknown feature',d.id,f);problems++}}}
for(const v of spec.views){if(!spec.features.some(f=>f.id===v.feature_id)){console.error('FAIL missing view feature',v);problems++}}
const source=fs.readFileSync(path.join(base,'src/pages/Traceability.tsx'),'utf8');
for(const id of spec.features.map(x=>x.id))if(!source.includes(id+':')&&!source.includes(id+'"')){console.warn('WARN feature fallback missing dedicated table mapping:',id)}
if(problems)process.exit(1);
console.log('PASS scope manifest cross-references. This does NOT validate backend migrations, auth, medical rules, sync, or full build.');

import {useMemo,useState} from 'react';
import {Download,FileJson,Search,ShieldAlert,Trash2} from 'lucide-react';
import spec from '../data/masterdocs.json';
import {Head,Notice,Panel,StatusPill} from '../components/UI';

/** Schema-aware DTO draft tool: intentionally never writes to SQLite or Supabase. */
export function DataIntakePage(){
 const [tableName,setTableName]=useState('vital_signs');
 const [query,setQuery]=useState('');
 const [values,setValues]=useState<Record<string,string>>({});
 const [preview,setPreview]=useState<string|null>(null);
 const [errors,setErrors]=useState<string[]>([]);
 const table=spec.tables.find(t=>t.name===tableName)!;
 const matches=useMemo(()=>spec.tables.filter(t=>(t.name+' '+t.group).toLowerCase().includes(query.toLowerCase())),[query]);
 function openTable(name:string){setTableName(name);setValues({});setPreview(null);setErrors([])}
 function generate(){const missing=table.columns.filter(k=>!values[k]?.trim());setErrors(missing);
  const record:Record<string,unknown>={};
  for(const k of table.columns){const val=values[k]?.trim();if(!val)continue;
   record[k]=k==='value'||k.endsWith('_value')||['quantity','duration','repetitions','dose','sample_size','attempt_count'].includes(k)?Number.isNaN(Number(val))?val:Number(val):val;
  }
  record.is_synthetic=true;
  record.source_type='synthetic';
  record.verification='review-required';
  record._prototype_note='FRONTEND DRAFT ONLY: backend must validate/migrate/authorize. No clinical approval.';
  setPreview(JSON.stringify({table:table.name,draft:record},null,2));
 }
 function download(){if(!preview)return;const blob=new Blob([preview],{type:'application/json'});const link=document.createElement('a');const url=URL.createObjectURL(blob);link.href=url;link.download=`${tableName}-synthetic-draft.json`;link.click();URL.revokeObjectURL(url)}
 return <main className="page"><Head eyebrow="MISSION DATA / SAMPLE RECORDS" title="Record Drafts" description="Prepare sample records using the mission data fields. Drafts can be downloaded for review; they are not saved to crew health records." actions={<StatusPill kind="pending">DRAFT ONLY · NOT SAVED</StatusPill>}/>
 <div className="intake-layout"><Panel title="Choose a data table" sub="MISSION DATA TABLES"><div className="searchbar intake-search"><Search size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search data tables"/></div><div className="table-picker">{matches.map(t=><button key={t.name} className={t.name===tableName?'selected':''} onClick={()=>openTable(t.name)}><span>{t.name}</span><small>{t.group}</small></button>)}</div></Panel>
 <div className="stack"><Panel title={`Draft ${table.name}`} sub="PDF MINIMUM STARTER FIELDS"><div className="record-intake-form">{table.columns.map(k=><label key={k}><span>{k}</span><input value={values[k]??''} onChange={e=>setValues(old=>({...old,[k]:e.target.value}))} placeholder={k.endsWith('_at')?'UTC timestamp (ISO 8601)':k.includes('id')?'UUID / canonical ID':`Value for ${k}`} aria-invalid={errors.includes(k)}/></label>)}<div className="intake-actions"><button className="primary-button" onClick={generate}><FileJson size={15}/> Generate draft JSON</button><button className="small-button" onClick={()=>{setValues({});setErrors([]);setPreview(null)}}><Trash2 size={14}/> Clear form</button></div>{errors.length>0&&<p className="intake-warning">Missing starter fields: {errors.join(', ')}. An incomplete draft can be previewed but is not ready for ingestion.</p>}</div></Panel>
 {preview&&<Panel title="Generated payload" sub="SIMULATED / NOT POSTED"><pre className="json-preview">{preview}</pre><div className="intake-actions"><button className="small-button" onClick={download}><Download size={14}/> Download JSON draft</button></div></Panel>}
 <Notice warning><ShieldAlert size={15}/> This is a development drafting tool, not a clinical record editor. The PDF requires Python Pydantic validation, SQLite commit, secure role checks, approved rule review, and cloud receipt before records count as persisted.</Notice></div></div>
 </main>}

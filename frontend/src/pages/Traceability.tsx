import {Link,useParams} from 'react-router-dom';
import {ArrowRight,BookOpen,CheckCircle2,FlaskConical,LockKeyhole,ShieldAlert} from 'lucide-react';
import spec from '../data/masterdocs.json';
import {Head,Notice,Panel,Stat,StatusPill} from '../components/UI';
import {useMission} from '../app/MissionContext';
import {dashboardCopy,domainLabel} from '../app/labels';
import {domainRecords} from '../lib/demo';

// Canonical associations to the PDF's exact table inventory. No substitute table names.
const mappings:Record<string,string[]>={
 F01:['missions','astronauts','mission_crew'],F02:['users','roles','user_role_assignments'],
 F03:['devices','device_assignments','data_import_batches','attachments'],F04:['vital_signs','data_quality_issues','attachments'],
 F05:['health_baselines'],F06:['symptom_reports'],F07:['alert_rules','health_alerts','alert_evidence'],
 F08:['medical_incidents','incident_events'],F09:['medical_procedures','procedure_steps','recommendation_records'],
 F10:['medical_exam_schedule'],F11:['sync_queue'],F12:['sync_queue','sync_receipts','audit_logs'],
 F13:['vital_signs','ecg_records'],F14:['vital_signs'],F15:['vascular_ultrasound_results','laboratory_results'],
 F16:['gravity_transition_events','functional_assessments'],F17:['functional_assessments'],
 F18:['fitness_assessments'],F19:['exercise_sessions'],F20:['bone_scans','bone_density_results'],
 F21:['ocular_assessments','ocular_results'],F22:['sleep_sessions'],F23:['nutrition_logs','fluid_balance_logs'],
 F24:['behavioral_checkins'],F25:['personal_dose_records','radiation_area_records'],
 F26:['radiation_events'],F27:['environmental_readings'],F28:['environmental_readings'],
 F29:['environmental_samples'],F30:['environmental_lab_results'],F31:['environmental_samples'],
 F32:['biological_samples','clinical_sample_chain'],F33:['laboratory_results','data_import_batches'],
 F34:['laboratory_results'],F35:['sequencing_runs','attachments'],
 F36:['medical_inventory'],F37:['clinical_condition_catalog'],F38:['medical_incidents','incident_events','alert_events'],
 F39:['medical_procedures','procedure_steps'],F40:['missions','astronauts','health_alerts'],
 F41:['vital_signs','ecg_records','symptom_reports','sleep_sessions'],
 F42:['medical_exam_schedule','vascular_ultrasound_results','ocular_results','bone_density_results','fitness_assessments'],
 F43:['personal_dose_records','radiation_events','environmental_readings','environmental_lab_results'],
 F44:['biological_samples','laboratory_results','sequencing_runs'],
 F45:['symptom_reports','behavioral_checkins','functional_assessments'],
 F46:['sync_receipts','medical_incidents','audit_logs'],
 F47:['missions','astronauts','vital_signs','health_alerts','sync_receipts']};
const allNames=new Set(spec.tables.map(t=>t.name));
for(const [feature,arr] of Object.entries(mappings))for(const table of arr)if(!allNames.has(table))throw new Error(`Bad mapping ${feature} → ${table}`);
export const FEATURE_TABLE_MAP=mappings;
export function FeatureDetailPage(){const {featureId}=useParams();const feature=spec.features.find(f=>f.id===featureId);const {role,isDemo}=useMission();if(!feature)return <main className="page"><Head title="Unknown feature" description="This requirement ID is not listed in the current MasterDocs."/></main>;
 const domains=spec.domains.filter(d=>d.feature_ids.includes(feature.id));const view=spec.views.find(v=>v.feature_id===feature.id);const viewCopy=view?dashboardCopy[view.id]:undefined;const tables=mappings[feature.id]??[];
 const restricted=role==='crew'&&[ 'F02','F24','F33','F34','F38','F44','F46'].includes(feature.id);
 return <main className="page"><Head eyebrow={`${feature.id} / ${feature.priority} MISSION FEATURE`} title={viewCopy?.title??feature.title} description="Feature status, related health areas, source data, and completion requirements. This screen does not indicate clinical approval." actions={<Link className="outline-cta" to="/coverage"><ArrowRight size={15}/> All features</Link>}/>
 <div className="overview-stats"><Stat label="FEATURE ID" value={feature.id}/><Stat label="BUILD PRIORITY" value={feature.priority}/><Stat label="CANONICAL TABLES" value={tables.length}/><Stat label="IMPLEMENTATION" value="SCAFFOLD" detail="API/backend integration pending"/></div>
 {restricted&&<Notice warning><LockKeyhole size={14}/> This role's UI preview does not disclose sensitive records. The FastAPI access policy and audit log must also deny an unauthorized request.</Notice>}
 <div className="content-grid"><Panel title="Data model dependencies" sub="CANONICAL SUPABASE TABLE NAMES"><div className="feature-data-list">{tables.map(t=>{const table=spec.tables.find(x=>x.name===t)!;return <Link to={`/data-model?table=${t}`} key={t}><strong>{t}</strong><small>{table.columns.join(' · ')}</small></Link>})}</div><div className="rule-caption">Measurements require measured_at, received_at, quality, verification, source, is_synthetic, and immutable event_id where applicable.</div></Panel>
 <Panel title="In the flight deck" sub="RELATED PAGES"><div className="feature-data-list">{view?<Link to={`/${view.id}`}><strong>{viewCopy?.title??view.name}</strong><small>Open this mission health view</small></Link>:null}{domains.map(d=><Link key={d.id} to={`/domains/${d.id}`}><strong>{domainLabel(d.id,d.name)}</strong><small>{d.inputs}</small></Link>)}<Link to={['F07','F08','F09','F38'].includes(feature.id)?'/cases':['F11','F12','F39'].includes(feature.id)?'/integration':feature.id==='F47'?'/simulation':'/domains'}><strong>Open related work area</strong><small>Health readings · medical alerts · mission scenarios</small></Link></div>{domains.length===0&&!view?<Notice>This feature is supported by shared mission systems. Full data entry depends on the connected mission service.</Notice>:null}</Panel></div>
 <Panel title="Acceptance evidence required for completion" sub="FINAL MASTERDOCS / SECTION 15"><div className="gate-grid">{['Implemented frontend or API code','Validated canonical data contract','Persistent synthetic records','Automated test and replay scenario','Role authorization and audit handling','Deployment and integration documentation'].map((x,i)=><div key={x}><b>0{i+1}</b><strong>{x}</strong><p>{i===0?'Frontend navigation prototype available; backend portion remains to be integrated.':'Evidence must be supplied and tested before this feature can be marked COMPLETE.'}</p></div>)}</div></Panel>
 <Notice warning>Prototype boundaries: no automatic diagnosis, medication selection, EVA clearance, or spacecraft actuation. Unsupported research formulas and unapproved procedures remain review-required.</Notice>
 </main>}
const research=[
 {name:'CHI / TME / QTL / EVAC / LOCL',availability:'FORMULAS NOT IMPLEMENTED',detail:'Store versioned research metric, available inputs, citation, calculation provenance and reviewer. Do not invent an equation.'},
 {name:'IMM / CLiFF condition catalogs',availability:'SOURCE VERIFICATION REQUIRED',detail:'Versioned code/title/provenance importer only. Do not claim all 219 source entries were imported.'},
 {name:'Nuclear radiation / particles',availability:'QUANTITY SPECIFIC',detail:'Record particle species, energy bin, flux/fluence when observed, detector and interval. No unsupported effective dose conversion.'},
 {name:'Shielding / SPE context',availability:'RULE REVIEW REQUIRED',detail:'Shelter and event metadata with evidence timeline. Do not create universal shielding efficiency or triggers.'},
 {name:'Light / noise / microbiology',availability:'METHOD AWARE',detail:'lux, weighted dB(A), CFU/sample denominator and measuring method with time windows.'},
 {name:'MinION sequencing',availability:'RESEARCH-ONLY RECORD',detail:'Sample, run, platform, FASTQ-like path, read count and QC; no autonomous pathogen conclusion.'},
 {name:'Fluids / medication / compression',availability:'AUTHORIZED COUNTERMEASURE',detail:'Ordered record, timing, reviewer, contraindication and inventory; no invented dose/schedule.'},
 {name:'MORD / antimicrobial guidance',availability:'CONTROLLED SOURCE PENDING',detail:'Versioned procedure decision nodes and clinician escalation; no autonomous antibiotic choice.'}
];
export function EvidencePage(){return <main className="page"><Head eyebrow="MISSION REFERENCES / RESEARCH SOURCES" title="Research References" description="Review the research sources behind mission health areas. Imported measurements need a verified source and review record."/>
 <div className="domain-card-grid">{research.map((r,i)=><article className="domain-card" key={r.name}><div className="domain-card-top"><span className="domain-no">RESEARCH {String(i+1).padStart(2,'0')}</span><FlaskConical size={21}/></div><h3>{r.name}</h3><p>{r.detail}</p><div className="domain-foot">{r.availability}</div></article>)}</div>
 <Panel title="Authoritative source candidates" sub="VERIFY REVISION, URL, APPLICABILITY AND REVIEWER"><div className="feature-data-list">{['NASA-STD-3001 Volumes 1 and 2 — verify current mission applicability','NASA Human Research Program risk documentation','NASA medical technical briefs','CSA Bio-Monitor / Bio-Analyzer / ACTIS descriptions','NASA Open Science Data Repository — dataset-specific provenance'].map(s=><div className="source-entry" key={s}><BookOpen size={16}/><div><strong>{s}</strong><small>Metadata required: title · URL · revision/date · page · reviewer · applicability</small></div><StatusPill kind="pending">VERIFY</StatusPill></div>)}</div></Panel>
 <Notice warning>These are research/source categories cited in the PDF, not imported datasets. The attached PDF does not contain actual astronaut physiological measurements; the UI uses synthetic fixtures only.</Notice></main>}

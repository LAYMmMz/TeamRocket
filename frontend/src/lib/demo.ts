import type {Alert,Astronaut,CaseRecord,CommandSnapshot,TrendPoint,Vital} from './types';

const FIXED_NOW='2026-06-15T12:00:00.000Z'; // fixed SIMULATION clock, never live NASA data
export const DEMO_NOW=FIXED_NOW;
export const astronauts:Astronaut[]=[
 {id:'CREW-01',crew_code:'CREW-01',display_name:'Avery Chen',role:'Mission Commander',status:'active'},
 {id:'CREW-02',crew_code:'CREW-02',display_name:'Morgan Reyes',role:'Medical Officer',status:'active'},
 {id:'CREW-03',crew_code:'CREW-03',display_name:'Riley Okafor',role:'Flight Engineer',status:'active'},
 {id:'CREW-04',crew_code:'CREW-04',display_name:'Jordan Park',role:'Science Specialist',status:'active'}
];
const seed=20261115;
function pseudo(i:number) {const x=Math.sin(i*127.1 + seed*0.00001)*43758.5453;return x-Math.floor(x)}
function idCode(s:string,i:number) {return `${s.toLowerCase()}-demo-${i.toString().padStart(5,'0')}`}
// 30-day, four-crew deterministic synthetic dataset. No thresholds or clinical claims.
export function generateVitals():Vital[]{
 const out:Vital[]=[]; let n=0;
 for(let a=0;a<4;a++) for(let d=0;d<30;d++) for(let h=0;h<24;h++){
  const timestamp=new Date(Date.parse(FIXED_NOW)-(29-d)*86400000-(23-h)*3600000).toISOString();
  const vals:[string,number,string,number][]=[['HR',Math.round(71+pseudo(a*50000+d*900+h*9)*14+(h>=9&&h<=11?6:0)),'bpm',74],['SpO2',Math.round((96.8+pseudo(a*50000+d*900+h*9+1)*2.1)*10)/10,'%',98],['RR',Math.round(12+pseudo(a*50000+d*900+h*9+2)*6),'breaths/min',15]];
  for(const [metric_code,value,unit,baseline] of vals){n++;out.push({id:idCode('vital',n),event_id:idCode('event',n),astronaut_id:astronauts[a].id,metric_code,value,unit,baseline,measured_at:timestamp,received_at:timestamp,source_device_id:'DEVICE-01',quality:'ok',verification:'verified-demo',is_synthetic:true,source_type:'synthetic'});}
 }
 // 4 crew × 30 days × 2 BP readings/day = 240 readings
 for(let a=0;a<4;a++)for(let d=0;d<30;d++)for(let r=0;r<2;r++){
  const timestamp=new Date(Date.parse(FIXED_NOW)-(29-d)*86400000-(r?6:18)*3600000).toISOString();
  n++;out.push({id:idCode('vital',n),event_id:idCode('event',n),astronaut_id:astronauts[a].id,metric_code:'BP_SYS',value:Math.round(111+pseudo(a*40000+d*12+r)*14),unit:'mmHg',baseline:118,measured_at:timestamp,received_at:timestamp,source_device_id:'DEVICE-02',quality:'ok',verification:'verified-demo',is_synthetic:true,source_type:'synthetic'});
 }
 return out;
}
export const vitals=generateVitals();
export function latestVitals(crewId:string,scenario:string):Vital[]{
 const filtered=vitals.filter(v=>v.astronaut_id===crewId);
 const keys=['HR','SpO2','RR','BP_SYS'];
 return keys.map(k=>{
  const v=filtered.filter(v=>v.metric_code===k).at(-1)!;
  if(scenario==='S03'&&k==='SpO2')return {...v,value:null,quality:'missing' as const,verification:'missing' as const,source_device_id:null};
  if(scenario==='S02'&&k==='HR')return {...v,value:118};
  return v;
 });
}
export function trend(crewId:string,scenario:string):TrendPoint[]{
 const byTime=new Map<string,TrendPoint>();
 const recent=vitals.filter(v=>v.astronaut_id===crewId&&['HR','SpO2','RR'].includes(v.metric_code)).slice(-72);
 for(const v of recent){const key=v.measured_at;let point=byTime.get(key);if(!point){point={timestamp:key,label:new Date(key).toLocaleTimeString('en-US',{timeZone:'UTC',hour:'2-digit',minute:'2-digit'}),HR:null,SpO2:null,RR:null};byTime.set(key,point)}
  if(v.metric_code==='HR')point.HR=v.value;
  if(v.metric_code==='SpO2')point.SpO2=v.value;
  if(v.metric_code==='RR')point.RR=v.value;
 }
 const points=Array.from(byTime.values());
 if(scenario==='S03'&&points.length)points[points.length-1].SpO2=null;
 if(scenario==='S02'&&points.length)points[points.length-1].HR=118;
 return points;
}
const baseAlerts:Alert[]=[{id:'ALT-001',event_id:'EVT-ALERT-001',astronaut_id:'CREW-01',title:'OCT follow-up examination due',severity:'informational',status:'open',rule_id:'DEMO-SCHEDULE-01',rule_version:'1.0-demo',approval_status:'approved-demo',evidence:['medical_exam_schedule:EXAM-008'],created_at:FIXED_NOW,clinician_acknowledged_at:null,is_synthetic:true}];
export function scenarioAlerts(scenario:string):Alert[]{
 if(scenario==='S01'||scenario==='S02')return [];
 const mapping:Record<string,[string,Alert['severity'],string[],Alert['approval_status']]>={
 S03:['Serious breathing symptom — SpO₂ unavailable','critical',['symptom_reports:SYM-S03','vital_signs:missing-SpO2'],'approved-demo'],
 S04:['Habitat CO₂ interval and headache linked for review','warning',['environmental_readings:ENV-S04','symptom_reports:SYM-S04'],'approved-demo'],
 S05:['D-dimer pending clinical review','advisory',['laboratory_results:LAB-S05'],'unapproved'],
 S06:['Left jugular report requires clinician review','advisory',['vascular_ultrasound_results:VAS-S06'],'approved-demo'],
 S07:['Solar particle event — dosimeter stale','warning',['radiation_events:RAD-S07','personal_dose_records:DOSE-S07'],'approved-demo'],
 S08:['OCT follow-up due; in-flight DXA unavailable','informational',['medical_exam_schedule:EXAM-S08','bone_scans:missing-inflight'],'approved-demo'],
 S09:['Water culture flagged — re-sampling review','advisory',['environmental_lab_results:WATER-S09'],'approved-demo'],
 S10:['Offline sync event pending receipt','informational',['sync_queue:QUEUE-S10'],'approved-demo'],
 S11:['Expired clinical reference — operational guidance blocked','data-unavailable',['medical_procedures:PROC-S11'],'expired'],
 S12:['Confidential check-in access denied (backend must audit)','warning',['audit_logs:AUDIT-S12'],'none']};
 const entry=mapping[scenario]; if(!entry)return baseAlerts;
 return [{id:`ALT-${scenario}`,event_id:`EVT-ALERT-${scenario}`,astronaut_id:scenario==='S04'||scenario==='S09'?null:'CREW-01',title:entry[0],severity:entry[1],status:'open',rule_id:scenario==='S11'?'UNAPPROVED-RULE':'DEMO-RULE-'+scenario,rule_version:'1.0-demo',approval_status:entry[3],evidence:entry[2],created_at:FIXED_NOW,clinician_acknowledged_at:null,is_synthetic:true},...baseAlerts];
}
export function getSnapshot(crewId:string,scenario:string):CommandSnapshot {return {mission_id:'DEMO-01',mission_phase:'IN-FLIGHT / SYNTHETIC',mission_day:64,timestamp:FIXED_NOW,crew:astronauts,vitals:latestVitals(crewId,scenario),alerts:scenarioAlerts(scenario),exam_backlog:3,sync_state:scenario==='S10'?'offline':'connected',devices_online:scenario==='S07'?8:10,devices_total:12}}
const valueByDomain:Record<string,[string,string,string,string,string][]>={
 cardiorespiratory:[['Heart rate','72','bpm','vital_signs','Hourly synthetic record'],['SpO₂','98','%','vital_signs','S03 demonstrates missing value'],['Respiratory rate','15','breaths/min','vital_signs','Measurement method preserved'],['ECG report','Review pending','—','ecg_records','Waveform reference in protected Storage'],['Blood pressure','118','mmHg','vital_signs','BP systolic fixture only']],
 vascular:[['D-dimer result','Review required','—','laboratory_results','Assay method and verification required'],['Doppler observation','Left jugular','—','vascular_ultrasound_results','Side-specific; clinician review'],['Clinical symptoms','None recorded','—','symptom_reports','No auto thrombosis diagnosis']],
 radiation:[['Personal dosimeter','0.18','mSv','personal_dose_records','Synthetic example dose quantity'],['Area radiation','Not available','—','radiation_area_records','Source-specific and unit-aware'],['SPE context','Simulation event','—','radiation_events','No dose conversion without coefficients'],['Dosimeter freshness','Stale in S07','—','devices','Quality not normal']],
 gravity:[['Gravity transition','1.0 → 0.0','g','gravity_transition_events','Scenario timeline'],['Balance test','Review required','—','functional_assessments','Protocol mandatory'],['Nausea report','None recorded','—','symptom_reports','No autonomous EVA clearance']],
 fitness:[['Aerobic fitness test','Pending','—','fitness_assessments','VO₂peak protocol identified'],['Exercise sessions','120','target rows','exercise_sessions','30-day target fixture'],['Workload','Method-specific','—','exercise_sessions','Adherence separate from outcome']],
 bone:[['DXA (preflight)','Report available','—','bone_scans','Preflight source only'],['DXA (inflight)','Not measured','—','bone_scans','Never invent in-flight BMD'],['Region comparison','Review required','—','bone_density_results','Compare same bone site/region']],
 vision:[['OCT follow-up','Due','—','medical_exam_schedule','S08 scenario'],['Left eye result','Pending review','—','ocular_results','Per-eye measured record'],['Right eye result','Pending review','—','ocular_results','Separate right eye interpretation']],
 immune:[['Biological samples','24','target rows','biological_samples','Custody chain tracked'],['Lab results','32','target rows','laboratory_results','Assay verification required'],['Immune score','Not inferred','—','laboratory_results','No derived immune score']],
 sleep:[['Sleep sessions','120','target rows','sleep_sessions','Source and start/end required'],['Fatigue check-in','Restricted','—','behavioral_checkins','Visibility classification enforced on backend'],['Actigraphy','Not connected','—','sleep_sessions','No fabricated sensor signal']],
 cabin:[['Habitat CO₂','Sample due','—','environmental_readings','Averaging window/unit needed'],['Cabin pressure','Available in demo','—','environmental_readings','Location-specific'],['Lighting','Pending','lux','environmental_readings','Location and duration'],['Noise','Pending','dB(A)','environmental_readings','Weighting/duration required']],
 microbiology:[['Water culture','Review required','CFU / method','environmental_lab_results','S09 method-specific flag'],['Surface sample','Collected','—','environmental_samples','Sampling source & location'],['Sequencing run','QC pending','—','sequencing_runs','No autonomous pathogen diagnosis']],
 medicalops:[['Incident register','8','target rows','medical_incidents','Synthetic incidents'],['Guidance library','8','demo procedures','medical_procedures','Not official NASA approved'],['Medical inventory','12','target items','medical_inventory','Expiry and location'],['Condition catalog','20','demo entries','clinical_condition_catalog','IMM / CLiFF not claimed imported']]
};
export function domainRecords(domainId:string):CaseRecord[]{return (valueByDomain[domainId]??[]).map((tuple,i)=>({id:`${domainId.toUpperCase()}-${i+1}`,label:tuple[0],value:tuple[1],unit:tuple[2],record_table:tuple[3],details:tuple[4],source:`DEMO-01 · ${tuple[3]}`,quality:tuple[1].toLowerCase().includes('pending')||tuple[1].toLowerCase().includes('review')?'review-required':'verified-demo',measured_at:FIXED_NOW,is_synthetic:true}))}

import {getAccessToken} from './auth';
import type {Alert,CaseRecord,CommandSnapshot,TrendPoint} from './types';

export const dataMode: 'demo'|'api' = import.meta.env.VITE_DATA_MODE === 'api' ? 'api':'demo';
const root=(import.meta.env.VITE_API_BASE_URL||(import.meta.env.DEV?'http://localhost:8000/api/v1':'/api/v1')).replace(/\/$/,'');
// Register the Supabase Auth token provider from your authentication module; keep tokens out of URLs.
let accessTokenProvider:()=>Promise<string|null>=getAccessToken;
export function configureAuthTokenProvider(fn:()=>Promise<string|null>){accessTokenProvider=fn;}

/** Transport ONLY. FastAPI handles authorization, SQLite persistence, rules and Supabase sync. */
export async function request<T>(path:string,opts:RequestInit={}):Promise<T>{
 const token=await accessTokenProvider();
 const response=await fetch(`${root}${path}`,{...opts,headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`} : {}),...opts.headers}});
 if(!response.ok){let message=`HTTP ${response.status}`;try{const json=await response.json();message=json.detail||json.message||message}catch{}throw new Error(message)}
 return response.json() as Promise<T>;
}
// These are PROPOSED concrete contracts under the PDF's logical API families.
// Backend must implement/document them in FastAPI OpenAPI. No direct browser SQLite/Supabase SQL.
export const api={
 command:(missionId:string,crewId:string)=>request<CommandSnapshot>(`/missions/${encodeURIComponent(missionId)}/command?astronaut_id=${encodeURIComponent(crewId)}`),
 trends:(crewId:string)=>request<TrendPoint[]>(`/measurements/trends?astronaut_id=${encodeURIComponent(crewId)}&hours=24`),
 domain:(domainId:string,crewId:string)=>request<CaseRecord[]>(`/reports/domains/${encodeURIComponent(domainId)}?astronaut_id=${encodeURIComponent(crewId)}`),
 acknowledge:(alertId:string)=>request<Alert>(`/alerts/${encodeURIComponent(alertId)}/acknowledgments`,{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({action:'acknowledge'})}),
 symptom:(body:{astronaut_id:string;symptom_code:string;severity:string;notes:string;event_id:string})=>request<unknown>('/symptoms',{method:'POST',headers:{'Idempotency-Key':body.event_id},body:JSON.stringify({...body,is_synthetic:true})}),
 sync:()=>request<{queue_depth:number;last_receipt_at:string|null;state:string}>('/sync/status'),
 createSyntheticMeasurement:(eventId:string,measuredAt:string)=>request<{measurement:{event_id:string;mission_id:string;is_synthetic:boolean}}>(
   '/measurements',{method:'POST',headers:{'Idempotency-Key':eventId},
   body:JSON.stringify({
     event_id:eventId,mission_id:'DEMO-01',astronaut_id:'CREW-01',
     metric:'heart_rate',value:72,unit:'bpm',
     source_type:'SIMULATED',is_synthetic:true,measured_at:measuredAt,
     quality:'VALID',verification:'UNVERIFIED',
     source_reference:'rocketpulse-end-to-end-test',source_revision:'v1'
   })}),
 runSync:(missionId:string)=>request<{
   delivered:number;failed:number;queue:{counts:Record<string,number>}
 }>(`/sync/run?mission_id=${encodeURIComponent(missionId)}`,{method:'POST'})
};

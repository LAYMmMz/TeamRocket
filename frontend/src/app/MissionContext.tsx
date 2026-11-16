import {createContext,useCallback,useContext,useEffect,useMemo,useState} from 'react';
import type {ReactNode} from 'react';
import {api,dataMode} from '../lib/api';
import {astronauts,getSnapshot,scenarioAlerts,trend} from '../lib/demo';
import type {Alert,CommandSnapshot,Role,TrendPoint} from '../lib/types';

const DEFAULT_MODULES=['command','individual','examinations','environment','laboratory','crew','ground','domains','cases','simulation','data-model','integration','evidence','data-intake','explorer'];
interface ContextValue{
 astronautId:string;setAstronautId:(v:string)=>void; role:Role;setRole:(v:Role)=>void; scenario:string;setScenario:(v:string)=>void;
 snapshot:CommandSnapshot;trends:TrendPoint[];alerts:Alert[];is3D:boolean;set3D:(v:boolean)=>void;
 isDemo:boolean; apiError:string|null;refresh:()=>void;acknowledge:(id:string)=>Promise<void>;
 enabledModules:string[];toggleModule:(id:string)=>void; simulatedDisconnected:boolean;setSimulatedDisconnected:(b:boolean)=>void;
}
const MissionContext=createContext<ContextValue|null>(null);
export function MissionProvider({children}:{children:ReactNode}){
 const [astronautId,setAstronautId]=useState('CREW-01');
 const [role,setRole]=useState<Role>('crew_medical_officer');
 const [scenario,setScenario]=useState('S04');
 const [simulatedDisconnected,setSimulatedDisconnected]=useState(false);
 const [enabledModules,setEnabledModules]=useState<string[]>(()=>{try{const value=localStorage.getItem('astrovitals-modules');return value?JSON.parse(value) as string[]:DEFAULT_MODULES}catch{return DEFAULT_MODULES}});
 const [is3D,set3D]=useState(true);
 const [acknowledged,setAcknowledged]=useState<string[]>([]);
 const [remote,setRemote]=useState<CommandSnapshot|null>(null);
 const [remoteTrends,setRemoteTrends]=useState<TrendPoint[]>([]);
 const [apiError,setApiError]=useState<string|null>(null);
 const [tick,setTick]=useState(0);
 useEffect(()=>{const update=()=>setTick(v=>v+1);window.addEventListener('rocketpulse-auth-changed',update);return()=>window.removeEventListener('rocketpulse-auth-changed',update)},[]);
 const isDemo=dataMode==='demo';
 useEffect(()=>{localStorage.setItem('astrovitals-modules',JSON.stringify(enabledModules))},[enabledModules]);
 useEffect(()=>{if(isDemo)return;let cancelled=false; const load=async()=>{
  try{const [snapshot,points]=await Promise.all([api.command('DEMO-01',astronautId),api.trends(astronautId)]);if(!cancelled){setRemote(snapshot);setRemoteTrends(points);setApiError(null)}}
  catch(err){if(!cancelled){setApiError(err instanceof Error?err.message:'API connection failed');setRemote(null);setRemoteTrends([])}}};
  void load();const t=setInterval(()=>void load(),15000);return()=>{cancelled=true;clearInterval(t)}
 },[astronautId,isDemo,tick]);
 const snapshot=useMemo(()=>remote??(isDemo?getSnapshot(astronautId,scenario):{...getSnapshot(astronautId,'S01'),vitals:[],alerts:[],crew:[],exam_backlog:0,devices_online:0,devices_total:0,sync_state:'offline' as const}),[remote,isDemo,astronautId,scenario]);
 const trends=useMemo(()=>isDemo?trend(astronautId,scenario):remoteTrends,[isDemo,astronautId,scenario,remoteTrends]);
 const alerts=useMemo(()=>{const source=isDemo?scenarioAlerts(scenario):snapshot.alerts;return source.map(a=>acknowledged.includes(a.id)?{...a,status:'acknowledged' as const,clinician_acknowledged_at:new Date().toISOString()}:a)},[isDemo,scenario,snapshot.alerts,acknowledged]);
 const refresh=useCallback(()=>setTick(v=>v+1),[]);
 const acknowledge=useCallback(async(id:string)=>{if(!isDemo)await api.acknowledge(id);setAcknowledged(prev=>prev.includes(id)?prev:[...prev,id]);},[isDemo]);
 const toggleModule=(id:string)=>setEnabledModules(v=>v.includes(id)?v.filter(x=>x!==id):[...v,id]);
 const value={astronautId,setAstronautId,role,setRole,scenario,setScenario,snapshot,trends,alerts,is3D,set3D,isDemo,apiError,refresh,acknowledge,enabledModules,toggleModule,simulatedDisconnected,setSimulatedDisconnected};
 return <MissionContext.Provider value={value}>{children}</MissionContext.Provider>
}
export function useMission(){const value=useContext(MissionContext);if(!value)throw new Error('useMission must be within MissionProvider');return value}
export const ROLES:{id:Role;label:string}[]=[{id:'crew',label:'Crew'}, {id:'crew_medical_officer',label:'Crew Medical Officer'},{id:'ground_clinician',label:'Ground Clinician'},{id:'mission_operator',label:'Mission Operator'},{id:'administrator',label:'Administrator'}];
export const LOCAL_CREW=astronauts;

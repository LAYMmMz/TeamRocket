import {useEffect,useState} from 'react';
import {useMission} from './MissionContext';
import {api} from '../lib/api';
import {supportedObservations} from '../lib/observations';
import type {CaseRecord} from '../lib/types';

// Scenario definitions are specifications, NOT executed clinical test results.
// Only these publicly releasable domains may supply linked synthetic evidence.
// S10–S12 need protected sync/audit/procedure evidence, so no public data is inferred.
export const SCENARIO_EVIDENCE_DOMAINS:Record<string,readonly string[]>={
 S01:['cardiorespiratory','cabin'],
 S02:['cardiorespiratory','fitness'],
 S03:['cardiorespiratory'],
 S04:['cabin','medicalops'],
 S05:['vascular'],
 S06:['vascular'],
 S07:['radiation'],
 S08:['vision','bone'],
 S09:['microbiology'],
 S10:[],
 S11:[],
 S12:[]
};
export interface ScenarioEvidenceGroup {domainId:string;records:CaseRecord[]}
interface EvidenceState {key:string;groups:ScenarioEvidenceGroup[];loading:boolean;error:string|null}

// The existing FastAPI /reports/domains endpoint reads Supabase's isolated
// approved synthetic feed in public mode, and authorized records in API mode.
// Abort and key every request by scenario + crew to prevent stale cross-crew UI.
export function useScenarioEvidence(scenarioId:string){
 const {astronautId,isDemo}=useMission();
 const key=scenarioId+':'+astronautId+':'+(isDemo?'demo':'database');
 const [state,setState]=useState<EvidenceState>({key:'',groups:[],loading:true,error:null});
 useEffect(()=>{
  const controller=new AbortController();
  const domains=SCENARIO_EVIDENCE_DOMAINS[scenarioId]??[];
  if(isDemo||domains.length===0){
   setState({key,groups:[],loading:false,error:null});
   return ()=>controller.abort();
  }
  setState({key,groups:[],loading:true,error:null});
  void Promise.all(domains.map(async domainId=>({
   domainId,
   records:supportedObservations(await api.domain(domainId,astronautId,controller.signal))
  }))).then(groups=>{
   if(!controller.signal.aborted)setState({key,groups,loading:false,error:null});
  }).catch(err=>{
   if(!controller.signal.aborted)setState({
    key,groups:[],loading:false,
    error:err instanceof Error?err.message:'Database evidence unavailable'
   });
  });
  return ()=>controller.abort();
 },[key,scenarioId,astronautId,isDemo]);
 return state.key===key?state:{key,groups:[],loading:true,error:null};
}

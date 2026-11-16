import {useEffect,useState} from 'react';
import {useMission} from './MissionContext';
import {api} from '../lib/api';
import {domainRecords} from '../lib/demo';
import {supportedObservations} from '../lib/observations';
import type {CaseRecord} from '../lib/types';

export function useDomainRecords(domainId:string){
 const {astronautId,isDemo}=useMission();
 const key=astronautId+':'+domainId;
 const [state,setState]=useState<{key:string;records:CaseRecord[];loading:boolean;error:string|null}>({key:'',records:[],loading:true,error:null});
 useEffect(()=>{
  const controller=new AbortController();
  setState({key,records:[],loading:true,error:null});
  if(isDemo){setState({key,records:domainRecords(domainId),loading:false,error:null});return()=>controller.abort();}
  api.domain(domainId,astronautId,controller.signal).then(records=>{
   if(!controller.signal.aborted)setState({key,records:supportedObservations(records),loading:false,error:null});
  }).catch(error=>{
   if(!controller.signal.aborted)setState({key,records:[],loading:false,error:error instanceof Error?error.message:'Database request failed'});
  });
  return()=>controller.abort();
 },[key,domainId,astronautId,isDemo]);
 // Never display the previous crew's records during a selection change.
 return state.key===key?state:{key,records:[],loading:true,error:null};
}

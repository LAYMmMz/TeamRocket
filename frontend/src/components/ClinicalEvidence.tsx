import {useEffect,useState} from 'react';
import {useMission} from '../app/MissionContext';
import {api,dataMode} from '../lib/api';
import type {CaseRecord} from '../lib/types';
import {Notice,Panel,RecordTable} from './UI';

/** Clinician-only SQLite research evidence; never mislabel as public Supabase data. */
export function ClinicalEvidence({kind}:{kind:'examinations'|'laboratory'}){
 const {astronautId}=useMission();
 const [records,setRecords]=useState<CaseRecord[]>([]);
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState<string|null>(null);
 useEffect(()=>{
  setRecords([]);setError(null);
  if(dataMode!=='api'){setLoading(false);return}
  const controller=new AbortController();
  setLoading(true);
  const request=kind==='examinations'
    ?api.examinationEvidence(astronautId,controller.signal)
    :api.laboratoryEvidence(astronautId,controller.signal);
  void request.then(rows=>{if(!controller.signal.aborted)setRecords(rows)})
    .catch(err=>{if(!controller.signal.aborted)setError(err instanceof Error?err.message:'Request failed')})
    .finally(()=>{if(!controller.signal.aborted)setLoading(false)});
  return ()=>controller.abort();
 },[astronautId,kind]);
 return <Panel title={kind==='examinations'?'Clinical examination evidence':'Laboratory and specimen evidence'}
  sub="LOCAL DEV2 SYNTHETIC / CLINICIAN AUTHORIZATION REQUIRED">
  {dataMode==='public'?<Notice>Clinical examinations and laboratory source records are protected and are not available in the public Supabase sample feed. No normal results are implied.</Notice>
    :dataMode==='demo'?<Notice>Browser demonstration mode has no persisted clinical evidence. Use an authorized API session to inspect synthetic local records.</Notice>
    :loading?<p role="status">Loading clinical evidence for selected crew…</p>
    :error?<Notice warning>Clinical evidence unavailable: {error}. No records were substituted.</Notice>
    :records.length===0?<Notice>No persisted eligible synthetic records for this crew in the local clinical SQLite store. This does not mean normal.</Notice>
    :<><Notice>Evidence from local synthetic SQLite, not an independently verified Supabase clinical record. Assay methods, eye/side/region, review status and source timestamps are preserved.</Notice><RecordTable records={records}/></>}
 </Panel>
}

import {createContext,useCallback,useContext,useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import {api,dataMode} from '../lib/api';
import {hasSession} from '../lib/auth';

type SyncMode='demo'|'signed-out'|'ready'|'running'|'delivered'|'blocked'|'error';
type SyncState={
  mode:SyncMode;
  lastAttempt:string|null;
  lastDelivery:string|null;
  delivered:number;
  failed:number;
  pending:number|null;
  message:string;
};
type AutoSyncValue=SyncState&{runNow:()=>void;intervalSeconds:number};
const initial:SyncState={
  mode:dataMode==='demo'?'demo':'signed-out',
  lastAttempt:null,lastDelivery:null,delivered:0,failed:0,pending:null,
  message:dataMode==='demo'?'Offline synthetic demonstration':'Sign in to activate session-based sync',
};
const context=createContext<AutoSyncValue|null>(null);
const intervalMs=45000;

/**
 * Automatic mission-scoped sync is driven only by the current authorized
 * browser session. No long-lived JWT is persisted on Railway. The endpoint
 * enforces signed Supabase JWTs, sync:manage and DEMO-01 mission access.
 *
 * This is not a headless 24/7 worker: closing the browser stops scheduled
 * attempts; queued records stay in durable SQLite for the next authorized
 * session. Never claim cloud delivery without a matching RPC receipt.
 */
export function AutoSyncProvider({children}:{children:ReactNode}){
  const [state,setState]=useState<SyncState>(initial);
  const [signedIn,setSignedIn]=useState(()=>dataMode==='api'&&hasSession());
  const running=useRef(false);
  const blocked=useRef(false);
  const mounted=useRef(true);

  const run=useCallback(async()=>{
    if(dataMode!=='api'||!hasSession()||blocked.current||running.current){
      return;
    }
    running.current=true;
    const attempt=new Date().toISOString();
    setState(prev=>({...prev,mode:'running',lastAttempt:attempt,message:'Checking mission outbox'}));
    try{
      const result=await api.runSync('DEMO-01');
      const counts=result.queue?.counts||{};
      const pending=(counts.pending||0)+(counts.retry||0)+(counts.sending||0);
      if(mounted.current)setState(prev=>({
        ...prev,mode:result.delivered>0?'delivered':result.failed>0?'error':'ready',
        delivered:prev.delivered+result.delivered,
        failed:prev.failed+result.failed,
        pending,
        lastDelivery:result.delivered>0?new Date().toISOString():prev.lastDelivery,
        message:result.failed>0
          ?'Some records could not be confirmed by Supabase; inspect sync receipts'
          :result.delivered>0
            ?`${result.delivered} record(s) delivered with matching receipts`
            :'No new cloud receipts; awaiting compatible queued records',
      }));
    }catch(err){
      const msg=err instanceof Error?err.message:String(err);
      const forbidden=/HTTP (401|403)|forbidden|invalid_session|cloud_session_required/i.test(msg);
      // Stop repeated requests if the current account lacks sync permission.
      if(forbidden)blocked.current=true;
      if(mounted.current)setState(prev=>({
        ...prev,mode:forbidden?'blocked':'error',
        message:forbidden
          ?'This account cannot synchronize. Requires a signed-in mission admin or flight surgeon.'
          :`Sync attempt failed: ${msg}`,
      }));
    }finally{running.current=false;}
  },[]);

  useEffect(()=>{
    mounted.current=true;
    const changed=()=>{
      blocked.current=false;
      const active=hasSession();
      setSignedIn(active);
      setState(prev=>({...prev,mode:active?'ready':'signed-out',
        message:active?'Authenticated session ready':'Sign in to activate session-based sync'}));
    };
    window.addEventListener('rocketpulse-auth-changed',changed);
    return()=>{mounted.current=false;window.removeEventListener('rocketpulse-auth-changed',changed);};
  },[]);

  useEffect(()=>{
    if(dataMode!=='api'||!signedIn)return;
    // Run after login and periodically while the dashboard remains open.
    void run();
    const timer=window.setInterval(()=>void run(),intervalMs);
    return()=>window.clearInterval(timer);
  },[signedIn,run]);

  const runNow=useCallback(()=>{void run();},[run]);
  return <context.Provider value={{...state,runNow,intervalSeconds:intervalMs/1000}}>
    {children}
  </context.Provider>;
}
export function useAutoSync(){
  const state=useContext(context);
  if(!state)throw new Error('useAutoSync requires AutoSyncProvider');
  return state;
}

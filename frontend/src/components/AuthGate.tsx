import {useEffect,useState} from 'react';
import type {ReactNode} from 'react';
import {authConfigured,hasSession,signIn,signOut} from '../lib/auth';

export function AuthGate({children}:{children:ReactNode}){
 const [authorized,setAuthorized]=useState(hasSession);
 const [email,setEmail]=useState('');
 const [password,setPassword]=useState('');
 const [message,setMessage]=useState('');
 const [busy,setBusy]=useState(false);
 useEffect(()=>{
  const update=()=>setAuthorized(hasSession());
  window.addEventListener('rocketpulse-auth-changed',update);
  return()=>window.removeEventListener('rocketpulse-auth-changed',update);
 },[]);
 if(authorized)return <>{children}</>;
 return <main style={{minHeight:'100vh',display:'grid',placeItems:'center',background:'#07080A',color:'#C7BFAF',padding:24}}>
  <section style={{width:'min(440px,100%)',border:'1px solid #304E58',borderRadius:18,padding:28,background:'#11191d'}}>
   <h1 style={{fontSize:30,marginBottom:12}}>RocketPulse</h1>
   <p style={{marginBottom:24}}>Sign in using your authorized mission account to access the connected astronaut monitoring dashboard.</p>
   {!authConfigured?<p role="alert">Supabase authentication is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in Vercel, then redeploy.</p>:
    <form onSubmit={async e=>{e.preventDefault();setBusy(true);setMessage('');try{await signIn(email,password);setPassword('')}catch(err){setMessage(err instanceof Error?err.message:'Sign-in failed')}finally{setBusy(false)}}} style={{display:'grid',gap:12}}>
     <label>Email<input aria-label="Email" type="email" required autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} style={{display:'block',width:'100%',padding:12,marginTop:5}}/></label>
     <label>Password<input aria-label="Password" type="password" required autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} style={{display:'block',width:'100%',padding:12,marginTop:5}}/></label>
     {message&&<p role="alert" style={{color:'#f3a98e'}}>{message}</p>}
     <button type="submit" disabled={busy} style={{padding:12,background:'#A68D6F',color:'#07080A',border:0,borderRadius:8,cursor:'pointer'}}>{busy?'Signing in…':'Sign in'}</button>
    </form>}
   <p style={{marginTop:20,fontSize:12}}>Synthetic research prototype. Role and mission permissions are enforced by FastAPI, not the dashboard role selector.</p>
  </section>
 </main>;
}
export function SignOutButton(){
 return <button type="button" onClick={signOut} title="End Supabase Auth session" style={{background:'transparent',border:'1px solid #304E58',padding:'6px 10px',borderRadius:8,color:'inherit',cursor:'pointer'}}>Sign out</button>;
}

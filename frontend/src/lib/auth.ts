/** Public Supabase Auth REST client. No service-role credentials belong in React.
 * Sessions are kept in sessionStorage (tab lifetime); clear on sign-out.
 * For a clinical production deployment, replace with reviewed auth SDK/cookie flow.
 */
type AuthSession = {access_token:string;refresh_token:string;expires_at:number};
const storageKey='rocketpulse-auth-session';
const url=(import.meta.env.VITE_SUPABASE_URL||'').replace(/\/$/,'');
const anon=import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY||import.meta.env.VITE_SUPABASE_ANON_KEY||''; // Support current publishable and legacy anon keys
const configured=Boolean(url && anon);
let session:AuthSession|null=null;
try {
 const saved=sessionStorage.getItem(storageKey);
 if(saved)session=JSON.parse(saved) as AuthSession;
}catch{session=null}
function notify(){window.dispatchEvent(new Event('rocketpulse-auth-changed'))}
function storeSession(data:{access_token:string;refresh_token:string;expires_in:number}){
 if(!data.access_token||!data.refresh_token)throw new Error('Authentication response missing session tokens');
 session={access_token:data.access_token,refresh_token:data.refresh_token,expires_at:Date.now()+data.expires_in*1000};
 sessionStorage.setItem(storageKey,JSON.stringify(session));notify();
}
async function authRequest(path:string,body:Record<string,string>){
 if(!configured)throw new Error('Supabase Auth is not configured for this deployment.');
 const response=await fetch(url+path,{method:'POST',headers:{'Content-Type':'application/json','apikey':anon},body:JSON.stringify(body)});
 const data=await response.json();
 if(!response.ok)throw new Error(data.msg||data.error_description||data.message||'Authentication failed');
 return data;
}
export const authConfigured=configured;
export function hasSession(){return Boolean(session?.refresh_token)}
export async function signIn(email:string,password:string){
 const data=await authRequest('/auth/v1/token?grant_type=password',{email,password});
 storeSession(data);
}
let refreshInFlight:Promise<string|null>|null=null;
export async function getAccessToken():Promise<string|null>{
 if(!session)return null;
 if(session.expires_at>Date.now()+60_000)return session.access_token;
 if(!refreshInFlight){
  refreshInFlight=(async()=>{
   try{
    const data=await authRequest('/auth/v1/token?grant_type=refresh_token',{refresh_token:session!.refresh_token});
    storeSession(data);return session?.access_token||null;
   }catch{signOut();return null}
  })().finally(()=>{refreshInFlight=null});
 }
 return refreshInFlight;
}
export function signOut(){session=null;sessionStorage.removeItem(storageKey);notify()}

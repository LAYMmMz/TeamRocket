/** Capability descriptions, never clinical or end-to-end completion claims. */
export function featureStatus(id:string,isDemo:boolean,isPublic:boolean){
 if(isDemo)return {label:'Fixture preview',detail:'Explicit demo mode; these readings are not database reads.'};
 if(['F13','F14','F19','F22','F25','F27','F40','F41','F43'].includes(id))return {label:'Connected read path',detail:'Reads available observations through FastAPI. Record availability is checked below; full feature acceptance is not established.'};
 if(['F02','F06','F07','F08','F11','F12','F38','F39','F46'].includes(id))return {label:isPublic?'Authorized workflow': 'Acceptance required',detail:isPublic?'Private workflow requires an authorized mission session; public visitors cannot run it.':'Verify persisted outcomes, role checks and scenario tests before marking complete.'};
 if(id==='F47')return {label:'Replay not verified',detail:'The scenario reference is not a successful offline/reconnect acceptance run.'};
 return {label:'Evidence required',detail:'Required by the PDF. Available domain records do not establish the full workflow or its acceptance tests.'};
}

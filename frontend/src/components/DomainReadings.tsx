import {useDomainRecords} from '../app/useDomainRecords';
import {RecordTable,Notice} from './UI';
export function DomainReadings({domainId,limit=3}:{domainId:string;limit?:number}){
 const {records,loading,error}=useDomainRecords(domainId);
 if(loading)return <p role="status">Loading selected crew records…</p>;
 if(error)return <Notice warning>Database readings unavailable: {error}. No substitute readings are shown.</Notice>;
 if(!records.length)return <Notice>No supported records available for this crew and health area. Missing data does not mean normal.</Notice>;
 return <RecordTable records={records.slice(0,limit)}/>;
}

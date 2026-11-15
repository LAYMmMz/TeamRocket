export type Role = 'crew' | 'crew_medical_officer' | 'ground_clinician' | 'mission_operator' | 'administrator';
export type Severity = 'informational' | 'advisory' | 'warning' | 'critical' | 'data-unavailable';
export type Verification = 'verified-demo' | 'review-required' | 'unreviewed' | 'missing';
export type DataSource = 'synthetic' | 'research-only' | 'imported';
export interface Provenance {
  event_id: string;
  is_synthetic: boolean;
  source_type: DataSource;
  measured_at: string;
  received_at: string;
  source_device_id: string | null;
  quality: 'ok' | 'stale' | 'missing' | 'review-required';
  verification: Verification;
}
export interface Astronaut { id:string; crew_code:string; display_name:string; role:string; status:string; }
export interface Vital extends Provenance { id:string; astronaut_id:string; metric_code:string; value:number|null; unit:string; baseline:number|null; }
export interface Alert {id:string;event_id:string; astronaut_id:string | null; title:string; severity:Severity;status:'open'|'acknowledged'|'closed'; rule_id:string|null;rule_version:string|null;approval_status:'approved-demo'|'unapproved'|'expired'|'none';evidence:string[];created_at:string;clinician_acknowledged_at:string|null;is_synthetic:boolean;}
export interface CaseRecord { id:string; label:string; value:string; unit:string; measured_at:string; source:string;quality:Verification; details:string; record_table:string; is_synthetic:boolean; }
export interface CommandSnapshot {mission_id:string;mission_phase:string;mission_day:number;timestamp:string;crew:Astronaut[];vitals:Vital[];alerts:Alert[];exam_backlog:number;sync_state:'connected'|'offline'|'pending';devices_online:number;devices_total:number;}
export interface TrendPoint {timestamp:string; label:string;HR:number|null;SpO2:number|null;RR:number|null;}

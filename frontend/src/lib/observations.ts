import type {CaseRecord} from './types';
// These legacy seed values have no measurement method or clinical definition.
// Do not present invented indices as physiology (MasterDocs sections 2 and 15).
const unsupported = new Set(['IMMUNE_INDEX','BONE_INDEX','VASCULAR_INDEX','OCT_INDEX','CULTURE_INDEX']);
export function supportedObservations(records:CaseRecord[]):CaseRecord[]{
 return records.filter(r=>!unsupported.has(r.label));
}

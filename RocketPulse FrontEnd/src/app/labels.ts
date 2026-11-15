export const moduleLabels:Record<string,string>={
 command:'Mission Overview',
 individual:'Personal Health',
 examinations:'Health Checks & Recovery',
 environment:'Radiation & Cabin Conditions',
 laboratory:'Lab & Immune Health',
 crew:'Daily Crew Check-in',
 ground:'Flight Surgeon Review',
 explorer:'Crew Health Explorer',
 domains:'Health Systems',
 cases:'Medical Alerts',
 simulation:'Mission Scenarios',
 'data-model':'Data Tables',
 integration:'Data & Sync Status',
 evidence:'Research References',
 'data-intake':'Record Drafts'
};

export const dashboardCopy:Record<string,{title:string;description:string}>={
 command:{title:'Mission Overview',description:'Check mission phase, crew status, health readings, alerts, and communications at a glance.'},
 individual:{title:'Personal Health',description:'Review the selected crew member’s health readings, baseline, activity, sleep, and history.'},
 examinations:{title:'Health Checks & Recovery',description:'Review upcoming checkups, test results, fitness assessments, and recovery items.'},
 environment:{title:'Radiation & Cabin Conditions',description:'Review radiation exposure and cabin readings, including air, lighting, noise, and samples.'},
 laboratory:{title:'Lab & Immune Health',description:'Check sample status, lab results, immune measures, and items awaiting review.'},
 crew:{title:'Daily Crew Check-in',description:'Record symptoms, fatigue, sleep, and adjustment to changing gravity; review reminders.'},
 ground:{title:'Flight Surgeon Review',description:'Review incoming crew health records, alerts, timelines, and follow-up items.'}
};

export const domainLabels:Record<string,string>={
 cardiorespiratory:'Heart & Breathing',
 vascular:'Blood Flow',
 radiation:'Radiation Exposure',
 gravity:'Gravity Adaptation',
 fitness:'Fitness & Muscle',
 bone:'Bone Health',
 vision:'Vision Health',
 immune:'Immune Health',
 sleep:'Sleep & Recovery',
 cabin:'Cabin Conditions',
 microbiology:'Microbe Samples',
 medicalops:'Medical Operations'
};

export function domainLabel(id:string,fallback:string){return domainLabels[id]??fallback}

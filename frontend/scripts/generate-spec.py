import json, pathlib
p=pathlib.Path(__file__).resolve().parents[1] / 'src/data/masterdocs.json'
table_groups={
'Identity / missions / devices':{
'astronauts':'id,crew_code,display_name,status','missions':'id,name,mission_type,launch_at,landing_at,phase','mission_crew':'mission_id,astronaut_id,crew_role','users':'id,authentication_identity,account_status','roles':'id,role_name,permissions','user_role_assignments':'user_id,role_id,mission_id','devices':'id,device_type,model,calibration_status','device_assignments':'device_id,astronaut_id,location_id,assigned_at,ended_at'},
'General physiological health':{
'vital_signs':'id,astronaut_id,metric_code,value,unit,measured_at,source_device_id,quality','ecg_records':'id,astronaut_id,start_at,end_at,waveform_reference,reviewed_interpretation','symptom_reports':'id,astronaut_id,symptom_code,severity,onset_at,reported_at,body_location','health_baselines':'id,astronaut_id,metric_code,baseline_value,measurement_method,validity','medical_findings':'id,astronaut_id,finding_code,interpretation,reviewer_id,reviewed_at','medical_incidents':'id,astronaut_id,mission_id,incident_type,priority,status','incident_events':'id,incident_id,event_type,actor_id,occurred_at'},
'Laboratory / immune':{
'biological_samples':'id,astronaut_id,sample_type,collected_at,source,processing_status','laboratory_results':'id,sample_id,test_code,result_value,unit,assay_method,verification','microbial_identifications':'id,sample_id,organism,identification_method,result_status','sequencing_runs':'id,sample_id,platform,run_quality,data_reference','clinical_sample_chain':'id,sample_id,custody_event,responsible_person,occurred_at'},
'Cardiovascular / eye / fitness / bone':{
'vascular_ultrasound_results':'id,astronaut_id,vein,side,flow_pattern,thrombus_finding,reviewed_by','ocular_assessments':'id,astronaut_id,test_type,assessed_at,report_reference','ocular_results':'id,assessment_id,eye,metric_code,value,unit,interpretation','fitness_assessments':'id,astronaut_id,test_type,metric_code,value,protocol,assessed_at','exercise_sessions':'id,astronaut_id,exercise_type,duration,workload,repetitions','bone_scans':'id,astronaut_id,scan_type,scanned_at,report_reference','bone_density_results':'id,scan_id,bone_region,bmd_value,t_score,z_score','functional_assessments':'id,astronaut_id,test_type,protocol,score,assessed_at'},
'Radiation / environment / gravity':{
'personal_dose_records':'id,astronaut_id,dosimeter_id,dose_quantity,value,unit,interval','radiation_area_records':'id,location_id,sensor_id,radiation_metric,value,measured_at','radiation_events':'id,event_type,started_at,ended_at,status','environmental_readings':'id,location_id,metric_code,value,unit,measured_at','environmental_samples':'id,sample_type,location_id,sample_size,collected_at','environmental_lab_results':'id,sample_id,test_code,result_value,unit,verification','mission_locations':'id,mission_id,zone_name,location_type','gravity_transition_events':'id,mission_id,from_g,to_g,occurred_at'},
'Sleep / nutrition / fluids / medication':{
'sleep_sessions':'id,astronaut_id,start_at,end_at,duration,source','behavioral_checkins':'id,astronaut_id,assessment_type,score,visibility_classification','nutrition_logs':'id,astronaut_id,meal_at,intake_details','fluid_balance_logs':'id,astronaut_id,period_start,period_end,intake,output,unit','medication_administrations':'id,astronaut_id,medication_reference,dose,unit,authorized_by'},
'Rules / alerts / procedures / exams':{
'health_alerts':'id,rule_id,astronaut_id,location_id,severity,status','alert_events':'id,alert_id,event_type,actor_id,occurred_at','alert_evidence':'id,alert_id,source_record_type,source_record_id','alert_rules':'id,version,condition_definition,severity,approval_status','medical_exam_schedule':'id,astronaut_id,exam_type,due_at,completion_status','medical_procedures':'id,title,version,approval_status,authoritative_source','procedure_steps':'id,procedure_id,step_order,instruction,acknowledgment_required','medical_inventory':'id,item_code,quantity,expiry_at,storage_location','clinical_condition_catalog':'id,condition_code,catalog_version,description','recommendation_records':'id,alert_id,procedure_id,displayed_at,action_status'},
'Import / sync / audit':{
'data_import_batches':'id,source,imported_at,validation_summary','sync_queue':'id,event_id,destination,priority,status,attempt_count','sync_receipts':'id,event_id,acknowledged_at,remote_status','audit_logs':'id,actor_id,action,resource_type,resource_id,occurred_at','data_quality_issues':'id,record_reference,issue_type,severity,resolution_status','attachments':'id,owner_record_reference,storage_path,hash,access_classification'} }
assert sum(map(len,table_groups.values()))==57
features_str='''F01|Mission and astronaut management|P0
F02|User roles and clinical data permissions|P0
F03|Device-agnostic sensor and report import|P0
F04|Measurement validation and provenance|P0
F05|Personal health baseline management|P0
F06|Shared symptom reporting|P0
F07|Configurable, versioned clinical alert engine|P0
F08|Central medical incident handling|P0
F09|Approved procedure and recommendation library|P0
F10|Mission-aware examination scheduling|P0
F11|Local storage and offline operation|P0
F12|Ground synchronization and audit history|P0
F13|Cardiovascular vital signs and ECG reporting|P1
F14|Respiratory and oxygenation monitoring|P0
F15|Vascular ultrasound and D-dimer result review|P1
F16|Gravity-adaptation and vestibular assessments|P0
F17|Cognitive and reaction-time assessments|P2
F18|Aerobic fitness and muscle assessments|P1
F19|Exercise and physical workload tracking|P0
F20|Bone-density and recovery examinations|P1
F21|SANS/OCT, visual acuity and fundoscopy|P1
F22|Sleep and circadian monitoring|P1
F23|Nutrition, hydration and fluid balance logs|P1
F24|Behavioral-health check-ins|P1
F25|Personal and area radiation dosimetry|P0
F26|Solar particle event and radiation incident monitoring|P0
F27|Cabin atmosphere and pressure monitoring|P0
F28|Light and noise monitoring|P1
F29|Environmental microbial sampling|P1
F30|Water, air, food and surface test results|P0
F31|Spacesuit microbial hygiene records where available|P2
F32|Blood, saliva, urine and other sample management|P1
F33|Onboard and Earth-laboratory test imports|P1
F34|Immune and viral biomarker result histories|P1
F35|Sequencing and multi-omics dataset records where available|P2
F36|Medical inventory and consumables|P1
F37|Versioned condition-reference catalog|P1
F38|Emergency clinical notification and acknowledgment|P0
F39|Offline crew guidance access|P0
F40|Mission Medical Command dashboard|P0
F41|Individual Astronaut Health dashboard|P0
F42|Clinical Examinations and Recovery dashboard|P0
F43|Radiation and Environment dashboard|P0
F44|Laboratory and Immune Health dashboard|P1
F45|Crew Self-Assessment dashboard|P0
F46|Ground Medical Review dashboard|P0
F47|Synthetic end-to-end mission demonstration|P0'''
features=[dict(id=parts[0],title=parts[1],priority=parts[2]) for line in features_str.splitlines() if (parts:=line.split('|'))]
assert len(features)==47
# data as specified in full monitoring scope on p.2
domains=[
('cardiorespiratory','Cardiovascular / Respiratory','F13 F14','vital_signs ecg_records health_baselines symptom_reports','Heart rate, blood pressure, respiration, SpO₂, ECG, temperature, activity and symptoms','Source quality and baseline; serious symptoms escalate manually even if SpO₂ missing','heart'),
('vascular','Vascular / Thrombosis','F15','laboratory_results vascular_ultrasound_results medical_findings','D-dimer assay and left/right jugular Doppler reports, symptoms','Assay-aware findings; never automatically diagnose thrombosis','veins'),
('radiation','Radiation','F25 F26','personal_dose_records radiation_area_records radiation_events','Personal dose/area rate, quantity/unit, particle species/energy, SPE context','Dose-quantity compatibility, stale detector flag, no invented conversion','radiation'),
('gravity','Gravity / Vestibular','F16 F17','gravity_transition_events functional_assessments symptom_reports fluid_balance_logs','Gravity transitions, nausea, dizziness, balance, reaction time, fluid balance','Track adaptation cases; never autonomously clear EVA','gravity'),
('fitness','Fitness / Muscle','F18 F19','fitness_assessments exercise_sessions functional_assessments','VO₂peak, standardized strength/endurance, exercise sessions, fatigue','Compare identical protocols and record adherence separately','fitness'),
('bone','Bone','F20','bone_scans bone_density_results exercise_sessions','DXA by bone site and region, recovery, exercise and injury','Pre/postflight comparisons only; never invent in-flight BMD','bone'),
('vision','Vision / SANS','F21','ocular_assessments ocular_results medical_exam_schedule','OCT, acuity, fundoscopy, each eye, visual symptoms','Eye-specific trend; specialist review and serious vision-symptom escalation','eye'),
('immune','Immune / Infection','F32 F33 F34','biological_samples laboratory_results microbial_identifications clinical_sample_chain','Sample custody, assay and biomarker details, viral findings','Verify test methods and results; no inferred immune score','immune'),
('sleep','Sleep / Behavior','F22 F24','sleep_sessions behavioral_checkins','Sleep intervals, actigraphy, fatigue and confidential check-ins','Trends versus baseline; restricted visibility','sleep'),
('cabin','Cabin Environment','F27 F28','environmental_readings mission_locations','CO₂, oxygen partial pressure, pressure, lux and dB(A)','Location, unit and averaging-window-aware review','cabin'),
('microbiology','Environmental Microbiology','F29 F30 F31 F35','environmental_samples environmental_lab_results microbial_identifications sequencing_runs','Water/air/food/surface samples, CFU and method, sequencing metadata','Verification and follow-up sampling, no autonomous pathogen diagnosis','microbe'),
('medicalops','Autonomous Medical Operations','F08 F09 F36 F37 F38 F39','medical_incidents incident_events medical_procedures procedure_steps medical_inventory clinical_condition_catalog','Incidents, guidance versions, inventory, delayed communication','Offline approved guidance, acknowledgement, clinician escalation and sync','medkit')]
domains=[dict(id=id,name=name,feature_ids=fids.split(),tables=tbls.split(),inputs=inputs,safety=safety,icon=icon) for id,name,fids,tbls,inputs,safety,icon in domains]
assert len(domains)==12
views=[
('command','Mission Medical Command','F40','Crew overview, mission phase, critical alerts, incidents, examination backlog and sync/device state',['cardiorespiratory','cabin','medicalops']),
('individual','Individual Astronaut Health','F41','Verified vitals and ECG, baseline, symptoms, exercise, sleep and history',['cardiorespiratory','sleep','fitness']),
('examinations','Clinical Examinations & Recovery','F42','D-dimer/vascular, OCT/vision, DXA/bone, fitness, due examinations and review',['vascular','vision','bone','fitness','gravity']),
('environment','Radiation & Environment','F43','Personal dose and particle records, SPE, environment, lighting, noise and microbiology',['radiation','cabin','microbiology']),
('laboratory','Laboratory & Immune Health','F44','Specimen custody, assay, instrument imports, sequencing and review',['immune','microbiology']),
('crew','Crew Self-Assessment','F45','Symptoms, fatigue, confidential check-ins, gravity adaptation, reminders and procedure acknowledgments',['sleep','gravity','medicalops']),
('ground','Ground Medical Review','F46','Synced clinical review queue, delayed receipts, incident timelines, reviewer actions and audit',['medicalops','vascular','vision'])]
views=[dict(id=id,name=name,feature_id=feature_id,summary=summary,domain_ids=di) for id,name,feature_id,summary,di in views]
scenarios=[
('S01','Normal crew vitals and environment','Normal charts, simulation badges, no spurious clinical alerts','normal'),
('S02','High HR coinciding with workout','Activity context; do not confuse elevated workout HR with resting abnormality','exercise'),
('S03','Serious breathing symptom; SpO₂ absent','Local incident; unavailable sensor remains missing, not fabricated','breathing'),
('S04','CO₂ time-window incident + headache symptom','One evidence-linked incident with a versioned demo rule and acknowledgement','co2'),
('S05','Clinically unreviewed D-dimer','Review queue, never diagnose clot','review'),
('S06','Left-side vascular ultrasound finding','Left-side record and clinician review','vascular'),
('S07','Solar particle event + stale dosimeter','Labeled radiation notification, dose compatibility and stale flag','spe'),
('S08','OCT due; no in-flight DXA','Reminders and missing BMD clearly marked; no invented readings','exam'),
('S09','Environmental water culture flag','Show sampling method/unit, review and re-sampling request','water'),
('S10','Disconnect and reconnect','Local persistence, receipts, no duplicate alerts','offline'),
('S11','Expired procedure and unapproved clinical rule','Historical reference only; no treatment guidance','expired'),
('S12','Unauthorized confidential check-in access','Deny and audit in backend; UI demo shows restricted view','denied')]
scenarios=[dict(id=id,name=name,expected=expected,kind=kind) for id,name,expected,kind in scenarios]
hazards=[dict(id='radiation',name='Space Radiation',scope='Personal/area doses, particle spectrum, solar particle events',domain_ids=['radiation']),dict(id='isolation',name='Isolation & Confinement',scope='Sleep, behavioral check-ins, privacy and wellness support',domain_ids=['sleep']),dict(id='distance',name='Distance from Earth',scope='Offline incidents, delayed sync, procedures and escalations',domain_ids=['medicalops']),dict(id='gravity',name='Gravity Fields',scope='Vestibular, bone, muscle and functional assessments',domain_ids=['gravity','bone','fitness']),dict(id='environment',name='Hostile / Closed Environments',scope='Cabin atmosphere, infectious risks and environmental sampling',domain_ids=['cabin','microbiology','immune'])]
offline=[dict(name=n,fields=f.split(','),cloud=cloud) for n,f,cloud in [
('offline_vital_signs','local_id,event_id,astronaut_id,mission_id,metric_code,value,unit,measured_at,received_at,quality,source_device_id,sync_status','vital_signs'),
('offline_symptom_reports','local_id,event_id,astronaut_id,mission_id,symptom_code,severity,onset_at,reported_at,notes,sync_status','symptom_reports'),
('offline_health_alerts','local_id,event_id,rule_id,rule_version,astronaut_id,location_id,severity,evidence,status,created_at,sync_status','health_alerts + evidence/events'),
('offline_alert_rules','rule_id,version,definition,scope,approval_signature,valid_from,expires_at,stored_at','alert_rules'),
('offline_medical_procedures','procedure_id,version,title,ordered_steps,source,approval_state,cached_at,validity','medical_procedures + steps'),
('sync_queue','queue_id,event_id,entity_type,local_ref,operation,payload_hash,priority,attempts,next_retry_at,status,receipt_id','sync receipts/events')]]
api=[dict(group=group,uses=uses) for group,uses in [
('/auth /missions /astronauts','Identity, mission phase, crew lookup and role-scoped access'),
('/devices /measurements /symptoms','Device registry, validated observations, symptom reports, baselines and trends'),
('/samples /examinations','Sample imports, per-eye/side/region examinations and clinician review'),
('/radiation /environment','Radiation, SPE, cabin sensors, environmental samples, units and location'),
('/alerts /incidents /procedures','Immutable evidence, state transitions, versioned rules, acknowledgement'),
('/inventory /reports','Inventory status and authorized mission reports'),
('/sync','Batch push/pull, idempotency, receipt, conflict and retry')]]
tables=[dict(name=name,group=group,columns=columns.split(',')) for group, group_items in table_groups.items() for name,columns in group_items.items()]
output=dict(version='2026-11-15',source='NASA_Astronaut_Health_Monitoring_MASTERDOCS_FINAL_DEVELOPMENT_2026.pdf',prototype_type='SYNTHETIC / NOT CLINICALLY VALIDATED',mission=dict(id='DEMO-01',duration_days=180,seed=20261115,crew=['CREW-01','CREW-02','CREW-03','CREW-04'],locations=['Habitat','Medical Bay','Exercise Area']),features=features,domains=domains,views=views,scenarios=scenarios,hazards=hazards,tables=tables,offline_tables=offline,api_groups=api)
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
print('wrote', p, 'features',len(features),'domains',len(domains),'views',len(views),'scenarios',len(scenarios),'tables',len(tables),'offline',len(offline))

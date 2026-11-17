import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox']});
const page=await browser.newPage();
const base=process.env.UI_TEST_URL||'http://127.0.0.1:5173';
const errors=[];page.on('pageerror',e=>errors.push(e.message));
let fail=false;
const calls=[];
await page.route('**/api/v1/**',async route=>{
 const url=new URL(route.request().url());calls.push(url.pathname+url.search);
 if(fail){await route.fulfill({status:503,json:{error:{message:'Test feed unavailable'}}});return;}
 const crew=url.searchParams.get('astronaut_id')||'CREW-01';
 const second=crew==='CREW-02';
 if(second)await new Promise(resolve=>setTimeout(resolve,200));
 const timestamp='2026-11-16T10:00:00+00:00';
 const rows=[{id:crew+'-sample',label:'SLEEP_H',value:second?'8.75':'6.25',unit:'h',measured_at:timestamp,source:'SIMULATED',quality:'unreviewed',details:'Test database response',record_table:'rocketpulse_public_demo_samples',is_synthetic:true}];
 if(url.pathname.endsWith('/schema/catalog'))await route.fulfill({json:{
  source:'supabase-approved-schema-snapshot', inspected_at:timestamp,expected_tables:57,verified_tables:57,
  count_policy:'synthetic_seed_only_no_private_record_counts',
  tables:[{name:'vital_signs',table_present:true,starter_fields_verified:true,starter_field_count:6,
           missing_starter_fields:[],published_synthetic_rows:8880}]
 }});
 else if(url.pathname.includes('/command'))await route.fulfill({json:{mission_id:'DEMO-01',mission_phase:'SYNTHETIC / PUBLIC',mission_day:0,timestamp,crew:['CREW-01','CREW-02'].map(id=>({id,crew_code:id,display_name:id,role:'simulated',status:'synthetic'})),vitals:[],alerts:[],exam_backlog:0,devices_online:0,devices_total:0,sync_state:'connected',data_source:'supabase-approved-synthetic'}});
 else if(url.pathname.includes('/trends'))await route.fulfill({json:[]});
 else if(url.pathname.endsWith('/immune'))await route.fulfill({json:[{...rows[0],label:'IMMUNE_INDEX',value:'1.0'}]});
 else await route.fulfill({json:rows});
});
try{
 await page.goto(base+'/command');
 await page.getByText('SUPABASE APPROVED SYNTHETIC DATA',{exact:true}).waitFor();
 await page.getByText('SYNTHETIC / 24-HOUR RECORDED WINDOW',{exact:true}).waitFor();
 assert.equal(await page.getByText('FOUR SIMULATED CREW MEMBERS',{exact:true}).count(),0);
 assert.equal(await page.getByText('SIMULATED / LAST 24 HOURS',{exact:true}).count(),0);
 assert.equal(await page.getByText('0/0',{exact:true}).count(),0);
 assert.equal(await page.getByText('Not declared',{exact:true}).count(),0);
 for(const path of ['/individual','/examinations','/environment','/laboratory','/crew','/ground']){
  await page.goto(base+path);await page.getByText('6.25',{exact:true}).first().waitFor();
  assert.equal(await page.getByLabel('Demo role view').count(),0);
 }
 await page.getByLabel('Selected crew member').selectOption('CREW-02');
 assert.equal(await page.getByText('6.25',{exact:true}).count(),0,'Old crew reading leaked during selection');
 await page.getByText('8.75',{exact:true}).first().waitFor();
 await page.goto(base+'/explorer');await page.getByText('6.25',{exact:true}).first().waitFor();
 const boneRead=page.waitForRequest(request=>request.url().includes('/reports/domains/bone'));
 const legs=page.getByRole('button',{name:'LEGS',exact:true});
 await legs.click();await boneRead;assert.equal(await legs.getAttribute('aria-pressed'),'true');
 await page.goto(base+'/domains/immune');await page.getByText('No records available. Missing data does not mean normal.').waitFor();
 assert.equal(await page.getByText('IMMUNE_INDEX',{exact:true}).count(),0);
 await page.goto(base+'/features/F22');await page.getByText('Connected read path',{exact:true}).waitFor();await page.getByText('6.25',{exact:true}).first().waitFor();
 assert.equal(await page.getByText('SCAFFOLD',{exact:true}).count(),0);
 await page.goto(base+'/cases');assert(await page.getByRole('button',{name:'Save simulated check-in'}).isDisabled());
 await page.getByText('Database-linked medical operations records').waitFor();
 await page.getByText('6.25',{exact:true}).first().waitFor();
 await page.goto(base+'/simulation');await page.getByText('Not executed',{exact:true}).waitFor();
 await page.getByText('Related database observations').waitFor();
 await page.getByText('6.25',{exact:true}).first().waitFor();
 assert(calls.some(c=>c.includes('/reports/domains/cabin')),'S04 must read cabin domain');
 assert(calls.some(c=>c.includes('/reports/domains/medicalops')),'S04 must read medicalops domain');
 const radiationCall=page.waitForRequest(request=>request.url().includes('/reports/domains/radiation'));
 await page.getByRole('button',{name:/S07 Solar particle event/}).click();
 await radiationCall;
 await page.getByRole('button',{name:/S10 Disconnect and reconnect/}).click();
 await page.getByText(/No released database evidence is available/).waitFor();
 await page.goto(base+'/data-model');
 await page.getByText('8,880',{exact:true}).waitFor();
 await page.getByText('VERIFIED',{exact:true}).first().waitFor();
 assert(calls.some(c=>c.includes('/api/v1/public/schema/catalog')),'Data Tables must read approved Supabase catalog');
 fail=true;await page.goto(base+'/data-model');
 await page.getByText(/Supabase catalog request failed/).waitFor();
 assert.equal(await page.getByText('8,880',{exact:true}).count(),0,'Stale catalog counts must disappear on error');
 await page.goto(base+'/domains/sleep');await page.getByText(/Mission data request failed: Test feed unavailable/).waitFor();
 assert.equal(await page.getByText('6.25',{exact:true}).count(),0);
 assert.equal(errors.length,0,errors.join('\n'));
 assert(calls.every(c=>c.startsWith('/api/v1/public/')),'Public UI requested a private API');
 console.log('PASS database UI: six dashboards, explorer, feature records, crew isolation, unsupported metrics, errors, read-only controls and scenario boundaries');
}finally{await browser.close();}

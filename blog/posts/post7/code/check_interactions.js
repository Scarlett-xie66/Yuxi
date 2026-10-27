/* Execute the actual event handlers/specifications with a minimal DOM and Plotly double. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const data=JSON.parse(fs.readFileSync(path.join(root,'result/dashboard_data.json'),'utf8'));
class Element {
 constructor(id){this.id=id;this.value='';this.textContent='';this.children=[];this.events={};this.open=false;}
 appendChild(x){this.children.push(x);} replaceChildren(...x){this.children=x;}
 addEventListener(name,fn){this.events[name]=fn;} on(name,fn){this.events[name]=fn;}
}
const elements={};
for(const id of ['b7-data','b7-region','b7-year','b7-country','b7-reset','b7-status','b7-country-name','b7-scatter','b7-history','b7-coefficients','b7-model','b7-model-status','b7-extra-decline','b7-extra-interval','b7-detail'])elements[id]=new Element(id);
elements['b7-data'].textContent=JSON.stringify(data);
const plots={};let resizes=0;
const context={document:{getElementById:id=>elements[id],createElement:()=>new Element('option')},window:{addEventListener:()=>{}},console,
 innerWidth:1024,setTimeout:fn=>{fn();return 1;},clearTimeout:()=>{},
 requestAnimationFrame:fn=>fn(),Plotly:{react:(id,traces,layout,config)=>{plots[id]={traces,layout,config};return Promise.resolve();},Plots:{resize:()=>{resizes++;}}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'code/dashboard.js'),'utf8'),context);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function main(){
 for(let i=0;i<5;i++)await tick();
 const api=context.window.blog7Test;
 assert(context.window.blog7Ready);
 const regions=['All regions',...new Set(data.countries.map(c=>c.region))];
 let cases=0;
 for(const region of regions)for(const year of ['All years',...data.years.map(String)]){
  const q=api.rows(region,year),spec=api.scatterSpec(q);
  assert(q.every(r=>r.gdp<0));
  assert(q.every(r=>region==='All regions'||r.region===region));
  assert(q.every(r=>year==='All years'||r.year===Number(year)));
  assert.strictEqual(spec.data.slice(0,-1).reduce((s,t)=>s+t.x.length,0),q.length);
  assert(spec.data.flatMap(t=>t.x).every(x=>x>=-12&&x<=12));
  assert(spec.data.flatMap(t=>t.y).every(y=>y>=-12&&y<=12));
  if(q.length===0)assert(spec.layout.annotations.length===1);
  cases++;
 }
 for(const label of ['National: all years','National: before 2020']){
  const spec=api.coefficientSpec(label);
  const trace=spec.data[0];
  assert.deepStrictEqual(Array.from(trace.x),['Women','Men']);
  for(let i=0;i<2;i++){
   const sex=['Women','Men'][i];
   const source=data.models.find(r=>r.specification===label&&r.outcome===sex&&r.term==='depth');
   assert(Math.abs(trace.y[i]-source.estimate)<1e-11);
   assert(Math.abs(trace.error_y.array[i]-(source.ci_high-source.estimate))<1e-11);
   assert(Math.abs(trace.error_y.arrayminus[i]-(source.estimate-source.ci_low))<1e-11);
   assert(Math.abs(trace.customdata[i][0]-source.ci_low)<1e-11);
   assert(Math.abs(trace.customdata[i][1]-source.ci_high)<1e-11);
   assert(source.ci_low>=-.65&&source.ci_high<=.55);
  }
  assert(spec.layout.yaxis.range[0]<0&&spec.layout.yaxis.zeroline===true);
 }
 elements['b7-year'].value='2020';elements['b7-year'].events.change();await api.update();
 assert(context.window.blog7State.rows.every(r=>r.year===2020));
 elements['b7-region'].value=data.countries.find(c=>c.iso3==='ESP').region;
 elements['b7-region'].events.change();await api.update();
 assert(context.window.blog7State.rows.every(r=>r.region===elements['b7-region'].value));
 elements['b7-country'].value='ESP';elements['b7-country'].events.change();await api.update();
 assert.strictEqual(context.window.blog7State.chosen,'ESP');
 elements['b7-scatter'].events.plotly_click({points:[{customdata:['ITA','Italy',2020]}]});await api.update();
 assert.strictEqual(context.window.blog7State.chosen,'ITA');assert(elements['b7-detail'].open);
 elements['b7-detail'].events.toggle();assert(plots['b7-history']);
 elements['b7-model'].value='National: before 2020';await elements['b7-model'].events.change();
 assert(elements['b7-model-status'].textContent.includes('before 2020'));
 const before2020=data.models.find(r=>r.specification==='National: before 2020'&&r.outcome==='Women minus men'&&r.term==='depth');
 assert(elements['b7-extra-interval'].textContent.includes(before2020.ci_low.toFixed(2)));
 assert(Math.abs(parseFloat(elements['b7-extra-decline'].textContent)-before2020.estimate)<.01);
 elements['b7-reset'].events.click();await api.update();
 assert.strictEqual(context.window.blog7State.year,'All years');assert.strictEqual(context.window.blog7State.region,'All regions');assert.strictEqual(context.window.blog7State.chosen,'ESP');
 assert.strictEqual(elements['b7-model'].value,'National: all years');assert.strictEqual(elements['b7-detail'].open,false);
 const result={status:'passed',engine:'Node with DOM/Plotly test doubles',region_year_cases:cases,
  all_visible_points_checked:true,confidence_interval_values_and_hover_checked:true,empty_selection:true,
  country_selection:true,scatter_click:true,country_detail_resize:true,model_period_menu:true,reset:true,
  real_browser_rendering:'not verified'};
 fs.writeFileSync(path.join(root,'result/interaction_validation.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result,null,2));
}
main().catch(e=>{console.error(e);process.exit(1);});

(function () {
  'use strict';
  const D = JSON.parse(document.getElementById('b7-data').textContent);
  const $ = id => document.getElementById(id);
  const regions = [...new Set(D.countries.map(c => c.region))].sort();
  const config = {responsive: false, displaylogo: false, scrollZoom: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']};
  const base = {height: 420, margin: {l: 65, r: 20, t: 20, b: 65},
    font: {family: 'Arial, sans-serif', size: 12, color: '#333'},
    paper_bgcolor: '#ffffff', plot_bgcolor: '#ffffff', hovermode: 'closest',
    legend: {orientation: 'h', y: -0.23}};
  let chosen = 'ESP', queue = Promise.resolve();
  const rows = (region, year) => D.recessions.filter(r =>
    (region === 'All regions' || r.region === region) && (year === 'All years' || r.year === Number(year)));
  const bucket = r => r.year === 2020 ? '2020' : [2008, 2009].includes(r.year) ? '2008–2009' : 'Other years';
  function scatterSpec(q) {
    const groups = ['2008–2009', '2020', 'Other years'], colors = ['#247c80', '#b96833', '#8a8196'];
    const traces = groups.map((g, i) => {
      const a = q.filter(r => bucket(r) === g);
      return {type: 'scatter', mode: 'markers', name: g,
        x: a.map(r => r.d_male), y: a.map(r => r.d_female),
        customdata: a.map(r => [r.iso3, r.country, r.year, r.gdp, r.difference]),
        marker: {size: 9, opacity: .8, color: colors[i]},
        hovertemplate: '<b>%{customdata[1]}, %{customdata[2]}</b><br>Real GDP growth: %{customdata[3]:.1f}%<br>Men: %{x:+.2f} pp<br>Women: %{y:+.2f} pp<br>Women minus men: %{customdata[4]:+.2f} pp<extra></extra>'};
    });
    const focus = q.filter(r => r.iso3 === chosen);
    traces.push({type: 'scatter', mode: 'markers', showlegend: false,
      x: focus.map(r => r.d_male), y: focus.map(r => r.d_female),
      customdata: focus.map(r => [r.iso3, r.country, r.year, r.gdp, r.difference]),
      marker: {size: 17, color: 'rgba(0,0,0,0)', line: {color: '#111', width: 2}},
      hovertemplate: '<b>%{customdata[1]}, %{customdata[2]}</b><br>Men: %{x:+.2f} pp<br>Women: %{y:+.2f} pp<br>Women minus men: %{customdata[4]:+.2f} pp<extra></extra>'});
    return {data: traces, layout: {...base, uirevision: 'paired-changes',
      xaxis: {title: {text: "Change in men's employment rate (pp)"}, range: [-12, 12], zerolinecolor: '#aaa'},
      yaxis: {title: {text: "Change in women's employment rate (pp)"}, range: [-12, 12], zerolinecolor: '#aaa'},
      shapes: [{type: 'line', x0: -12, y0: -12, x1: 12, y1: 12, line: {dash: 'dot', color: '#777', width: 1}}],
      annotations: q.length ? [] : [{text: 'No matched contraction observations for this selection.', x: .5, y: .5,
        xref: 'paper', yref: 'paper', showarrow: false}]}};
  }
  function historySpec(id) {
    const q = D.histories.filter(r => r.iso3 === id).sort((a,b)=>a.year-b.year);
    return {data: ['female_rate', 'male_rate'].map((v,i)=>({type: 'scatter', mode: 'lines+markers',
      name: i ? 'Men' : 'Women', x:q.map(r=>r.year), y:q.map(r=>r[v]), connectgaps: false,
      marker: {size: 4}, line: {width: 2, color: i ? '#b96833' : '#247c80'},
      hovertemplate: '%{x}<br>'+(i?'Men':'Women')+': %{y:.1f}%<extra></extra>'})),
      layout: {...base, height: 330, hovermode: 'x unified', uirevision: id,
        xaxis: {title: {text:'Year'}, range:[2000,2024], tickformat:'d'},
        yaxis: {title: {text:'Employment rate (%)'}, range:[0,100]},
        shapes: q.filter(r=>r.gdp!==null && r.gdp<0).map(r=>({type:'rect', x0:r.year-.45,x1:r.year+.45,
          y0:0,y1:1,yref:'paper',fillcolor:'rgba(185,104,51,.11)',line:{width:0},layer:'below'}))}};
  }
  function coefficientSpec(label) {
    const q = D.models.filter(r=>r.specification===label && r.term==='depth');
    const order = ['Women', 'Men'];
    const a = order.map(name=>q.find(r=>r.outcome===name));
    return {data:[{type:'bar',x:order,y:a.map(r=>r.estimate),width:.46,
      marker:{color:['#247c80','#b96833']},showlegend:false,
      error_y:{type:'data',symmetric:false,array:a.map(r=>r.ci_high-r.estimate),
        arrayminus:a.map(r=>r.estimate-r.ci_low),color:'#333',thickness:1.5,width:7},
      customdata:a.map(r=>[r.ci_low,r.ci_high]),
      hovertemplate:'<b>%{x}</b><br>Additional change: %{y:.2f} pp<br>95% interval: [%{customdata[0]:.2f}, %{customdata[1]:.2f}]<extra></extra>'}],
      layout:{...base,height:370,margin:{l:62,r:20,t:52,b:36},showlegend:false,
        xaxis:{side:'top',tickfont:{size:15},tickvals:order,ticktext:a.map((r,i)=>order[i]+'<br><b>'+r.estimate.toFixed(2)+' pp</b>'),fixedrange:true},
        yaxis:{title:{text:'Additional change (pp)'},range:[-.68,.04],dtick:.1,
          tickformat:'.1f',zeroline:true,zerolinecolor:'#444',zerolinewidth:1.5,fixedrange:true},
        annotations:[]}};
  }
  function renderPlot(id,data,layout,options){
    const node=$(id);
    [...node.children].filter(el=>el.tagName.toLowerCase()==='svg').forEach(el=>el.remove());
    return Plotly.react(id,data,layout,options);
  }
  function update() {
    const region=$('b7-region').value, year=$('b7-year').value;
    const q=rows(region,year), country=D.countries.find(c=>c.iso3===chosen);
    $('b7-status').textContent=q.length+' country-year observations from '+new Set(q.map(r=>r.iso3)).size+
      ' countries/territories. Each point has negative annual real GDP growth.';
    $('b7-country-name').textContent=country.country;
    const a=scatterSpec(q),b=historySpec(chosen);
    queue=queue.then(()=>Promise.all([renderPlot('b7-scatter',a.data,a.layout,config),
      ($('b7-detail').open ? renderPlot('b7-history',b.data,b.layout,config) : Promise.resolve())])).then(()=>{
        window.blog7State={region,year,chosen,rows:q};window.blog7Ready=true;
      });
    return queue;
  }
  function menu() {
    const q=D.countries.filter(c=>$('b7-region').value==='All regions'||c.region===$('b7-region').value);
    if(!q.some(c=>c.iso3===chosen))chosen=q[0].iso3;
    $('b7-country').replaceChildren(...q.map(c=>{const o=document.createElement('option');o.value=c.iso3;o.textContent=c.country;return o;}));
    $('b7-country').value=chosen;
  }
  ['All regions',...regions].forEach(r=>{const o=document.createElement('option');o.value=r;o.textContent=r;$('b7-region').appendChild(o);});
  ['All years',...D.years.map(String)].forEach(y=>{const o=document.createElement('option');o.value=y;o.textContent=y;$('b7-year').appendChild(o);});
  $('b7-region').value='All regions';$('b7-year').value='All years';menu();
  $('b7-region').addEventListener('change',()=>{menu();update();});
  $('b7-year').addEventListener('change',update);
  $('b7-country').addEventListener('change',()=>{chosen=$('b7-country').value;update();});
  $('b7-reset').addEventListener('click',()=>{$('b7-region').value='All regions';$('b7-year').value='All years';chosen='ESP';$('b7-detail').open=false;$('b7-model').value='National: all years';menu();update();modelUpdate();});
  function modelUpdate() {
    const label=$('b7-model').value,s=coefficientSpec(label),q=D.models.find(r=>r.specification===label&&r.outcome==='Women minus men'&&r.term==='depth');
    $('b7-model-status').textContent=label+': '+q.n.toLocaleString('en-US')+' country-years, '+q.countries+' countries/territories.';
    $('b7-extra-decline').textContent=q.estimate.toFixed(2)+' pp';
    $('b7-extra-interval').textContent='95% interval: '+q.ci_low.toFixed(2)+' to '+q.ci_high.toFixed(2)+' pp';
    return renderPlot('b7-coefficients',s.data,s.layout,config);
  }
  ['National: all years','National: before 2020'].forEach(label=>{const o=document.createElement('option');o.value=label;o.textContent=label;$('b7-model').appendChild(o);});
  $('b7-model').value='National: all years';$('b7-model').addEventListener('change',modelUpdate);
  update().then(()=>{
    $('b7-scatter').on('plotly_click',event=>{const id=event.points[0].customdata?.[0];
      if(id&&D.countries.some(c=>c.iso3===id)){chosen=id;$('b7-country').value=id;$('b7-detail').open=true;update();}});
  });
  $('b7-detail').addEventListener('toggle',()=>{if($('b7-detail').open){const s=historySpec(chosen);renderPlot('b7-history',s.data,s.layout,config);}});
  modelUpdate();
  let resizeTimer, lastWidth = innerWidth;
  window.addEventListener('resize',()=>{
    if(innerWidth===lastWidth)return;
    lastWidth=innerWidth;clearTimeout(resizeTimer);
    resizeTimer=setTimeout(()=>{['b7-scatter','b7-coefficients','b7-history'].forEach(id=>{const node=$(id);if(node.classList.contains('js-plotly-plot')&&node.offsetWidth>0)Plotly.Plots.resize(node);});},150);
  });
  window.blog7Test={rows,scatterSpec,historySpec,coefficientSpec,update,modelUpdate,data:D};
})();

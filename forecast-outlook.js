/* FarmConnect forecast presentation. Never present synthetic samples as actual market prices. */
(()=>{
  const API='https://qlfsmwvehigoildkuevq.supabase.co/functions/v1/farmconnect-api';
  const el=(id)=>document.getElementById(id);
  const commodity=el('fcForecastCommodity'),market=el('fcForecastMarket'),months=el('fcForecastMonths');
  const form=el('fcForecastForm'),button=el('fcForecastSubmit');
  const status=el('fcForecastStatus'),results=el('fcForecastResults');
  if(!form||!commodity||!market||!results)return;
  const money=(amount)=>'ZMW '+Number(amount).toLocaleString('en-ZM',{minimumFractionDigits:2,maximumFractionDigits:2});
  const readable=(date)=>new Date(date+'T00:00:00Z').toLocaleDateString('en-ZM',{month:'short',year:'numeric',timeZone:'UTC'});
  const say=(message,kind='info')=>{status.textContent=message;status.dataset.kind=kind;};
  const get=async(path)=>{
    const response=await fetch(API+path,{headers:{'Accept':'application/json'}});
    const data=await response.json();
    if(!response.ok||data.success===false){
      const error=new Error(data.error||'Forecast data unavailable');
      error.code=data.code;throw error;
    }
    return data;
  };
  const fill=(node,rows,name)=>{
    node.replaceChildren();
    for(const entry of rows){
      const option=document.createElement('option');
      option.value=entry.name;option.textContent=entry.name;node.append(option);
    }
    if(rows.some(x=>x.name===name))node.value=name;
  };
  function svgChart(history,forecasts){
    const svg=el('fcForecastSVG');svg.replaceChildren();
    const namespace='http://www.w3.org/2000/svg';
    const create=(tag,attrs={})=>{const node=document.createElementNS(namespace,tag);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,String(value));return node;};
    const all=[...history.map(x=>Number(x.price)),...forecasts.flatMap(x=>[x.predicted_price,x.lower_estimate,x.upper_estimate])].filter(Number.isFinite);
    if(!all.length)return;
    const width=900,height=265,padding={left:58,right:18,top:18,bottom:36};
    const low=Math.max(0,Math.min(...all)*.93),high=Math.max(...all)*1.07;
    const range=high-low||1,count=history.length+forecasts.length;
    const x=(index)=>padding.left+(width-padding.left-padding.right)*index/Math.max(1,count-1);
    const y=(value)=>padding.top+(height-padding.top-padding.bottom)*(1-(value-low)/range);
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    svg.setAttribute('role','img');
    svg.setAttribute('aria-label','Historical and forecast price trends in Zambian kwacha. Exact prices are shown in the table.');
    for(let i=0;i<4;i++){
      const value=low+(high-low)*i/3,yy=y(value);
      svg.append(create('line',{x1:padding.left,y1:yy,x2:width-padding.right,y2:yy,stroke:'currentColor','stroke-opacity':'.13'}));
      const label=create('text',{x:padding.left-8,y:yy+4,'text-anchor':'end',fill:'currentColor','font-size':'12'});
      label.textContent=value.toFixed(0);svg.append(label);
    }
    const histPoints=history.map((p,i)=>`${x(i)},${y(p.price)}`).join(' ');
    if(history.length>1)svg.append(create('polyline',{points:histPoints,fill:'none',stroke:'#25784c','stroke-width':'2.5','stroke-linejoin':'round','stroke-linecap':'round'}));
    const anchor=history[history.length-1];
    const forecastPoints=[`${x(history.length-1)},${y(anchor.price)}`,...forecasts.map((p,i)=>`${x(history.length+i)},${y(p.predicted_price)}`)].join(' ');
    svg.append(create('polyline',{points:forecastPoints,fill:'none',stroke:'#c18736','stroke-width':'2.5','stroke-dasharray':'6 5'}));
    for(const [i,p] of forecasts.entries()){
      const xx=x(history.length+i);
      svg.append(create('line',{x1:xx,y1:y(p.lower_estimate),x2:xx,y2:y(p.upper_estimate),stroke:'#c18736','stroke-width':'6','stroke-opacity':'.28'}));
      svg.append(create('circle',{cx:xx,cy:y(p.predicted_price),r:4,fill:'#c18736'}));
      const label=create('text',{x:xx,y:height-9,'text-anchor':'middle',fill:'currentColor','font-size':'12'});
      label.textContent=readable(p.date);svg.append(label);
    }
    const recentLabel=create('text',{x:x(0),y:height-9,fill:'currentColor','font-size':'12'});
    recentLabel.textContent=readable(history[0].date);svg.append(recentLabel);
  }
  function render(data){
    results.hidden=false;
    el('fcForecastDataLabel').textContent='Sourced historical market data';
    el('fcForecastModel').textContent=data.model_used;
    el('fcForecastObservations').textContent=String(data.observations)+' recorded dates';
    el('fcForecastCurrent').textContent=money(data.current_price);
    el('fcForecastFirst').textContent=money(data.forecast[0].predicted_price);
    el('fcForecastLast').textContent=money(data.forecast[data.forecast.length-1].predicted_price);
    el('fcForecastUnit').textContent='Prices per '+data.unit;
    el('fcForecastChartTitle').textContent=data.commodity+' — '+data.market;
    el('fcForecastExplanation').textContent=data.notice;
    const tbody=el('fcForecastRows');tbody.replaceChildren();
    for(const row of data.forecast){
      const tr=document.createElement('tr');
      for(const value of [readable(row.date),money(row.predicted_price),money(row.lower_estimate)+' – '+money(row.upper_estimate)]){
        const td=document.createElement('td');td.textContent=value;tr.append(td);
      }
      tbody.append(tr);
    }
    svgChart(data.historical,data.forecast);
    say(data.notice,'verified');
  }
  async function requestForecast(){
    if(!commodity.value||!market.value)return;
    button.disabled=true;results.hidden=true;say('Checking historical prices and calculating outlook…');
    const params=new URLSearchParams({commodity:commodity.value,market:market.value,months:months.value});
    try{render(await get('/forecast?'+params.toString()))}
    catch(err){
      if(err.code==='INSUFFICIENT_HISTORY'){
        say(err.message,'error');
      }else say(err.message||'Unable to load the forecast. Please try again.','error');
    }finally{button.disabled=false}
  }
  form.addEventListener('submit',event=>{event.preventDefault();requestForecast()});
  Promise.all([get('/commodities'),get('/markets')])
    .then(([commodities,markets])=>{
      fill(commodity,commodities.commodities||[],'Maize');
      fill(market,markets.markets||[],'National Average');
      requestForecast();
    })
    .catch(()=>say('Market and commodity options could not be loaded. Check your connection and refresh.','error'));
})();

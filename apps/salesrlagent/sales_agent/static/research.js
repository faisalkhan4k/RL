async function refresh(){
 const r=await fetch('/api/research');if(!r.ok){document.getElementById('action').textContent='Open the store and start a conversation first.';return;}
 const {latest:d,voice}=await r.json();document.getElementById('action').textContent=d.executed_action||'No turn yet';
 document.getElementById('provenance').textContent=`Policy: ${d.strategy_policy?.source||'not run'} • Language: ${d.language_source||'not run'}`;
 document.getElementById('belief').textContent=JSON.stringify(d.belief||{},null,2);
 document.getElementById('override').textContent=d.override?`Customer/safety override: ${d.override}`:'No override';
 const host=document.getElementById('distribution');host.replaceChildren();
 Object.entries(d.strategy_policy?.probabilities||{}).sort((a,b)=>b[1]-a[1]).slice(0,8).forEach(([name,value])=>{const row=document.createElement('p');row.textContent=`${name}: ${(value*100).toFixed(1)}% `;const meter=document.createElement('progress');meter.max=1;meter.value=value;row.append(meter);host.append(row);});
 if(voice){const heading=document.createElement('h2');heading.textContent=`Voice: ${voice.action} (${voice.source})`;host.append(heading);Object.entries(voice.probabilities).sort((a,b)=>b[1]-a[1]).forEach(([name,p])=>{const row=document.createElement('p');row.textContent=`${name}: ${(p*100).toFixed(1)}%`;host.append(row);});}
}
document.getElementById('refresh').onclick=refresh;refresh();

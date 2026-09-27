'use strict';
const $ = id => document.getElementById(id);
let catalog = [], cart = [], lastTurn = null, busy = false, voice = false, handsFree = false;
function el(tag, className, text) { const n = document.createElement(tag); if (className) n.className = className; if (text !== undefined) n.textContent = text; return n; }
async function api(path, method='GET', data) {
  const response = await fetch(path, {method, headers: data ? {'Content-Type':'application/json'} : {}, body:data ? JSON.stringify(data) : undefined});
  let result; try { result = await response.json(); } catch { throw new Error('The store is unavailable. Please try again.'); }
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Please check your input and try again.');
  return result;
}
function error(message) { $('error').textContent=message; $('error').hidden=!message; }
let toastTimer;
function toast(message) { $('toast').textContent=message; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,3500); }
function bubble(role, text) { $('conversation').append(el('div',`bubble ${role}`,text)); $('conversation').scrollTop=$('conversation').scrollHeight; }
function renderProducts(products, highlights=[]) {
  $('products').replaceChildren(); $('result-count').textContent=`${products.length} ${products.length===1?'product':'products'} to explore`;
  if (!products.length) { $('products').append(el('p','empty','No exact matches. Try a different budget or feature.')); return; }
  products.forEach(p=>{
    const card=el('article',`product${highlights.includes(p.id)?' recommended':''}`); card.id=`product-${p.id}`;
    const art=el('div','product-art'); art.setAttribute('aria-hidden','true');
    art.append(el('span','product-emoji',p.icon || '◻'));
    if (highlights.includes(p.id)) art.append(el('span','badge','YOUR GUIDE’S PICK'));
    const heading=el('div','product-heading'); heading.append(el('h3','',p.name),el('span','price',`$${p.price}`));
    const detail=el('details'); detail.append(el('summary','','Specs & trade-offs'));
    const specs=el('dl','spec-list'); Object.entries(p.specs||{}).forEach(([key,value])=>specs.append(el('dt','',key),el('dd','',value)));
    detail.append(specs,el('p','',`Good for: ${p.features.join(' · ')}`),el('p','',`Know before buying: ${p.tradeoff}`));
    const add=el('button','add-button','Add to bag +'); add.addEventListener('click',async()=>{
      add.disabled=true;
      try { const qty=(cart.find(x=>x.product_id===p.id)?.quantity||0)+1; if(qty>5) throw new Error('Maximum five of each item in this demo.'); const result=await api('/api/cart','PUT',{product_id:p.id,quantity:qty}); cart=result.cart; renderCart(); toast(`${p.name} added to your cart`); } catch(e) {error(e.message);} finally {add.disabled=false;}
    });
    add.textContent='Add to cart +'; card.append(art,heading,el('p','product-description',p.description),detail,add); $('products').append(card);
  });
}
function renderRequirements(req) {
  $('requirements').replaceChildren();
  const labels=[req.category||req.department,req.budget!==undefined?`Up to $${req.budget}`:null,...(req.features||[]),...(req.uses||[]),req.use].filter(Boolean);
  labels.forEach(x=>$('requirements').append(el('span','chip',x)));
}
const controller=new VoiceController({
  status:state=>{
    handsFree=controller.enabled;
    $('mic').textContent=handsFree?'Stop talking':'Start talking';
    $('mic').setAttribute('aria-pressed',String(handsFree));
    $('voice-orb').classList.toggle('listening',state==='listening');
    const labels={off:'Voice is off',connecting:'Connecting microphone…',listening:'I am listening',thinking:'Thinking…',preparing:'Preparing my reply…',speaking:'Speaking — microphone paused',waiting:'Getting ready to listen…'};
    $('guide-status').textContent=labels[state]||state;
    $('interrupt').hidden=!['speaking','preparing'].includes(state);
  },transcript:text=>{$('chat-input').value=text;},turn:send,error
});
function scheduleListening(){if(!busy&&controller.enabled&&controller.state==='thinking')controller.resume();}
function stopAudio(resume=true){controller.cancelPlayback();if(resume)controller.resume();}
function speak(text){if(voice)controller.speak(text);else controller.resume();}
function setBusy(value) { busy=value; document.querySelectorAll('#chat-form button,#search-form button,.suggestions button,nav button,#clear-search,#reset').forEach(b=>b.disabled=value); $('guide-status').textContent=value?'Finding your fit…':(handsFree?'Microphone ready…':'Ready when you are'); if(!value)scheduleListening(); }
async function send(text) {
  text=text.trim(); if(!text || busy) return; stopAudio(false); controller.pause(); error(''); setBusy(true); lastTurn=null; $('rating').hidden=true; bubble('user',text); $('chat-input').value='';
  try {
    const result=await api('/api/chat','POST',{text,request_id:crypto.randomUUID()});
    bubble('assistant',result.reply); renderRequirements(result.requirements);
    const highlighted=result.actions.filter(a=>a.type==='highlight').flatMap(a=>a.product_ids);
    renderProducts(result.products,highlighted); $('comparison').hidden=true;
    const compare=result.actions.find(a=>a.type==='compare');
    if(compare) { $('comparison').replaceChildren(el('h3','','Side by side')); compare.product_ids.forEach(id=>{const p=catalog.find(x=>x.id===id); if(p) $('comparison').append(el('p','',`${p.name} · $${p.price} — ${p.features.join(', ')}. Trade-off: ${p.tradeoff}.`));}); $('comparison').hidden=false; }
    document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.category===(result.requirements.category||'all')));
    lastTurn=result.turn_id; $('rating').hidden=false; document.querySelectorAll('[data-rating]').forEach(b=>b.disabled=false);
    $('trace-status').textContent=`Last response: ${result.latency_ms} ms · Trace ${result.trace_id}`;
    $('model-status').textContent=`Strategy: ${result.strategy}. Source: ${result.debug.strategy_policy.source}. Wording: ${result.debug.language_source}.`;
    setBusy(false); speak(result.reply);
  } catch(e) { error(e.message); setBusy(false); }
}
function renderCart() {
  $('bag-count').textContent=cart.reduce((sum,x)=>sum+x.quantity,0); $('bag-items').replaceChildren();
  let total=0;
  cart.forEach(item=>{ const p=catalog.find(x=>x.id===item.product_id); if(!p) return; total+=p.price*item.quantity; const row=el('div','bag-row'); row.append(el('span','',`${p.name} × ${item.quantity}`),el('span','',`$${p.price*item.quantity}`)); const remove=el('button','','Remove'); remove.onclick=async()=>{try{cart=(await api('/api/cart','PUT',{product_id:p.id,quantity:0})).cart;renderCart();}catch(e){toast(e.message);}}; row.append(remove); $('bag-items').append(row); });
  if(!cart.length) $('bag-items').append(el('p','','Your cart is waiting for a good fit.'));
  $('bag-total').textContent=`Total $${total}`; $('checkout').disabled=!cart.length;
}
$('chat-form').onsubmit=e=>{e.preventDefault();send($('chat-input').value);};
$('search-form').onsubmit=e=>{e.preventDefault();send($('search-input').value);};
document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>send(b.dataset.prompt));
document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>send(b.dataset.category==='all'?'start over':`start over, show me ${b.dataset.category}`));
$('clear-search').onclick=()=>send('start over');
$('bag-button').onclick=()=>{$('checkout-status').textContent='';renderCart();$('bag').showModal();}; $('close-bag').onclick=()=>$('bag').close();
$('checkout').onclick=async()=>{ $('checkout').disabled=true; try{const result=await api('/api/checkout','POST');cart=[];renderCart();$('checkout-status').textContent=result.message;}catch(e){$('checkout-status').textContent=e.message;$('checkout').disabled=false;} };
document.querySelectorAll('[data-rating]').forEach(b=>b.onclick=async()=>{if(!lastTurn)return;try{await api('/api/feedback','POST',{turn_id:lastTurn,helpful:b.dataset.rating==='true'});document.querySelectorAll('[data-rating]').forEach(x=>x.disabled=true);toast('Thanks. Your feedback is saved.');}catch(e){error(e.message);}});
$('reset').onclick=async()=>{if(busy)return;stopAudio(false);controller.pause();try{await api('/api/session','DELETE');await api('/api/session','POST');cart=[];lastTurn=null;$('conversation').replaceChildren();$('rating').hidden=true;$('comparison').hidden=true;renderRequirements({});renderProducts(catalog);renderCart();error('');toast('Conversation and cart deleted');scheduleListening();}catch(e){error(e.message);}};
$('mute').onclick=()=>{voice=!voice;$('mute').textContent=`Read replies aloud: ${voice?'on':'off'}`;$('mute').setAttribute('aria-pressed',String(voice));if(!voice)stopAudio();};
$('mic').onclick=async()=>{
  if(controller.enabled){controller.stop();return;}
  if(busy)return;error('');voice=true;$('mute').textContent='Read replies aloud: on';$('mute').setAttribute('aria-pressed','true');await controller.start();
};
$('interrupt').onclick=()=>controller.interrupt();
window.addEventListener('pagehide',()=>controller.stop());
document.addEventListener('visibilitychange',()=>{if(document.hidden&&controller.enabled)controller.stop();});
async function init() { setBusy(true);try{const [data,session]=await Promise.all([api('/api/catalog'),api('/api/session','POST')]);catalog=data.products;cart=session.cart;renderProducts(session.products);renderRequirements(session.requirements);renderCart();session.messages.forEach(m=>bubble(m.role,m.content));$('model-status').textContent=session.model==='not_trained'?'Conversion model: not trained. Recommendations use catalog rules.':'Experimental conversion model loaded; estimates are not calibrated for real shoppers.';}catch(e){error(e.message);}finally{setBusy(false);} }
init();

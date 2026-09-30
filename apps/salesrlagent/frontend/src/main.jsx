import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import '../../sales_agent/static/cascade-controller.js';
import {ProductArt,VoiceGraphic} from './graphics.jsx';
import './storefront.css';

async function api(path,method='GET',data){
 const r=await fetch(path,{method,headers:data?{'Content-Type':'application/json'}:{},body:data?JSON.stringify(data):undefined});
 const body=await r.json();if(!r.ok)throw new Error(typeof body.detail==='string'?body.detail:'Please try again.');return body;
}
const labels={off:'Ready when you are.',connecting:'Connecting microphone…',listening:'I am listening',thinking:'Thinking — you can keep talking',preparing:'Preparing my reply…',speaking:'Speaking — you can interrupt me',waiting:'Getting ready to listen…'};
const money=value=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(value);
const categoryName=value=>value==='earbuds'?'Earphones & earbuds':value.charAt(0).toUpperCase()+value.slice(1);
function Mic(){return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><rect x="9" y="2" width="6" height="13" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/></svg>;}
function App(){
 const [route,setRoute]=useState(location.pathname),[orderId,setOrderId]=useState('DEMO-1001');
 const pageTitle=useRef(null);
 function navigate(path){if(location.pathname!==path)history.pushState({},'',path);setRoute(path);}
 function Link({to,children,...props}){return <a href={to} {...props} onClick={e=>{if(!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.altKey){e.preventDefault();navigate(to);}}}>{children}</a>;}
 useEffect(()=>{const back=()=>setRoute(location.pathname);window.addEventListener('popstate',back);return()=>window.removeEventListener('popstate',back);},[]);

 const [products,setProducts]=useState([]),[catalog,setCatalog]=useState([]),[messages,setMessages]=useState([]),[cart,setCart]=useState([]);
 const [text,setText]=useState(''),[status,setStatus]=useState('off'),[error,setError]=useState(''),[busy,setBusy]=useState(true),[voice,setVoice]=useState(false);
 const [highlights,setHighlights]=useState([]),[comparison,setComparison]=useState(false),[notice,setNotice]=useState(''),[debug,setDebug]=useState(null);
 const [turn,setTurn]=useState(null),[rated,setRated]=useState(false),[voiceDecision,setVoiceDecision]=useState(null);
 const controller=useRef(null),sendRef=useRef(null),busyRef=useRef(true),voiceRef=useRef(false),bag=useRef(null),log=useRef(null);
 const chat=useRef(null),settings=useRef(null),details=useRef(null),orb=useRef(null),level=useRef(0);
 const [selected,setSelected]=useState(null),[department,setDepartment]=useState('All'),[page,setPage]=useState(0),[pageSize,setPageSize]=useState(2);
 const applyRef=useRef(null);const [focusId,setFocusId]=useState(null);
 const setWorking=v=>{busyRef.current=v;setBusy(v);};
 useEffect(()=>{
  controller.current=new window.CascadeController({status:setStatus,transcript:setText,level:v=>{level.current=v;},error:message=>{setError(message);setWorking(false);},
    user:(text,generation)=>{setWorking(false);setMessages(m=>[...m,{role:'user',content:text}]);setTurn(null);setRated(false);},
    assistant:(text,generation)=>setMessages(m=>{const found=m.findIndex(x=>x.streamGeneration===generation);return found<0?[...m,{role:'assistant',content:text,streamGeneration:generation}]:m.map((x,i)=>i===found?{...x,content:text}:x);}),
    result:r=>applyRef.current(r),focus:id=>setFocusId(id)
  });
  const onHide=()=>{if(document.hidden)controller.current.stop();};
  const onPolicy=e=>setVoiceDecision(e.detail);
  document.addEventListener('visibilitychange',onHide);window.addEventListener('voice-policy',onPolicy);
  Promise.all([api('/api/catalog'),api('/api/session','POST')]).then(([c,s])=>{setCatalog(c.products);setProducts(c.products);setMessages(s.messages);setCart(s.cart);}).catch(e=>setError(e.message)).finally(()=>setWorking(false));
  return()=>{controller.current.stop();document.removeEventListener('visibilitychange',onHide);window.removeEventListener('voice-policy',onPolicy);};
 },[]);
 useEffect(()=>{log.current?.scrollTo({top:log.current.scrollHeight,behavior:'auto'});},[messages]);
 async function send(value){
  if(!value.trim()||busyRef.current)return;
  if(controller.current.enabled){controller.current.sendText(value);setText('');return;}
  controller.current.cancelPlayback();controller.current.pause();setWorking(true);setError('');setText('');setTurn(null);setRated(false);
  setMessages(m=>[...m,{role:'user',content:value}]);
  try{
   const r=await api('/api/chat','POST',{text:value,request_id:crypto.randomUUID()});
   setMessages(m=>[...m,{role:'assistant',content:r.reply}]);applyRef.current(r);
   setWorking(false);
  }catch(e){setError(e.message);setWorking(false);controller.current.resume();}
 }
 sendRef.current=send;
 async function toggleVoice(){
  if(controller.current.enabled){controller.current.stop();return;}
  setError('');setVoice(true);voiceRef.current=true;controller.current.setMuted(false);await controller.current.start();
 }
 async function changeCart(id,quantity){try{const r=await api('/api/cart','PUT',{product_id:id,quantity});setCart(r.cart);setNotice(quantity?'Added to your cart.':'Removed from your cart.');}catch(e){setError(e.message);}}
 async function reset(){controller.current.stop();setWorking(true);try{await api('/api/session','DELETE');const s=await api('/api/session','POST');setMessages([]);setCart([]);setProducts(catalog);setDepartment('All');setPage(0);setHighlights([]);setDebug(null);setTurn(null);setText('');setError('');setNotice('Conversation cleared.');}catch(e){setError(e.message);}finally{setWorking(false);}}

 useEffect(()=>{
  const resize=()=>setPageSize(window.innerWidth<720?1:window.innerWidth>=1200?4:3);
  resize();window.addEventListener('resize',resize);return()=>window.removeEventListener('resize',resize);
 },[]);
 useEffect(()=>setPage(0),[pageSize]);
 useEffect(()=>{
  let frame;const samples=new Uint8Array(256);
  const animate=()=>{const c=controller.current;let power=level.current;
   if(c?.state==='speaking'&&c.analyser){c.analyser.getByteTimeDomainData(samples);power=Math.sqrt(samples.reduce((sum,x)=>sum+((x-128)/128)**2,0)/samples.length);}
   orb.current?.style.setProperty('--level',String(Math.min(1,power*5)));
   frame=requestAnimationFrame(animate);
  };frame=requestAnimationFrame(animate);return()=>cancelAnimationFrame(frame);
 },[]);
 useEffect(()=>{
  if(route==='/recommendations'||route==='/cart'||route==='/orders')return;
  const category=route.startsWith('/categories/')?decodeURIComponent(route.slice(12)):null;
  const sales=catalog.filter(p=>p.compare_at_price>p.price);
  setProducts(route==='/deals'?sales.slice(0,1):route==='/sales'?sales:category?catalog.filter(p=>p.category===category):catalog);
  setDepartment(category||'All');setPage(0);setHighlights([]);setFocusId(null);setComparison(false);
 },[route,catalog]);
 useEffect(()=>{document.title=(route==='/cart'?'Your cart':route==='/orders'?'Order lookup':route==='/deals'?'Deal of the day':route==='/sales'?'Sales':'Shop')+' · CircuitWise';document.querySelector('.workspace')?.scrollTo(0,0);},[route]);
 const enabled=controller.current?.enabled||false;
 const pages=Math.max(1,Math.ceil(products.length/pageSize)),currentPage=Math.min(page,pages-1);
 const visibleProducts=products.slice(currentPage*pageSize,(currentPage+1)*pageSize);
 const categories=[...new Set(catalog.map(p=>p.category))];
 function browse(value){navigate(value==='All'?'/categories':'/categories/'+encodeURIComponent(value));setFocusId(null);setDepartment(value);setPage(0);setHighlights([]);setComparison(false);setProducts(value==='All'?catalog:catalog.filter(p=>p.category===value));}
 function applyResult(r){
  const pageAction=r.actions.find(a=>a.type==='navigate_page');
  if(pageAction&&['/','/deals','/sales','/categories','/orders'].includes(pageAction.path)){chat.current?.close();navigate(pageAction.path);}
  const navigation=r.actions.find(a=>a.type==='navigate_products');
  const openCart=r.actions.some(a=>a.type==='open_cart');
  if(r.actions.some(a=>a.type==='close_panels')){navigate('/categories');bag.current?.close();chat.current?.close();settings.current?.close();details.current?.close();}
  if(r.cart)setCart(r.cart);
  if(r.strategy!=='CUSTOMER_COMMAND'||r.actions.some(a=>a.type==='highlight')){
   navigate('/recommendations');setProducts(r.products);setDepartment('Recommended');setPage(0);setFocusId(r.focus_product_id||null);
   setHighlights(r.actions.flatMap(a=>a.product_ids||[]));setComparison(r.actions.some(a=>a.type==='compare'));
  }
  if(r.strategy==='CUSTOMER_COMMAND'&&(navigation||r.focus_product_id))chat.current?.close();
  if(navigation)setPage(p=>Math.max(0,Math.min(pages-1,p+navigation.direction)));
  if(openCart){chat.current?.close();details.current?.close();settings.current?.close();navigate('/cart');}
  setDebug(r.debug);setTurn(r.turn_id);
 }
 applyRef.current=applyResult;
 useEffect(()=>{if(focusId){const index=products.findIndex(p=>p.id===focusId);if(index>=0){setPage(Math.floor(index/pageSize));setHighlights([focusId]);}}},[focusId,products,pageSize]);
 const viewKey=visibleProducts.map(p=>p.id).join(',');
 useEffect(()=>{if(!viewKey)return;const ids=viewKey.split(',');const abort=new AbortController();
  fetch('/api/view',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_ids:ids,focused_product:ids.includes(focusId)?focusId:ids[0]}),signal:abort.signal}).catch(e=>{if(e.name!=='AbortError')setError('Could not sync the product view. Please reconnect.');});
  return()=>abort.abort();
 },[viewKey,focusId]);
 function showProduct(p){setFocusId(p.id);setSelected(p);details.current.showModal();}
 const lastReply=messages.filter(m=>m.role==='assistant').at(-1)?.content;
 return <div className="app-shell">
 <header className="site-header"><Link className="brand" to="/" aria-label="CircuitWise home"><span className="brand-mark">c<span>↗</span></span>CircuitWise</Link><nav aria-label="Main"><Link to="/" aria-current={route==='/'?'page':undefined}>Home</Link><Link to="/deals" aria-current={route==='/deals'?'page':undefined}>Deal of the day</Link><Link to="/sales" aria-current={route==='/sales'?'page':undefined}>Sales</Link><Link to="/categories" aria-current={route.startsWith('/categories')?'page':undefined}>Categories</Link><Link to="/orders" aria-current={route==='/orders'?'page':undefined}>Order lookup</Link></nav><div className="header-tools"><button onClick={()=>settings.current.showModal()} aria-label="Settings">⚙</button><Link className="cart-button" to="/cart">Cart <span aria-live="polite">{cart.reduce((n,p)=>n+p.quantity,0)}</span></Link></div></header>
 <main className="workspace">
  {route!=='/cart'&&route!=='/orders'&&<section className={'shop'+(route==='/deals'?' featured':'')} aria-label="Product selection">
   <div className="shop-heading"><div><p className="eyebrow">{route==='/deals'?'A LITTLE MORE FOR LESS':route==='/sales'?'THE SAVINGS EDIT':route==='/recommendations'?'YOUR PERSONAL SHORTLIST':'CURATED TECH. HUMAN GUIDANCE.'}</p><h1 ref={pageTitle} tabIndex="-1">{route==='/'?'Good tech. Your kind.':route==='/deals'?'Deal of the day.':route==='/sales'?'Worth a closer look.':department==='Recommended'?'Picked for you.':department==='All'?'Find your category.':categoryName(department)+'.'}</h1></div><p className="page-intro">{route==='/'?'Tell us what matters. Find something that fits.':route==='/deals'?'Our featured saving from the manufacturer price snapshot.':route==='/sales'?'Products with a lower listed price in our snapshot.':'Browse at your pace. Your guide is always nearby.'}</p></div>
   <div className="category-strip" aria-label="Product categories"><Link to="/categories" aria-current={route==='/categories'?'page':undefined}>All products</Link>{categories.map(c=><Link key={c} to={'/categories/'+encodeURIComponent(c)} aria-current={department===c?'page':undefined}>{categoryName(c)}</Link>)}</div>
   <p className="selection-note">{catalog.length} real products · Manufacturer price references reviewed September 27, 2026 · Demo cart and inventory.{route==='/deals'&&' Featured pick, not a retailer’s timed promotion.'}</p>
   <div className="products">{visibleProducts.map(p=><article className={`product ${highlights.includes(p.id)?'recommended':''}`} key={p.id}><button className="product-visual" onClick={()=>showProduct(p)} aria-label={`View ${p.name}`}><span className="product-category">{highlights.includes(p.id)?'YOUR MATCH':p.category}</span><ProductArt category={p.category}/><span className="art-label">Illustration</span><span className="expand-icon" aria-hidden="true">↗</span></button><div className="product-info"><div className="product-heading"><h3>{p.name}</h3><span className="price">{p.compare_at_price&&<del>{money(p.compare_at_price)}</del>}{money(p.price)}</span></div><p className="product-description">{p.description}</p><span className="price-context">{p.price_kind==='launch_reference'?'Launch reference price':p.compare_at_price?'Manufacturer sale snapshot':'Manufacturer price snapshot'}</span><div className="spec-chips">{Object.values(p.specs).slice(0,2).map((v,i)=><span key={i}>{v}</span>)}</div><div className="product-actions"><button onClick={()=>showProduct(p)}>View details ↗</button><button className="add-button" aria-label={`Add ${p.name} to cart`} onClick={()=>changeCart(p.id,(cart.find(x=>x.product_id===p.id)?.quantity||0)+1)}>Add +</button></div></div></article>)}
   {!products.length&&<div className="empty"><h3>Let's try another direction.</h3><p>Change the category or tell me a different budget.</p><button onClick={()=>browse('All')}>Explore all products</button></div>}</div>
   <div className="catalog-footer"><span>{products.length?`${currentPage*pageSize+1}–${Math.min((currentPage+1)*pageSize,products.length)} of ${products.length} products`:'No matching products'}</span><div className="pager"><button aria-label="Previous products" disabled={currentPage===0} onClick={()=>{setFocusId(null);setPage(currentPage-1);}}>←</button><span>{currentPage+1} / {pages}</span><button aria-label="Next products" disabled={currentPage>=pages-1} onClick={()=>{setFocusId(null);setPage(currentPage+1);}}>→</button></div></div>
   <button className="reply-preview" onClick={()=>chat.current.showModal()}><span className="tiny-dot"/><span>{lastReply||'Not sure where to start? Ask me about your next laptop, phone, or everyday upgrade.'}</span><span aria-hidden="true">↗</span></button>
  </section>}
  {route==='/orders'&&<section className="order-page"><p className="eyebrow">CONNECTED THROUGH MCP</p><h1>Where is my order?</h1><p>This local demo uses sample orders. No real store or customer records are connected.</p><form onSubmit={e=>{e.preventDefault();send('Where is order '+orderId+'?');chat.current.showModal();}}><label htmlFor="order-id">Demo order number</label><input id="order-id" value={orderId} onChange={e=>setOrderId(e.target.value)} pattern="DEMO-100[123]" required/><button className="primary" disabled={busy}>Check order ↗</button></form><div className="sample-orders">{['DEMO-1001','DEMO-1002','DEMO-1003'].map(id=><button key={id} onClick={()=>setOrderId(id)}>{id}</button>)}</div><p className="selection-note">Read-only tools: inventory lookup · order lookup</p></section>}
 {route==='/cart'&&<section className="cart-page" aria-labelledby="cart-title"><div className="dialog-heading"><h2 id="cart-title">Your cart</h2><Link to="/categories">Continue shopping ↗</Link></div>{!cart.length&&<p>Your next great find belongs here.</p>}{cart.map(i=>{const p=catalog.find(p=>p.id===i.product_id);return <div className="bag-row" key={i.product_id}><span>{p?.name} × {i.quantity}</span><span>{money((p?.price||0)*i.quantity)}</span><button onClick={()=>changeCart(i.product_id,0)}>Remove</button></div>;})}<p className="cart-total">Total: {money(cart.reduce((n,i)=>n+(catalog.find(p=>p.id===i.product_id)?.price||0)*i.quantity,0))}</p><p>Demo only. No payment will be taken.</p><button className="primary" disabled={!cart.length} onClick={async()=>{try{const r=await api('/api/checkout','POST');setCart([]);setNotice(r.message);navigate('/categories');}catch(e){setError(e.message);}}}>Complete demo checkout</button></section>}
 </main>
 <footer className="voice-dock" aria-label="Voice assistant"><div className="dock-meta"><span className="status-label" role="status"><i className={enabled?'online':''}/>{busy?'Finding your fit…':labels[status]}</span><a href="https://github.com/faisalkhan4k/RL" target="_blank" rel="noopener noreferrer">View on GitHub ↗</a></div><button className="voice-pill" aria-label={enabled?'End conversation':'Talk to CircuitWise'} aria-pressed={enabled} disabled={busy&&!enabled} onClick={toggleVoice}><VoiceGraphic status={busy?'thinking':status} orbRef={orb}/><span>{enabled?'End conversation':'Talk to CircuitWise'}</span><span className="mic-circle"><Mic/></span></button><div className="dock-actions"><button className="chat-launch" onClick={()=>chat.current.showModal()}>Type / history ↗</button>{['speaking','thinking','preparing'].includes(status)&&<button onClick={()=>controller.current.interrupt()}>Stop reply</button>}<span role="status">{notice}</span></div>{error&&<div className="error" role="alert">{error}</div>}</footer>
 <dialog className="chat-dialog" ref={chat} aria-labelledby="chat-title"><div className="dialog-heading"><div><p className="eyebrow">AT YOUR PACE</p><h2 id="chat-title">Our conversation</h2></div><button aria-label="Close conversation" onClick={()=>chat.current.close()}>✕</button></div><div ref={log} className="conversation" role="log" aria-label="Conversation" aria-live="polite">{!messages.length&&<div className="chat-empty"><h3>What are you looking for?</h3><p>Tell me about your day, your budget, or the device you have in mind.</p><div className="suggestions">{['A laptop for school','Earphones under $150','A phone under $500'].map(x=><button disabled={busy} key={x} onClick={()=>send(x)}>{x} ↗</button>)}</div></div>}{messages.map((m,i)=><div key={i} className={`bubble ${m.role}`}><span>{m.role==='user'?'YOU':'CIRCUITWISE'}</span><p>{m.content}</p></div>)}</div><form className="chat-form" onSubmit={e=>{e.preventDefault();send(text);}}><label className="sr-only" htmlFor="question">Your question</label><input autoComplete="off" id="question" value={text} onChange={e=>setText(e.target.value)} placeholder="Type your question…" maxLength={2000} required/><button className="primary" disabled={busy}>Send ↗</button></form>{turn&&!rated&&<div className="rating">Was that helpful?{[true,false].map(v=><button key={String(v)} onClick={async()=>{try{await api('/api/feedback','POST',{turn_id:turn,helpful:v});setRated(true);}catch(e){setError(e.message);}}}>{v?'Yes':'No'}</button>)}</div>}</dialog>
 <dialog ref={settings} aria-labelledby="settings-title"><div className="dialog-heading"><h2 id="settings-title">Make yourself comfortable.</h2><button aria-label="Close settings" onClick={()=>settings.current.close()}>✕</button></div><button className="settings-row" aria-pressed={voice} onClick={()=>{voiceRef.current=!voice;setVoice(!voice);controller.current.setMuted(voice);}}>Read replies aloud <b>{voice?'On':'Off'}</b></button><p>The microphone stays on during replies so you can interrupt. Sessions stop after three minutes or 30 seconds of inactivity to save credits.</p><button className="settings-row" disabled={busy} onClick={reset}>Clear conversation and cart ↗</button><a href="/research" target="_blank" rel="noopener">Open research dashboard ↗</a></dialog>
 <dialog ref={details} aria-labelledby="product-title"><div className="dialog-heading"><h2 id="product-title">{selected?.name}</h2><button aria-label="Close product details" onClick={()=>details.current.close()}>✕</button></div>{selected&&<><div className="detail-art"><ProductArt category={selected.category}/></div><p>{selected.description}</p><p className="selection-note">Category illustration · Real product</p><a href={selected.source_url} target="_blank" rel="noopener noreferrer">Manufacturer details & current price ↗</a><p className="selection-note">{selected.price_kind==='launch_reference'?'Launch reference price':'Price snapshot'} · Checked {selected.price_checked_at}. Demo stock; confirm availability with the manufacturer.</p><button onClick={()=>{details.current.close();send('Is '+selected.name+' in stock?');chat.current.showModal();}}>Check demo inventory</button><dl className="spec-list">{Object.entries(selected.specs).map(([k,v])=><React.Fragment key={k}><dt>{k}</dt><dd>{v}</dd></React.Fragment>)}</dl><div className="tradeoff"><b>Worth considering</b><p>{selected.tradeoff}</p></div><button className="primary" onClick={()=>changeCart(selected.id,(cart.find(x=>x.product_id===selected.id)?.quantity||0)+1)}>Add to cart · ${selected.price}</button></>}</dialog>

 </div>;
}
createRoot(document.getElementById('root')).render(<App/>);

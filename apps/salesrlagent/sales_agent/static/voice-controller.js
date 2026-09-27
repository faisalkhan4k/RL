/* Single owner for capture/playback. Epochs reject audio from previous turns. */
class VoiceController {
  constructor({status,transcript,turn,error}){
    Object.assign(this,{status,transcript,turn,error});this.enabled=false;this.epoch=0;this.generation=0;
    this.state='off';this.resumeAt=0;this.pending='';this.pendingAt=0;this.lastSpeech=performance.now();
  }
  reset(paused){
    this.epoch++;this.pending='';
    if(this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify({type:'reset',epoch:this.epoch,paused}));
  }
  setState(state){this.state=state;this.status(state);}
  async start(){
    if(this.enabled)return;this.enabled=true;const generation=++this.generation;this.setState('connecting');
    try{
      const stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
      if(generation!==this.generation){stream.getTracks().forEach(t=>t.stop());return;}
      this.stream=stream;this.context=new AudioContext();await this.context.audioWorklet.addModule('/static/microphone-worklet.js');
      if(generation!==this.generation)return;
      const socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/api/voice`);this.socket=socket;
      await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>reject(new Error('Voice connection timed out')),15000);
        socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.ready){clearTimeout(timer);resolve();}else if(m.error){clearTimeout(timer);reject(new Error(m.error));}};
        socket.onerror=()=>{clearTimeout(timer);reject(new Error('Voice connection failed'));};
        socket.onclose=()=>{clearTimeout(timer);reject(new Error('Voice disconnected'));};
      });
      if(generation!==this.generation)return;
      socket.onclose=()=>{if(this.enabled){this.stop();this.error('Voice disconnected. Select Start talking to reconnect.');}};
      socket.onmessage=e=>this.message(JSON.parse(e.data));
      this.source=this.context.createMediaStreamSource(stream);this.processor=new AudioWorkletNode(this.context,'microphone');
      this.source.connect(this.processor);this.processor.connect(this.context.destination);
      this.processor.port.onmessage=e=>this.frame(e.data);
      await this.context.resume();this.reset(false);this.setState('listening');
    }catch(e){if(generation===this.generation){this.stop();this.error(e.name==='NotAllowedError'?'Allow microphone access, then select Start talking.':e.message);}}
  }
  frame({pcm,energy}){
    if(!this.enabled||this.state!=='listening'||performance.now()<this.resumeAt||document.hidden||this.socket?.readyState!==WebSocket.OPEN)return;
    const now=performance.now(),user=energy>.02;if(user)this.lastSpeech=now;
    this.socket.send(pcm);
    this.socket.send(JSON.stringify({type:'timing',observation:[+user,0,Math.min((now-this.lastSpeech)/2000,1),+!!this.pending,0,Math.min(energy*10,1)]}));
    // A bounded safety deadline prevents an experimental policy from deadlocking.
    if(this.pending&&now-this.pendingAt>1800)this.submit();
  }
  message(m){
    if(m.epoch!==this.epoch||!this.enabled||this.state!=='listening'||performance.now()<this.resumeAt)return;
    if(m.partial)this.transcript(m.partial);
    if(m.text){this.pending=m.text;this.pendingAt=performance.now();this.transcript(m.text);}
    if(m.timing){window.dispatchEvent(new CustomEvent('voice-policy',{detail:m.timing}));if(this.pending&&m.timing.action==='SPEAK')this.submit();}
  }
  submit(){const text=this.pending;if(!text)return;this.pause();this.turn(text);}
  pause(){clearTimeout(this.resumeTimer);if(!this.enabled)return;this.reset(true);this.setState('thinking');this.stream?.getAudioTracks().forEach(t=>t.enabled=false);}
  cancelPlayback(){
    this.playbackGeneration=(this.playbackGeneration||0)+1;this.abort?.abort();
    if(this.audio){this.audio.pause();this.audio.removeAttribute('src');this.audio.load();this.audio=null;}
    if(this.url){URL.revokeObjectURL(this.url);this.url=null;}
    this.finishPlayback?.();this.finishPlayback=null;
  }
  resume(){
    if(!this.enabled){this.setState('off');return;}clearTimeout(this.resumeTimer);this.setState('waiting');
    this.resumeTimer=setTimeout(()=>{if(!this.enabled)return;this.reset(false);this.resumeAt=performance.now()+250;
      this.stream?.getAudioTracks().forEach(t=>t.enabled=true);this.setState('listening');},900);
  }
  async speak(text){
    this.cancelPlayback();this.pause();const generation=this.playbackGeneration;this.setState('preparing');this.abort=new AbortController();
    try{
      const r=await fetch('/api/speech',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text}),signal:this.abort.signal});
      if(!r.ok)throw new Error('The spoken reply is unavailable. Please read the answer below.');
      const blob=await r.blob();if(generation!==this.playbackGeneration)return;
      this.url=URL.createObjectURL(blob);this.audio=new Audio(this.url);this.setState('speaking');
      await new Promise((resolve,reject)=>{this.finishPlayback=resolve;this.audio.onended=resolve;this.audio.onerror=()=>reject(new Error('Audio playback failed'));this.audio.play().catch(reject);});
    }catch(e){if(e.name!=='AbortError'&&generation===this.playbackGeneration)this.error(e.message);}
    finally{if(generation===this.playbackGeneration){this.cancelPlayback();this.resume();}}
  }
  interrupt(){this.cancelPlayback();this.resume();}
  stop(){
    this.enabled=false;this.generation++;clearTimeout(this.resumeTimer);this.cancelPlayback();this.reset(true);
    this.socket?.close();this.socket=null;this.processor?.disconnect();this.source?.disconnect();
    this.stream?.getTracks().forEach(t=>t.stop());this.stream=null;this.context?.close().catch(()=>{});this.context=null;this.setState('off');
  }
}
window.VoiceController=VoiceController;

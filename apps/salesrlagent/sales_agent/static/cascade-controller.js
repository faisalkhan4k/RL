/* Full-duplex capture with echo cancellation; generation IDs discard cancelled audio. */
class CascadeController {
  constructor(callbacks){Object.assign(this,callbacks);this.enabled=false;this.generation=-1;this.nodes=new Set();this.nextTime=0;this.lifecycle=0;this.muted=false;}
  setState(s){this.state=s;this.status(s);}
  async start(){
    if(this.enabled)return;
    this.enabled=true;const lifecycle=++this.lifecycle;this.setState('connecting');
    try{
      const r=await fetch('/api/voice/config'),config=await r.json();
      if(lifecycle!==this.lifecycle)return;
      if(!config.configured)throw new Error('Voice needs DEEPGRAM_API_KEY and GROQ_API_KEY on the server. No API connection has been opened.');
      this.context=new AudioContext();await this.context.resume();
      this.analyser=this.context.createAnalyser();this.analyser.fftSize=256;this.analyser.connect(this.context.destination);
      const stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
      if(lifecycle!==this.lifecycle){stream.getTracks().forEach(t=>t.stop());return;}
      this.stream=stream;await this.context.audioWorklet.addModule('/static/microphone-worklet.js');
      if(lifecycle!==this.lifecycle)return;
      this.generation=-1;this.localInterrupt=false;this.done=false;
      const socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/api/voice/cascade`);this.socket=socket;
      socket.onmessage=e=>{if(lifecycle===this.lifecycle)this.message(JSON.parse(e.data));};
      socket.onclose=()=>{if(lifecycle===this.lifecycle&&this.enabled){this.stop();this.error('Voice disconnected. Select Start talking to reconnect.');}};
      socket.onerror=()=>{if(lifecycle===this.lifecycle){this.stop();this.error('Voice connection failed.');}};
      this.source=this.context.createMediaStreamSource(stream);this.processor=new AudioWorkletNode(this.context,'microphone');
      this.source.connect(this.processor);this.processor.connect(this.context.destination);
      this.processor.port.onmessage=e=>{
        this.level?.(e.data.energy||0);
        if(this.enabled&&this.ready&&socket.readyState===WebSocket.OPEN&&socket.bufferedAmount<64000)socket.send(e.data.pcm);
      };
      this.startTimer=setTimeout(()=>{if(!this.ready&&lifecycle===this.lifecycle){this.stop();this.error('Voice connection timed out.');}},12000);
    }catch(e){if(lifecycle===this.lifecycle){this.stop();this.error(e.name==='NotAllowedError'?'Allow microphone access, then try again.':e.message);}}
  }
  message(m){
    if(m.type==='error'){this.stop();this.error(m.message);return;}
    if(m.type==='ready'){clearTimeout(this.startTimer);this.ready=true;this.generation=m.generation;this.setState('listening');return;}
    if(m.type==='interrupted'){
      if(m.generation<this.generation)return;
      this.generation=m.generation;this.localInterrupt=false;this.clearAudio();this.setState('listening');return;
    }
    if(m.generation!==this.generation||this.localInterrupt)return;
    if(m.type==='partial')this.transcript(m.text);
    if(m.type==='user'){this.transcript('');this.user?.(m.text,m.generation);this.setState('thinking');}
    if(m.type==='result')this.result?.(m.result);
    if(m.type==='focus')this.focus?.(m.product_id);
    if(m.type==='assistant')this.assistant?.(m.text,`${this.lifecycle}:${m.generation}`);
    if(m.type==='audio'&&!this.muted)this.play(m.pcm,m.sample_rate);
    if(m.type==='done'){this.done=true;this.completed?.();this.playbackFinished();}
  }
  playbackFinished(){
    if(!this.done||this.nodes.size||!this.enabled)return;
    this.done=false;
    if(this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify({type:'playback_finished',generation:this.generation}));
    this.setState('listening');
  }
  play(encoded,sampleRate){
    if(!this.context||!this.enabled)return;
    const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));const view=new DataView(bytes.buffer);
    const buffer=this.context.createBuffer(1,bytes.length/2,sampleRate),samples=buffer.getChannelData(0);
    for(let i=0;i<samples.length;i++)samples[i]=view.getInt16(i*2,true)/32768;
    const node=this.context.createBufferSource();node.buffer=buffer;node.connect(this.analyser||this.context.destination);this.nodes.add(node);
    const when=Math.max(this.context.currentTime+.025,this.nextTime);this.nextTime=when+buffer.duration;
    node.onended=()=>{this.nodes.delete(node);node.disconnect();this.playbackFinished();};
    this.done=false;node.start(when);this.setState('speaking');
  }
  clearAudio(){for(const node of this.nodes){node.onended=null;try{node.stop();node.disconnect();}catch{}}this.nodes.clear();this.nextTime=0;this.done=false;}
  interrupt(){
    this.clearAudio();this.localInterrupt=true;
    if(this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify({type:'interrupt'}));
    this.setState(this.enabled?'listening':'off');
  }
  sendText(text){if(!this.ready){this.error('Wait for the microphone connection.');return;}this.interrupt();this.socket.send(JSON.stringify({type:'text',text}));}
  setMuted(value){this.muted=value;if(value){const done=this.done;this.clearAudio();this.done=done;this.playbackFinished();}}
  pause(){} // Capture deliberately stays enabled during replies.
  resume(){if(!this.enabled)this.setState('off');}
  cancelPlayback(){if(this.enabled)this.interrupt();else this.clearAudio();}
  speak(){this.error('Start talking to hear streamed replies.');}
  stop(){
    this.enabled=false;this.ready=false;this.lifecycle++;clearTimeout(this.startTimer);this.clearAudio();
    if(this.socket){this.socket.onclose=null;this.socket.close();this.socket=null;}
    this.processor?.disconnect();this.source?.disconnect();this.stream?.getTracks().forEach(t=>t.stop());this.stream=null;
    this.context?.close().catch(()=>{});this.context=null;this.analyser=null;this.level?.(0);this.setState('off');
  }
}
window.CascadeController=CascadeController;

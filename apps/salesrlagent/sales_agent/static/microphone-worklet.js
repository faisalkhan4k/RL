class MicrophoneProcessor extends AudioWorkletProcessor {
  constructor(){super();this.buffer=[];this.sum=0;this.count=0;this.phase=0;}
  process(inputs){
    const input=inputs[0]?.[0];if(!input)return true;
    for(const value of input){
      this.sum+=value;this.count++;this.phase+=16000;
      if(this.phase>=sampleRate){
        this.phase-=sampleRate;const s=Math.max(-1,Math.min(1,this.sum/this.count));
        this.buffer.push(s<0?s*32768:s*32767);this.sum=0;this.count=0;
      }
    }
    if(this.buffer.length>=1280){
      const pcm=new Int16Array(this.buffer.splice(0,1280));
      let power=0;for(const s of pcm)power+=(s/32768)**2;
      this.port.postMessage({pcm:pcm.buffer,energy:Math.sqrt(power/pcm.length)},[pcm.buffer]);
    }
    return true;
  }
}
registerProcessor('microphone',MicrophoneProcessor);

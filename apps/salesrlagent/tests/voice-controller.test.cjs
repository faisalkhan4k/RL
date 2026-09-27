const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function setup(){
 const timers=new Map();let next=0;const sent=[],turns=[],tracks=[{enabled:true}];
 const context={window:{dispatchEvent(){}},WebSocket:{OPEN:1},document:{hidden:false},performance:{now:()=>3000},
  setTimeout:f=>{timers.set(++next,f);return next;},clearTimeout:n=>timers.delete(n),URL:{revokeObjectURL(){}},CustomEvent:class {}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../sales_agent/static/voice-controller.js'),'utf8'),context);
 const c=new context.window.VoiceController({status(){},transcript(){},turn:t=>turns.push(t),error(){}});
 c.enabled=true;c.state='listening';c.socket={readyState:1,send:s=>sent.push(s)};c.stream={getAudioTracks:()=>tracks};
 return {c,timers,sent,turns,tracks};
}
test('pause cancels pending microphone resume and disables capture',()=>{
 const {c,timers,tracks}=setup();c.resume();assert.equal(timers.size,1);c.pause();assert.equal(timers.size,0);assert.equal(tracks[0].enabled,false);
});
test('frames cannot leak during speech or echo cooldown',()=>{
 const {c,sent}=setup();c.state='speaking';c.frame({pcm:new ArrayBuffer(8),energy:.5});assert.equal(sent.length,0);
 c.state='listening';c.resumeAt=4000;c.frame({pcm:new ArrayBuffer(8),energy:.5});assert.equal(sent.length,0);
});
test('previous epoch transcripts cannot create another turn',()=>{
 const {c,turns}=setup();c.epoch=4;c.message({epoch:3,text:'old reply'});c.message({epoch:3,timing:{action:'SPEAK'}});assert.equal(turns.length,0);
 c.message({epoch:4,text:'my question'});c.message({epoch:4,timing:{action:'SPEAK'}});assert.deepEqual(turns,['my question']);
 c.message({epoch:4,text:'duplicate'});assert.equal(turns.length,1);
});

// Exportiert die Szenenliste für sfx.py (nutzt timing.js, falls vorhanden)
let TIMING=null; try{TIMING=require('./timing.js').TIMING;}catch(e){}
const {SEGMENTS,buildSchedule}=require('./timeline.js');
const {segs,duration}=buildSchedule(SEGMENTS,TIMING);
require('fs').writeFileSync('schedule.json',JSON.stringify({duration,segs:segs.map(s=>({scene:s.scene,start:s.start,end:s.end,
  jump:!!s.jumpFrom,red:!!s.red,lampsOut:!!s.lampsOut,flicker:!!s.flicker,exit:!!s.exit,reveal:s.scene==='two'?s.chunksT[2].start:undefined,psst:s.scene==='mimeClose'?s.chunksT[2].start:undefined,
  blinks:s.scene==='eyeClose'?[s.chunksT[2].start+0.15,s.chunksT[3].start+0.05]:(s.scene==='agentBlink'?[s.chunksT[0].start+0.1,s.chunksT[1].start+0.1]:undefined),
  last:s.scene==='intro'?s.chunksT[s.chunksT.length-1].start:undefined,
  dBeeps:s.scene==='mimic'?[s.chunksT[0].start,s.chunksT[0].start+0.3,s.chunksT[2].start]:undefined,
  pBeeps:s.scene==='mimic'?[s.chunksT[4].start,s.chunksT[4].start+0.3]:undefined,
  lunge:s.scene==='snap'?s.chunksT[2].start:undefined, post:s.scene==='phone'?s.chunksT[5].start:undefined,
  knock:s.scene==='nightDoor'?s.chunksT[1].start:undefined, badge:s.scene==='agents'?s.chunksT[4].start:undefined,
  standort:s.scene==='viral'?s.chunksT[4].start:undefined, lift:s.scene==='glasses'?s.chunksT[3].start:undefined}))},null,1));
console.log('Dauer',duration.toFixed(1));

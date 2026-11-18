// Exportiert die Szenenliste für sfx.py (nutzt timing.js, falls vorhanden)
let TIMING=null; try{TIMING=require('./timing.js').TIMING;}catch(e){}
const {SEGMENTS,buildSchedule}=require('./timeline.js');
const {segs,duration}=buildSchedule(SEGMENTS,TIMING);
require('fs').writeFileSync('schedule.json',JSON.stringify({duration,segs:segs.map(s=>({scene:s.scene,start:s.start,end:s.end,
  jump:!!s.jumpFrom,red:!!s.red,lampsOut:!!s.lampsOut,flicker:!!s.flicker,exit:!!s.exit,reveal:s.scene==='two'?s.chunksT[2].start:undefined,psst:s.scene==='mimeClose'?s.chunksT[2].start:undefined}))},null,1));
console.log('Dauer',duration.toFixed(1));

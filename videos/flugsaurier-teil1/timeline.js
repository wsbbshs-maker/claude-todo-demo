// Timeline für "Der Flugsaurier – Teil 1".
// *Wort* = gelb, "M|" = zweite Stimme (Agent). hud.count + fmt 'views' = Aufrufzähler.
const DRONE = { tag: 'FLUG 12', time: '16:42', loc: 'SELVA LACANDONA · MX' };
const NIGHT = { tag: 'NACHT 1', time: '03:07', loc: 'HOSTEL · PALENQUE' };
const SEGMENTS = [
  { scene: 'dronePOV', lead: 0.9, hud: { ...DRONE, label: 'HÖHE', val: '340 M' },
    chunks: ['IN *340 METERN*', 'HÖHE', '*KLOPFT* ETWAS', 'AN MEINE *DROHNE*'] },
  { scene: 'eyeClose', hud: { ...DRONE, label: 'OBJEKT', val: '0,5 M', red: true },
    chunks: ['ICH DREHE', 'DIE *KAMERA*', 'UND ES *BLINZELT*', '*SEITWÄRTS*'] },
  { scene: 'intro', hud: { ...DRONE, loc: 'AUSSICHTSPUNKT', label: 'HÖHE', val: '340 M' },
    chunks: ['ICH BIN *TIM*, 19', 'ICH FILME IN *MEXIKO*', '*HOCHZEITEN*', 'MIT MEINER DROHNE', 'HEUTE NUR *DSCHUNGEL*', '*DACHTE ICH*'] },
  { scene: 'reveal', hud: { ...DRONE, label: 'OBJEKT', val: '4 M' },
    chunks: ['NEBEN MEINER DROHNE', 'FLIEGT EIN *FLUGSAURIER*', '*ZEHN METER*', 'SPANNWEITE', 'UND AM BEIN', 'EIN BLINKENDER *SENDER*'] },
  { scene: 'mimic', hud: { ...DRONE, label: 'AKKU', val: '18 %', red: true },
    chunks: ['DANN *PIEPT*', 'MEIN AKKU', '*18 PROZENT*', 'UND ER', '*PIEPT NACH*', '*EXAKT* GLEICH'] },
  { scene: 'snap', hud: { ...DRONE, label: 'SIGNAL', val: 'SCHWACH', after: { chunk: 2, delay: 0.45, val: 'WEG', red: true } },
    chunks: ['ER LEGT', 'DEN KOPF *SCHIEF*', 'UND *SCHNAPPT* ZU'], tail: 0.9 },
  { scene: 'phone', hud: { ...DRONE, time: '16:44', loc: 'AUSSICHTSPUNKT', label: 'AUFRUFE', fmt: 'views', count: [0, 1204], countFrom: 5 },
    chunks: ['SIGNAL WEG', 'DROHNE WEG', 'ABER DAS VIDEO', 'IST AUF MEINEM *HANDY*', 'NATÜRLICH', '*POSTE* ICH ES', 'SOFORT', 'DAS GEHT *SAFE VIRAL*'] },
  { scene: 'nightDoor', hud: { ...NIGHT, label: 'AUFRUFE', fmt: 'views', count: [48210, 312400] },
    chunks: ['NACHTS UM *DREI*', '*KLOPFT* ES', '*WIEDER*', 'DIESMAL', 'AN MEINER *TÜR*'] },
  { scene: 'agents', hud: { ...NIGHT, label: 'AUFRUFE', fmt: 'views', count: [312400, 893100] },
    chunks: ['ZWEI *MÄNNER*', 'SCHWARZE *ANZÜGE*', '*SONNENBRILLEN*', 'MITTEN IN DER *NACHT*', 'AUF DEM AUSWEIS', '*PROYECTO QUETZAL*'] },
  { scene: 'agentTalk', hud: { ...NIGHT, time: '03:08', label: 'AUFRUFE', fmt: 'views', count: [893100, 1450200] },
    chunks: ['EINER SAGT', 'M|*LÖSCH* DAS VIDEO', 'M|WIR JAGEN IHN *NICHT*', 'M|WIR *VERSTECKEN* IHN'] },
  { scene: 'viral', hud: { ...NIGHT, time: '03:08', label: 'AUFRUFE', fmt: 'views', count: [1450200, 2000000] },
    chunks: ['DANN *VIBRIERT*', 'MEIN HANDY', '*ZWEI MILLIONEN*', 'AUFRUFE', 'MIT *STANDORT*'] },
  { scene: 'glasses', hud: { ...NIGHT, time: '03:08', label: 'AUFRUFE', val: '2.000.000', red: true },
    chunks: ['DER MANN', 'WIRD *STILL*', 'DANN NIMMT ER', 'DIE *SONNENBRILLE* AB'] },
  { scene: 'agentBlink', hud: { ...NIGHT, time: '03:08', label: 'AUFRUFE', val: '2.000.000', red: true },
    chunks: ['UND *BLINZELT*', '*SEITWÄRTS*'], tail: 1.4 },
  { scene: 'end', hud: null, chunks: ['*TEIL 2*', 'MORGEN'], tail: 1.0 },
];

function buildSchedule(segs, timing) {
  timing = timing || (typeof TIMING !== 'undefined' ? TIMING : null);
  if (timing) {
    return { duration: timing.duration + 0.4, segs: segs.map((s, i) => {
      const tm = timing.segs[i];
      return { ...s, start: tm.start, end: i === segs.length - 1 ? timing.duration + 0.4 : tm.end, chunksT: tm.chunks };
    }) };
  }
  let t = 0; const out = [];
  segs.forEach(s => {
    const seg = { ...s, start: t, chunksT: [] };
    t += s.lead || 0.15;
    s.chunks.forEach(c => {
      const speaker = c.startsWith('M|') ? 'mehmet' : 'jonas';
      c = c.replace(/^M\|/, '');
      const d = Math.max(0.55, c.replace(/\*/g, '').length / 13);
      seg.chunksT.push({ text: c, start: t, end: t + d, speaker });
      t += d;
    });
    t += (s.tail || 0.35); seg.end = t; out.push(seg);
  });
  return { segs: out, duration: t };
}
if (typeof module !== 'undefined') module.exports = { SEGMENTS, buildSchedule };

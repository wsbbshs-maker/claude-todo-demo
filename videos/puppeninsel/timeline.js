// Timeline für "Die Insel der Puppen". Erzählerin: das Mädchen. Ort bleibt bis zum Ende "???".
const HIDE = { tag: 'NACHT', time: '23:58', loc: 'ORT: ???', label: 'PUPPEN', val: '1.004' };
const SHOW = { tag: 'HEUTE', time: '06:12', loc: 'XOCHIMILCO · MEXIKO', label: 'PUPPEN', val: '1.004' };
const SEGMENTS = [
  { scene: 'dollBlink', lead: 0.9, hud: { ...HIDE },
    chunks: ['EINE DIESER *PUPPEN*', 'IST *KEINE* PUPPE'] },
  { scene: 'canal', hud: { ...HIDE },
    chunks: ['DU SIEHST GERADE', 'EINEN DER *GRUSELIGSTEN*', '*ORTE* DER WELT', 'WO ER IST', 'SAG ICH DIR', 'AM *ENDE*'] },
  { scene: 'ghostGirl', hud: { ...HIDE },
    chunks: ['ICH WAR NOCH', 'EIN *KIND*', 'ALS ICH HIER', 'INS *WASSER* GEFALLEN BIN', 'SEITDEM', 'BIN ICH *HIER*'] },
  { scene: 'oldMan', hud: { ...HIDE, tag: 'DAMALS', time: '19??', unit: '' },
    chunks: ['DANN KAM', 'EIN *ALTER MANN*', 'ER HAT EINE *PUPPE*', 'IM WASSER GEFUNDEN', '*MEINE* PUPPE'] },
  { scene: 'hangFirst', hud: { ...HIDE, tag: 'DAMALS', time: '19??', unit: '', val: '1' },
    chunks: ['ER HAT SIE', 'IN EINEN *BAUM* GEHÄNGT', 'DAMIT ICH', 'NICHT *ALLEIN* BIN'] },
  { scene: 'timelapse', hud: { ...HIDE, tag: 'ZEIT', tcount: [1, 50], unit: 'JAHRE', fmt: 'views', count: [1, 1004] },
    chunks: ['DANN NOCH EINE', 'UND NOCH EINE', '*FÜNFZIG JAHRE* LANG', 'AM ENDE', '*ÜBER TAUSEND*'] },
  { scene: 'whisper', hud: { ...HIDE, time: '03:00' },
    chunks: ['NACHTS HAT ER SIE', '*FLÜSTERN* GEHÖRT', 'ER HAT GESAGT', 'SIE BEWEGEN', 'DIE *AUGEN*', 'ER HATTE *RECHT*'] },
  { scene: 'watchers', hud: { ...HIDE, time: '03:01' },
    chunks: ['*SPEICHER* DIR DAS', 'LIEBER', 'BEIM *ZWEITEN* MAL', 'SIEHST DU', 'WELCHE PUPPE DICH', 'DIE GANZE ZEIT *ANSCHAUT*'] },
  { scene: 'man2001', hud: { ...HIDE, tag: 'JAHR', time: '2001', unit: '' },
    chunks: ['IM JAHR *2001*', 'HABEN SIE IHN', '*GEFUNDEN*', 'IM KANAL', 'GENAU DA', 'WO ER *MICH* GEFUNDEN HAT'] },
  { scene: 'notAlone', hud: { ...HIDE, tag: 'HEUTE', time: '23:59' },
    chunks: ['SEITDEM', 'BIN ICH', 'NICHT MEHR *ALLEIN*'], tail: 0.6 },
  { scene: 'loop', hud: { ...HIDE, tag: 'HEUTE', time: '00:00', red: true },
    chunks: ['ICH HAB AM ANFANG', 'GESAGT', 'EINE DIESER PUPPEN', 'IST *KEINE* PUPPE', '*DAS WAR ICH*'], tail: 0.7 },
  { scene: 'placeReveal', hud: { ...SHOW },
    chunks: ['DIESER ORT HEISST', '*ISLA DE LAS MUÑECAS*', 'DIE *INSEL DER PUPPEN*', 'IN *MEXIKO*'] },
  { scene: 'follow', hud: { ...SHOW },
    chunks: ['*FOLG MIR*', 'DANN ZEIG ICH DIR', 'WAS ER IN SEINER', '*LETZTEN NACHT*', 'GESEHEN HAT'], tail: 1.6 },
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
      const d = Math.max(0.55, c.replace(/\*/g, '').length / 12);
      seg.chunksT.push({ text: c, start: t, end: t + d, speaker });
      t += d;
    });
    t += (s.tail || 0.35); seg.end = t; out.push(seg);
  });
  return { segs: out, duration: t };
}
if (typeof module !== 'undefined') module.exports = { SEGMENTS, buildSchedule };

// Timeline für "Schicht im Tunnel – Teil 2".
// *Wort* = gelb, "M|" = Mehmet (über Funk). hud.count = [von, bis] zählt während der Szene herunter.
const SEGMENTS = [
  { scene: 'balloon', hud: { time: '03:14', loc: 'CONTAINER', label: 'ABSTAND', val: '0 M', red: true },
    chunks: ['DANN *SCHWEBT*', 'EIN *ROTER*', '*LUFTBALLON*', 'AN MIR VORBEI'] },
  { scene: 'clownReveal', hud: { time: '03:14', loc: 'CONTAINER', label: 'ABSTAND', val: '2 M', red: true },
    chunks: ['ICH DREHE MICH', '*DOCH* UM', 'EIN *CLOWN*', 'WEISSES *GRINSEN*', 'RIESIGE *SCHUHE*'] },
  { scene: 'face', hud: { time: '03:14', loc: 'CONTAINER', label: 'ABSTAND', val: '2 M', red: true },
    chunks: ['OKAY', 'ICH BIN *COOKED*'], tail: 0.6 },
  { scene: 'newspaper', hud: { time: '03:15', loc: 'CONTAINER', label: 'ABSTAND', val: '2 M', red: true },
    chunks: ['ICH *KENNE* IHN', 'AUS DER *ZEITUNG*', '*1994*', 'WURDE HIER', 'EIN *ZIRKUSWAGEN*', '*VERSCHÜTTET*', 'DER CLOWN', 'WURDE *NIE GEFUNDEN*'] },
  { scene: 'run', hud: { time: '03:15', loc: 'RÖHRE OST', label: 'VORSPRUNG', val: '20 M' },
    chunks: ['ICH *RENNE*'], tail: 0.9 },
  { scene: 'radio', running: true, hud: { time: '03:15', loc: 'RÖHRE OST', label: 'NOTAUSGANG', val: '800 M' }, radio: 'NORDPORTAL · MEHMET',
    chunks: ['MEHMET *SCHREIT*', 'M|*DIGGA*, LAUF!', 'M|*NOTAUSGANG*', 'M|*800 METER*', 'M|UND SCHAU *IHN AN*', 'M|SOLANGE DU', 'M|IHN *ANSIEHST*', 'M|BEWEGT ER SICH *NICHT*'] },
  { scene: 'beam', hud: { time: '03:16', loc: 'RÖHRE OST', label: 'NOTAUSGANG', count: [600, 400] },
    chunks: ['ALSO RENNE ICH', '*RÜCKWÄRTS*', '*TASCHENLAMPE*', 'AUF IHN', 'ER BLEIBT *STEHEN*', 'UND *GRINST*'] },
  { scene: 'beam', lampsOut: true, hud: { time: '03:17', loc: 'RÖHRE OST', label: 'NOTAUSGANG', count: [400, 250] },
    chunks: ['HINTER IHM', 'GEHEN DIE *LAMPEN AUS*', 'EINE NACH', 'DER *ANDEREN*'] },
  { scene: 'beam', exit: true, allOut: true, hud: { time: '03:18', loc: 'RÖHRE OST', label: 'NOTAUSGANG', count: [200, 50] },
    chunks: ['*200 METER*', '*100*', '*50*'] },
  { scene: 'beam', flicker: true, allOut: true, exit: true, hud: { time: '03:18', loc: 'RÖHRE OST', label: 'AKKU', val: '3 %', red: true },
    chunks: ['DANN *FLACKERT*', 'DIE TASCHENLAMPE', '*EINMAL*', '*ZWEIMAL*'] },
  { scene: 'neck', hud: { time: '03:18', loc: 'RÖHRE OST', label: 'HINTER DIR', val: '0 M', red: true },
    chunks: ['UND DANN', '*SPÜRE* ICH ES', '*WARMER ATEM*', 'IN MEINEM *NACKEN*'], tail: 0.6 },
  { scene: 'mimeReveal', hud: { time: '03:18', loc: 'RÖHRE OST', label: 'HINTER DIR', val: '0 M', red: true },
    chunks: ['HINTER MIR', 'STEHT *JEMAND*', '*KREIDEWEISSES* GESICHT', '*SCHWARZE* LIPPEN', 'EIN *PANTOMIME*'] },
  { scene: 'mimeClose', hud: { time: '03:19', loc: 'RÖHRE OST', label: 'HINTER DIR', val: '0 M', red: true },
    chunks: ['ER SAGT', '*KEIN WORT*', 'ER LEGT NUR', 'DEN *FINGER*', 'AUF DIE *LIPPEN*'] },
  { scene: 'between', hud: { time: '03:19', loc: 'RÖHRE OST', label: 'ABSTAND', val: '?? M', red: true },
    chunks: ['VOR MIR', 'DER *CLOWN*', 'HINTER MIR', 'DER *PANTOMIME*', 'ICH MUSS', 'HIER *RAUS*', 'ABER ICH KANN NUR', '*EINEN* ANSCHAUEN'], tail: 1.4 },
  { scene: 'end', hud: null, chunks: ['*TEIL 3*', 'MORGEN'], tail: 1.0 },
];

function buildSchedule(segs, timing) {
  timing = timing || (typeof TIMING !== 'undefined' ? TIMING : null);
  if (timing) {
    return { duration: timing.duration + 0.4, segs: segs.map((s, i) => {
      const tm = timing.segs[i];
      return { ...s, start: tm.start, end: i === segs.length - 1 ? timing.duration + 0.4 : tm.end, chunksT: tm.chunks };
    }) };
  }
  let t = 0.2; const out = [];
  segs.forEach(s => {
    const seg = { ...s, start: t, chunksT: [] };
    s.chunks.forEach(c => {
      const speaker = c.startsWith('M|') ? 'mehmet' : 'jonas';
      c = c.replace(/^M\|/, '');
      const d = Math.max(0.55, c.replace(/\*/g, '').length / 13);
      seg.chunksT.push({ text: c, start: t, end: t + d, speaker });
      t += d;
    });
    t += (s.tail || 0.45); seg.end = t; out.push(seg);
  });
  return { segs: out, duration: t };
}
if (typeof module !== 'undefined') module.exports = { SEGMENTS, buildSchedule };

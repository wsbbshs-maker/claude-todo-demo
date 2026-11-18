// Timeline für "Schicht im Tunnel – Teil 1".
// Untertitel-Chunks: *Wort* = gelb hervorgehoben.
// Dauer wird aus der Textlänge geschätzt, bis echte Wort-Zeitstempel der Stimme vorliegen
// (dann: chunk.start / chunk.end direkt setzen).
const SEGMENTS = [
  { scene: 'monitorWall', hud: { time: '03:07', loc: 'KONTROLLRAUM', val: '400 M' },
    text: 'Wenn du nachts allein in einem Tunnel arbeitest, gibt es eine Regel: Schau nicht auf Kamera vier.',
    chunks: ['WENN DU *NACHTS*', 'ALLEIN IM *TUNNEL*', 'ARBEITEST', 'GIBT ES EINE *REGEL*', 'SCHAU NICHT', 'AUF *KAMERA VIER*'] },
  { scene: 'tunnel', hud: { time: '03:07', loc: 'BRANDBERGTUNNEL', val: '400 M' },
    text: 'Ich bin Jonas. Nachtwache im neuen Brandbergtunnel. Noch nicht eröffnet. Niemand darf hier rein.',
    chunks: ['ICH BIN *JONAS*', '*NACHTWACHE*', 'IM NEUEN', '*BRANDBERGTUNNEL*', 'NOCH NICHT *ERÖFFNET*', 'NIEMAND DARF', '*HIER REIN*'] },
  { scene: 'cam', camScale: 1.0, hud: { time: '03:07', loc: 'KAMERA 4', val: '400 M' },
    text: 'Um drei Uhr sieben steht auf Kamera vier jemand. Mitten auf der Fahrbahn. Er schaut direkt in die Kamera.',
    chunks: ['UM *DREI UHR SIEBEN*', 'STEHT AUF KAMERA VIER', '*JEMAND*', 'MITTEN AUF DER *FAHRBAHN*', 'ER SCHAUT *DIREKT*', 'IN DIE *KAMERA*'] },
  { scene: 'radio', hud: { time: '03:08', loc: 'KONTROLLRAUM', val: '400 M' }, radio: 'NORDPORTAL · MEHMET',
    text: 'Ich funke Mehmet an, am Nordportal. Er sagt: Das Tor ist zu. Hier ist keiner reingekommen.',
    chunks: ['ICH FUNKE *MEHMET* AN', 'AM *NORDPORTAL*', 'ER SAGT', 'M|DAS TOR *IST ZU*', 'M|HIER IST *KEINER*', 'M|REINGEKOMMEN'] },
  { scene: 'cam', camScale: 1.7, jumpFrom: '400 M', hud: { time: '03:09', loc: 'KAMERA 4', val: '280 M' },
    text: 'Ich schaue wieder hin. Er ist näher.',
    chunks: ['ICH SCHAUE', '*WIEDER* HIN', 'ER IST *NÄHER*'] },
  { scene: 'tunnelWalk', hud: { time: '03:10', loc: 'RÖHRE OST', val: '280 M' },
    text: 'Ich gehe raus in die Röhre. Die Lampen summen. Die Fahrbahn ist leer.',
    chunks: ['ICH GEHE RAUS', 'IN DIE *RÖHRE*', 'DIE LAMPEN *SUMMEN*', 'DIE FAHRBAHN', 'IST *LEER*'] },
  { scene: 'cam', camScale: 2.5, marker: true, jumpFrom: '280 M', hud: { time: '03:11', loc: 'KAMERA 4', val: '200 M' },
    text: 'Zurück im Container. Kamera vier. Er steht genau da, wo ich eben stand.',
    chunks: ['ZURÜCK IM *CONTAINER*', '*KAMERA VIER*', 'ER STEHT *GENAU DA*', 'WO ICH EBEN *STAND*'] },
  { scene: 'face', hud: { time: '03:11', loc: 'KONTROLLRAUM', val: '200 M' },
    text: 'Und jetzt verstehe ich es. Er bewegt sich nur, wenn ich nicht hinsehe.',
    chunks: ['UND JETZT', '*VERSTEHE* ICH ES', 'ER BEWEGT SICH NUR', 'WENN ICH *NICHT*', '*HINSEHE*'] },
  { scene: 'radio', red: true, hud: { time: '03:14', loc: 'KONTROLLRAUM', val: '??? M', red: true }, radio: 'NORDPORTAL · MEHMET',
    text: 'Dann knackt das Funkgerät. Mehmet flüstert: Jonas … auf meiner Kamera ist er auch. Und er ist schon bei dir.',
    chunks: ['DANN *KNACKT*', 'DAS FUNKGERÄT', 'MEHMET *FLÜSTERT*', 'M|*JONAS*', 'M|AUF MEINER KAMERA', 'M|IST ER *AUCH*', 'M|UND ER IST SCHON', 'M|*BEI DIR*'] },
  { scene: 'behind', hud: { time: '03:14', loc: 'KAMERA 1 · CONTAINER', val: '0 M', red: true },
    text: 'Ich drehe mich nicht um.',
    chunks: ['ICH DREHE MICH', '*NICHT* UM'], tail: 1.2 },
  { scene: 'end', hud: null,
    text: 'Teil zwei … morgen.',
    chunks: ['*TEIL 2*', 'MORGEN'], tail: 1.0 },
];

// Zeitplan berechnen (Schätzung ~13 Zeichen/Sek. + Pausen)
function buildSchedule(segs, timing) {
  timing = timing || (typeof TIMING !== 'undefined' ? TIMING : null);
  if (timing) { // echtes Timing aus der Sprachaufnahme (voice.py)
    return { duration: timing.duration + 0.4, segs: segs.map((s, i) => {
      const tm = timing.segs[i];
      return { ...s, start: tm.start, end: i === segs.length - 1 ? timing.duration + 0.4 : tm.end, chunksT: tm.chunks };
    }) };
  }
  let t = 0.3;
  const out = [];
  segs.forEach((s, i) => {
    const seg = { ...s, start: t, chunksT: [] };
    s.chunks.forEach(c => {
      const speaker = c.startsWith('M|') ? 'mehmet' : 'jonas';
      c = c.replace(/^M\|/, '');
      const plain = c.replace(/\*/g, '');
      const d = Math.max(0.55, plain.length / 13);
      seg.chunksT.push({ text: c, start: t, end: t + d, speaker });
      t += d;
    });
    t += (s.tail || 0.45);
    seg.end = t;
    out.push(seg);
  });
  return { segs: out, duration: t };
}
if (typeof module !== 'undefined') module.exports = { SEGMENTS, buildSchedule };

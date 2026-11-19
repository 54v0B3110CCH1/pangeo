// Venticinquesima estensione: il calore da satellite (NASA FIRMS) letto con lo storico. Per ogni Stato: fascia di confine
// con ogni vicino, zone accese che prima erano spente, zone accese quasi ogni giorno, rilevamenti di notte; in Live i
// cambiamenti rispetto ai giorni prima. Solo conteggi: nessun punto preciso.
// Uso: node tools/build25.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 24)
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);
h = h.replace(/(<\/html>)\s*<\/body><\/html>\s*$/, '$1\n');
if (h.includes('function caloreZona(')) { console.log('già presente'); fs.writeFileSync(out, h); process.exit(0); }
const a = h.indexOf('function caloreHtml(L, stato) {'), b = h.indexOf('\nfunction dalVivoHtml(nome) {');
if (a < 0 || b < a || h.indexOf('function caloreHtml(L, stato) {', a + 1) >= 0) throw new Error('caloreHtml non trovata');
h = h.slice(0, a) + String.raw`function caloreZona(C, stato) {
  const z = (C.zone || {})[stato], st = C.storia, n1 = x => String(x).replace('.', ',');
  let o = '';
  if (z) {
    (z.note || []).forEach(n => { o += '<div class="x"><b>' + esc(n.replace(/(\d)\.(\d)/g, '$1,$2')) + '</b></div>'; });
    const conf = Object.entries(z.conf || {}).filter(e => e[1][0] >= 3).slice(0, 3);
    if (conf.length) o += '<div class="s">Nella fascia di confine (entro circa 30 km): ' + conf.map(([q, v]) => 'con ' + esc(q) + ' ' + v[0] + (v[1] != null ? ' (di solito ' + n1(v[1]) + ')' : '')).join(' · ') + '</div>';
    if (z.nuove) o += '<div class="s">Zone accese che nelle due settimane prima erano spente: ' + z.nuove[0] + ' (' + z.nuove[1] + ' rilevamenti) · in zone accese quasi ogni giorno: ' + z.fisse + ' · di notte: ' + z.notte + '</div>';
    else o += '<div class="s">Di notte: ' + z.notte + '. Zone nuove e zone sempre accese si distinguono dopo 5 giorni di storico.</div>';
    if (z.solito) o += '<div class="s">Quasi tutto viene da zone accese quasi ogni giorno: industria, pozzi, vulcani o incendi stagionali.</div>';
  }
  if (st && st.giorni) o += '<div class="s">Confronto con ' + st.giorni + (st.giorni === 1 ? ' giorno' : ' giorni') + ' di storico dello stesso satellite (' + esc(st.satellite) + ').</div>';
  return o;
}
function caloreHtml(L, stato) {
  const C = L && L.calore; if (!C || !C.paesi) return '';
  const nota = 'Fonte: ' + esc(C.fonte) + '. Il satellite vede il calore, non chi lo produce: incendi, campi bruciati, industria, esplosioni. Conteggi per Stato e per fascia di confine, nessun punto preciso. Ogni cambiamento va confermato con le notizie.';
  if (stato) {
    const v = C.paesi[stato]; if (!v) return '';
    return '<div class="item"><div class="t">Fonti di calore da satellite</div><div class="x">' + v[0] + ' nelle ultime 24 ore' + (v[1] != null ? ' · di solito ' + String(v[1]).replace('.', ',') : '') + (v[2] ? ' · <b>forte aumento</b>' : '') + '</div>' + caloreZona(C, stato) + '<div class="s">' + nota + '</div></div>';
  }
  const seg = Object.entries(C.paesi).filter(e => e[1][2]);
  const cambi = Object.entries(C.zone || {}).filter(e => (e[1].note || []).length);
  const top = Object.entries(C.paesi).sort((x, y) => y[1][0] - x[1][0]).slice(0, 15);
  return '<h3 id="lv-calore">Fonti di calore da satellite</h3><div class="item"><div class="x">' + C.totale + ' rilevamenti nel mondo (' + esc(C.agg) + ')' + (C.storia && C.storia.giorni ? ', confrontati con ' + C.storia.giorni + (C.storia.giorni === 1 ? ' giorno' : ' giorni') + ' di storico' : '') + '.</div>'
    + (cambi.length ? '<div class="s" style="margin-top:6px">Diverso dai giorni prima</div><ul class="plain">' + cambi.map(([p, z]) => '<li><a href="#live/' + encodeURIComponent(p) + '">' + esc(p) + '</a>: ' + z.note.map(n => esc(n.replace(/(\d)\.(\d)/g, '$1,$2'))).join(' ') + '</li>').join('') + '</ul>' : (C.storia ? '<div class="s" style="margin-top:6px">Nessun cambiamento insolito ai confini o in zone nuove rispetto ai giorni prima.</div>' : ''))
    + (seg.length ? '<div class="s" style="margin-top:6px">Forti aumenti rispetto al solito</div><div class="members">' + seg.map(([p, v]) => '<a href="#live/' + encodeURIComponent(p) + '">' + esc(p) + ' (' + v[0] + ' invece di ' + String(v[1]).replace('.', ',') + ')</a>').join('') + '</div>' : '') + '<div class="s" style="margin-top:6px">Più rilevamenti</div><div class="members">' + top.map(([p, v]) => '<a href="#live/' + encodeURIComponent(p) + '">' + esc(p) + ' ' + v[0] + '</a>').join('') + '</div><div class="s">' + nota + '</div></div>';
}` + h.slice(b);
fs.writeFileSync(out, h);
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
console.log('ok', out, h.length);

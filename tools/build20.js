// Ventesima estensione: diario del programma (che cosa raccoglie a ogni giro) e memoria dei fatti confermati per Stato.
// Uso: node tools/build20.js base.html out.html
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);          // toglie la riga-cornice della pubblicazione
h = h.replace(/(<\/body>\s*<\/html>)(\s*<\/body>\s*<\/html>)+\s*$/, '$1\n');               // e le chiusure doppie in fondo
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
sost('\nfunction render() {', String.raw`
// Ventesima estensione, 18 novembre 2026: diario del programma e memoria dei fatti confermati (solo dove gira il programma)
const TAPPE_NOME = { temi: 'ricerche per tema', stati: 'rotazione degli Stati', ricerca: 'ricerca autonoma', feed: 'feed delle testate', telegram: 'Telegram', video: 'YouTube', altro: 'altro' };
function diarioHtml(L) {
  const D = (L && L.diario) || []; if (!D.length) return '';
  const z = D[D.length - 1], lim = new Date(Date.parse(z.iso) - 24 * 3600e3).toISOString();
  const g = D.filter(x => x.iso >= lim), i0 = D.indexOf(g[0]), a = i0 > 0 ? D[i0 - 1] : g[0];
  const tot = k => g.reduce((s, x) => s + (x[k] || 0), 0);
  const pd = x => { const l = x.livelli || {}; return Math.round(100 * (l.D || 0) / Math.max(1, (l.A || 0) + (l.B || 0) + (l.C || 0) + (l.D || 0))); };
  const fr = (v0, v1, u) => v0 === v1 ? num(v1) + (u || '') + ' (come prima)' : 'da ' + num(v0) + (u || '') + ' a ' + num(v1) + (u || '');
  const da = {}; g.forEach(x => Object.keys(x.da || {}).forEach(k => { da[k] = (da[k] || 0) + x.da[k]; }));
  const nuoviF = [].concat(...g.map(x => x.fonti_nuove || []));
  const tgN = (z.tg_trovati || []).filter(c => !(a.tg_trovati || []).includes(c));
  const coperti = (a.senza || []).filter(s => !(z.senza || []).includes(s)), persi = (z.senza || []).filter(s => !(a.senza || []).includes(s));
  const rif = {}; g.forEach(x => Object.keys(x.rifiuti || {}).forEach(k => { rif[k] = (rif[k] || 0) + x.rifiuti[k]; }));
  const nr = Object.keys(rif).reduce((s, k) => s + rif[k], 0), ma = a.memoria || [0, 0], mz = z.memoria || [0, 0];
  let o = '<h3 id="lv-diario">Diario del programma</h3><div class="item"><div class="x">' + g.length + (g.length === 1 ? ' giro' : ' giri') + ' nelle ultime 24 ore (dal ' + esc(g[0].quando) + ' al ' + esc(z.quando) + ', versione ' + esc(z.v) + '): ' + num(tot('nuove')) + ' voci nuove raccolte.</div><dl class="kv" style="margin-top:8px">';
  o += '<dt>Da dove arrivano</dt><dd>' + Object.keys(da).sort((p, q) => da[q] - da[p]).map(k => esc(TAPPE_NOME[k] || k) + ' ' + num(da[k])).join(' · ') + '</dd>';
  o += '<dt>Notizie degli ultimi 3 giorni</dt><dd>' + fr(a.live, z.live) + '</dd>';
  o += '<dt>Confermate da più fonti</dt><dd>' + fr(Math.round(100 * a.quota), Math.round(100 * z.quota), '%') + '</dd>';
  o += '<dt>Da fonti non classificate</dt><dd>' + fr(pd(a), pd(z), '%') + '</dd>';
  o += '<dt>Stati senza notizie</dt><dd>' + fr(a.scoperti, z.scoperti) + (coperti.length ? '. Ora coperti: ' + coperti.map(esc).join(', ') : '') + (persi.length ? '. Tornati senza: ' + persi.map(esc).join(', ') : '') + '</dd>';
  o += '<dt>Feed attivi</dt><dd>' + fr(a.fonti[0], z.fonti[0]) + ' su ' + num(z.fonti[1]) + (nuoviF.length ? '. Trovati da solo: ' + nuoviF.map(esc).join(', ') : '') + '</dd>';
  if (tgN.length) o += '<dt>Canali Telegram trovati da solo</dt><dd>' + tgN.map(esc).join(', ') + '</dd>';
  o += '<dt>Stati studiati su Wikipedia</dt><dd>' + fr(a.sapere || 0, z.sapere || 0) + '</dd>';
  o += '<dt>Fatti confermati in memoria</dt><dd>' + fr(ma[1], mz[1]) + '</dd>';
  o += '<dt>Richieste ai siti</dt><dd>' + num(Math.round(tot('richieste') / g.length)) + ' per giro; rifiuti per troppe richieste: ' + nr + (nr ? ' (' + Object.keys(rif).map(k => esc(k) + ' ' + rif[k]).join(', ') + ')' : '') + '</dd>';
  o += '<dt>Durata di un giro</dt><dd>' + Math.max(1, Math.round(tot('durata') / g.length / 60)) + ' minuti in media; avvisi per giro: ' + (tot('errori') / g.length).toFixed(1).replace('.', ',') + '</dd>';
  o += '<dt>Titoli tradotti</dt><dd>' + num(z.tradotti || 0) + '</dd>';
  o += '<dt>Spesa del cervello</dt><dd>oggi ' + (z.usd_oggi || 0).toFixed(3).replace('.', ',') + ' $, questo mese ' + (z.usd_mese || 0).toFixed(2).replace('.', ',') + ' $</dd></dl>';
  return o + '<div class="s">Il confronto è con il giro prima di queste 24 ore. ' + (APP_OK ? 'Tutti i giri, uno per riga: <a href="tabelle.html#diario">tabelle aperte</a>.' : 'Tutti i giri, uno per riga, sono nelle tabelle aperte del sito.') + ' Sul telefono: python castello.py rapporto</div></div>';
}
function memoriaHtml(nome) {
  const m = window.MEMORIA && window.MEMORIA[nome]; if (!m || !m.length) return '';
  return '<details class="crit"><summary>Fatti confermati negli ultimi mesi (' + m.length + ')</summary><ul class="plain">' + m.slice(0, 40).map(x => '<li>' + esc(String(x[0]).split('-').reverse().join('/')) + ' · <a href="' + safeU(x[4]) + '" target="_blank" rel="noopener">' + esc(x[1]) + '</a> <span class="s">' + esc(x[2]) + ' e altre ' + (x[3] - 1) + (x[3] === 2 ? ' fonte' : ' fonti') + '</span></li>').join('') + '</ul><div class="s">La memoria del programma: tiene per 120 giorni i fatti riportati da almeno due fonti, di cui una affidabile. Sono titoli di giornale, da leggere alla fonte.</div></details>';
}
function caricaMemoria() {
  if (!(APP_OK || location.protocol === 'file:')) return;
  const s = document.createElement('script'); s.src = 'memoria.js?v=' + Date.now();
  s.onload = () => { render(); s.remove(); }; s.onerror = () => s.remove(); document.head.appendChild(s);
}
` + '\nfunction render() {');
sost("return h + (stato ? '' : miglioratoreHtml(L) + analisiHtml(L.analisi) + ext);", "return h + (stato ? memoriaHtml(stato) : miglioratoreHtml(L) + diarioHtml(L) + analisiHtml(L.analisi) + ext);");
sost("+ cieloHtml(L, nome) + caloreHtml(L, nome) : '')", "+ cieloHtml(L, nome) + caloreHtml(L, nome) : '') + memoriaHtml(nome)");
sost('caricaSapere();\n', 'caricaSapere();\ncaricaMemoria();\n');
fs.writeFileSync(out, h);
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
console.log('ok', out, h.length, 'inizio tolto:', inizio, 'fine:', JSON.stringify(h.slice(-40)));

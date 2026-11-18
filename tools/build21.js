// Ventunesima estensione (comprende la Ventesima): «Dall'ultima volta» in cima alla pagina, diario del programma
// nella cartella Live, memoria dei fatti confermati per Stato. Uso: node tools/build21.js base.html out.html
// La base è la pagina SENZA la Ventesima (es. la versione pubblicata numero 30).
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);          // toglie la riga-cornice della pubblicazione
h = h.replace(/(<\/body>\s*<\/html>)(\s*<\/body>\s*<\/html>)+\s*$/, '$1\n');               // e le chiusure doppie in fondo
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }

// Stile: stessi colori e caratteri della pagina (solo variabili già definite in :root)
sost('</style>', `
/* Ventunesima estensione: novità dall'ultima visita e diario del programma */
.nv { background: var(--surface); border: 1px solid var(--rule); border-left: 4px solid var(--accent); border-radius: 10px; padding: 14px 14px 12px; margin: 0 0 20px; display: grid; gap: 12px; }
.nv-top { display: grid; gap: 2px; }
.nv-top b { font-family: var(--display); font-size: 21px; font-weight: 600; line-height: 1.2; text-wrap: balance; }
.nv-top span { font-size: 13px; color: var(--muted); }
.nv-tiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
@media (min-width: 560px) { .nv-tiles { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
.nv-tile { background: var(--bg); border-radius: 8px; padding: 10px 12px; display: grid; gap: 2px; align-content: start; min-width: 0; }
.nv-tile b { font-family: var(--display); font-size: 27px; line-height: 1.1; font-weight: 600; font-variant-numeric: tabular-nums; }
.nv-tile span { font-size: 12px; color: var(--muted); line-height: 1.3; }
.nv-riga { display: grid; gap: 6px; font-size: 14px; }
.nv-riga > span { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.nv-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.nv-chip { font-size: 13px; padding: 3px 10px; border-radius: 12px; background: var(--accent-soft); color: var(--accent); text-decoration: none; overflow-wrap: anywhere; }
.nv-barre { display: grid; grid-template-columns: max-content minmax(40px, 1fr) max-content; gap: 7px 10px; align-items: center; font-size: 14px; }
.nv-bar { height: 10px; border-radius: 0 4px 4px 0; background: var(--accent); min-width: 2px; }
.nv-barre .n { font-variant-numeric: tabular-nums; color: var(--muted); text-align: right; }
.nv-pd { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 7px 12px; align-items: baseline; font-size: 14px; margin: 0; }
.nv-pd dt { color: var(--muted); }
.nv-pd dd { margin: 0; text-align: right; font-variant-numeric: tabular-nums; }
.nv-delta { display: inline-block; font-size: 12px; font-weight: 600; padding: 0 7px; border-radius: 9px; margin-left: 6px; border: 1px solid var(--rule); color: var(--muted); white-space: nowrap; }
.nv-delta.ok { color: var(--st1); }
.nv-delta.no { color: var(--st4); }
.nv-diario { display: grid; gap: 14px; }
.nv-giri { border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }
.nv-giri th { color: var(--muted); font-weight: 500; font-size: 12px; text-align: right; }
.nv-giri td, .nv-giri th { padding: 5px 0 5px 10px; border-bottom: 1px solid var(--rule); text-align: right; }
.nv-giri td:first-child, .nv-giri th:first-child { text-align: left; padding-left: 0; }
</style>`);

sost('\nfunction render() {', String.raw`
// Ventunesima estensione, 18 novembre 2026: che cosa ha aggiunto il programma dall'ultima visita, diario dei giri,
// memoria dei fatti confermati (i dati arrivano dal programma: LIVE.diario, LIVE.ricerca.verifiche, memoria.js)
const TAPPE_NOME = { temi: 'ricerche per tema', stati: 'rotazione degli Stati', ricerca: 'ricerca autonoma', lingue: 'giro delle lingue', feed: 'feed delle testate', telegram: 'Telegram', video: 'YouTube', altro: 'altro' };
const LINGUE_NOME = { fr: 'francese', es: 'spagnolo', pt: 'portoghese', ar: 'arabo', ru: 'russo', de: 'tedesco', zh: 'cinese', 'zh-TW': 'cinese (Taiwan)', ja: 'giapponese', ko: 'coreano', tr: 'turco', hi: 'hindi', id: 'indonesiano', uk: 'ucraino', pl: 'polacco', nl: 'olandese', sv: 'svedese', el: 'greco', he: 'ebraico', vi: 'vietnamita', th: 'thailandese', bn: 'bengalese', ro: 'rumeno', hu: 'ungherese', cs: 'ceco', sk: 'slovacco', bg: 'bulgaro', sr: 'serbo', sl: 'sloveno', lt: 'lituano', lv: 'lettone', no: 'norvegese', ta: 'tamil', te: 'telugu', mr: 'marathi', ml: 'malayalam', fa: 'persiano', ur: 'urdu', sw: 'swahili', fi: 'finlandese', da: 'danese', hr: 'croato', sq: 'albanese', et: 'estone', ka: 'georgiano', hy: 'armeno', az: 'azero', kk: 'kazako', mn: 'mongolo', ne: 'nepalese', si: 'singalese', ms: 'malese', so: 'somalo', mk: 'macedone', bs: 'bosniaco', is: 'islandese', ca: 'catalano', gl: 'galiziano', af: 'afrikaans', pa: 'punjabi', gu: 'gujarati', kn: 'kannada', bo: 'tibetano' };
const VISTO_PRIMA = (() => { try { return localStorage.getItem('pg_visto') || ''; } catch (e) { return ''; } })();
window.addEventListener('load', () => setTimeout(() => { try { localStorage.setItem('pg_visto', new Date().toISOString()); } catch (e) {} }, 20000));
function nvChips(v, max, fn) { return '<div class="nv-chips">' + v.slice(0, max).map(fn).join('') + (v.length > max ? '<a class="nv-chip" href="#live">e altri ' + (v.length - max) + '</a>' : '') + '</div>'; }
function nvTile(n, t) { return '<div class="nv-tile"><b>' + n + '</b><span>' + t + '</span></div>'; }
function nvDelta(v0, v1, altoBuono, unita) {
  const d = v1 - v0; if (!d) return '<span class="nv-delta">come prima</span>';
  return '<span class="nv-delta ' + ((d > 0) === altoBuono ? 'ok' : 'no') + '">' + (d > 0 ? '▲ +' : '▼ −') + num(Math.abs(d)) + (unita || '') + '</span>';
}
function nvDati(D, giri, prima) {
  const z = D[D.length - 1], som = (k, i) => giri.reduce((s, x) => s + (i == null ? (x[k] || 0) : ((x[k] || [])[i] || 0)), 0);
  const da = {}; giri.forEach(x => Object.keys(x.da || {}).forEach(k => { da[k] = (da[k] || 0) + x.da[k]; }));
  return { z, som, da,
    fonti: [].concat(...giri.map(x => x.fonti_nuove || [])),
    tg: (z.tg_trovati || []).filter(c => !(prima.tg_trovati || []).includes(c)),
    coperti: (prima.senza || []).filter(s => !(z.senza || []).includes(s)),
    persi: (z.senza || []).filter(s => !(prima.senza || []).includes(s)) };
}
function novitaHtml() {
  const D = (liveOk() && window.LIVE.diario) || []; if (!D.length) return '';
  const giri = VISTO_PRIMA ? D.filter(x => x.iso > VISTO_PRIMA) : D.slice(-8), z = D[D.length - 1];
  const quando = VISTO_PRIMA ? new Date(VISTO_PRIMA).toLocaleString('it-IT', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }) : '';
  if (!giri.length) return '<section class="nv" aria-label="Novità"><div class="nv-top"><b>Niente di nuovo dall’ultima volta</b><span>Sei entrato il ' + esc(quando) + '. L’ultimo giro del programma è del ' + esc(z.quando) + '; il prossimo arriva entro 3 ore.</span></div></section>';
  const i0 = D.indexOf(giri[0]), prima = i0 > 0 ? D[i0 - 1] : giri[0], N = nvDati(D, giri, prima);
  let o = '<section class="nv" aria-label="Novità"><div class="nv-top"><b>' + (VISTO_PRIMA ? 'Dall’ultima volta che sei entrato' : 'Che cosa ha aggiunto il programma') + '</b><span>' + (giri.length === 1 ? (VISTO_PRIMA ? 'Dal ' + esc(quando) + ': un giro del programma, il ' : 'Nell’ultimo giro del programma, il ') : (VISTO_PRIMA ? 'Dal ' + esc(quando) + ': ' : 'Negli ultimi ') + giri.length + ' giri del programma, l’ultimo il ') + esc(z.quando) + (VISTO_PRIMA && D[0].iso > VISTO_PRIMA ? ' (qui si vedono gli ultimi ' + D.length + ' giri)' : '') + '</span></div>';
  o += '<div class="nv-tiles">' + nvTile(num(N.som('nuove')), 'voci nuove raccolte') + nvTile(num(N.fonti.length + N.tg.length), 'fonti e canali trovati da solo') + nvTile(num(N.coperti.length), 'Stati che prima erano senza notizie') + nvTile(num(N.som('memoria', 0)), 'fatti confermati messi in memoria') + '</div>';
  if (N.coperti.length) o += '<div class="nv-riga"><span>Stati ora coperti</span>' + nvChips(N.coperti, 8, s => '<a class="nv-chip" href="#live/' + encodeURIComponent(s) + '">' + esc(s) + '</a>') + '</div>';
  if (N.fonti.length || N.tg.length) o += '<div class="nv-riga"><span>Fonti nuove, da valutare</span>' + nvChips(N.fonti.concat(N.tg.map(c => 'Telegram: ' + c)), 4, f => '<span class="nv-chip">' + esc(f) + '</span>') + '</div>';
  const altro = [];
  if (N.som('verifiche', 0)) altro.push(N.som('verifiche', 0) + ' verifiche cercate, ' + N.som('verifiche', 1) + ' confermate da una fonte affidabile');
  if (N.som('seguiti', 0)) altro.push(N.som('seguiti', 0) + ' domande di seguito sui fatti più confermati (' + num(N.som('seguiti', 1)) + ' notizie)');
  if ((z.sapere || 0) > (prima.sapere || 0)) altro.push(((z.sapere || 0) - (prima.sapere || 0)) + ' Stati studiati in più su Wikipedia');
  if (z.v !== prima.v) altro.push('programma aggiornato alla versione ' + esc(z.v));
  if (altro.length) o += '<div class="nv-riga"><span>Inoltre</span><div>' + altro.join(' · ') + '</div></div>';
  return o + '<div class="s"><a href="#live">Apri Live</a> per il diario completo e le notizie.</div></section>';
}
function verificheHtml(L) {
  const V = (L.ricerca && L.ricerca.verifiche) || []; if (!V.length) return '';
  return '<details class="crit"><summary>Ultime verifiche cercate (' + V.length + ')</summary><ul class="plain">' + V.slice().reverse().map(v => '<li>' + (v[4] === 'confermata' ? '✓ confermata' + (v[6] ? ' da ' + esc(v[6]) : '') : 'nessuna conferma trovata') + ' · <a href="' + safeU(v[5]) + '" target="_blank" rel="noopener">' + esc(v[1]) + '</a> <span class="s">' + esc(v[2]) + '</span></li>').join('') + '</ul><div class="s">Per le notizie di fonti di parte o non classificate il programma cerca se una fonte affidabile riporta lo stesso fatto. Non trovare conferma non vuol dire che la notizia è falsa.</div></details>';
}
function diarioHtml(L) {
  const D = (L && L.diario) || []; if (!D.length) return '';
  const z = D[D.length - 1], lim = new Date(Date.parse(z.iso) - 24 * 3600e3).toISOString();
  const g = D.filter(x => x.iso >= lim), i0 = D.indexOf(g[0]), a = i0 > 0 ? D[i0 - 1] : g[0], N = nvDati(D, g, a);
  const pd = x => { const l = x.livelli || {}; return Math.round(100 * (l.D || 0) / Math.max(1, (l.A || 0) + (l.B || 0) + (l.C || 0) + (l.D || 0))); };
  const riga = (t, v0, v1, altoBuono, u) => '<dt>' + t + '</dt><dd>' + num(v0) + (u || '') + ' → ' + num(v1) + (u || '') + nvDelta(v0, v1, altoBuono, u) + '</dd>';
  const rif = {}; g.forEach(x => Object.keys(x.rifiuti || {}).forEach(k => { rif[k] = (rif[k] || 0) + x.rifiuti[k]; }));
  const nr = Object.keys(rif).reduce((s, k) => s + rif[k], 0), ma = a.memoria || [0, 0], mz = z.memoria || [0, 0];
  const chiavi = Object.keys(N.da).sort((p, q) => N.da[q] - N.da[p]), mx = Math.max(1, ...chiavi.map(k => N.da[k])), tot = Math.max(1, N.som('nuove'));
  let o = '<h3 id="lv-diario">Diario del programma</h3><div class="item nv-diario"><div class="x">' + g.length + (g.length === 1 ? ' giro' : ' giri') + ' nelle ultime 24 ore, dal ' + esc(g[0].quando) + ' al ' + esc(z.quando) + ' (versione ' + esc(z.v) + ').</div>';
  o += '<div class="nv-tiles">' + nvTile(num(N.som('nuove')), 'voci nuove raccolte') + nvTile(Math.round(100 * z.quota) + '%', 'notizie confermate da più fonti') + nvTile(num(z.scoperti), 'Stati senza notizie') + nvTile(num(z.fonti[0]), 'feed attivi su ' + num(z.fonti[1])) + '</div>';
  o += '<div class="nv-riga"><span>Da dove arrivano le voci nuove</span><div class="nv-barre">' + chiavi.map(k => '<div>' + esc(TAPPE_NOME[k] || k) + '</div><div title="' + esc(TAPPE_NOME[k] || k) + ': ' + num(N.da[k]) + ' voci nuove, ' + Math.round(100 * N.da[k] / tot) + '% del totale"><div class="nv-bar" style="width:' + Math.max(1, Math.round(100 * N.da[k] / mx)) + '%"></div></div><div class="n">' + num(N.da[k]) + '</div>').join('') + '</div></div>';
  o += '<div class="nv-riga"><span>I giri, uno per uno</span><table class="nv-giri"><tr><th>Quando</th><th>Minuti</th><th>Voci nuove</th><th>Richieste</th><th>Avvisi</th></tr>' + D.slice(-8).reverse().map(x => '<tr><td>' + esc(x.quando) + '</td><td>' + Math.max(1, Math.round(x.durata / 60)) + '</td><td>' + num(x.nuove) + '</td><td>' + num(x.richieste) + '</td><td>' + x.errori + '</td></tr>').join('') + '</table><div class="s">Un giro ogni 3 ore, al minuto 17: 8 al giorno. Se tra due righe passano più di 3 ore e mezza, in quell’intervallo il telefono era fermo.</div></div>';
  if (z.lingue && Object.keys(z.lingue).length) o += '<div class="nv-riga"><span>Lingue delle voci nuove dell’ultimo giro</span><div class="nv-chips">' + Object.keys(z.lingue).map(k => '<span class="nv-chip">' + esc(LINGUE_NOME[k] || k) + ' ' + z.lingue[k] + '</span>').join('') + '</div><div class="s">Oltre a italiano e inglese. I titoli vengono tradotti in italiano.</div></div>';
  o += '<div class="nv-riga"><span>Prima e dopo</span><dl class="nv-pd">' + riga('Notizie degli ultimi 3 giorni', a.live, z.live, true) + riga('Confermate da più fonti', Math.round(100 * a.quota), Math.round(100 * z.quota), true, '%') + riga('Da fonti non classificate', pd(a), pd(z), false, '%') + riga('Stati senza notizie', a.scoperti, z.scoperti, false) + riga('Feed attivi', a.fonti[0], z.fonti[0], true) + riga('Fatti confermati in memoria', ma[1], mz[1], true) + riga('Stati studiati su Wikipedia', a.sapere || 0, z.sapere || 0, true) + '</dl></div>';
  if (N.coperti.length || N.persi.length) o += '<div class="nv-riga"><span>Stati</span><div>' + (N.coperti.length ? 'Ora coperti: ' + N.coperti.map(s => '<a href="#live/' + encodeURIComponent(s) + '">' + esc(s) + '</a>').join(', ') + '. ' : '') + (N.persi.length ? 'Tornati senza notizie: ' + N.persi.map(esc).join(', ') + '.' : '') + '</div></div>';
  if (N.fonti.length || N.tg.length) o += '<div class="nv-riga"><span>Fonti trovate da solo, da valutare</span><div class="nv-chips">' + N.fonti.concat(N.tg.map(c => 'Telegram: ' + c)).map(f => '<span class="nv-chip">' + esc(f) + '</span>').join('') + '</div></div>';
  o += '<div class="nv-riga"><span>Domande e verifiche</span><dl class="nv-pd"><dt>Domande di seguito sui fatti più confermati</dt><dd>' + N.som('seguiti', 0) + ' (' + num(N.som('seguiti', 1)) + ' notizie)</dd><dt>Verifiche cercate</dt><dd>' + N.som('verifiche', 0) + ', confermate ' + N.som('verifiche', 1) + '</dd></dl>' + verificheHtml(L) + '</div>';
  o += '<div class="nv-riga"><span>Carico e spesa</span><dl class="nv-pd"><dt>Richieste ai siti per giro</dt><dd>' + num(Math.round(N.som('richieste') / g.length)) + '</dd><dt>Rifiuti per troppe richieste</dt><dd>' + nr + (nr ? ' (' + Object.keys(rif).map(k => esc(k) + ' ' + rif[k]).join(', ') + ')' : '') + '</dd><dt>Durata media di un giro</dt><dd>' + Math.max(1, Math.round(N.som('durata') / g.length / 60)) + ' minuti</dd><dt>Titoli tradotti</dt><dd>' + num(z.tradotti || 0) + '</dd><dt>Spesa del cervello</dt><dd>oggi ' + (z.usd_oggi || 0).toFixed(3).replace('.', ',') + ' $ · mese ' + (z.usd_mese || 0).toFixed(2).replace('.', ',') + ' $</dd></dl></div>';
  return o + '<div class="s">Il confronto è con il giro prima di queste 24 ore. ' + (APP_OK ? 'Tutti i giri, uno per riga: <a href="tabelle.html#diario">tabelle aperte</a>. ' : 'Tutti i giri, uno per riga, sono nelle tabelle aperte del sito. ') + 'Sul telefono: python castello.py rapporto</div></div>';
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
sost('else html = viewHome();', 'else html = novitaHtml() + viewHome();');
sost('caricaSapere();\n', 'caricaSapere();\ncaricaMemoria();\n');
fs.writeFileSync(out, h);
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
console.log('ok', out, h.length, 'inizio tolto:', inizio);

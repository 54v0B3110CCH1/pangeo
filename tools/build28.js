// Ventottesima estensione: revisione della lettura. (1) «Niente di nuovo» non compare più da solo: se dall'ultima visita
// non c'è stato un giro, si vede che cosa ha raccolto il programma nelle ultime 24 ore. (2) Live: argomenti in ordine
// fisso, giorni separati, e in cima la cronologia degli eventi confermati, un fatto per riga. (3) Schede degli Stati:
// notizie in ordine di data e date scritte tutte allo stesso modo.
// Uso: node tools/build28.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 27)
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);
h = h.replace(/(<\/html>)\s*<\/body><\/html>\s*$/, '$1\n');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function cronologiaHtml(')) {
  // (1) novità
  sost("const giri = VISTO_PRIMA ? D.filter(x => x.iso > VISTO_PRIMA) : D.slice(-8), z = D[D.length - 1];", "let giri = VISTO_PRIMA ? D.filter(x => x.iso > VISTO_PRIMA) : D.slice(-8), recap = ''; const z = D[D.length - 1];");
  sost("  if (!giri.length) return (fermo || senzaRete || inPausa) || '<section class=\"nv\" aria-label=\"Novità\"><div class=\"nv-top\"><b>Niente di nuovo dall’ultima volta</b><span>Sei entrato il ' + esc(quando) + '. L’ultimo giro del programma è del ' + esc(z.quando) + '.' + dove + '</span></div></section>';",
       "  if (!giri.length) { recap = 'Dalla tua visita del ' + esc(quando) + ' non c’è ancora stato un giro nuovo: l’ultimo è del ' + esc(z.quando) + '.' + dove + ' Intanto, ecco che cosa ha raccolto nelle ultime 24 ore.'; giri = D.filter(x => Date.parse(x.iso) > Date.now() - 864e5); if (!giri.length) giri = D.slice(-8); }");
  sost("<b>' + (VISTO_PRIMA ? 'Dall’ultima volta che sei entrato' : 'Che cosa ha aggiunto il programma') + '</b><span>' + (giri.length === 1 ?", "<b>' + (recap ? 'Nelle ultime 24 ore' : VISTO_PRIMA ? 'Dall’ultima volta che sei entrato' : 'Che cosa ha aggiunto il programma') + '</b><span>' + (recap || (giri.length === 1 ?");
  sost("' (qui si vedono gli ultimi ' + D.length + ' giri)' : '') + '</span></div>';", "' (qui si vedono gli ultimi ' + D.length + ' giri)' : '')) + '</span></div>';");
  // (2) Live: ordine degli argomenti, giorni, cronologia
  sost('\nfunction viewLive(stato) {', String.raw`
const TEMI_ORDINE = ['Conflitti e guerre', 'Difesa e forze armate', 'Basi e truppe all’estero', 'Industria e appalti', 'Alleanze e diplomazia', 'Ambasciate e relazioni diplomatiche', 'Accordi di pace e normalizzazione', 'Accordi commerciali e dazi', 'Terrorismo, spionaggio e attacchi informatici', 'Proteste e crisi politiche', 'Tensioni etniche, religiose e sociali', 'OMS, Interpol e organismi internazionali', 'Rotte, stretti e infrastrutture', 'Cielo e spazio aereo', 'Sicurezza privata e mercenari', 'Aziende: proprietà e azionisti', 'Propaganda e disinformazione', 'Disastri ed emergenze', 'Inchieste OSINT', 'Copertura degli Stati', 'Ricerca autonoma', 'Voci ufficiali e organismi internazionali', 'Voci ufficiali (Telegram)', 'Media statali (voce dei governi)', 'Notizie dal mondo', 'Scoperte automatiche (da valutare)'];
function temaPos(t) { const i = TEMI_ORDINE.indexOf(t); return i < 0 ? TEMI_ORDINE.length - 3 : i; }
function giornoNome(d) {
  const g = String(d || '').slice(0, 5), o = new Date(), f = x => String(x.getDate()).padStart(2, '0') + '/' + String(x.getMonth() + 1).padStart(2, '0'), ieri = new Date(o - 864e5);
  if (g === f(o)) return 'Oggi'; if (g === f(ieri)) return 'Ieri';
  const m = g.match(/^(\d\d)\/(\d\d)$/); return m ? +m[1] + ' ' + ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'][+m[2] - 1] : g;
}
function conGiorni(lista, riga) { let g = '', o = ''; lista.forEach(n => { const k = String(n.data || '').slice(0, 5); if (k !== g) { g = k; o += '<div class="s" style="margin:12px 0 2px;font-weight:600">' + esc(giornoNome(n.data)) + '</div>'; } o += riga(n); }); return o; }
function cronologiaHtml(items) {
  const visti = {}, ev = [];
  items.forEach(n => { if (!n.conf) return; if (n.gr != null) { if (visti[n.gr]) return; visti[n.gr] = 1; } ev.push(n); });
  if (!ev.length) return '';
  return '<h3 id="lv-crono">Cronologia degli eventi confermati</h3><div class="item">' + conGiorni(ev.slice(0, 60), n => '<div class="x" style="margin:4px 0"><span class="s">' + esc(String(n.data || '').slice(6)) + '</span> <a href="' + safeU(n.u) + '" target="_blank" rel="noopener">' + esc(n.it || n.t) + '</a> <span class="s">· ' + esc(n.fonte || '') + ((n.nf || 1) > 1 ? ' e altre ' + ((n.nf || 1) - 1) : '') + ((n.paesi || []).length ? ' · ' + n.paesi.slice(0, 3).map(esc).join(', ') : '') + '</span></div>') + '<div class="s" style="margin-top:8px">Un fatto per riga, dal più recente: solo le notizie che un’altra fonte affidabile ha riportato con parole molto simili' + (ev.length > 60 ? ' (le prime 60 di ' + ev.length + ')' : '') + '. È un controllo automatico, non una verifica dei fatti. Tutta la cronologia è in <a href="tabelle.html#cronologia">tabelle › cronologia</a>.</div></div>';
}
` + '\nfunction viewLive(stato) {');
  sost("const temi = [...new Set(items.map(n => n.tema))];", "const temi = [...new Set(items.map(n => n.tema))].map((t, i) => [t, i]).sort((a, b) => temaPos(a[0]) - temaPos(b[0]) || a[1] - b[1]).map(x => x[0]);");
  sost("if (!stato) h += briefHtml(L.brief) + segnaliHtml(L, '') + peggioraHtml(L);", "if (!stato) h += briefHtml(L.brief) + cronologiaHtml(items) + segnaliHtml(L, '') + peggioraHtml(L);\n  if (stato) h += cronologiaHtml(items);");
  sost("h += '<h3 id=\"lv-' + i + '\">' + esc(t) + '</h3>' + items.filter(n => n.tema === t).slice(0, 40).map(n => '<div class=\"item\">", "h += '<h3 id=\"lv-' + i + '\">' + esc(t) + '</h3>' + conGiorni(items.filter(n => n.tema === t).slice(0, 40), n => '<div class=\"item\">");
  sost("'</div></div>').join(''); });\n  if (!stato && (L.video || []).length) h += '<h3 id=\"lv-video\">", "'</div></div>'); });\n  if (!stato && (L.video || []).length) h += '<h3 id=\"lv-video\">");
  // (3) schede: notizie in ordine di data, date scritte allo stesso modo
  sost('\nfunction render() {', String.raw`
let SCHEDE_ORDINATE = false;
function ordinaSchede() {
  if (SCHEDE_ORDINATE) return; SCHEDE_ORDINATE = true;
  const M = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];
  const num = d => { d = String(d || '').toLowerCase(); const a = (d.match(/(19|20)\d\d/) || [0])[0], m = M.findIndex(x => d.includes(x.slice(0, 3))), g = (d.match(/^(\d{1,2})\b/) || [0, 0])[1]; return a ? a * 10000 + (m + 1) * 100 + +g : 0; };
  const bella = d => { const m = String(d || '').match(/^(\d{1,2} )?([a-zà]{3,9})\.? ((?:19|20)\d\d)$/i); if (!m) return d; const i = M.findIndex(x => x.startsWith(m[2].toLowerCase().slice(0, 3))); return i < 0 ? d : (m[1] || '') + M[i] + ' ' + m[3]; };
  Object.values(SCHEDE).forEach(s => { if (!Array.isArray(s.nz)) return; s.nz.forEach(z => { z[0] = bella(z[0]); }); s.nz = s.nz.map((z, i) => [z, i]).sort((a, b) => num(b[0][0]) - num(a[0][0]) || a[1] - b[1]).map(x => x[0]); });
}
` + '\nfunction render() {\n  ordinaSchede();');
}
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
fs.writeFileSync(out, h);
console.log('ok', out, h.length);

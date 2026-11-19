// Ventinovesima estensione: (1) lavoro a piano del programma (alleanze, patti, appalti) in Live, in una vista sua
// (#piano, #piano/<Stato>) e dentro le schede degli Stati; (2) «Le domande che il programma si fa»; (3) fermate del
// programma nel diario e nel riquadro delle novità.
// Uso: node tools/build29.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 28)
const fs = require('fs'), path = require('path');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);
h = h.replace(/(<\/html>)\s*<\/body><\/html>\s*$/, '$1\n');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function viewPiano(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext29.js'), 'utf8');
  sost('\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n', ext + '\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n');
  sost('caricaMemoria();\nif (APP_OK) {', 'caricaMemoria();\ncaricaPiano();\nif (APP_OK) {');
  // stile della domanda scritta dal programma
  sost('.nv-tiles { display: grid;', '.dq { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12.5px; line-height: 1.45; background: var(--bg); padding: 1px 6px; border-radius: 6px; overflow-wrap: anywhere; display: inline-block; margin-top: 2px; }\n.nv-tiles { display: grid;');
  // Live: piano e domande prima del diario
  sost("miglioratoreHtml(L) + diarioHtml(L) + analisiHtml(L.analisi) + ext);", "miglioratoreHtml(L) + pianoBoxHtml(L) + domandeHtml(L) + diarioHtml(L) + analisiHtml(L.analisi) + ext);");
  // vista
  sost("  else if (parts[0] === 'appalti') html = viewAppalti();", "  else if (parts[0] === 'appalti') html = viewAppalti();\n  else if (parts[0] === 'piano') html = viewPiano(parts[1] || '');");
  // cartella in prima pagina
  sost('<a class="folder big" href="#appalti"><b>Appalti e contratti</b><small>${APPALTI.length} grandi contratti della difesa del 2026</small></a>',
       '<a class="folder big" href="#appalti"><b>Appalti e contratti</b><small>${APPALTI.length} grandi contratti della difesa del 2026</small></a>\n    <a class="folder big" href="#piano"><b>Lavoro a piano</b><small>${pianoRias() ? pianoRias().i + \' Stati su \' + pianoRias().totale + \': \' + pianoRias().accordi + \' accordi e \' + pianoRias().appalti + \' appalti trovati dal programma\' : \'Alleanze, patti e appalti: uno Stato alla volta, con le domande e le fonti\'}</small></a>');
  // schede degli Stati
  sost("else if (u.id === 'alleanze') html += alleanzeHtml(s);", "else if (u.id === 'alleanze') html += alleanzeHtml(s) + pianoStatoHtml(s.nome, 'accordi');");
  sost("else if (u.id === 'appalti') html += appaltiHtml(appaltiDi(s.nome)) + '<p class=\"note\">", "else if (u.id === 'appalti') html += appaltiHtml(appaltiDi(s.nome)) + pianoStatoHtml(s.nome, 'appalti') + '<p class=\"note\">");
  sost("case 'appalti': return appaltiDi(s.nome).length > 0;", "case 'appalti': return appaltiDi(s.nome).length > 0 || pianoDi(s.nome, 'appalti').length > 0;");
  sost("if (id === 'appalti') return appaltiDi(s.nome).length;", "if (id === 'appalti') return appaltiDi(s.nome).length + pianoDi(s.nome, 'appalti').length;");
  // diario: tappa, fermate, ritmo
  sost("lingue: 'giro delle lingue', feed: 'feed delle testate', telegram: 'Telegram', video: 'YouTube', altro: 'altro' };\nconst LINGUE_NOME", "lingue: 'giro delle lingue', piano: 'lavoro a piano', feed: 'feed delle testate', telegram: 'Telegram', video: 'YouTube', altro: 'altro' };\nconst LINGUE_NOME");
  sost("(t.pausa ? ', in pausa per proteggere il telefono ' + t.pausa : '') + '.'", "(t.pausa ? ', in pausa per proteggere il telefono ' + t.pausa : '') + (t.fermo ? ', fermate ' + t.fermo : '') + '.'");
  sost("  const fuori = g.filter(x => x.tipo === 'senza rete');\n  if (fuori.length) o += '<div class=\"nv-riga\"><span>Senza rete</span>", "  o += fermateHtml(g);\n  const fuori = g.filter(x => x.tipo === 'senza rete');\n  if (fuori.length) o += '<div class=\"nv-riga\"><span>Senza rete</span>");
  // novità: piano e fermate
  sost("  if (N.som('attesa', 0)) altro.push(", "  if (N.som('piano', 0)) altro.push('lavoro a piano: ' + N.som('piano', 0) + (N.som('piano', 0) === 1 ? ' Stato lavorato' : ' Stati lavorati') + ', ' + N.som('piano', 1) + ' accordi e ' + N.som('piano', 2) + ' appalti trovati (<a href=\"#piano\">apri</a>)');\n  const nferme = giri.filter(x => x.tipo === 'fermo'); if (nferme.length) altro.push('<b>si è fermato ' + (nferme.length === 1 ? 'una volta' : nferme.length + ' volte') + '</b> (' + nferme.reduce((t, x) => t + ((x.fermo || [])[2] || 0), 0) + ' minuti in tutto): ' + esc(nferme[nferme.length - 1].motivo || ''));\n  if (N.som('attesa', 0)) altro.push(");
}
fs.writeFileSync(out, h);
console.log('ok', h.length);

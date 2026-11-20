// Trentacinquesima estensione (programma 2.24): pezzi del puzzle nelle cartelle Energia, Trasporti, Cibo e nella nuova
// cartella «IA in campo militare» (più la vista #ia), siti militari da Wikidata nelle cartelle delle basi (basi.js),
// tappe precedenti dei fatti fusi.  Uso: node tools/build35.js base.html out.html  (base con le estensioni fino alla 34)
const fs = require('fs'), path = require('path');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function viewIa(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext35.js'), 'utf8');
  sost('\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n', ext + '\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n');
  sost('caricaInfra();\nif (APP_OK) {', 'caricaInfra();\ncaricaBasi();\nif (APP_OK) {');
  // cartella nuova e vista
  sost("  { id: 'intelligence', nome: 'Intelligence', col: '--numeri' },", "  { id: 'intelligence', nome: 'Intelligence', col: '--numeri' },\n  { id: 'ia', nome: 'IA in campo militare', col: '--numeri' },");
  sost("  else if (parts[0] === 'risorse') html = viewRisorse();", "  else if (parts[0] === 'risorse') html = viewRisorse();\n  else if (parts[0] === 'ia') html = viewIa();");
  sost('    <a class="folder big" href="#risorse">', '    <a class="folder big" href="#ia"><b>IA in campo militare</b><small>${puzzleTutti(\'ia\').length ? puzzleTutti(\'ia\').length + \' fatti trovati dal programma sulla stampa\' : \'Sistemi, contratti, regole e incidenti: che cosa scrive la stampa, Stato per Stato\'}</small></a>\n    <a class="folder big" href="#risorse">');
  // dove compaiono le cartelle
  sost("    case 'energia': return !!infraDi(s.nome, 'energia');", "    case 'ia': return puzzleDi(s.nome, 'ia').length > 0;\n    case 'basi': return !!s.items.basi || (basiWdDi(s.nome) || []).length > 0;\n    case 'estero': return !!s.items.estero || basiWdEsteroDi(s.nome).length > 0;\n    case 'energia': return !!infraDi(s.nome, 'energia') || puzzleDi(s.nome, 'energia').length > 0;");
  sost("    case 'logistica': return !!infraDi(s.nome, 'trasporti');", "    case 'logistica': return !!infraDi(s.nome, 'trasporti') || puzzleDi(s.nome, 'trasporti').length > 0;");
  sost("    case 'cibo': return !!infraDi(s.nome, 'cibo');", "    case 'cibo': return !!infraDi(s.nome, 'cibo') || puzzleDi(s.nome, 'cibo').length > 0;");
  sost("  if (ITEM_SUBS.includes(id)) return s.items[id].length;", "  if (id === 'basi') return ((s.items.basi || []).length + (basiWdDi(s.nome) || []).filter(e => !e.ch).length) || null;\n  if (id === 'estero') return ((s.items.estero || []).length + basiWdEsteroDi(s.nome).length) || null;\n  if (id === 'ia') return puzzleDi(s.nome, 'ia').length || null;\n  if (ITEM_SUBS.includes(id)) return s.items[id].length;");
  // che cosa mostrano
  sost("    else if (u.id === 'energia') html += energiaHtml(s.nome);", "    else if (u.id === 'ia') html += puzzleStatoHtml(s.nome, 'ia') + '<p class=\"note\"><a href=\"#ia\">L’IA in campo militare in tutti gli Stati →</a></p>';\n    else if (u.id === 'energia') html += energiaHtml(s.nome) + puzzleStatoHtml(s.nome, 'energia');");
  sost("    else if (u.id === 'logistica') html += logisticaHtml(s.nome);", "    else if (u.id === 'logistica') html += logisticaHtml(s.nome) + puzzleStatoHtml(s.nome, 'trasporti');");
  sost("    else if (u.id === 'cibo') html += ciboHtml(s.nome);", "    else if (u.id === 'cibo') html += ciboHtml(s.nome) + puzzleStatoHtml(s.nome, 'cibo');");
  sost("    else html += s.items[u.id].map(x => {", "    else html += (s.items[u.id] || []).map(x => {");
  sost("    }).join('') + (u.id === 'basi' ? wdBasiHtml(s) : '');", "    }).join('') + (u.id === 'basi' ? (s.items.basi ? wdBasiHtml(s) : '') + basiWdHtml(s.nome) : u.id === 'estero' ? basiWdEsteroHtml(s.nome) : '');");
  // tappe dei fatti fusi, puzzle nel lavoro a piano e nelle novità
  sost("function pianoPiede(x) { return '<div class=\"s\">' + rilBadge(x.r) + pianoStato(x.st) + ((x.f || []).length > 1 ? 'più fonti' : 'una fonte') + ': ' + pianoFonti(x.f) + '</div>'; }",
       "function pianoPiede(x) { return '<div class=\"s\">' + rilBadge(x.r) + pianoStato(x.st) + ((x.f || []).length > 1 ? 'più fonti' : 'una fonte') + ': ' + pianoFonti(x.f) + '</div>' + tappeHtml(x); }");
  sost("  h += intelSezionePiano(s);", "  h += intelSezionePiano(s);\n  h += puzzleSezionePiano(s);");
  sost("  if (N.som('quadro', 1)) altro.push(", "  if (N.som('puzzle', 0)) altro.push('puzzle: ' + N.som('puzzle', 0) + (N.som('puzzle', 0) === 1 ? ' pezzo nuovo' : ' pezzi nuovi') + ' su energia, IA militare, trasporti e cibo');\n  if (N.som('quadro', 1)) altro.push(");
}
fs.writeFileSync(out, h);
console.log('ok', h.length);

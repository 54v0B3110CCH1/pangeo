// Trentesima estensione: (1) sezione Intelligence (vista #intelligence, cartella in ogni Stato, fatti del lavoro a piano);
// (2) l'avviso rosso guarda il diario e sul sito pubblico distingue «telefono fermo» da «sito che non riceve i dati».
// Uso: node tools/build30.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 29)
// Prima va rigenerato l'elenco dei servizi:  python3 tools/intel_base.py --siti
const fs = require('fs'), path = require('path');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function viewIntelligence(')) {
  const intel = JSON.parse(fs.readFileSync(path.join(__dirname, 'dati', 'intel.json'), 'utf8'));
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext30.js'), 'utf8').replace('/*INTEL_JSON*/', JSON.stringify(intel));
  // dopo la ventinovesima (usa le sue funzioni), prima della ventiduesima
  sost('\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n', ext + '\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n');
  sost('caricaMemoria();\ncaricaPiano();\nif (APP_OK) {', 'caricaMemoria();\ncaricaPiano();\ncaricaDiario();\nif (APP_OK) {');
  // vista e cartella in prima pagina
  sost("  else if (parts[0] === 'piano') html = viewPiano(parts[1] || '');", "  else if (parts[0] === 'piano') html = viewPiano(parts[1] || '');\n  else if (parts[0] === 'intelligence') html = viewIntelligence(parts[1] || '');");
  sost('    <a class="folder big" href="#propaganda"><b>Propaganda e voci ufficiali</b>', '    <a class="folder big" href="#intelligence"><b>Intelligence</b><small>${Object.keys(INTEL.stati).length} Stati: i servizi, che cosa pubblicano, con chi scambiano informazioni, che cosa ne scrive la stampa</small></a>\n    <a class="folder big" href="#propaganda"><b>Propaganda e voci ufficiali</b>');
  // cartella nella scheda di ogni Stato
  sost("  { id: 'pmc', nome: 'Sicurezza privata e mercenari', col: '--basi' },", "  { id: 'pmc', nome: 'Sicurezza privata e mercenari', col: '--basi' },\n  { id: 'intelligence', nome: 'Intelligence', col: '--numeri' },");
  sost("    case 'pmc': return pmcDi(s.nome).length > 0;", "    case 'pmc': return pmcDi(s.nome).length > 0;\n    case 'intelligence': return intelDi(s.nome).length > 0 || pianoDi(s.nome, 'intel').length > 0 || INTEL_REL.some(r => r[0] === s.nome) || intelScambiDi(s.nome).length > 0;");
  sost("  if (id === 'pmc') return pmcDi(s.nome).length;", "  if (id === 'pmc') return pmcDi(s.nome).length;\n  if (id === 'intelligence') return (intelDi(s.nome).length + pianoDi(s.nome, 'intel').length) || null;");
  sost("    else if (u.id === 'appalti') html += appaltiHtml(appaltiDi(s.nome))", "    else if (u.id === 'intelligence') html += intelStatoHtml(s.nome);\n    else if (u.id === 'appalti') html += appaltiHtml(appaltiDi(s.nome))");
  // lavoro a piano: i fatti sui servizi nella scheda dello Stato e nelle novità
  sost("((s.appalti || []).map(pianoAppalto).join('') || '<p class=\"note\">Nessuno nei titoli letti.</p>');\n", "((s.appalti || []).map(pianoAppalto).join('') || '<p class=\"note\">Nessuno nei titoli letti.</p>');\n  h += intelSezionePiano(s);\n");
  sost("  if (N.som('attesa', 0)) altro.push(", "  if (N.som('intel', 0)) altro.push('intelligence: ' + N.som('intel', 0) + (N.som('intel', 0) === 1 ? ' fatto pubblico sui servizi' : ' fatti pubblici sui servizi') + ' trovati sulla stampa (<a href=\"#intelligence\">apri</a>)');\n  if (N.som('attesa', 0)) altro.push(");
  // avviso rosso: guarda l'ultimo giro del diario (arriva dopo ogni giro) e sul sito pubblico dice le due cause possibili
  sost("const sulTelefono = /^(localhost|127\\.0\\.0\\.1)$/.test(location.hostname), minuti = Math.round((Date.now() - Date.parse(z.iso)) / 60000);",
       "const zu = (window.DIARIO_ULT && window.DIARIO_ULT.iso > z.iso) ? window.DIARIO_ULT : z;\n  const sulTelefono = /^(localhost|127\\.0\\.0\\.1)$/.test(location.hostname), minuti = Math.round((Date.now() - Date.parse(zu.iso)) / 60000);");
  sost("const fermo = APP_OK && minuti > (sulTelefono && z.tipo ? 95 : 200) ? '<section class=\"nv nv-fermo\" role=\"status\"><div class=\"nv-top\"><b>Il programma è fermo da ' + durata(minuti) + '</b><span>L’ultimo giro è del ' + esc(z.quando) + '. Per farlo ripartire apri Termux e lancia <code>bash avvia.sh</code>, poi lascia Termux aperto in sottofondo, con la batteria su «Senza restrizioni».</span></div></section>' : '';",
       "const fermo = APP_OK && minuti > (sulTelefono && zu.tipo ? 95 : 200) ? '<section class=\"nv nv-fermo\" role=\"status\"><div class=\"nv-top\"><b>' + (sulTelefono ? 'Il programma è fermo da ' : 'Questo sito non riceve dati da ') + durata(minuti) + '</b><span>' + (sulTelefono ? 'L’ultimo giro è del ' + esc(zu.quando) + '. Per farlo ripartire apri Termux e lancia <code>bash avvia.sh</code>, poi lascia Termux aperto in sottofondo, con la batteria su «Senza restrizioni».' : 'L’ultimo giro arrivato qui è del ' + esc(zu.quando) + '. Le cause possibili sono due. Il telefono è fermo: in Termux lancia <code>bash avvia.sh</code>. Oppure gira ma non è più collegato a GitHub: in Termux lancia <code>bash github.sh</code>. Sul telefono la pagina sempre aggiornata è <code>http://127.0.0.1:8080/</code>.') + '</span></div></section>' : '';");
}
fs.writeFileSync(out, h);
console.log('ok', h.length);

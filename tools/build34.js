// Trentaquattresima estensione: cartelle «Energia», «Trasporti e logistica», «Cibo e risorse», «Dipendenze e commercio»
// in ogni Stato, la spesa per settori nella cartella «Numeri» e la vista #risorse con il confronto tra tutti gli Stati.
// I dati stanno in tabelle/infra.json:  python3 tools/infra_base.py   (va rifatto prima, se il Factbook cambia)
// Uso: node tools/build34.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 33)
const fs = require('fs'), path = require('path');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function viewRisorse(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext34.js'), 'utf8');
  sost('\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n', ext + '\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n');
  sost('caricaDiario();\ncaricaServizi();\nif (APP_OK) {', 'caricaDiario();\ncaricaServizi();\ncaricaInfra();\nif (APP_OK) {');
  // cartelle nuove in ogni Stato
  sost("  { id: 'aeroporti', nome: 'Aeroporti e spazio aereo', col: '--aero' },",
       "  { id: 'energia', nome: 'Energia', col: '--infra' },\n  { id: 'logistica', nome: 'Trasporti e logistica', col: '--infra' },\n  { id: 'cibo', nome: 'Cibo e risorse', col: '--infra' },\n  { id: 'dipendenze', nome: 'Dipendenze e commercio', col: '--aziende' },\n  { id: 'aeroporti', nome: 'Aeroporti e spazio aereo', col: '--aero' },");
  sost("    case 'numeri': return !!s.dati;",
       "    case 'numeri': return !!s.dati || !!infraDi(s.nome, 'spesa');\n    case 'energia': return !!infraDi(s.nome, 'energia');\n    case 'logistica': return !!infraDi(s.nome, 'trasporti');\n    case 'cibo': return !!infraDi(s.nome, 'cibo');\n    case 'dipendenze': return !!(infraDi(s.nome, 'commercio') || ((infraDi(s.nome, 'energia') || {}).dipendenza));");
  sost("    else if (u.id === 'numeri') html += numeriHtml(s.dati);",
       "    else if (u.id === 'numeri') html += (s.dati ? numeriHtml(s.dati) : '') + spesaSettoriHtml(s.nome);\n    else if (u.id === 'energia') html += energiaHtml(s.nome);\n    else if (u.id === 'logistica') html += logisticaHtml(s.nome);\n    else if (u.id === 'cibo') html += ciboHtml(s.nome);\n    else if (u.id === 'dipendenze') html += dipendenzeHtml(s.nome);");
  // vista di confronto e cartella in prima pagina
  sost("  else if (parts[0] === 'quadro') html = viewQuadro();", "  else if (parts[0] === 'quadro') html = viewQuadro();\n  else if (parts[0] === 'risorse') html = viewRisorse();");
  sost('    <a class="folder big" href="#propaganda"><b>Propaganda e voci ufficiali</b>',
       '    <a class="folder big" href="#risorse"><b>Energia, risorse e dipendenze</b><small>Per ogni Stato: reti e fonti di energia, trasporti, cibo, da chi compra e a chi vende, spesa per settori</small></a>\n    <a class="folder big" href="#propaganda"><b>Propaganda e voci ufficiali</b>');
  sost("  document.querySelectorAll('.fchip').forEach(b => b.addEventListener('click', () => { filtroStab = +b.dataset.l; render(); }));",
       "  document.querySelectorAll('.fchip:not(.ris-ord)').forEach(b => b.addEventListener('click', () => { filtroStab = +b.dataset.l; render(); }));\n  document.querySelectorAll('.ris-ord').forEach(b => b.addEventListener('click', () => { risorseOrd = b.dataset.o; render(); }));");
}
fs.writeFileSync(out, h);
console.log('ok', h.length);

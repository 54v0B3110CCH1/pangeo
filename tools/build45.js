// Quarantacinquesima estensione (programma 2.35): il potere, istituzionale e non. Testo in dati/ext45.js.
// Uso: node tools/build45.js base.html out.html   (base con l'estensione 44)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function sistemaSchedaHtml(')) throw new Error('manca l’estensione 44');
if (!h.includes('function viewPotere(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext45.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  sost("  else if (parts[0] === 'storia') html = viewStoria();", "  else if (parts[0] === 'storia') html = viewStoria();\n  else if (parts[0] === 'potere') html = viewPotere(parts[1]);");
  sost("  ['Stati e politica', ['#stati', '#avvisi', '#andamento', '#fatti', '#storia', '#alleanze', '#live', '#temi', '#propaganda']],",
       "  ['Stati e politica', ['#stati', '#avvisi', '#andamento', '#fatti', '#storia', '#alleanze', '#live', '#temi', '#propaganda']],\n  ['Potere e soldi', ['#potere']],");
  sost("  tess['#economia'] = ", "  tess['#potere'] = '<a class=\"folder big\" href=\"#potere\"><b>Potere, istituzionale e non</b><small>Chi guida FMI, Banca Mondiale e banche centrali; fondi sovrani, grandi gestori e banche con le loro quote nella difesa; i più ricchi; chi gestisce porti e aeroporti; gruppi armati non statali</small></a>';\n  tess['#economia'] = ");
  sost('statoFattoHtml(n) + sistemiStatoHtml(n) + schedeStatoHtml(n);', 'statoFattoHtml(n) + sistemiStatoHtml(n) + potereStatoHtml(n) + schedeStatoHtml(n);');
  sost("  if (rows.length) html += `<div class=\"item\"><dl class=\"kv\">${rows.map(r => `<dt>${esc(r[0])}</dt><dd>${esc(r[1])}</dd>`).join('')}</dl></div>`;",
       "  if (rows.length) html += `<div class=\"item\"><dl class=\"kv\">${rows.map(r => `<dt>${esc(r[0])}</dt><dd>${esc(r[1])}</dd>`).join('')}</dl></div>`;\n  { const gH = potGruppoHtml(a.nome); if (gH) html += '<h3 id=\"az-gruppo\"><span class=\"dot\" style=\"background:var(--aziende)\"></span>Chi la controlla e che cosa controlla</h3>' + gH; }");
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

// Quarantunesima estensione (programma 2.33): la storia di ogni Stato. Testo in dati/ext41.js.
// Uso: node tools/build41.js base.html out.html   (base con le estensioni 38, 39 e 40)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('// Quarantesima estensione')) throw new Error('manca l’estensione 40');
if (!h.includes('function viewStoria(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext41.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  sost("  else if (parts[0] === 'economia') html = viewEconomia();", "  else if (parts[0] === 'economia') html = viewEconomia();\n  else if (parts[0] === 'storia') html = viewStoria();");
  sost("  ['Stati e politica', ['#stati', '#avvisi', '#andamento', '#fatti',", "  ['Stati e politica', ['#stati', '#avvisi', '#andamento', '#fatti', '#storia',");
  sost("  tess['#economia'] = ", "  tess['#storia'] = '<a class=\"folder big\" href=\"#storia\"><b>Storia</b><small>Conflitti armati dal 1946, colpi di Stato dal 1950 e la cronologia di ogni Stato, collegati ai fatti di oggi</small></a>';\n  tess['#economia'] = ");
  sost("sapereHtml(s.nome, 'storia') + archiviHtml(s.nome);", "sapereHtml(s.nome, 'storia') + storiaHtml(s.nome) + archiviHtml(s.nome);");
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

// Quarantatreesima estensione (programma 2.34): com'è fatto ogni Stato. Testo in dati/ext43.js.
// Uso: node tools/build43.js base.html out.html   (base con l'estensione 42)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('// Quarantaduesima estensione')) throw new Error('manca l’estensione 42');
if (!h.includes('function statoFattoHtml(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext43.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  sost('  return leg + andamentoHtml(n) + economiaStatoHtml(n) + schedeStatoHtml(n);', '  return leg + andamentoHtml(n) + economiaStatoHtml(n) + statoFattoHtml(n) + schedeStatoHtml(n);');
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

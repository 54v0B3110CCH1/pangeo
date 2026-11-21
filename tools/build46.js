// Quarantaseiesima estensione (programma 2.35): biblioteca e studi. Testo in dati/ext46.js.
// Uso: node tools/build46.js base.html out.html   (base con l'estensione 45)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function viewPotere(')) throw new Error('manca l’estensione 45');
if (!h.includes('function viewBiblioteca(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext46.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  const st = h.indexOf('</style>'); h = h.slice(0, st) + '.bib-cit { font-style: italic; color: var(--muted); margin: 4px 0; }\n' + h.slice(st);
  sost("  else if (parts[0] === 'potere') html = viewPotere(parts[1]);", "  else if (parts[0] === 'potere') html = viewPotere(parts[1]);\n  else if (parts[0] === 'biblioteca') html = viewBiblioteca(parts[1], parts[2]);");
  sost("  ['Potere e soldi', ['#potere']],", "  ['Potere e soldi', ['#potere']],\n  ['Studi', ['#biblioteca']],");
  sost("  tess['#potere'] = ", "  tess['#biblioteca'] = '<a class=\"folder big\" href=\"#biblioteca\"><b>Biblioteca e studi</b><small>I classici su potere, guerra, denaro e storia letti capitolo per capitolo, con le dinamiche e le citazioni; gli studi recenti dei centri di ricerca</small></a>';\n  tess['#potere'] = ");
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

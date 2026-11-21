// Quarantaduesima estensione: riquadro delle novità più chiaro. Testo in dati/ext42.js e dati/ext42.css.
// Uso: node tools/build42.js base.html out.html   (base con l'estensione 41)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
if (!h.includes('function viewStoria(')) throw new Error('manca l’estensione 41');
if (!h.includes('// Quarantaduesima estensione')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext42.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  const css = fs.readFileSync(path.join(__dirname, 'dati', 'ext42.css'), 'utf8');
  const st = h.indexOf('</style>'); if (st < 0) throw new Error('manca </style>');
  h = h.slice(0, st) + css + h.slice(st);
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

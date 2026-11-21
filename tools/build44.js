// Quarantaquattresima estensione (programma 2.35): la scheda di ogni sistema d'arma. Testo in dati/ext44.js e dati/ext44.css.
// Uso: node tools/build44.js base.html out.html   (base con l'estensione 43)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function statoFattoHtml(')) throw new Error('manca l’estensione 43');
if (!h.includes('function sistemaSchedaHtml(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext44.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  const css = fs.readFileSync(path.join(__dirname, 'dati', 'ext44.css'), 'utf8');
  const st = h.indexOf('</style>'); if (st < 0) throw new Error('manca </style>');
  h = h.slice(0, st) + css + h.slice(st);
  sost("    let h = '<h2>' + esc(S.nome) + '</h2><p class=\"note\">' + esc(S.tipo) + ' · ' + (az.length ? az.map(a => azLink(a.nome)).join(', ') : esc(S.chi)) + '</p>';",
       "    let h = '<h2>' + esc(S.nome) + '</h2><p class=\"note\">' + esc(S.tipo) + ' · ' + (az.length ? az.map(a => azLink(a.nome)).join(', ') : esc(S.chi)) + '</p>';\n    h += sistemaSchedaHtml(id);");
  sost('  return leg + andamentoHtml(n) + economiaStatoHtml(n) + statoFattoHtml(n) + schedeStatoHtml(n);',
       '  return leg + andamentoHtml(n) + economiaStatoHtml(n) + statoFattoHtml(n) + sistemiStatoHtml(n) + schedeStatoHtml(n);');
  sost('function viewSistemi(id) {\n  const I = sistemiIndice().I;', 'function viewSistemi(id) {\n  caricaSistemi();\n  const I = sistemiIndice().I;');
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

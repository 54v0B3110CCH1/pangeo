// Trentanovesima estensione (programma 2.30): economia e canali trovati da soli. Testo in dati/ext39.js.
// Uso: node tools/build39.js base.html out.html   (base con l'estensione 38)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function viewLegami(')) throw new Error('manca l’estensione 38');
if (!h.includes('function viewEconomia(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext39.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  sost("  else if (parts[0] === 'avvisi') html = viewAvvisi();", "  else if (parts[0] === 'avvisi') html = viewAvvisi();\n  else if (parts[0] === 'economia') html = viewEconomia();");
  sost("  ['Risorse ed energia', ['#risorse']],", "  ['Risorse ed energia', ['#risorse', '#economia']],");
  sost("  tess['#documenti'] = ", "  tess['#economia'] = '<a class=\"folder big\" href=\"#economia\"><b>Economia</b><small>Titoli di Stato, valute, materie prime, commercio e armi dalle dogane ONU, dati della Banca Mondiale</small></a>';\n  tess['#documenti'] = ");
  sost("  return leg + andamentoHtml(n) + schedeStatoHtml(n);", "  return leg + andamentoHtml(n) + economiaStatoHtml(n) + schedeStatoHtml(n);");
  sost("  const C = copertura(), tot = C.length, conta = k => C.filter(x => x[1][k]).length;", "  h += canaliHtml();\n  const C = copertura(), tot = C.length, conta = k => C.filter(x => x[1][k]).length;");
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

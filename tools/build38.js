// Trentottesima estensione (programma 2.29): rete dei legami, andamento per Stato, fatti in schede, avvisi, ricerca per
// significato. Testo in dati/ext38.js.   Uso: node tools/build38.js base.html out.html
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function viewLegami(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext38.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  sost("  else if (parts[0] === 'live') html = viewLive(parts[1] || '');",
       "  else if (parts[0] === 'legami') html = viewLegami(parts[1] || '');\n  else if (parts[0] === 'andamento') html = viewAndamento();\n" +
       "  else if (parts[0] === 'fatti') html = viewFatti();\n  else if (parts[0] === 'avvisi') html = viewAvvisi();\n  else if (parts[0] === 'live') html = viewLive(parts[1] || '');");
  sost("  if (q) html = viewSearch(q) + cercaFattiHtml(q) + cercaTelHtml(q);", "  if (q) html = viewSearch(q) + cercaFattiHtml(q) + cercaTelHtml(q) + cercaSigHtml(q);");
  sost("  else html = novitaHtml() + quadroHome() + viewHome2();", "  else html = avvisiBanner() + novitaHtml() + quadroHome() + viewHome2();");
  sost("  html += (only ? '' : sintesiHtml(s.nome)) + subGruppiHtml(s, subs);", "  html += (only ? '' : sintesiHtml(s.nome)) + subGruppiHtml(s, subs) + (only ? '' : statoExtraHtml(s.nome));");
  sost("  ['Stati e politica', ['#stati', '#alleanze', '#live', '#temi', '#propaganda']],",
       "  ['Stati e politica', ['#stati', '#avvisi', '#andamento', '#fatti', '#alleanze', '#live', '#temi', '#propaganda']],");
  sost("  ['Industria e appalti', ['#aziende', '#appalti', '#industria', '#rete', '#piano']],", "  ['Industria e appalti', ['#aziende', '#appalti', '#legami', '#industria', '#rete', '#piano']],");
  sost("  tess['#documenti'] = ", "  tess['#avvisi'] = '<a class=\"folder big\" href=\"#avvisi\"><b>Avvisi</b><small>Quando uno Stato si accende: picchi di notizie confermate, fatti gravi, cieli che si svuotano, calore</small></a>';\n" +
       "  tess['#andamento'] = '<a class=\"folder big\" href=\"#andamento\"><b>Andamento</b><small>Giorno per giorno, Stato per Stato: dove se ne parla più del solito</small></a>';\n" +
       "  tess['#fatti'] = '<a class=\"folder big\" href=\"#fatti\"><b>Fatti in schede</b><small>Ogni notizia confermata con tipo, Stati e numeri: attacchi, accordi, acquisti, tregue…</small></a>';\n" +
       "  tess['#legami'] = '<a class=\"folder big\" href=\"#legami\"><b>Rete dei legami</b><small>Chi firma accordi con chi e chi vende armi a chi: tocchi uno Stato e vedi tutti i suoi legami</small></a>';\n" +
       "  tess['#documenti'] = ");
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

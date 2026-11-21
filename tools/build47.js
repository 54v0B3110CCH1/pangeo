// Quarantasettesima estensione (programma 2.38): il controllo dei dati (chi guida su più fonti, con il voto), le armi
// vendute e comprate (SIPRI), i fatti dagli articoli. Testo in dati/ext47.js.
// Uso: node tools/build47.js base.html out.html   (base con l'estensione 46)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function viewBiblioteca(')) throw new Error('manca l’estensione 46');
if (!h.includes('function viewArmi(')) {
  const st = h.indexOf('</style>');
  h = h.slice(0, st) + '.voto { display: inline-block; padding: 0 6px; border-radius: 4px; font-size: .78em; font-weight: 600; white-space: nowrap; border: 1px solid currentColor; }\n' +
    '.voto.v-ok { color: #1b7f3b; } .voto.v-medio { color: #8a6d00; } .voto.v-no { color: #b3261e; }\n' +
    '@media (prefers-color-scheme: dark) { .voto.v-ok { color: #6fd28f; } .voto.v-medio { color: #e3c35a; } .voto.v-no { color: #ff8a80; } }\n' +
    '.avviso-dato { color: #b3261e; margin-top: 3px; } @media (prefers-color-scheme: dark) { .avviso-dato { color: #ff8a80; } }\n.capi-st { margin-top: 6px; }\n' + h.slice(st);
  sost('function potGuida(x) {', 'function potGuidaWd(x) {');
  sost("[x.nato ? 'dal ' + esc(x.nato) : '', (x.att || []).length ? 'attivi ' + esc(x.att[0]) : '', (x.capi || []).length ? 'guida: ' + esc(x.capi.join(', ')) : '']",
    "[x.nato ? 'dal ' + esc(x.nato) : '', (x.att || []).length ? 'attivi ' + esc(x.att[0]) : '', potGuida(x)]");
  sost("  const tSez = sez === 'gruppi' ? 'Chi controlla chi: aziende della difesa' :", "  const tSez = sez === 'controllo' ? 'Controllo dei dati: chi guida' : sez === 'gruppi' ? 'Chi controlla chi: aziende della difesa' :");
  sost("    return h + '</div>';\n  }\n  if (sez === 'gruppi') return h + potGruppiVista();",
    "    h += '<a class=\"folder big\" href=\"#potere/controllo\"><b>Controllo dei dati: chi guida</b><small>Ogni nome confrontato su Wikidata, Wikipedia, notizie e sito ufficiale, con il voto alla NATO e la data; i disaccordi in evidenza</small></a>';\n" +
    "    return h + '</div>';\n  }\n  if (sez === 'controllo') return h + capiControlloVista();\n  if (sez === 'gruppi') return h + potGruppiVista();");
  sost("${rows.map(r => `<dt>${esc(r[0])}</dt><dd>${esc(r[1])}</dd>`).join('')}</dl>${sch(s).f ? `<div class=\"s\">Fonti: ${srcAny(sch(s).f)}</div>` : ''}",
    "${rows.map(r => `<dt>${esc(r[0])}</dt><dd>${esc(r[1])}</dd>`).join('')}</dl>${capiStatoHtml(s.nome, g)}${sch(s).f ? `<div class=\"s\">Fonti: ${srcAny(sch(s).f)}</div>` : ''}");
  sost('statoFattoHtml(n) + sistemiStatoHtml(n) + potereStatoHtml(n) + schedeStatoHtml(n) + archiviStatoHtml(n);',
    'statoFattoHtml(n) + fattiStatoHtml(n) + sistemiStatoHtml(n) + armiStatoHtml(n) + potereStatoHtml(n) + schedeStatoHtml(n) + archiviStatoHtml(n);');
  sost("  else if (parts[0] === 'biblioteca') html = viewBiblioteca(parts[1], parts[2]);",
    "  else if (parts[0] === 'biblioteca') html = viewBiblioteca(parts[1], parts[2]);\n  else if (parts[0] === 'armi') html = viewArmi(parts[1]);");
  sost("  ['Difesa', ['#forze', '#sistemi', '#unita'", "  ['Difesa', ['#forze', '#sistemi', '#armi', '#unita'");
  sost("  tess['#sistemi'] = ", "  tess['#armi'] = '<a class=\"folder big\" href=\"#armi\"><b>Armi vendute e comprate</b><small>Chi vende che cosa a chi negli ultimi dieci anni, con gli ordini non ancora consegnati (registro SIPRI)</small></a>';\n  tess['#sistemi'] = ");
  sost('    h += sistemaSchedaHtml(id);\n', '    h += sistemaSchedaHtml(id);\n    h += armiSistemaHtml(S);\n');
  // il testo dell'estensione va dopo le sostituzioni: contiene la nuova potGuida
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext47.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

// Quarantesima estensione (programma 2.31): avvisi con il tipo, fonti dirette invece di Wikipedia. Testo in dati/ext40.js.
// Uso: node tools/build40.js base.html out.html   (base con le estensioni 38 e 39). Le funzioni di ext40 sostituiscono
// quelle con lo stesso nome (in JavaScript vale l'ultima dichiarata).
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
if (!h.includes('function viewEconomia(')) throw new Error('manca l’estensione 39');
if (!h.includes('// Quarantesima estensione')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext40.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  h = h.split("Il programma avvisa quando uno Stato si accende: molte più notizie confermate del solito, fatti con 10 morti o più, un cielo che si svuota, calore in forte aumento. Sono segnali da guardare, non previsioni.")
    .join("Il programma avvisa quando uno Stato si accende: molte più notizie confermate del solito, fatti con 10 morti o più, movimenti di truppe, spie e sabotaggi, esplosioni e incendi gravi, spazio aereo chiuso, colpi di Stato, legge marziale, attentati, test missilistici, un cielo che si svuota, calore in forte aumento, monete che crollano, titoli di Stato che salgono. Un avviso per tipo, Stato e giorno, solo da fatti confermati da più testate. Sono segnali da guardare, non previsioni.");
  h = h.split("const INTEL_NOTA_ELENCO = 'Elenco fatto in automatico da Wikipedia e Wikidata il ' + pianoData(INTEL.agg) + ' e poi ripulito a mano: può contenere errori o lasciare fuori qualcosa. Fa fede il sito ufficiale.';")
    .join("const INTEL_NOTA_ELENCO = 'Elenco fatto in automatico il ' + pianoData(INTEL.agg) + ' (Wikidata) e ripulito a mano: può contenere errori o lasciare fuori qualcosa. Il nome porta al sito ufficiale del servizio; fa fede quello.';");
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

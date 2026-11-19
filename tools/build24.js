// Ventiquattresima estensione: fonti corrette con le prove del 19 novembre 2026 (UCDP e ReliefWeb chiedono un codice,
// WikiLeaks entra come archivio da consultare a mano) e, in ogni Stato, il collegamento alla ricerca nell'archivio WikiLeaks.
// Uso: node tools/build24.js base.html out.html  (base = pagina con la 23)
const fs = require('fs'), vm = require('vm'), path = require('path');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
const dati = [path.join(__dirname, 'dati', 'en.json'), path.join(__dirname, '..', 'out24', 'en.json')].find(p => fs.existsSync(p));
const EN = JSON.parse(fs.readFileSync(dati, 'utf8'));
sost('"Eventi georeferenziati e morti nei conflitti","API gratuita"', '"Eventi georeferenziati e morti nei conflitti","L’API chiede un codice di accesso, da domandare all’università di Uppsala (provata il 19/11/2026: senza codice risponde «non autorizzato»)"');
sost('"Rapporti umanitari e di situazione","API gratuita"', '"Rapporti umanitari e di situazione","Feed RSS libero: il programma lo legge a ogni giro. L’API invece chiede un nome di applicazione approvato (provata il 19/11/2026: rifiuta senza)"');
sost('["Conflitti","ReliefWeb (ONU)"', '["Notizie","WikiLeaks","https://wikileaks.org","Archivio di documenti riservati resi pubblici dal 2006: cablogrammi diplomatici, posta di governi e aziende, documenti militari. Si cerca per parola","Sito libero con ricerca interna (search.wikileaks.org). Non ha un feed (provato il 19/11/2026): il programma non lo legge da solo, in ogni Stato c’è il collegamento per cercarlo a mano","Media","Documenti trafugati e pubblicati senza contesto né replica degli interessati; quasi tutti vecchi di anni; contengono nomi di persone private, da non riportare. Un documento autentico non prova che ciò che dice sia vero"],["Conflitti","ReliefWeb (ONU)"');
sost('\nfunction render() {', String.raw`
// Ventiquattresima estensione: archivi da consultare a mano, Stato per Stato
const EN_STATI = ` + JSON.stringify(EN) + String.raw`;
function archiviHtml(nome) {
  const en = EN_STATI[nome]; if (!en) return '';
  return '<div class="item"><div class="t">Archivi da consultare a mano</div><div class="x"><a href="https://search.wikileaks.org/?query=' + encodeURIComponent('"' + en + '"') + '" target="_blank" rel="noopener">Cerca «' + esc(en) + '» nell’archivio WikiLeaks</a></div><div class="s">Documenti riservati resi pubblici, quasi tutti vecchi di anni: servono per la storia, non per le notizie di oggi. Sono pubblicati senza contesto e senza replica, e contengono nomi di persone private. Il programma non li legge da solo: WikiLeaks non ha un feed.</div></div>';
}
` + '\nfunction render() {');
sost("+ sapereHtml(s.nome, 'storia');", "+ sapereHtml(s.nome, 'storia') + archiviHtml(s.nome);");
fs.writeFileSync(out, h);
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
console.log('ok', out, h.length);

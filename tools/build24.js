// Ventiquattresima estensione: fonti corrette con le prove del 19 novembre 2026 (UCDP e ReliefWeb chiedono un codice,
// WikiLeaks entra come archivio da consultare a mano) e, in ogni Stato, il collegamento alla ricerca nell'archivio WikiLeaks.
// Uso: node tools/build24.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 23)
const fs = require('fs'), vm = require('vm'), path = require('path');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
// La base è la pagina pubblicata così com'è (con i blocchi notturni dentro): si tolgono la riga-cornice in cima e la
// chiusura doppia in fondo, che la pubblicazione rimette ogni volta.
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);
h = h.replace(/(<\/html>)\s*<\/body><\/html>\s*$/, '$1\n');
// Diario e novità: giro «senza rete» e sala d'attesa delle testate locali. Le stesse modifiche sono già in build21.js:
// qui servono per una pagina costruita con il build21 di prima (se ci sono già, si salta).
const DIARIO = [
  [String.raw`(x.tipo === 'leggero' ? ' <span class="s">leggero</span>' : '')`, String.raw`(x.tipo === 'leggero' ? ' <span class="s">leggero</span>' : x.tipo === 'senza rete' ? ' <span class="s">senza rete</span>' : '')`],
  [String.raw`Se tra due righe passa molto più di un’ora, in quell’intervallo il telefono era fermo.</div></div>';`, String.raw`Se tra due righe passa molto più di un’ora, in quell’intervallo il telefono era fermo. «Senza rete» vuol dire che il telefono non raggiungeva internet: in quel giro il programma non raccoglie, rilegge l’archivio che ha già e cerca conferme tra le notizie; appena la rete torna fa subito un giro completo.</div></div>';
  const fuori = g.filter(x => x.tipo === 'senza rete');
  if (fuori.length) o += '<div class="nv-riga"><span>Senza rete</span><div>' + fuori.length + (fuori.length === 1 ? ' giro' : ' giri') + ' senza rete nelle ultime 24 ore (dal ' + esc(fuori[0].quando) + '). Lavoro fatto intanto sull’archivio: ' + num(fuori.reduce((t, x) => t + ((x.offline || [])[0] || 0), 0)) + ' conferme in più tra le notizie, ' + num(fuori.reduce((t, x) => t + ((x.offline || [])[1] || 0), 0)) + ' fatti messi in memoria.</div></div>';`],
  [String.raw`<dt>Titoli tradotti</dt><dd>' + num(z.tradotti || 0) + '</dd>`, String.raw`<dt>Titoli tradotti</dt><dd>' + num(z.tradotti || 0) + '</dd>' + (z.attesa ? '<dt>Testate locali nella loro lingua</dt><dd>' + num(N.som('attesa', 0)) + ' titoli scelti e tradotti · ' + num(N.som('attesa', 1)) + ' scartati · ' + num(z.attesa[2] || 0) + ' in coda</dd>' : '') + '`],
  [String.raw`  const dove = !APP_OK ?`, String.raw`  const R = window.LIVE.rete, gd = R && R.giu_dal ? new Date(R.giu_dal) : null;
  const senzaRete = gd && !isNaN(gd) ? '<section class="nv nv-fermo" role="status"><div class="nv-top"><b>Il telefono è senza rete</b><span>Dal ' + esc(gd.toLocaleString('it-IT', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })) + ' il programma non raggiunge internet. Non è fermo: rilegge l’archivio, cerca conferme tra le notizie che ha già e riprova ogni minuto; appena la rete torna fa subito un giro completo.</span></div></section>' : '';
  const dove = !APP_OK ?`],
  [String.raw`  if (!giri.length) return fermo || '<section`, String.raw`  if (!giri.length) return (fermo || senzaRete) || '<section`],
  [String.raw`  let o = fermo + '<section class="nv" aria-label="Novità">`, String.raw`  let o = (fermo || senzaRete) + '<section class="nv" aria-label="Novità">`],
  [String.raw`  if (z.v !== prima.v) altro.push(`, String.raw`  const nfuori = giri.filter(x => x.tipo === 'senza rete').length;
  if (nfuori) altro.push(nfuori + (nfuori === 1 ? ' giro' : ' giri') + ' senza rete: archivio riletto, ' + num(giri.reduce((t, x) => t + ((x.offline || [])[0] || 0), 0)) + ' conferme in più');
  if (N.som('attesa', 0)) altro.push(num(N.som('attesa', 0)) + ' titoli presi da testate locali nella loro lingua e tradotti');
  if (z.v !== prima.v) altro.push(`]];
if (!h.includes('Il telefono è senza rete')) DIARIO.forEach(([v, n]) => sost(v, n));
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

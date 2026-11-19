// Ventiseiesima estensione: il diario al ritmo di un giro ogni mezz'ora. Riepilogo delle 24 ore (quanti giri per tipo,
// intervallo più lungo), 12 righe nella tabella dei giri, testi aggiornati.
// Uso: node tools/build26.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 25)
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);
h = h.replace(/(<\/html>)\s*<\/body><\/html>\s*$/, '$1\n');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function nvRitmo(')) {
  sost('\nfunction diarioHtml(L) {', String.raw`
// Ventiseiesima estensione: quanti giri per tipo e l'intervallo più lungo tra due giri (per vedere se si è fermato)
function nvRitmo(g) {
  const t = { completo: 0, leggero: 0, 'senza rete': 0 }; g.forEach(x => { t[x.tipo || 'completo'] = (t[x.tipo || 'completo'] || 0) + 1; });
  let buco = 0, quando = ''; for (let i = 1; i < g.length; i++) { const m = Math.round((Date.parse(g[i].iso) - Date.parse(g[i - 1].iso)) / 60000); if (m > buco) { buco = m; quando = g[i - 1].quando; } }
  const d = m => m < 90 ? m + ' minuti' : Math.floor(m / 60) + ' ore' + (m % 60 >= 5 ? ' e ' + (m % 60) + ' minuti' : '');
  return ' Completi ' + t.completo + ', leggeri ' + t.leggero + (t['senza rete'] ? ', senza rete ' + t['senza rete'] : '') + '.' + (g.length > 1 ? ' Intervallo più lungo tra due giri: ' + d(buco) + (buco > 100 ? ' (dopo il giro del ' + esc(quando) + ': lì il telefono era fermo)' : '') + '.' : '');
}
` + '\nfunction diarioHtml(L) {');
  sost("' al ' + esc(z.quando) + ' (versione ' + esc(z.v) + ').</div>';", "' al ' + esc(z.quando) + ' (versione ' + esc(z.v) + ').' + nvRitmo(g) + '</div>';");
  sost("D.slice(-8).reverse().map(x => '<tr><td>' + esc(x.quando)", "D.slice(-12).reverse().map(x => '<tr><td>' + esc(x.quando)");
  sost("<div class=\"s\">Un giro ogni ora: ogni 3 ore completo (ricerche comprese), gli altri leggeri (feed, Telegram, YouTube, cielo). Se tra due righe passa molto più di un’ora,", "<div class=\"s\">Dalla versione 2.17 un giro ogni mezz’ora (prima uno all’ora): ogni 3 ore completo (ricerche comprese), gli altri leggeri (feed, Telegram, YouTube, cielo). Qui gli ultimi 12; tutti i giri sono in <a href=\"tabelle.html#diario\">tabelle › diario</a>. Se tra due righe passa molto più del solito,");
  sost("(z.tipo ? ' Il prossimo giro arriva entro un’ora.' : ' Il prossimo giro arriva entro 3 ore.')", "(z.tipo ? ' Il prossimo giro arriva entro ' + (z.v >= '2.17' ? 'mezz’ora.' : 'un’ora.') : ' Il prossimo giro arriva entro 3 ore.')");
}
fs.writeFileSync(out, h);
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
console.log('ok', out, h.length);

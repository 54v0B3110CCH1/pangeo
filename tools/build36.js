// Trentaseiesima estensione (programma 2.25): pagina più leggera, collegamenti nei testi (Stati, aziende, sistemi d'arma),
// vista #sistemi, schede degli altri Stati, sintesi di ogni Stato, cartelle di uno Stato in cinque gruppi, prima pagina in
// sei aree con il planisfero a richiesta, Documenti con rapporti e copertura. Testo dell'estensione in dati/ext36.js.
// Uso: node tools/build36.js base.html out.html   (base con le estensioni fino alla 35)
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function viewSistemi(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext36.js'), 'utf8');
  // l'estensione va in fondo allo script, prima dell'ultimo render(): usa funzioni già definite e ne cambia una (basiWdRiga)
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  // planisfero a richiesta: niente librerie da 1 MB a ogni apertura
  sost('<script src="https://cdn.jsdelivr.net/npm/echarts@4.9.0/dist/echarts.min.js"></script>\n<script src="https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/js/world.js"></script>\n', '');
  // un solo ridisegno e file in cache per 10 minuti
  sost("s.onload = () => { render(); s.remove(); };", "s.onload = () => { ridisegna(); s.remove(); };", 4);
  sost("s.onload = () => { basiWdIndice(); render(); s.remove(); };", "s.onload = () => { basiWdIndice(); ridisegna(); s.remove(); };");
  sost("function caricaLive(ridisegna) {", "function caricaLive(rifai) {");
  sost("ls.onload = () => { if (ridisegna) render(); ls.remove(); };", "ls.onload = () => { if (rifai) ridisegna(); ls.remove(); };");
  sost("window.DIARIO_ULT = d[d.length - 1]; window.DIARIO_TUTTO = d; render(); }", "window.DIARIO_ULT = d[d.length - 1]; window.DIARIO_TUTTO = d; ridisegna(); }");
  sost("if (d && d.stati) { window.INFRA = d; render()", "if (d && d.stati) { window.INFRA = d; ridisegna()");
  for (const f of ['sapere', 'memoria', 'piano', 'servizi', 'basi', 'live']) sost(".src = '" + f + ".js?v=' + Date.now()", ".src = '" + f + ".js?v=' + verDati()");
  sost('caricaLive(true);\ncaricaSapere();\ncaricaMemoria();\ncaricaPiano();\ncaricaDiario();\ncaricaServizi();\ncaricaInfra();\ncaricaBasi();\n',
       'caricaLive(true);\ncaricaDiario();\n// i file grossi dopo la prima vista (subito se si apre una pagina interna)\ncaricaDopo(() => { caricaPiano(); caricaMemoria(); caricaSapere(); caricaServizi(); caricaBasi(); caricaInfra(); });\n');
  // prima pagina in sei aree, Documenti nuovi, sistemi d'arma
  sost("  else html = novitaHtml() + quadroHome() + viewHome();", "  else html = novitaHtml() + quadroHome() + viewHome2();");
  sost("  else if (parts[0] === 'documenti') html = viewDocs();", "  else if (parts[0] === 'documenti') html = viewDocumenti(parts[1] || '');\n  else if (parts[0] === 'sistemi') html = viewSistemi(parts[1] || '');");
  // cartella di uno Stato: sintesi in cima, cartelle in cinque gruppi, accordi e appalti scritti nelle schede degli altri Stati
  sost("  const subs = SUB.filter(u => hasSub(s, u.id));", "  const subs = subOrdinati().filter(u => hasSub(s, u.id));");
  sost("  html += `<div class=\"sub\">${subs.map(u => { const n = subCount(s, u.id); return `<a href=\"#stati/${s.slug}/${u.id}\"><span class=\"dot\" style=\"background:var(${subCol(s, u)})\"></span>${esc(u.nome)}${n ? ' (' + n + ')' : ''}</a>`; }).join('')}</div>`;",
       "  html += (only ? '' : sintesiHtml(s.nome)) + subGruppiHtml(s, subs);");
  sost("    else if (u.id === 'alleanze') html += alleanzeHtml(s) + pianoStatoHtml(s.nome, 'accordi');",
       "    else if (u.id === 'alleanze') html += alleanzeHtml(s) + pianoStatoHtml(s.nome, 'accordi') + pianoAltriHtml(s.nome, 'accordi');");
  sost("    else if (u.id === 'appalti') html += appaltiHtml(appaltiDi(s.nome)) + pianoStatoHtml(s.nome, 'appalti') +",
       "    else if (u.id === 'appalti') html += appaltiHtml(appaltiDi(s.nome)) + pianoStatoHtml(s.nome, 'appalti') + pianoAltriHtml(s.nome, 'appalti') +");
  // collegamenti nei testi
  sost("' + esc(x.cosa) + '", "' + collega(x.cosa) + '", 3);
  sost("x.con ? 'con ' + esc(x.con) : ''", "x.con ? 'con ' + collega(x.con) : ''");
  sost("' + esc(x.ogg) + '", "' + collega(x.ogg) + '");
  sost("x.acq ? 'compra ' + stLink(x.acq) : '', x.forn ? 'fornisce ' + esc(x.forn) : ''", "x.acq ? 'compra ' + (STATI[x.acq] ? stLink(x.acq) : collega(x.acq)) : '', x.forn ? 'fornisce ' + collega(x.forn) : ''");
  sost("${esc(r[1])}${withSrc", "${collega(r[1])}${withSrc");
  sost("' + esc(x[2]) + '</div><div class=\"m\">' + esc(x[0]) + ' · compra ' + stLink(x[1]) + ' · fornisce ' + esc(x[3])",
       "' + collega(x[2]) + '</div><div class=\"m\">' + esc(x[0]) + ' · compra ' + stLink(x[1]) + ' · fornisce ' + collega(x[3])");
  sost("' + esc(c.testo) + '", "' + collega(c.testo) + '");
  sost("' · <a href=\"' + safeU(x[4]) + '\" target=\"_blank\" rel=\"noopener\">' + esc(x[1]) + '</a> <span class=\"s\">' + esc(x[2]) + ' e altre '",
       "' · ' + collega(x[1]) + ' <span class=\"s\"><a href=\"' + safeU(x[4]) + '\" target=\"_blank\" rel=\"noopener\">' + esc(x[2]) + '</a> e altre '");
}
// sintassi
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

// Trentaduesima estensione (programma 2.23): servizi riassunti in italiano, rilevanza dei fatti del lavoro a piano,
// quadro del cervello (scaletta delle voci più rilevanti, collegamenti tra fatti con domanda e risposta).
// Uso: node tools/build32.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 31)
const fs = require('fs'), path = require('path');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function viewQuadro(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext32.js'), 'utf8');
  sost('\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n', ext + '\n// Ventiduesima estensione: ambasciate e società di ogni Stato\n');
  sost('caricaDiario();\nif (APP_OK) {', 'caricaDiario();\ncaricaServizi();\nif (APP_OK) {');
  // quadro: vista propria, in prima pagina (le prime 5) e in Live dopo «Da sapere adesso»
  sost("  else if (parts[0] === 'intelligence') html = viewIntelligence(parts[1] || '');",
       "  else if (parts[0] === 'intelligence') html = viewIntelligence(parts[1] || '');\n  else if (parts[0] === 'quadro') html = viewQuadro();");
  sost('else html = novitaHtml() + viewHome();', 'else html = novitaHtml() + quadroHome() + viewHome();');
  sost('if (!stato) h += briefHtml(L.brief) + ', 'if (!stato) h += briefHtml(L.brief) + quadroHtml(quadroDati(), true) + ');
  // servizi: il riassunto in italiano sotto il nome
  sost("function intelServizio(x) { return '<li><a href=\"' + safeU(x[2]) + '\" target=\"_blank\" rel=\"noopener\">' + esc(x[0]) + '</a>' + (x[1] ? ' <span class=\"s\">dal ' + esc(x[1]) + '</span>' : '') + (x[3] ? ' · <a href=\"' + safeU(x[3]) + '\" target=\"_blank\" rel=\"noopener\">sito ufficiale</a>' : '') + '</li>'; }",
       "function intelServizio(x) { const v = servizioSintesi(x[4]); return '<li><a href=\"' + safeU(x[2]) + '\" target=\"_blank\" rel=\"noopener\">' + esc(x[0]) + '</a>' + (x[1] ? ' <span class=\"s\">dal ' + esc(x[1]) + '</span>' : '') + (x[3] ? ' · <a href=\"' + safeU(x[3]) + '\" target=\"_blank\" rel=\"noopener\">sito ufficiale</a>' : '') + (v ? '<div class=\"x\" style=\"margin:2px 0 8px\">' + esc(v.s) + ' <span class=\"s\">(riassunto dal programma, dalla <a href=\"' + safeU(v.u || x[2]) + '\" target=\"_blank\" rel=\"noopener\">voce di Wikipedia</a>)</span></div>' : '') + '</li>'; }");
  sost("nvTile(num(nServ), 'servizi in elenco')", "nvTile(num(nServ), 'servizi in elenco') + nvTile(num(Object.keys(window.SERVIZI || {}).length), 'servizi riassunti in italiano')");
  // rilevanza: badge su intelligence, accordi e appalti; nella sezione Intelligence prima i più rilevanti
  sost("<div class=\"s\"><span class=\"badge\" style=\"--c:var(' + t[1] + ')\">' + esc(t[0]) + '</span> '", "<div class=\"s\">' + rilBadge(x.r) + '<span class=\"badge\" style=\"--c:var(' + t[1] + ')\">' + esc(t[0]) + '</span> '");
  sost("function pianoPiede(x) { return '<div class=\"s\">' + pianoStato(x.st)", "function pianoPiede(x) { return '<div class=\"s\">' + rilBadge(x.r) + pianoStato(x.st)");
  sost("return l.sort((a, b) => String(b[1].d || '').localeCompare(String(a[1].d || '')));",
       "return l.sort((a, b) => ((b[1].r || 0) - (a[1].r || 0)) || String(b[1].d || '').localeCompare(String(a[1].d || '')));");
  sost("' Qui i 15 più recenti su ' + fatti.length", "' Qui i 15 più rilevanti su ' + fatti.length");
  // novità: i collegamenti nuovi e le domande cercate
  sost("  if (N.som('attesa', 0)) altro.push(", "  if (N.som('quadro', 1)) altro.push(N.som('quadro', 1) + (N.som('quadro', 1) === 1 ? ' collegamento nuovo' : ' collegamenti nuovi') + ' tra i fatti (<a href=\"#quadro\">apri</a>)');\n  if (N.som('quadro', 2)) altro.push(N.som('quadro', 2) + (N.som('quadro', 2) === 1 ? ' domanda di un collegamento cercata' : ' domande dei collegamenti cercate'));\n  if (N.som('attesa', 0)) altro.push(");
}
fs.writeFileSync(out, h);
console.log('ok', h.length);

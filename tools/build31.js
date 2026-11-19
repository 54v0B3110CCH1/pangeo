// Trentunesima estensione: sul sito pubblico le novità e il diario dei giri leggono diario.json, che il telefono
// manda dopo ogni giro, invece del diario dentro live.json, che arriva solo ogni 3 ore.
// Prima la pagina diceva «non c'è ancora stato un giro nuovo» anche quando il telefono girava ogni 10 minuti.
// Uso: node tools/build31.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 30)
const fs = require('fs');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('function diarioFresco(')) {
  sost('window.DIARIO_ULT = d[d.length - 1]; render();', 'window.DIARIO_ULT = d[d.length - 1]; window.DIARIO_TUTTO = d; render();');
  sost('function novitaHtml() {\n  const D = (liveOk() && window.LIVE.diario) || [];',
       '// il diario più recente tra quello dentro live.json (ogni 3 ore) e diario.json (dopo ogni giro)\n' +
       'function diarioFresco(L) {\n  const D0 = (L && L.diario) || [], DT = window.DIARIO_TUTTO || [];\n' +
       '  return DT.length && (!D0.length || DT[DT.length - 1].iso > D0[D0.length - 1].iso) ? DT : D0;\n}\n' +
       'function novitaHtml() {\n  const D = liveOk() ? diarioFresco(window.LIVE) : [];');
  sost('function diarioHtml(L) {\n  const D = (L && L.diario) || [];', 'function diarioHtml(L) {\n  const D = diarioFresco(L);');
  sost("' Sul sito i dati arrivano ogni 3 ore.'", "' Sul sito il diario dei giri arriva dopo ogni giro, le notizie complete ogni 3 ore.'");
}
fs.writeFileSync(out, h);
console.log('ok', h.length);

// Ventiduesima estensione: ambasciate di ogni Stato negli altri Stati (Wikidata) e «Fedi, etnie e disuguaglianze»
// (copia d'archivio del World Factbook, Banca Mondiale). Uso: node tools/build22.js base.html out.html
// La base è la pagina con la Ventunesima; i dati sono in out22/dati22.json.
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
const D = JSON.parse(fs.readFileSync(require('path').join(__dirname, 'dati', 'dati22.json'), 'utf8'));
const ANCORA = 'const $ = s => document.querySelector(s);';
const js = o => JSON.stringify(o).replace(/<\//g, '<\\/');
sost(ANCORA, '\n// Ventiduesima estensione, 18 novembre 2026: sedi diplomatiche (Wikidata) e società (fedi, etnie, disuguaglianze). Chiavi delle fonti qh_\n' +
  "Object.assign(F, { qh_wd_sedi: ['Wikidata, ambasciate, alte commissioni e nunziature (interrogazione del 18 novembre 2026, tolte le sedi chiuse)', 'https://www.wikidata.org/wiki/Q3917681'], " +
  "qh_factbook: ['CIA World Factbook, «People and Society» (copia d’archivio factbook.json; il Factbook ha chiuso il 4 febbraio 2026)', 'https://github.com/factbook/factbook.json'], " +
  "qh_gini: ['Banca Mondiale, indice di Gini (SI.POV.GINI), ultimo anno disponibile', 'https://data.worldbank.org/indicator/SI.POV.GINI'] });\n" +
  'const SOC_FEDI = ' + js(D.FE) + ';\nconst SOC_ETNIE = ' + js(D.ET) + ';\nconst SOC_GINI = ' + js(D.G) + ';\n' +
  'const DIPLO = {};\n((N, DD) => { Object.keys(DD).forEach(i => { const a = N[i]; (DIPLO[a] = DIPLO[a] || { fuori: [], dentro: [] }).fuori = DD[i].map(j => N[j]); DD[i].forEach(j => { const b = N[j]; (DIPLO[b] = DIPLO[b] || { fuori: [], dentro: [] }).dentro.push(a); }); }); })(' + js(D.DN) + ', ' + js(D.DD) + ');\n' + ANCORA);
sost('\nfunction render() {', String.raw`
// Ventiduesima estensione: ambasciate e società di ogni Stato
function statiLink(v) { return v.slice().sort((a, b) => a.localeCompare(b, 'it')).map(n => STATI[n] ? '<a href="#stati/' + STATI[n].slug + '">' + esc(n) + '</a>' : esc(n)).join(', '); }
function diploHtml(nome) {
  const d = DIPLO[nome]; if (!d) return '';
  const soloFuori = d.fuori.filter(n => !d.dentro.includes(n)), soloDentro = d.dentro.filter(n => !d.fuori.includes(n));
  let o = '<div class="item"><div class="nv-tiles">' + nvTile(num(d.fuori.length), 'Stati dove ha un’ambasciata') + nvTile(num(d.dentro.length), 'Stati che hanno un’ambasciata qui') + '</div>';
  if (d.fuori.length) o += '<div class="t" style="margin-top:12px">Ambasciate di ' + esc(nome) + ' all’estero</div><div class="x">' + statiLink(d.fuori) + '</div>';
  if (d.dentro.length) o += '<div class="t" style="margin-top:12px">Ambasciate straniere in ' + esc(nome) + '</div><div class="x">' + statiLink(d.dentro) + '</div>';
  if (soloFuori.length || soloDentro.length) o += '<details class="crit"><summary>Scambi non reciproci nell’elenco (' + (soloFuori.length + soloDentro.length) + ')</summary><div class="x">' + (soloFuori.length ? 'Ha un’ambasciata, ma l’altro Stato non ne ha una qui: ' + statiLink(soloFuori) + '. ' : '') + (soloDentro.length ? 'Ospita un’ambasciata, ma non ne ha una nell’altro Stato: ' + statiLink(soloDentro) + '.' : '') + '</div></details>';
  return o + '<div class="s">Ambasciate, alte commissioni e nunziature, una per coppia di Stati; le sedi sono quasi sempre nella capitale. Elenco aperto di Wikidata, letto il 18 novembre 2026 e senza le sedi segnate come chiuse: può avere buchi, può comprendere sedi sospese o chiuse da poco e non comprende i consolati. Aperture e chiusure recenti: in Live, tema «Ambasciate e relazioni diplomatiche». Fonti: ' + src(['qh_wd_sedi']) + '</div></div>';
}
function societaHtml(nome) {
  const f = SOC_FEDI[nome], e = SOC_ETNIE[nome], g = SOC_GINI[nome]; if (!f && !e && !g) return '';
  let o = '<div class="item">';
  if (f) o += '<div class="t">Fedi religiose</div><div class="x">' + esc(f) + '</div>';
  if (e) o += '<div class="t" style="margin-top:12px">Etnie e minoranze</div><div class="x" lang="en">' + esc(e) + '</div><div class="s">Testo originale in inglese, come nella fonte.</div>';
  if (g) o += '<div class="t" style="margin-top:12px">Disuguaglianza dei redditi</div><div class="x">Indice di Gini ' + num(g[0]) + ' (' + g[1] + '). Da 0, tutti uguali, a 100, tutto a uno solo: sopra 40 la disuguaglianza è alta.</div>';
  return o + '<div class="s">Percentuali e anni sono quelli della fonte e possono essere vecchi; le caste non hanno statistiche ufficiali confrontabili. Tensioni di oggi: in Live, tema «Tensioni etniche, religiose e sociali». Fonti: ' + src([f || e ? 'qh_factbook' : null, g ? 'qh_gini' : null].filter(Boolean)) + '</div></div>';
}
` + '\nfunction render() {');
sost("  { id: 'siti', nome: 'Siti ufficiali', col: '--accent' },", "  { id: 'siti', nome: 'Siti ufficiali', col: '--accent' },\n  { id: 'sedi', nome: 'Ambasciate e sedi diplomatiche', col: '--voci' },\n  { id: 'societa', nome: 'Fedi, etnie e disuguaglianze', col: '--proteste' },");
sost("    case 'siti': return !!SITI[s.nome];", "    case 'siti': return !!SITI[s.nome];\n    case 'sedi': return !!DIPLO[s.nome];\n    case 'societa': return !!(SOC_FEDI[s.nome] || SOC_ETNIE[s.nome] || SOC_GINI[s.nome]);");
sost("  if (id === 'siti') return SITI[s.nome].length;", "  if (id === 'siti') return SITI[s.nome].length;\n  if (id === 'sedi') return DIPLO[s.nome].fuori.length + DIPLO[s.nome].dentro.length;\n  if (id === 'societa') return [SOC_FEDI, SOC_ETNIE, SOC_GINI].filter(o => o[s.nome]).length;");
sost("    else if (u.id === 'unita') html += unitaHtml(", "    else if (u.id === 'sedi') html += diploHtml(s.nome);\n    else if (u.id === 'societa') html += societaHtml(s.nome);\n    else if (u.id === 'unita') html += unitaHtml(");
fs.writeFileSync(out, h);
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
console.log('ok', out, h.length);

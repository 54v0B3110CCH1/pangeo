// Da dove parte il lavoro a piano del programma: per ogni Stato, ciò che l'archivio della pagina ha già su alleanze,
// trattati e appalti. Il cervello lo riceve come «già in archivio», così segnala solo le novità.
// Uso: node tools/piano_base.js index.html programma/piano_base.json
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
const h = fs.readFileSync(base, 'utf8');
const s0 = h.indexOf('<script>') + 8, js = h.slice(s0, h.indexOf('</script>', s0));
const el = () => ({ innerHTML: '', value: '', style: {}, dataset: {}, addEventListener() {}, setAttribute() {}, appendChild() {}, querySelectorAll() { return []; }, classList: { add() {}, remove() {}, toggle() {} } });
const ctx = { console, setTimeout, clearTimeout, encodeURIComponent, decodeURIComponent, document: { querySelector: () => el(), getElementById: () => null, querySelectorAll: () => [], createElement: el, head: el(), body: el(), addEventListener() {} }, localStorage: { getItem: () => null, setItem() {} }, location: { hash: '', hostname: 'x', protocol: 'https:' }, navigator: {}, addEventListener() {}, history: { replaceState() {} }, matchMedia: () => ({ matches: false, addEventListener() {} }) };
ctx.window = ctx; vm.createContext(ctx);
try { vm.runInContext(js, ctx); } catch (e) { /* la pagina prova a disegnarsi: qui servono solo i dati */ }
const G = n => vm.runInContext('typeof ' + n + ' !== "undefined" ? ' + n + ' : null', ctx);
const A = G('ALLEANZE'), S = G('SCHEDE'), AP = G('APPALTI') || [];
const B = {};
Object.keys(S).forEach(n => {
  const al = Object.values(A).filter(a => (a.m || []).includes(n)).map(a => a.n);
  const tr = (S[n].tr || []).map(t => String(t).slice(0, 140));
  const ap = AP.filter(a => a[1] === n).map(a => (a[0] + ' – ' + a[2] + ' – ' + a[3] + (a[4] ? ' – ' + a[4] : '')).slice(0, 220));
  if (al.length || tr.length || ap.length) B[n] = { al, tr, ap };
});
fs.writeFileSync(out, JSON.stringify(B));
console.log(Object.keys(B).length + ' Stati, ' + fs.statSync(out).size + ' byte');

// Smoke test: esegue tutto lo script della pagina con un DOM finto e prova le viste.
const fs = require('fs'), vm = require('vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const s0 = html.indexOf('<script>') + 8, s1 = html.indexOf('</script>', s0);
const js = html.slice(s0, s1);
const el = () => ({ innerHTML: '', textContent: '', value: '', style: {}, dataset: {}, addEventListener() {}, setAttribute() {}, appendChild() {}, scrollIntoView() {}, querySelectorAll() { return []; } });
const els = {};
function enc(pts) { const q = pts.map(([x, y]) => [Math.round(x * 1024), Math.round(y * 1024)]); let [px, py] = q[0]; let s = ''; q.forEach(([x, y]) => { const dx = x - px, dy = y - py; px = x; py = y; s += String.fromCharCode(((dx << 1) ^ (dx >> 31)) + 64) + String.fromCharCode(((dy << 1) ^ (dy >> 31)) + 64); }); return [s, q[0]]; }
const [si, oi] = enc([[7, 37], [18, 37], [18, 47], [7, 47], [7, 37]]);
const world = { UTF8Encoding: true, features: [{ properties: { name: 'Italy' }, geometry: { type: 'Polygon', coordinates: [si], encodeOffsets: [oi] } }] };
const ctx = {
  console, setTimeout, clearTimeout, encodeURIComponent, decodeURIComponent,
  document: { querySelector: s => (els[s] = els[s] || el()), getElementById: () => null, querySelectorAll: () => [], createElement: el, head: el(), body: el(), addEventListener() {} },
  location: { hash: '', protocol: 'https:', hostname: 'example.org' }, navigator: {}, localStorage: { getItem() { return null; }, setItem() {} },
  echarts: { getMap: () => ({ geoJson: world }) }, addEventListener() {}, scrollTo() {}, matchMedia: () => ({ matches: false, addEventListener() {} })
};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(js, ctx);
const live = process.argv[3] ? fs.readFileSync(process.argv[3], 'utf8') : '';
if (live) vm.runInContext(live, ctx);
const prove = process.argv.slice(4);
for (const hsh of prove) {
  ctx.location.hash = '#' + hsh;
  vm.runInContext('render()', ctx);
  const out = els['#view'].innerHTML;
  console.log('#' + hsh, '→', out.length, 'caratteri', out.includes('undefined') ? '(contiene "undefined")' : '');
  if (process.env.RAW) console.log(out.match(new RegExp(process.env.RAW, "g")));
  if (process.env.SHOW) console.log(out.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, +process.env.SHOW));
}

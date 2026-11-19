// Ventisettesima estensione: nel diario si vedono le pause volute (telefono caldo, batteria), i dati scaricati,
// la temperatura del telefono e il tetto di spesa raggiunto.
// Uso: node tools/build27.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 26)
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
const inizio = h.indexOf('<!DOCTYPE html>'); if (inizio > 0) h = h.slice(inizio);
h = h.replace(/(<\/html>)\s*<\/body><\/html>\s*$/, '$1\n');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('nvTelefono(')) {
  sost(String.raw`(x.tipo === 'leggero' ? ' <span class="s">leggero</span>' : x.tipo === 'senza rete' ? ' <span class="s">senza rete</span>' : '')`,
       String.raw`(x.tipo && x.tipo !== 'completo' ? ' <span class="s">' + esc(x.tipo) + (x.motivo ? ': ' + esc(x.motivo) : '') + '</span>' : '')`);
  sost("(t['senza rete'] ? ', senza rete ' + t['senza rete'] : '') + '.'", "(t['senza rete'] ? ', senza rete ' + t['senza rete'] : '') + (t.pausa ? ', in pausa per proteggere il telefono ' + t.pausa : '') + '.'");
  sost('\nfunction diarioHtml(L) {', String.raw`
function nvTelefono(z, g) {
  let o = '';
  const mb = g.reduce((s, x) => s + (x.mb || 0), 0), conMb = g.filter(x => x.mb != null).length;
  if (conMb) o += '<dt>Dati scaricati</dt><dd>' + String(Math.round(mb)).replace('.', ',') + ' MB nelle ultime 24 ore · ' + String(Math.round(10 * mb / conMb) / 10).replace('.', ',') + ' MB a giro</dd>';
  const t = z.tel;
  if (t && (t[0] != null || t[1] != null)) o += '<dt>Telefono</dt><dd>' + [t[0] != null ? String(t[0]).replace('.', ',') + ' gradi' : '', t[1] != null ? 'batteria ' + t[1] + '%' : '', t[2] === true ? 'in carica' : t[2] === false ? 'non in carica' : ''].filter(Boolean).join(' · ') + '</dd>';
  if (z.tetto) o += '<dt>Tetto di spesa</dt><dd><b>raggiunto quello del ' + (z.tetto === 'mese' ? 'mese' : 'giorno') + '</b>: il cervello è fermo, la raccolta continua</dd>';
  return o;
}
` + '\nfunction diarioHtml(L) {');
  sost("<dt>Titoli tradotti</dt><dd>' + num(z.tradotti || 0) + '</dd>'", "<dt>Titoli tradotti</dt><dd>' + num(z.tradotti || 0) + '</dd>' + nvTelefono(z, g)");
  sost("  const dove = !APP_OK ?", "  const inPausa = z.tipo === 'pausa' ? '<section class=\"nv nv-fermo\" role=\"status\"><div class=\"nv-top\"><b>Il programma è in pausa</b><span>' + esc(z.motivo || '') + ' (' + esc(z.quando) + '). Riparte da solo appena il telefono si raffredda o va sotto carica.</span></div></section>' : '';\n  const dove = !APP_OK ?");
  sost("  if (!giri.length) return (fermo || senzaRete) || '<section", "  if (!giri.length) return (fermo || senzaRete || inPausa) || '<section");
  sost("  let o = (fermo || senzaRete) + '<section class=\"nv\" aria-label=\"Novità\">", "  let o = (fermo || senzaRete || inPausa) + '<section class=\"nv\" aria-label=\"Novità\">");
}
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
fs.writeFileSync(out, h);
console.log('ok', out, h.length);

// Trentasettesima estensione (programma 2.26): file per Stato per memoria e lavoro a piano, ricerca nei fatti del programma
// e, sul telefono, nel magazzino. Testo in dati/ext37.js.   Uso: node tools/build37.js base.html out.html
const fs = require('fs'), path = require('path'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo, volte = 1) {
  const n = h.split(vecchio).length - 1;
  if (n !== volte) throw new Error('àncora trovata ' + n + ' volte (attese ' + volte + '): ' + vecchio.slice(0, 90));
  h = h.split(vecchio).join(nuovo);
}
if (!h.includes('function caricaFileStato(')) {
  const ext = fs.readFileSync(path.join(__dirname, 'dati', 'ext37.js'), 'utf8');
  const fine = h.indexOf('</script>', h.indexOf('<script>')), ult = h.lastIndexOf('\nrender();\n', fine);
  if (ult < 0 || fine - ult > 200) throw new Error('manca il render() finale');
  h = h.slice(0, ult) + '\n' + ext + h.slice(ult);
  sost("function viewStato(sl, only) {\n  const s = Object.values(STATI).find(v => v.slug === sl);\n  if (!s) return viewStati();\n",
       "function viewStato(sl, only) {\n  const s = Object.values(STATI).find(v => v.slug === sl);\n  if (!s) return viewStati();\n  caricaFileStato(s.nome);\n");
  sost("function viewPiano(slug) {\n  const nome = slug ? Object.keys(STATI).find(n => STATI[n].slug === slug) : '';\n",
       "function viewPiano(slug) {\n  const nome = slug ? Object.keys(STATI).find(n => STATI[n].slug === slug) : '';\n  if (nome) caricaFileStato(nome);\n");
  sost("  if (q) html = viewSearch(q);", "  if (q) html = viewSearch(q) + cercaFattiHtml(q) + cercaTelHtml(q);");
  sost("'<details class=\"crit\"><summary>Fatti confermati negli ultimi mesi (' + m.length + ')</summary><ul class=\"plain\">' + m.slice(0, 40)",
       "'<details class=\"crit\"><summary>Fatti confermati negli ultimi mesi (' + memoriaTot(nome) + ')</summary><ul class=\"plain\">' + m.slice(0, 80)");
  sost("La memoria del programma: tiene per 120 giorni i fatti riportati da almeno due fonti",
       "La memoria del programma: tiene per un anno (fino a 300 per Stato) i fatti riportati da almeno due fonti");
  sost("const c = { 'notizie confermate': (M[n] || []).length,", "const c = { 'notizie confermate': memoriaTot(n),");
  // piano.js leggero ha una fonte per riga: quante erano lo dice nf
  sost("((x.f || []).length > 1 ? 'più fonti' : 'una fonte')", "((x.nf || (x.f || []).length) > 1 ? 'più fonti' : 'una fonte')", 3);
}
const s0 = h.indexOf('<script>') + 8, s1 = h.indexOf('</script>', s0);
new vm.Script(h.slice(s0, s1));
fs.writeFileSync(out, h);
console.log('ok', h.length);

// Ventitreesima estensione: il «sapere» non è più solo Wikipedia (World Factbook d'archivio) e mostra la traduzione
// italiana quando il programma l'ha fatta. Uso: node tools/build23.js base.html out.html  (base = pagina con la 22)
const fs = require('fs'), vm = require('vm');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
sost("'</div><div class=\"x\">' + esc(v.testo) + '</div><div class=\"s\">Raccolto dal programma il '", "'</div><div class=\"x\">' + esc(v.testo_it || v.testo) + '</div><div class=\"s\">' + (v.testo_it ? 'Tradotto in automatico dall’inglese. ' : '') + 'Raccolto dal programma il '");
sost('\nfunction render() {', String.raw`
// Ventitreesima estensione: forze armate e sicurezza dal World Factbook d'archivio (lo legge il programma, Stato per Stato)
function factbookHtml(nome) {
  const v = window.SAPERE && window.SAPERE[nome] && window.SAPERE[nome].factbook; if (!v) return '';
  const parti = String(v.testo_it || v.testo).split(/ (?=(?:Forces|Personnel|Spending|Equipment|Service|Deployments|Forze|Personale|Spesa|Equipaggiamento|Servizio|Schieramenti|Dispiegamenti)[^:]{0,25}: )/);
  return '<div class="item"><div class="t">Dal World Factbook: forze armate e sicurezza</div><ul class="plain">' + parti.map(p => '<li>' + esc(p) + '</li>').join('') + '</ul><div class="s">' + (v.testo_it ? 'Tradotto in automatico dall’inglese. ' : 'Testo originale in inglese. ') + 'Copia d’archivio: il Factbook della CIA ha chiuso il 4 febbraio 2026, quindi i dati si fermano lì. È una fonte del governo degli Stati Uniti: utile per orientarsi, da confrontare con le altre. <a href="' + safeU(v.url) + '" target="_blank" rel="noopener">Apri la fonte</a></div></div>';
}
` + '\nfunction render() {');
sost("html += forzeHtml(s.nome) + sapereHtml(s.nome, 'forze');", "html += forzeHtml(s.nome) + sapereHtml(s.nome, 'forze') + factbookHtml(s.nome);");
fs.writeFileSync(out, h);
const t0 = h.indexOf('<script>') + 8; new vm.Script(h.slice(t0, h.indexOf('</script>', t0)));
console.log('ok', out, h.length);

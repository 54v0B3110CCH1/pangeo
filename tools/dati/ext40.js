// Quarantesima estensione (programma 2.31, 20 novembre 2026): avvisi con il loro tipo (truppe, spie, esplosioni, spazio
// aereo, colpi di Stato…) e fonti dirette prima di tutto: i servizi di intelligence portano al loro sito ufficiale; Wikipedia
// resta accanto come fonte di appoggio, di affidabilità media (la scrivono e la correggono i lettori): utile per orientarsi,
// da incrociare per i fatti importanti.
function avvisoHtml(a) {
  const t = Date.parse(a.quando || ''), q = t ? new Date(t).toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  const tipo = a.nome || { picco: 'molte più notizie confermate del solito', fatto: 'fatto grave', cielo: 'cielo', calore: 'calore dal satellite', valuta: 'moneta', tasso: 'titoli di Stato' }[a.tipo] || a.tipo;
  return '<div class="item avv' + (a.livello >= 2 ? ' l2' : '') + '"><div class="t">' + collega(a.testo) + '</div><div class="m">' + esc(q) + ' · ' + esc(tipo) +
    (a.u ? ' · <a href="' + safeU(a.u) + '" target="_blank" rel="noopener">' + esc(a.f || 'fonte') + '</a>' : '') + (STATI[a.stato] ? ' · ' + stLink(a.stato) : '') + '</div></div>';
}
function wikiAppoggio(u, testo) {
  return /^https?:\/\//.test(String(u || '')) ? '<a href="' + safeU(u) + '" target="_blank" rel="noopener">' + esc(testo || 'Wikipedia') + '</a> <span class="s">(fonte di appoggio, affidabilità media)</span>' : '';
}
function intelServizio(x) {
  const v = servizioSintesi(x[4]), w = wikiAppoggio(x[2]);
  const nome = x[3] ? '<a href="' + safeU(x[3]) + '" target="_blank" rel="noopener">' + esc(x[0]) + '</a> <span class="s">sito ufficiale</span>' + (w ? ' · ' + w : '')
    : esc(x[0]) + ' <span class="s">(sito ufficiale non trovato)</span>' + (w ? ' · ' + w : '');
  const sv = v ? wikiAppoggio(v.u || x[2], 'voce di Wikipedia') : '';
  return '<li>' + nome + (x[1] ? ' <span class="s">· dal ' + esc(x[1]) + '</span>' : '') +
    (v ? '<div class="x" style="margin:2px 0 8px">' + esc(v.s) + ' <span class="s">— riassunto dal programma' + (sv ? ' dalla ' + sv : '') + '</span></div>' : '') + '</li>';
}
function sapereHtml(nome, chiave) {
  const v = window.SAPERE && window.SAPERE[nome] && window.SAPERE[nome][chiave]; if (!v) return '';
  const da = /^https?:\/\//.test(String(v.url || '')) ? '<a href="' + safeU(v.url) + '" target="_blank" rel="noopener">Wikipedia</a>' : 'Wikipedia';
  return '<div class="item"><div class="t">Scheda enciclopedica: ' + esc(v.titolo) + '</div><div class="x">' + esc(v.testo_it || v.testo) + '</div><div class="s">Da ' + da +
    (v.lingua === 'en' ? ' in inglese' : '') + (v.testo_it ? ', tradotta in automatico' : '') + ', raccolta il ' + esc(String(window.SAPERE[nome].data || '').split('-').reverse().join('/')) +
    '. Fonte di appoggio, di affidabilità media: la scrivono e la correggono i lettori. Serve per orientarsi; i fatti importanti si incrociano con siti ufficiali, agenzie e giornali.</div></div>';
}

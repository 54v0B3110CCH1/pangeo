// Quarantesima estensione (programma 2.31, 20 novembre 2026): avvisi con il loro tipo (truppe, spie, esplosioni, spazio
// aereo, colpi di Stato…) e fonti dirette: i servizi di intelligence portano al loro sito ufficiale, non a Wikipedia
// (che chiunque può modificare); dove il sito ufficiale non c'è, si dice.
function avvisoHtml(a) {
  const t = Date.parse(a.quando || ''), q = t ? new Date(t).toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  const tipo = a.nome || { picco: 'molte più notizie confermate del solito', fatto: 'fatto grave', cielo: 'cielo', calore: 'calore dal satellite', valuta: 'moneta', tasso: 'titoli di Stato' }[a.tipo] || a.tipo;
  return '<div class="item avv' + (a.livello >= 2 ? ' l2' : '') + '"><div class="t">' + collega(a.testo) + '</div><div class="m">' + esc(q) + ' · ' + esc(tipo) +
    (a.u ? ' · <a href="' + safeU(a.u) + '" target="_blank" rel="noopener">' + esc(a.f || 'fonte') + '</a>' : '') + (STATI[a.stato] ? ' · ' + stLink(a.stato) : '') + '</div></div>';
}
function intelServizio(x) {
  const v = servizioSintesi(x[4]);
  return '<li>' + (x[3] ? '<a href="' + safeU(x[3]) + '" target="_blank" rel="noopener">' + esc(x[0]) + '</a> <span class="s">sito ufficiale</span>' : esc(x[0]) + ' <span class="s">(sito ufficiale non trovato)</span>') +
    (x[1] ? ' <span class="s">· dal ' + esc(x[1]) + '</span>' : '') + (v ? '<div class="x" style="margin:2px 0 8px">' + esc(v.s) + ' <span class="s">(riassunto dal programma da un’enciclopedia: da verificare sul sito ufficiale)</span></div>' : '') + '</li>';
}
function sapereHtml(nome, chiave) {
  const v = window.SAPERE && window.SAPERE[nome] && window.SAPERE[nome][chiave]; if (!v) return '';
  return '<div class="item"><div class="t">Scheda enciclopedica: ' + esc(v.titolo) + '</div><div class="x">' + esc(v.testo_it || v.testo) + '</div><div class="s">Da Wikipedia' +
    (v.lingua === 'en' ? ' in inglese' : '') + (v.testo_it ? ', tradotta in automatico' : '') + ', raccolta il ' + esc(String(window.SAPERE[nome].data || '').split('-').reverse().join('/')) +
    '. Wikipedia la può modificare chiunque: è un riassunto da verificare, non una fonte. Per i fatti valgono i siti ufficiali e le notizie con fonte.</div></div>';
}

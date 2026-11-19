
// Trentaduesima estensione (20 novembre 2026, programma 2.23): i servizi di intelligence riassunti in italiano dal
// programma (servizi.js), la rilevanza da 1 a 5 dei fatti del lavoro a piano, e il quadro del cervello: la scaletta delle
// voci più rilevanti e i collegamenti tra fatti diversi, ognuno con la domanda per verificarlo e la risposta trovata.
function caricaServizi() {
  if (!(APP_OK || location.protocol === 'file:')) return;
  const s = document.createElement('script'); s.src = 'servizi.js?v=' + Date.now();
  s.onload = () => { render(); s.remove(); }; s.onerror = () => s.remove(); document.head.appendChild(s);
}
function servizioSintesi(q) { const v = q && window.SERVIZI && window.SERVIZI[q]; return v && v.s ? v : null; }
function rilBadge(r) { return r ? '<span class="badge" style="--c:var(' + (r >= 4 ? '--accent' : r === 3 ? '--st2' : '--muted') + ')" title="Rilevanza da 1 a 5, secondo il cervello">rilevanza ' + r + '/5</span> ' : ''; }
const QUADRO_TIPO = { notizia: 'notizia confermata', accordo: 'accordo', appalto: 'appalto', intelligence: 'intelligence' };
const QUADRO_NOTA = 'Scaletta e collegamenti li scrive il cervello ogni 3 ore, leggendo solo le notizie confermate da più fonti e i fatti del lavoro a piano. La rilevanza è un suo giudizio, non un dato. Un collegamento «possibile» resta da verificare: per questo ognuno ha la sua domanda, che il programma cerca nei giri dopo.';
function quadroDati() { const Q = liveOk() && window.LIVE.quadro; return Q && ((Q.scaletta || []).length || (Q.collegamenti || []).length) ? Q : null; }
function quadroVoce(v, i) {
  return '<div class="item"><div class="t"><span class="s">' + (i + 1) + '.</span> <a href="' + safeU(v.u) + '" target="_blank" rel="noopener">' + esc(v.t) + '</a></div>' +
    '<div class="m">' + [rilBadge(v.r), esc(QUADRO_TIPO[v.tipo] || v.tipo || ''), (v.paesi || []).map(p => stLink(p)).join(', '), esc(pianoData(v.d)), esc(v.fonte || '') + ((v.nf || 1) > 1 ? ' e altre ' + (v.nf - 1) : '')].filter(Boolean).join(' · ') + '</div>' +
    (v.perche ? '<div class="x">' + esc(v.perche) + '</div>' : '') + '</div>';
}
function collegamentoHtml(c) {
  const r = c.risposta;
  return '<div class="item"><div class="t"><span class="dot" style="background:var(--accent)"></span> ' + esc(c.testo) + '</div>' +
    '<div class="m">' + [esc(c.stati || ''), esc(pianoOra(c.iso))].filter(Boolean).join(' · ') + '</div>' +
    '<ul class="plain">' + (c.voci || []).map(v => '<li><span class="s">' + esc(QUADRO_TIPO[v.tipo] || v.tipo || '') + ':</span> <a href="' + safeU(v.u) + '" target="_blank" rel="noopener">' + esc(v.t) + '</a> <span class="s">' + esc(v.fonte || '') + '</span></li>').join('') + '</ul>' +
    '<div class="s"><b>Domanda</b>: ' + esc(c.perche || c.q) + ' (cerca «' + esc(c.q) + '»' + (c.l ? ', ' + esc(c.l) : '') + ')</div>' +
    '<div class="x">' + (r ? '<b>Risposta</b>: ' + esc(r.r) + (r.f && r.f.length ? ' — ' + pianoFonti(r.f) : '') : '<span class="s">Da cercare nei prossimi giri.</span>') + '</div></div>';
}
function quadroHtml(Q, breve) {
  if (!Q) return '';
  const sc = Q.scaletta || [], co = Q.collegamenti || [];
  let h = '<h3 id="lv-quadro">Le più rilevanti adesso</h3>' + (sc.length ? sc.slice(0, breve ? 5 : 15).map(quadroVoce).join('') : '<p class="note">Ancora nessuna scaletta.</p>');
  if (breve) return h + '<p class="note">Scaletta del cervello, ' + esc(Q.agg || '') + '. <a href="#quadro">Tutta la scaletta e ' + (co.length === 1 ? 'il collegamento' : 'i ' + co.length + ' collegamenti') + ' tra i fatti →</a></p>';
  h += '<h3>Collegamenti tra i fatti</h3>' + (co.length ? co.map(collegamentoHtml).join('') : '<p class="note">Ancora nessuno.</p>');
  return h + '<p class="note">' + esc(QUADRO_NOTA) + (Q.agg ? ' Ultimo quadro: ' + esc(Q.agg) + '.' : '') + '</p>';
}
function quadroHome() { const Q = quadroDati(); return Q ? '<section class="nv" aria-label="Le più rilevanti">' + quadroHtml(Q, true) + '</section>' : ''; }
function viewQuadro() {
  crumbs([['', 'Quadro: rilevanza e collegamenti']]);
  const Q = quadroDati();
  return '<h2>Quadro: rilevanza e collegamenti</h2>' + (Q ? quadroHtml(Q, false) : '<p class="note">Il quadro arriva con la versione 2.23 del programma. Ogni 3 ore il cervello mette in scaletta le notizie e i fatti più rilevanti, cerca i collegamenti tra fatti diversi e per ognuno scrive la domanda da verificare; nei giri dopo il programma la cerca e scrive la risposta con le fonti.</p>');
}

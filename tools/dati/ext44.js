// Quarantaquattresima estensione (programma 2.35, 21 novembre 2026): la scheda di ogni sistema d'arma, come il riquadro
// a lato delle voci di Wikipedia. Foto, che cos'è, chi lo costruisce, date, quanti ne sono stati fatti, specifiche, da
// che cosa deriva, varianti, chi lo usa, concorrenti e link. Dati da Wikidata (CC0) e Wikipedia (appoggio), raccolti
// dal programma sul telefono (sistemi.js). Nella pagina di ogni Stato: i sistemi che usa secondo Wikidata.
const CAR_SIS = {};
function caricaSistemi() { caricaJs('sistemi.js', 'SISTEMI_SCHEDE', CAR_SIS); sisNuovi(); }
// i sistemi che il programma ha aggiunto all'elenco dopo questa pagina: entrano nei collegamenti e nell'elenco
function sisNuovi() {
  const X = window.SISTEMI_SCHEDE; if (!X || X._uniti) return; X._uniti = 1;
  let nuovi = 0;
  (X.elenco || []).forEach(s => { if (!SIS[s[0]] && Array.isArray(s[4])) { SISTEMI.push(s); SIS[s[0]] = { id: s[0], nome: s[1], tipo: s[2], chi: s[3], alias: s[4] }; nuovi++; } });
  if (nuovi) { COLL = null; SIS_IDX = null; }
}
function sisScheda(id) { const X = window.SISTEMI_SCHEDE; return X && X.schede ? X.schede[id] : null; }
function sisAnno(d) { return String(d || '').slice(0, 4); }
function sisData(d) {
  d = String(d || ''); if (!d) return '';
  const m = d.match(/^(-?\d{1,4})(?:-(\d\d))?(?:-(\d\d))?$/); if (!m) return esc(d);
  const mesi = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];
  return (m[3] ? Number(m[3]) + ' ' : '') + (m[2] ? mesi[Number(m[2]) - 1] + ' ' : '') + m[1];
}
function sisWiki(lingua, titolo) { return 'https://' + lingua + '.wikipedia.org/wiki/' + encodeURIComponent(String(titolo).replace(/ /g, '_')); }
function sisFotoUrl(f, w) { return 'https://commons.wikimedia.org/wiki/Special:FilePath/' + encodeURIComponent(f) + '?width=' + (w || 480); }
// un nome (di un concorrente, di una variante) diventa un collegamento se è un sistema dell'elenco
function sisNome(n) {
  const C = collegaIndice(); const v = C.m.get(n) || C.m.get(String(n).split(' (')[0]);
  if (v && v[1] === 'w') return '<a class="cl cl-w" href="#sistemi/' + v[2] + '">' + esc(n) + '</a>';
  const s = SISTEMI.find(x => x[1] === n || x[4].includes(n)); if (s) return '<a class="cl cl-w" href="#sistemi/' + s[0] + '">' + esc(n) + '</a>';
  return esc(n);
}
function sisAnnoServizio(x) { const d = (x && x.date) || {}; return Number(sisAnno(d.servizio || d.volo || d.nasce)) || null; }
// concorrenti calcolati: stesso tipo nell'elenco, entrata in servizio a meno di 12 anni di distanza
function sisStessaEpoca(id) {
  const S = SIS[id], x = sisScheda(id), a = sisAnnoServizio(x); if (!S) return [];
  return SISTEMI.filter(s => s[0] !== id && s[2] === S.tipo).map(s => [s, sisAnnoServizio(sisScheda(s[0]))])
    .filter(([s, b]) => !a || !b || Math.abs(a - b) <= 12).sort((p, q) => Math.abs((p[1] || a || 0) - (a || 0)) - Math.abs((q[1] || a || 0) - (a || 0)))
    .slice(0, 10).map(([s, b]) => '<a class="cl-w" href="#sistemi/' + s[0] + '">' + esc(s[1]) + (b ? ' <span class="s">' + b + '</span>' : '') + '</a>');
}
function sistemaSchedaHtml(id) {
  caricaSistemi();
  const X = window.SISTEMI_SCHEDE;
  if (!X) return CAR_SIS.c === 3 ? '' : '<p class="note">Carico la scheda…</p>';
  const x = sisScheda(id); if (!x) return '<p class="note">La scheda di questo sistema non è ancora pronta: il programma la scrive da Wikidata e Wikipedia, poche a giro.</p>';
  const d = x.date || {};
  const righe = [];
  if (x.d) righe.push(['Che cos’è', esc(x.d)]);
  if ((x.cl || []).length) righe.push(['Classe', esc(x.cl.join(', '))]);
  if ((x.costr || []).length) righe.push(['Costruttore', x.costr.map(n => AZIENDE.find(a => a.nome === n) ? azLink(n) : esc(n)).join(', ')]);
  if ((x.prog || []).length) righe.push(['Progettista', esc(x.prog.join(', '))]);
  if ((x.orig || []).length) righe.push(['Origine', x.orig.map(n => stLink(n)).join(', ')]);
  if (d.nasce) righe.push(['Progetto avviato', sisData(d.nasce)]);
  if (d.volo) righe.push(['Primo volo', sisData(d.volo)]);
  if (d.servizio) righe.push(['In servizio dal', sisData(d.servizio)]);
  if (d.ritiro) righe.push(['Ritirato', sisData(d.ritiro)]);
  if (x.prod) righe.push(['Esemplari prodotti', esc(x.prod)]);
  if ((x.costo || []).length) righe.push(['Costo unitario', esc(x.costo.join(' · '))]);
  (x.spec || []).forEach(s => righe.push([s[0][0].toUpperCase() + s[0].slice(1), esc(s[1])]));
  let h = '<div class="sis-box">';
  if (x.img) h += '<figure class="sis-foto"><a href="https://commons.wikimedia.org/wiki/File:' + encodeURIComponent(x.img.replace(/ /g, '_')) + '" target="_blank" rel="noopener">' +
    '<img loading="lazy" decoding="async" src="' + sisFotoUrl(x.img) + '" alt="' + esc(x.n || '') + '"></a><figcaption>Foto: Wikimedia Commons (tocca per autore e licenza)</figcaption></figure>';
  h += '<dl class="kv">' + righe.map(r => '<dt>' + esc(r[0]) + '</dt><dd>' + r[1] + '</dd>').join('') + '</dl></div>';
  if (x.st) h += '<h3>Storia in breve</h3><div class="item"><div class="x">' + esc(x.st) + '</div><div class="s">Da Wikipedia' + (x.stl === 'en' ? ' in inglese' : '') +
    ': fonte di appoggio, di affidabilità media. <a href="' + sisWiki(x.stl === 'en' ? 'en' : 'it', x.stl === 'en' ? x.we : x.w) + '" target="_blank" rel="noopener">Continua a leggere</a></div></div>';
  const da = [].concat((x.prima || []).map(n => ['viene dopo', n]), (x.base || []).map(n => ['deriva da', n]));
  if (da.length) h += '<h3>Da dove deriva</h3><div class="item">' + da.map(p => '<div>' + esc(p[0]) + ' ' + sisNome(p[1]) + '</div>').join('') + '</div>';
  const poi = [].concat((x.var || []).map(v => [v[0], v[1]]), (x.deriv || []).map(n => [n, '']), (x.dopo || []).map(n => [n, 'successore']));
  if (poi.length) h += '<h3>Evoluzioni e varianti</h3><div class="members">' + poi.map(v => '<span class="sis-v">' + sisNome(v[0]) + (v[1] ? ' <span class="s">' + esc(v[1]) + '</span>' : '') + '</span>').join('') + '</div>';
  const w = x.opw || {}, att = new Set([].concat(Object.keys(x.op || {}).filter(n => n !== '?'), w.attuali || []));
  const op = [...att].filter(n => !(w.passati || []).includes(n) || (w.attuali || []).includes(n)).sort((a, b) => a.localeCompare(b, 'it'));
  if (op.length) h += '<h3>Chi lo usa <span class="s">(' + op.length + ')</span></h3><div class="members">' + op.map(n => '<span class="sis-v">' + stLink(n) +
    (((x.op || {})[n] || []).length ? ' <span class="s">' + esc(x.op[n].slice(0, 2).join(', ')) + '</span>' : '') + '</span>').join('') + '</div>';
  if ((w.futuri || []).length) h += '<div class="item"><div class="m">Ordinato, in consegna o valutato (secondo Wikipedia)</div><div class="members">' + w.futuri.map(n => '<span class="sis-v">' + stLink(n) + '</span>').join('') + '</div></div>';
  if ((w.passati || []).length) h += '<div class="item"><div class="m">Lo usavano (secondo Wikipedia)</div><div class="members">' + w.passati.map(n => '<span class="sis-v">' + stLink(n) + '</span>').join('') + '</div></div>';
  if (op.length || (w.futuri || []).length) h += '<p class="note">Da Wikidata e dalla sezione «Operators» di Wikipedia in inglese: fonti di appoggio, da incrociare con i fatti recenti più sotto.</p>';
  const ep = sisStessaEpoca(id);
  if ((x.sim || []).length || ep.length) {
    h += '<h3>Concorrenti</h3>';
    if ((x.sim || []).length) h += '<div class="item"><div class="m">Simili per ruolo ed epoca, secondo Wikipedia in inglese</div><div class="members">' + x.sim.map(n => '<span class="sis-v">' + sisNome(n) + '</span>').join('') + '</div></div>';
    if (ep.length) h += '<div class="item"><div class="m">Dello stesso tipo nell’archivio, entrati in servizio a meno di 12 anni di distanza</div><div class="members">' + ep.join('') + '</div></div>';
  }
  const link = [];
  if (x.w) link.push('<a href="' + sisWiki('it', x.w) + '" target="_blank" rel="noopener">Wikipedia in italiano</a>');
  if (x.we) link.push('<a href="' + sisWiki('en', x.we) + '" target="_blank" rel="noopener">Wikipedia in inglese</a>');
  if (x.com) link.push('<a href="https://commons.wikimedia.org/wiki/Category:' + encodeURIComponent(x.com.replace(/ /g, '_')) + '" target="_blank" rel="noopener">foto e video su Commons</a>');
  if (x.q) link.push('<a href="https://www.wikidata.org/wiki/' + esc(x.q) + '" target="_blank" rel="noopener">Wikidata</a>');
  if (link.length) h += '<p class="note">Per vederlo e approfondire: ' + link.join(' · ') + '. Scheda aggiornata il ' + esc(String(x.agg || '').split('-').reverse().join('/')) + '.</p>';
  return h + '<h3>Dove compare nei fatti raccolti</h3>';
}
// nella pagina di uno Stato: i sistemi che usa secondo Wikidata, quelli che compaiono nei fatti su questo Stato e quelli
// progettati o costruiti qui
function sistemiStatoHtml(n) {
  caricaSistemi();
  const X = window.SISTEMI_SCHEDE, sk = (X && X.schede) || {};
  const chip = s => '<a class="cl-w" href="#sistemi/' + s[0] + '">' + esc(s[1]) + ' <span class="s">' + esc(s[2]) + '</span></a>';
  const usa = SISTEMI.filter(s => ((sk[s[0]] || {}).op || {})[n] || (((sk[s[0]] || {}).opw || {}).attuali || []).includes(n));
  const I = sistemiIndice().I;
  const nei = SISTEMI.filter(s => (I[s[0]] || []).some(v => v.st === n)).map(s => [s, (I[s[0]] || []).filter(v => v.st === n).length]).sort((a, b) => b[1] - a[1]);
  const qui = SISTEMI.filter(s => ((sk[s[0]] || {}).orig || []).includes(n));
  if (!usa.length && !nei.length && !qui.length) return '';
  let h = '<h3 id="st-sistemi"><span class="dot" style="background:var(--numeri)"></span>Sistemi d’arma</h3>';
  if (usa.length) h += '<div class="item"><div class="m">In uso secondo Wikidata (' + usa.length + ')</div><div class="members">' + usa.map(chip).join('') + '</div></div>';
  if (nei.length) h += '<div class="item"><div class="m">Nei fatti raccolti su questo Stato (acquisti, consegne, accordi, notizie)</div><div class="members">' +
    nei.map(([s, k]) => '<a class="cl-w" href="#sistemi/' + s[0] + '">' + esc(s[1]) + ' <span class="s">' + k + '</span></a>').join('') + '</div></div>';
  if (qui.length) h += '<div class="item"><div class="m">Progettati o costruiti qui</div><div class="members">' + qui.map(chip).join('') + '</div></div>';
  return h + '<p class="note">Comprende solo i ' + SISTEMI.length + ' sistemi che l’archivio segue; Wikidata può essere incompleto. I numeri dei mezzi sono in «Uomini e mezzi».</p>';
}

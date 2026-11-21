// Quarantaseiesima estensione (programma 2.35, 21 novembre 2026): biblioteca e studi. I classici liberi da diritti sul
// potere, la guerra, il denaro e la storia, letti dal programma capitolo per capitolo: per ognuno le «dinamiche» che il
// cervello ne tira fuori, ognuna con una citazione esatta controllata nel testo. Sotto, gli studi recenti dei centri di
// ricerca (titolo, fonte, link). Dati in biblioteca.js.
const CAR_BIB = {};
function caricaBiblioteca() { caricaJs('biblioteca.js', 'BIBLIOTECA', CAR_BIB); }
function bibLibro(id) { const B = window.BIBLIOTECA; return B ? (B.libri || []).find(l => l[0] === id) : null; }
function bibDinamica(z) {
  const l = bibLibro(z[0]) || [z[0], z[0], ''];
  return '<div class="item"><div class="t">' + esc(z[3]) + '</div><div class="x bib-cit">«' + esc(z[4]) + '»</div><div class="m">' +
    '<a href="#biblioteca/libro/' + esc(z[0]) + '">' + esc(l[1]) + '</a> di ' + esc(l[2]) + ' · ' + esc(z[2]) + ' · ' +
    (z[5] || []).map(t => '<a href="#biblioteca/tema/' + encodeURIComponent(t) + '">' + esc(t) + '</a>').join(', ') + '</div></div>';
}
function viewBiblioteca(a, b) {
  caricaBiblioteca();
  const B = window.BIBLIOTECA;
  const tit = a === 'libro' && B ? ((bibLibro(b) || [])[1] || 'Libro') : a === 'tema' ? 'Tema: ' + decodeURIComponent(b || '') : a === 'studi' ? 'Studi' : '';
  crumbs(a ? [['#biblioteca', 'Biblioteca e studi'], ['', tit]] : [['', 'Biblioteca e studi']]);
  let h = '<h2>' + (a ? esc(tit) : 'Biblioteca e studi') + '</h2>';
  if (!B) return h + '<p class="note">' + (CAR_BIB.c === 3 ? 'La biblioteca arriva con il prossimo giro completo del programma (versione 2.35).' : 'Carico…') + '</p>';
  const lez = B.lezioni || [];
  if (a === 'libro') {
    const l = bibLibro(b); if (!l) return h + '<p class="note">Libro non trovato.</p>';
    h += '<p class="note">' + esc(l[2]) + ' · ' + esc(String(l[3])) + ' · ' + esc(l[7]) + (l[5] ? ' · ' + l[6] + ' capitoli studiati su ' + l[5] : '') +
      ' · <a href="' + safeU(l[4]) + '" target="_blank" rel="noopener">il testo completo (pubblico dominio)</a></p>';
    const mie = lez.filter(z => z[0] === b);
    return h + (mie.length ? mie.map(bibDinamica).join('') : '<p class="note">Nessuna dinamica ancora: il programma studia pochi capitoli a giro.</p>');
  }
  if (a === 'tema') {
    const t = decodeURIComponent(b || ''), mie = lez.filter(z => (z[5] || []).includes(t));
    return h + '<p class="note">' + mie.length + ' dinamiche. Chiavi di lettura tratte dai classici, non giudizi sui fatti di oggi.</p>' + mie.slice().reverse().slice(0, 200).map(bibDinamica).join('');
  }
  if (a === 'studi') {
    const fonte = b ? decodeURIComponent(b) : '';
    const l = (B.studi || []).filter(s => !fonte || s[3] === fonte);
    h += '<div class="members">' + (B.fonti_studi || []).map(f => '<a href="#biblioteca/studi/' + encodeURIComponent(f[0]) + '">' + esc(f[0]) + ' <span class="s">' + esc(f[2]) + '</span></a>').join('') + '</div>';
    return h + l.slice(0, 300).map(s => '<div class="item"><div class="t"><a href="' + safeU(s[2]) + '" target="_blank" rel="noopener">' + esc(s[1]) + '</a></div><div class="m">' + esc(s[0].split('-').reverse().join('/')) + ' · ' + esc(s[3]) + ' (' + esc(s[4]) + ')</div></div>').join('') +
      '<p class="note">Solo titolo, data e link: gli studi si leggono alla fonte. Centri di orientamenti diversi, da leggere insieme.</p>';
  }
  h += '<p class="note">Il programma legge i classici liberi da diritti su potere, guerra, denaro e storia e, capitolo per capitolo, ne tira fuori le dinamiche, ognuna con una citazione esatta controllata nel testo. Sono chiavi di lettura (spunti, non giudizi). Sotto, gli studi recenti dei centri di ricerca.</p>';
  const nT = {}; lez.forEach(z => (z[5] || []).forEach(t => { nT[t] = (nT[t] || 0) + 1; }));
  if (lez.length) h += '<h3>Temi</h3><div class="members">' + Object.keys(nT).sort((x, y) => nT[y] - nT[x]).map(t => '<a href="#biblioteca/tema/' + encodeURIComponent(t) + '">' + esc(t) + ' <span class="s">' + nT[t] + '</span></a>').join('') + '</div>';
  h += '<h3>Libri <span class="s">(' + (B.libri || []).length + ')</span></h3>' + (B.libri || []).map(l => '<div class="item"><div class="t"><a href="#biblioteca/libro/' + esc(l[0]) + '">' + esc(l[1]) + '</a></div><div class="m">' +
    esc(l[2]) + ' · ' + esc(String(l[3])) + ' · ' + esc(l[7]) + (l[5] ? ' (' + l[6] + ' capitoli studiati su ' + l[5] + ')' : '') + '</div></div>').join('');
  if (lez.length) h += '<h3>Ultime dinamiche</h3>' + lez.slice(-12).reverse().map(bibDinamica).join('');
  const st = B.studi || [];
  h += '<h3>Studi recenti <span class="s">(' + st.length + ')</span></h3>' + st.slice(0, 15).map(s => '<div class="item"><div class="t"><a href="' + safeU(s[2]) + '" target="_blank" rel="noopener">' + esc(s[1]) + '</a></div><div class="m">' + esc(s[0].split('-').reverse().join('/')) + ' · ' + esc(s[3]) + '</div></div>').join('') +
    '<p class="note"><a href="#biblioteca/studi">Tutti gli studi, per centro di ricerca</a>. I video non si trascrivono: restano titolo e link nella sezione Live.</p>';
  return h;
}
// documenti desecretati (FRUS) e trapelati (WikiLeaks) di ogni Stato, con le ricerche negli archivi (dalla 2.37)
function archiviStatoHtml(n) {
  caricaBiblioteca();
  const B = window.BIBLIOTECA, A = B && B.archivi ? B.archivi[n] : null;
  const en = encodeURIComponent((A && A.en) || n);
  const cerca = [['CIA Reading Room (CREST)', 'https://www.cia.gov/readingroom/search/site/' + en], ['National Security Archive', 'https://nsarchive.gwu.edu/search?search_api_fulltext=' + en],
    ['FRUS, Dipartimento di Stato', 'https://history.state.gov/search?q=' + en + '&within=documents'], ['Wilson Center Digital Archive', 'https://digitalarchive.wilsoncenter.org/search?q=' + en],
    ['Archivi nazionali USA (NARA)', 'https://catalog.archives.gov/search?q=' + en], ['Archivi nazionali britannici', 'https://discovery.nationalarchives.gov.uk/results/r?_q=' + en],
    ['WikiLeaks', 'https://search.wikileaks.org/?q=' + en]];
  let h = '<h3 id="st-archivi"><span class="dot" style="background:var(--muted)"></span>Documenti desecretati e trapelati</h3>';
  const riga = r => '<div class="item"><div class="t"><a href="' + safeU(r[2]) + '" target="_blank" rel="noopener">' + esc(r[1]) + '</a></div><div class="m">' + esc(r[0] || '') + ' · ' + esc(r[3] || '') + '</div></div>';
  if (A && (A.frus || []).length) h += '<div class="m">Desecretati: documenti diplomatici degli Stati Uniti (FRUS), letti il ' + esc(String(A.d).split('-').reverse().join('/')) + '</div>' + A.frus.map(riga).join('');
  if (A && (A.wl || []).length) h += '<div class="m">Trapelati (WikiLeaks): cablogrammi e documenti di Stato. Non verificati e senza la replica di chi è citato: da leggere con cautela, alla fonte.</div>' + A.wl.map(riga).join('');
  return h + '<p class="note">Cerca negli archivi: ' + cerca.map(c => '<a href="' + c[1] + '" target="_blank" rel="noopener">' + esc(c[0]) + '</a>').join(' · ') + '. Il programma legge pochi Stati a giro; gli altri archivi si consultano dai link.</p>';
}

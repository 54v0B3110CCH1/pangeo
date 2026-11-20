// Trentasettesima estensione (20 novembre 2026, programma 2.26): i file per Stato (memoria e lavoro a piano pieni, scaricati
// solo quando si apre uno Stato), la ricerca nei fatti raccolti dal programma e, sul telefono, in tutto il magazzino.

// 1. file per Stato: piano.js e memoria.js sono leggeri; la scheda piena arriva quando apri lo Stato
const FILE_STATO = {};
function caricaFileStato(nome) {
  if (!nome || typeof fetch !== 'function' || !(APP_OK || location.protocol === 'file:')) return;
  // i nomi dei file arrivano con piano.js e memoria.js: finché non ci sono si riprova al ridisegno dopo
  const fp = ((window.PIANO || {}).file || {})[nome], fm = (window.MEMORIA_FILE || {})[nome];
  if (fp && !FILE_STATO[nome + '|p']) { FILE_STATO[nome + '|p'] = 1; fetch('piano/' + fp + '.json?v=' + verDati()).then(r => r.ok ? r.json() : null).then(d => {
    if (d && d.stato && window.PIANO && window.PIANO.stati) { const c = Object.assign({}, d); delete c.stato; window.PIANO.stati[d.stato] = c; SIS_IDX = null; ridisegna(); }
  }).catch(() => {}); }
  if (fm && !FILE_STATO[nome + '|m']) { FILE_STATO[nome + '|m'] = 1; fetch('memoria/' + fm + '.json?v=' + verDati()).then(r => r.ok ? r.json() : null).then(d => {
    if (d && d.stato && Array.isArray(d.fatti) && window.MEMORIA) { window.MEMORIA[d.stato] = d.fatti; ridisegna(); }
  }).catch(() => {}); }
}
function memoriaTot(nome) { return ((window.MEMORIA_N || {})[nome]) || ((window.MEMORIA || {})[nome] || []).length; }

// 2. ricerca nei fatti del programma (lavoro a piano e fatti confermati): funziona anche sul sito pubblico
function cercaFattiHtml(q) {
  const k = norm(q).split(/\s+/).filter(w => w.length > 1); if (!k.length) return '';
  const va = t => { const n = norm(t || ''); return k.every(w => n.includes(w)); };
  const fuori = [];
  Object.entries((window.PIANO || {}).stati || {}).forEach(([st, s]) => {
    (s.accordi || []).forEach(x => { if (va([x.cosa, x.con].join(' '))) fuori.push([x.d, st, 'accordo', x.cosa, x.f]); });
    (s.appalti || []).forEach(x => { if (va([x.ogg, x.acq, x.forn].join(' '))) fuori.push([x.d, st, 'appalto', x.ogg, x.f]); });
    (s.intel || []).forEach(x => { if (va([x.cosa, x.ente].join(' '))) fuori.push([x.d, st, 'intelligence', x.cosa, x.f]); });
    (s.puzzle || []).forEach(x => { if (va(x.cosa)) fuori.push([x.d, st, PUZZLE_NOME[x.tema] || 'risorse', x.cosa, x.f]); });
  });
  Object.entries(window.MEMORIA || {}).forEach(([st, l]) => (l || []).forEach(x => { if (va(x[1])) fuori.push([x[0], st, 'confermato', x[1], [[x[2], x[4]]]]); }));
  if (!fuori.length) return '';
  fuori.sort((a, b) => String(b[0] || '').localeCompare(String(a[0] || '')));
  return '<h3>Nei fatti raccolti dal programma (' + fuori.length + ')</h3>' + fuori.slice(0, 40).map(r => '<div class="item"><div class="t">' + collega(r[3]) + '</div><div class="m">' + [esc(pianoData(r[0])), stLink(r[1]), esc(r[2])].join(' · ') + '</div><div class="s">' + (r[4] || []).slice(0, 2).map(f => f && f[1] ? '<a href="' + safeU(f[1]) + '" target="_blank" rel="noopener">' + esc(f[0] || 'fonte') + '</a>' : '').filter(Boolean).join(' · ') + '</div></div>').join('') + (fuori.length > 40 ? '<p class="note">Qui i 40 più recenti.</p>' : '');
}

// 3. sul telefono: la ricerca in tutto il magazzino (anche i mesi passati), fatta dal programma con la potenza del telefono
const SUL_TELEFONO = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
const CERCA_TEL = {}; let cercaTelT = null;
function cercaTelHtml(q) {
  if (!SUL_TELEFONO || typeof fetch !== 'function') return '';
  q = String(q || '').trim(); if (q.length < 3) return '';
  const R = CERCA_TEL[q];
  if (!R) {
    clearTimeout(cercaTelT);
    cercaTelT = setTimeout(() => {
      CERCA_TEL[q] = { attesa: true };
      fetch('/api/cerca?q=' + encodeURIComponent(q) + '&giorni=120&max=60').then(r => r.json()).then(d => { CERCA_TEL[q] = { l: Array.isArray(d) ? d : [] }; if ($('#q').value.trim() === q) ridisegna(); }).catch(() => { CERCA_TEL[q] = { l: [] }; });
    }, 700);
    return '<h3>Nell’archivio del telefono</h3><p class="note">Cerco in tutto ciò che il telefono conserva, anche i mesi passati…</p>';
  }
  if (R.attesa) return '<h3>Nell’archivio del telefono</h3><p class="note">Sto cercando…</p>';
  if (!R.l.length) return '<h3>Nell’archivio del telefono</h3><p class="note">Nessun risultato negli ultimi 120 giorni.</p>';
  return '<h3>Nell’archivio del telefono (' + R.l.length + ')</h3>' + R.l.map(r => '<div class="item"><div class="t">' + (r.u ? '<a href="' + safeU(r.u) + '" target="_blank" rel="noopener">' + esc(r.t) + '</a>' : esc(r.t)) + '</div><div class="m">' + [esc(pianoData(r.d)), (r.p || []).slice(0, 3).map(n => stLink(n)).join(', '), esc(r.dove || ''), r.c ? 'confermata' : '', esc(r.f || '')].filter(Boolean).join(' · ') + '</div></div>').join('') + '<p class="note">Dal magazzino del telefono: notizie, fatti confermati e lavoro a piano. Sul telefono il comando  python castello.py cerca parole  cerca in tutti gli anni.</p>';
}

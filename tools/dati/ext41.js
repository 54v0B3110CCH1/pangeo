// Quarantunesima estensione (programma 2.33, 20 novembre 2026): la storia di ogni Stato. Cronologia scritta dal programma
// solo dalle fonti (ogni tappa con la sua), conflitti armati dal 1946 (UCDP, Università di Uppsala), colpi di Stato dal
// 1950 (Powell e Thyne), violenza contro i civili e scontri tra gruppi armati; negli avvisi i precedenti dello stesso Stato.
const CAR_STO = {};
function caricaStoria() { caricaJs('storia.js', 'STORIA', CAR_STO); }
const STO_LETTERE = { F: 'World Factbook', W: 'Wikipedia (appoggio)', U: 'UCDP', G: 'Powell e Thyne', R: 'fatti confermati' };
function stoAnni(a, b) { return a === b ? String(a) : a + '–' + b; }
function stoMorti(n) { return n ? Number(n).toLocaleString('it-IT') + ' morti (stima)' : ''; }
function storiaHtml(n) {
  caricaStoria();
  const S = window.STORIA;
  if (!S) return '<h3>La storia studiata dal programma</h3>' + attesaHtml(CAR_STO, 'La storia');
  const s = (S.stati || {})[n], F = S.fonti || {};
  if (!s) return '<h3>La storia studiata dal programma</h3><p class="note">Per ' + esc(n) + ' gli archivi non registrano conflitti armati dal 1946 né colpi di Stato dal 1950.</p>';
  const fl = k => { const u = (k === 'F' || k === 'W') ? (s.tf || {})[k] : (F[k] || [])[1]; const t = STO_LETTERE[k] || k; return u ? '<a href="' + safeU(u) + '" target="_blank" rel="noopener">' + esc(t) + '</a>' : esc(t); };
  let h = '<h3>La storia studiata dal programma</h3>';
  if (s.t && s.t.length) {
    h += '<div class="item"><ul class="plain">' + s.t.map(t => '<li><b>' + esc(t[0]) + '</b> · ' + esc(t[1]) + ' <span class="s">(' + fl(t[2]) + ')</span></li>').join('') + '</ul>' +
      '<div class="s">Cronologia scritta il ' + esc(pianoData(s.tq)) + ' dal cervello del programma solo con le fonti indicate; il programma ha tenuto soltanto le tappe il cui anno compare davvero nella fonte citata. Wikipedia è un’enciclopedia di appoggio, di affidabilità media.</div></div>';
  } else h += '<p class="note">Cronologia: il programma la scrive pochi Stati alla volta, prima quelli con avvisi recenti.</p>';
  const r = s.r || [];
  h += '<div class="item"><div class="t">In numeri</div><div class="x">' + [r[0] ? r[0] + (r[0] === 1 ? ' conflitto armato' : ' conflitti armati') + ' dal 1946' + (r[4] ? ', l’ultimo attivo nel ' + r[4] : '') : 'nessun conflitto armato dal 1946',
    r[1] ? r[1] + ' anni con più di mille morti in battaglia' : '', (r[2] || r[3]) ? (r[2] || 0) + ' colpi di Stato riusciti e ' + (r[3] || 0) + ' falliti dal 1950' : 'nessun colpo di Stato dal 1950'].filter(Boolean).map(esc).join(' · ') + '</div></div>';
  if (s.c && s.c.length) h += '<h3>Conflitti armati dal 1946</h3><div class="item"><ul class="plain">' + s.c.map(c => '<li><b>' + esc(stoAnni(c[0], c[1])) + '</b> · ' + esc(c[3]) + ' contro ' + esc(c[4]) + (c[5] ? ' (' + esc(c[5]) + ')' : '') +
    ' <span class="s">· ' + esc(c[2]) + (c[6] ? ', per ' + esc({ governo: 'il governo', territorio: 'un territorio' }[c[6]] || 'territorio e governo') : '') + (c[7] ? ' · ' + c[7] + (c[7] === 1 ? ' anno' : ' anni') + ' di guerra' : '') +
    (c[9] ? ' · con l’appoggio di ' + esc(c[9]) : '') + '</span></li>').join('') + '</ul><div class="s">Fonte: ' + fl('U') + '. Conflitto armato: almeno 25 morti in battaglia in un anno; anno di guerra: più di mille. I nomi storici (Unione Sovietica, Jugoslavia, Zaire…) sono contati con lo Stato di oggi.</div></div>';
  if (s.g && s.g.length) h += '<h3>Colpi di Stato dal 1950</h3><div class="item"><ul class="plain">' + s.g.map(g => '<li><b>' + esc(pianoData(g[0])) + '</b> · ' + (g[1] ? 'riuscito' : 'fallito') + '</li>').join('') + '</ul><div class="s">Fonte: ' + fl('G') + ', elenco accademico aggiornato più volte l’anno.</div></div>';
  if (s.v && s.v.length) h += '<h3>Violenza contro i civili</h3><div class="item"><ul class="plain">' + s.v.map(v => '<li>' + esc(v[0]) + ' <span class="s">· ' + esc(stoAnni(v[1], v[2])) + ' · ' + esc(stoMorti(v[3])) + (v[4] === '1' ? ' · governo' : '') + '</span></li>').join('') + '</ul><div class="s">Fonte: ' + fl('U') + ' (violenza unilaterale). Sono stime: il numero vero può essere più alto o più basso.</div></div>';
  if (s.n && s.n.length) h += '<h3>Scontri tra gruppi armati</h3><div class="item"><ul class="plain">' + s.n.map(v => '<li>' + esc(v[0]) + ' <span class="s">· ' + esc(stoAnni(v[1], v[2])) + ' · ' + esc(stoMorti(v[3])) + '</span></li>').join('') + '</ul><div class="s">Fonte: ' + fl('U') + ' (conflitti senza governi). Stime.</div></div>';
  return h;
}
function viewStoria() {
  crumbs([['#storia', 'Storia']]);
  caricaStoria();
  const S = window.STORIA;
  let h = '<h2>Storia</h2><p class="note">Il programma studia il passato di ogni Stato e lo collega al presente: conflitti armati dal 1946 (UCDP, Università di Uppsala), colpi di Stato dal 1950 (Powell e Thyne), una cronologia per Stato scritta solo da fonti controllate, e negli avvisi i precedenti dello stesso Stato. Ogni Stato ha la sua storia nella sua scheda, alla voce Storia.</p>';
  if (!S) return h + attesaHtml(CAR_STO, 'La storia');
  const E = Object.entries(S.stati || {});
  const guerra = E.filter(([n, s]) => (s.r || [])[1]).sort((a, b) => b[1].r[1] - a[1].r[1]).slice(0, 20);
  const golpe = E.filter(([n, s]) => (s.r || [])[2] || (s.r || [])[3]).sort((a, b) => (b[1].r[2] + b[1].r[3]) - (a[1].r[2] + a[1].r[3])).slice(0, 20);
  const recenti = [];
  E.forEach(([n, s]) => (s.g || []).forEach(g => { if (g[0] >= String(new Date().getFullYear() - 6)) recenti.push([g[0], n, g[1]]); }));
  recenti.sort((a, b) => a[0] < b[0] ? 1 : -1);
  const conCron = E.filter(([n, s]) => s.t && s.t.length).length;
  h += '<div class="item"><div class="x">Archivi aggiornati al ' + esc(pianoData(S.agg)) + ' · ' + E.length + ' Stati con conflitti o colpi di Stato registrati · cronologie scritte: ' + conCron + ' su 198</div></div>';
  if (recenti.length) h += '<h3>Colpi di Stato degli ultimi anni</h3><div class="item"><ul class="plain">' + recenti.map(r => '<li><b>' + esc(pianoData(r[0])) + '</b> · <a href="#stati/' + (STATI[r[1]] ? STATI[r[1]].slug : '') + '/storia">' + esc(r[1]) + '</a> · ' + (r[2] ? 'riuscito' : 'fallito') + '</li>').join('') + '</ul></div>';
  const tab = (titolo, righe, col, fmt) => '<h3>' + esc(titolo) + '</h3><div class="item tab-wrap"><table class="fatti"><thead><tr><th>Stato</th><th>' + esc(col) + '</th></tr></thead><tbody>' +
    righe.map(([n, s]) => '<tr><td><a href="#stati/' + (STATI[n] ? STATI[n].slug : '') + '/storia">' + esc(n) + '</a></td><td>' + fmt(s) + '</td></tr>').join('') + '</tbody></table></div>';
  if (guerra.length) h += tab('Più anni di guerra dal 1946', guerra, 'Anni con più di mille morti', s => s.r[1] + ' <span class="s">(' + s.r[0] + ' conflitti, l’ultimo attivo nel ' + s.r[4] + ')</span>');
  if (golpe.length) h += tab('Più colpi di Stato dal 1950', golpe, 'Riusciti e falliti', s => s.r[2] + ' riusciti, ' + s.r[3] + ' falliti');
  const F = S.fonti || {};
  return h + '<p class="note">Fonti: ' + Object.keys(F).map(k => (F[k][1] ? '<a href="' + safeU(F[k][1]) + '" target="_blank" rel="noopener">' + esc(F[k][0]) + '</a>' : esc(F[k][0]))).join(' · ') + '.</p>';
}
function avvisoHtml(a) {
  const t = Date.parse(a.quando || ''), q = t ? new Date(t).toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  const tipo = a.nome || { picco: 'molte più notizie confermate del solito', fatto: 'fatto grave', cielo: 'cielo', calore: 'calore dal satellite', valuta: 'moneta', tasso: 'titoli di Stato' }[a.tipo] || a.tipo;
  return '<div class="item avv' + (a.livello >= 2 ? ' l2' : '') + '"><div class="t">' + collega(a.testo) + '</div><div class="m">' + esc(q) + ' · ' + esc(tipo) +
    (a.u ? ' · <a href="' + safeU(a.u) + '" target="_blank" rel="noopener">' + esc(a.f || 'fonte') + '</a>' : '') + (STATI[a.stato] ? ' · ' + stLink(a.stato) : '') + '</div>' +
    (a.prec ? '<div class="s">' + esc(a.prec) + (STATI[a.stato] ? ' <a href="#stati/' + STATI[a.stato].slug + '/storia">Storia →</a>' : '') + '</div>' : '') + '</div>';
}

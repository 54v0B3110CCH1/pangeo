
// Ventinovesima estensione (19 novembre 2026): lavoro a piano del programma (alleanze, patti, appalti: uno Stato alla
// volta, con le fonti), le domande che il programma si fa, e le fermate scritte dalla scatola nera.
const PIANO_COL = { 'firmato': '--st1', 'ratificato': '--st1', 'in vigore': '--st1', 'in consegna': '--st1', 'consegnato': '--st1', 'approvato': '--accent', 'in trattativa': '--st2', 'annunciato': '--st2', 'sospeso': '--st3', 'disdetto': '--st4', 'annullato': '--st4' };
const PIANO_TIPO = { accordi: 'accordi e patti', appalti: 'appalti e contratti', aperta: 'domanda rimasta aperta' };
const DOM_TIPO = { programma: ['Domande di base', 'su uno Stato poco coperto'], seguito: ['Domande di seguito', 'nate da un fatto confermato da più fonti, per saperne di più'], verifica: ['Verifiche', 'cercano se una fonte affidabile conferma una notizia di una fonte debole'], cervello: ['Proposte dal cervello', 'scritte dal cervello nel rapporto del giorno'] };
function pianoDati() { return (typeof window !== 'undefined' && window.PIANO && window.PIANO.stati) ? window.PIANO : null; }
function pianoRias() { return (liveOk() && window.LIVE.piano) || null; }
function pianoDi(nome, tipo) { const P = pianoDati(), s = P && P.stati[nome]; return (s && s[tipo]) || []; }
function pianoData(d) { const m = String(d || '').match(/^(\d{4})-(\d\d)-(\d\d)/); return m ? +m[3] + ' ' + ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'][+m[2] - 1] + ' ' + m[1] : ''; }
function pianoOra(iso) { const t = Date.parse(iso || ''); return t ? new Date(t).toLocaleString('it-IT', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }) : ''; }
function pianoFonti(f) { return (f || []).map(x => '<a href="' + safeU(x[1]) + '" target="_blank" rel="noopener" title="' + esc(x[3] || '') + '">' + esc(x[0] || 'fonte') + '</a>').join(' · '); }
function pianoStato(st) { return st ? '<span class="badge" style="--c:var(' + (PIANO_COL[st] || '--muted') + ')">' + esc(st) + '</span> ' : ''; }
function pianoPiede(x) { return '<div class="s">' + pianoStato(x.st) + ((x.f || []).length > 1 ? 'più fonti' : 'una fonte') + ': ' + pianoFonti(x.f) + '</div>'; }
function pianoAccordo(x) { return '<div class="item"><div class="t"><span class="dot" style="background:var(--b-nato)"></span> ' + esc(x.cosa) + '</div><div class="m">' + [esc(pianoData(x.d)), x.con ? 'con ' + esc(x.con) : ''].filter(Boolean).join(' · ') + '</div>' + pianoPiede(x) + '</div>'; }
function pianoAppalto(x) { return '<div class="item"><div class="t"><span class="dot" style="background:var(--aziende)"></span> ' + esc(x.ogg) + '</div><div class="m">' + [esc(pianoData(x.d)), x.acq ? 'compra ' + stLink(x.acq) : '', x.forn ? 'fornisce ' + esc(x.forn) : '', x.val ? esc(x.val) : ''].filter(Boolean).join(' · ') + '</div>' + pianoPiede(x) + '</div>'; }
const PIANO_NOTA = 'Sono titoli di giornale letti dal programma, non un registro ufficiale: «firmato» o «in consegna» lo dice il titolo. Prima di usarli vanno confermati alla fonte.';
function pianoStatoHtml(nome, tipo) {
  const l = pianoDi(nome, tipo); if (!l.length) return '';
  const s = pianoDati().stati[nome];
  return '<h4 style="margin:16px 0 4px">Trovati dal programma (lavoro a piano)</h4>' + l.map(tipo === 'appalti' ? pianoAppalto : pianoAccordo).join('') + '<p class="note">Ultimo passaggio su ' + esc(nome) + ': ' + esc(pianoOra(s.quando)) + ', ' + (s.titoli || 0) + ' titoli letti. ' + PIANO_NOTA + ' <a href="#piano/' + (STATI[nome] ? STATI[nome].slug : '') + '">Domande e risposte su ' + esc(nome) + ' →</a></p>';
}
function pianoDomandeLista(l) { return '<ul class="plain">' + l.map(d => '<li>' + (d.stato ? '<b>' + esc(d.stato) + '</b> · ' : '') + esc(PIANO_TIPO[d.tipo] || d.tipo) + ', in ' + esc(LINGUE_NOME[d.l] || (d.l === 'it' ? 'italiano' : d.l === 'en' ? 'inglese' : d.l)) + ' <span class="s">→ ' + d.n + (d.n === 1 ? ' titolo' : ' titoli') + '</span><br><span class="dq">' + esc(d.q) + '</span></li>').join('') + '</ul>'; }
function pianoAperteLista(l) { return '<ul class="plain">' + l.map(d => '<li>' + (d.stato ? '<b>' + esc(d.stato) + '</b> · ' : '') + esc(d.perche || '') + ' <span class="s">' + (d.fatta ? '(già cercata)' : '(da cercare al prossimo giro)') + '</span><br><span class="dq">' + esc(d.q) + '</span></li>').join('') + '</ul>'; }
function pianoRisposteLista(l) { return '<ul class="plain">' + l.map(r => '<li>' + (r.stato ? '<b>' + esc(r.stato) + '</b> · ' : '') + esc(r.perche || r.q || '') + '<br>→ ' + esc(r.r || '') + ((r.f || []).length ? ' <span class="s">(' + pianoFonti(r.f) + ')</span>' : '') + '</li>').join('') + '</ul>'; }
function pianoScheda(nome) {
  const P = pianoDati(), s = P && P.stati[nome];
  if (!s) return '<div class="item"><div class="x">Il programma non è ancora passato da ' + esc(nome) + ' in questo lavoro. ' + (P ? 'È arrivato a ' + P.i + ' Stati su ' + P.totale + '.' : '') + '</div></div>';
  let h = '<p class="note">' + esc(s.blocco || '') + ' · ultimo passaggio ' + esc(pianoOra(s.quando)) + ' (passata ' + (s.passata || 1) + ') · ' + (s.titoli || 0) + ' titoli letti' + (s.cervello ? '' : ' · il cervello non li ha ancora letti') + '. ' + stLink(nome) + '</p>';
  h += '<h3>Accordi e patti (' + (s.accordi || []).length + ')</h3>' + ((s.accordi || []).map(pianoAccordo).join('') || '<p class="note">Nessuno nei titoli letti.</p>');
  h += '<h3>Appalti e contratti (' + (s.appalti || []).length + ')</h3>' + ((s.appalti || []).map(pianoAppalto).join('') || '<p class="note">Nessuno nei titoli letti.</p>');
  if ((s.da_leggere || []).length) h += '<h3>Titoli da leggere</h3><div class="item"><ul class="plain">' + s.da_leggere.map(t => '<li><a href="' + safeU(t[1]) + '" target="_blank" rel="noopener">' + esc(t[0]) + '</a> <span class="s">' + esc(t[2]) + ' · ' + esc(pianoData(t[3])) + '</span></li>').join('') + '</ul></div>';
  h += '<h3>Le domande fatte</h3><div class="item">' + pianoDomandeLista((s.domande || []).map(d => ({ tipo: d[0], l: d[1], q: d[2], n: d[3] }))) + '</div>';
  if ((s.aperte || []).length) h += '<h3>Che cosa resta da chiarire</h3><div class="item">' + pianoAperteLista(s.aperte) + '</div>';
  if ((s.risposte || []).length) h += '<h3>Risposte trovate</h3><div class="item">' + pianoRisposteLista(s.risposte.slice().reverse()) + '</div>';
  return h + '<p class="note">' + PIANO_NOTA + '</p>';
}
function viewPiano(slug) {
  const nome = slug ? Object.keys(STATI).find(n => STATI[n].slug === slug) : '';
  crumbs([['#live', 'Live dal mondo']].concat(nome ? [['#piano', 'Lavoro a piano'], ['', nome]] : [['', 'Lavoro a piano']]));
  if (nome) return '<h2>Lavoro a piano: ' + esc(nome) + '</h2>' + pianoScheda(nome);
  const P = pianoDati(), R = pianoRias();
  let h = '<h2>Lavoro a piano: alleanze, patti e appalti</h2><p class="note">Il programma passa uno Stato alla volta, blocco per blocco a partire dall’Europa. Per ogni Stato fa tre domande alla stampa degli ultimi quattro mesi (una nella lingua del posto), legge i titoli e ne tira fuori accordi e appalti, ognuno con la sua fonte e il suo stato. Poi scrive che cosa resta da chiarire e lo cerca nei giri dopo. Finiti tutti gli Stati ricomincia e aggiorna.</p>';
  if (!P && !R) return h + '<div class="item"><div class="x">Il lavoro a piano parte con la versione 2.20 del programma: i risultati compaiono qui, dal telefono o dal sito su GitHub, dopo il primo giro.</div></div>';
  const X = P || R, S = P ? P.stati : {};
  const nAcc = P ? Object.keys(S).reduce((t, k) => t + (S[k].accordi || []).length, 0) : R.accordi, nApp = P ? Object.keys(S).reduce((t, k) => t + (S[k].appalti || []).length, 0) : R.appalti;
  h += '<div class="item nv-diario"><div class="nv-tiles">' + nvTile(X.i + ' su ' + X.totale, 'Stati lavorati nella passata ' + X.passata) + nvTile(num(nAcc), 'accordi e patti trovati') + nvTile(num(nApp), 'appalti e contratti trovati') + nvTile(esc(String(X.agg || '').slice(0, 5) + ' ' + String(X.agg || '').slice(11)), 'ultimo passo') + '</div>';
  h += '<div class="nv-riga"><span>Avanzamento</span><div class="nv-barre"><div>passata ' + X.passata + '</div><div><div class="nv-bar" style="width:' + Math.max(1, Math.round(100 * X.i / Math.max(1, X.totale))) + '%"></div></div><div class="n">' + Math.round(100 * X.i / Math.max(1, X.totale)) + '%</div></div></div></div>';
  if (P) {
    (P.blocchi || []).forEach(b => {
      const fatti = b[1].filter(s => S[s]);
      h += '<h3>' + esc(b[0]) + ' · ' + fatti.length + ' su ' + b[1].length + '</h3><div class="members">' + b[1].map(s => S[s] ? '<a href="#piano/' + (STATI[s] ? STATI[s].slug : '') + '" title="' + (S[s].accordi || []).length + ' accordi, ' + (S[s].appalti || []).length + ' appalti">' + esc(s) + ' <span class="s">' + ((S[s].accordi || []).length + (S[s].appalti || []).length) + '</span></a>' : '<span style="opacity:.55">' + esc(s) + '</span>').join('') + '</div>';
    });
    const ult = (P.ultimi || []).slice().reverse().filter(s => S[s]).slice(0, 6);
    if (ult.length) h += '<h3>Gli ultimi Stati lavorati</h3>' + ult.map(s => '<div class="item"><div class="t">' + esc(s) + ' <span class="s">' + esc(pianoOra(S[s].quando)) + '</span></div><div class="x">' + (S[s].accordi || []).length + ' accordi e patti, ' + (S[s].appalti || []).length + ' appalti e contratti, da ' + (S[s].titoli || 0) + ' titoli letti.</div><div class="s"><a href="#piano/' + (STATI[s] ? STATI[s].slug : '') + '">Apri la scheda con domande e fonti →</a></div></div>').join('');
  } else {
    h += '<div class="item"><div class="x">Ora nel blocco «' + esc(R.blocco) + '». Prossimi: ' + esc((R.prossimi || []).join(', ')) + '.</div><div class="s">Su claude.ai questa è un’istantanea: l’elenco completo, Stato per Stato, è sul telefono e sul sito.</div></div>';
    if ((R.ultimi || []).length) h += '<h3>Gli ultimi Stati lavorati</h3><div class="item"><ul class="plain">' + R.ultimi.map(u => '<li><b>' + esc(u[0]) + '</b>: ' + u[2] + ' accordi e patti, ' + u[3] + ' appalti e contratti, da ' + u[4] + ' titoli <span class="s">' + esc(pianoOra(u[1])) + '</span></li>').join('') + '</ul></div>';
  }
  return h + domandePianoHtml(R) + '<p class="note">' + PIANO_NOTA + '</p>';
}
function domandePianoHtml(R) {
  if (!R) return '';
  let o = '';
  if ((R.domande || []).length) o += '<h3>Le domande del piano, come le scrive</h3><div class="item">' + pianoDomandeLista(R.domande.slice(0, 9).map(d => ({ stato: d[0], tipo: d[1], l: d[2], q: d[3], n: d[4] }))) + '</div>';
  if ((R.aperte || []).length) o += '<h3>Che cosa resta da chiarire</h3><div class="item">' + pianoAperteLista(R.aperte.map(d => ({ stato: d[0], l: d[1], q: d[2], perche: d[3], fatta: d[4] }))) + '</div>';
  if ((R.risposte || []).length) o += '<h3>Risposte trovate</h3><div class="item">' + pianoRisposteLista(R.risposte.map(r => ({ stato: r[0], perche: r[1], r: r[2], f: r[3] }))) + '</div>';
  return o;
}
function pianoBoxHtml(L) {
  const R = L.piano; if (!R) return '';
  return '<h3 id="lv-piano">Lavoro a piano: alleanze, patti e appalti</h3><div class="item nv-diario"><div class="x">Passata ' + R.passata + ': ' + R.i + ' Stati su ' + R.totale + ', ora nel blocco «' + esc(R.blocco) + '». Prossimi: ' + esc((R.prossimi || []).slice(0, 4).join(', ')) + '.</div><div class="nv-tiles">' + nvTile(num(R.accordi), 'accordi e patti trovati') + nvTile(num(R.appalti), 'appalti e contratti trovati') + nvTile(num(R.con_scheda), 'Stati con una scheda') + nvTile(Math.round(100 * R.i / Math.max(1, R.totale)) + '%', 'della passata ' + R.passata) + '</div><div class="s"><a href="#piano">Apri il lavoro a piano, Stato per Stato →</a></div></div>';
}
function domandeHtml(L) {
  const U = (L.ricerca && L.ricerca.ultime) || [], R = L.piano;
  if (!U.length && !R) return '';
  let o = '<h3 id="lv-domande">Le domande che il programma si fa</h3><div class="item nv-diario"><div class="x">A ogni giro completo il programma scrive da solo delle ricerche, le prova su Google News e tiene quelle che portano notizie nuove. Qui sotto le ultime, scritte come le ha scritte lui.</div>';
  Object.keys(DOM_TIPO).forEach(k => {
    const l = U.filter(x => (x[3] || 'programma') === k); if (!l.length) return;
    o += '<div class="nv-riga"><span>' + DOM_TIPO[k][0] + ': ' + DOM_TIPO[k][1] + '</span><ul class="plain">' + l.map(x => '<li>' + (x[4] ? '<b>' + esc(x[4]) + '</b> ' : '') + '<span class="s">→ ' + x[1] + (x[1] === 1 ? ' notizia nuova' : ' notizie nuove') + '</span><br><span class="dq">' + esc(x[0]) + '</span></li>').join('') + '</ul></div>';
  });
  if (R && (R.domande || []).length) o += '<div class="nv-riga"><span>Lavoro a piano: alleanze, patti e appalti</span>' + pianoDomandeLista(R.domande.slice(0, 6).map(d => ({ stato: d[0], tipo: d[1], l: d[2], q: d[3], n: d[4] }))) + '</div>';
  if (R && (R.aperte || []).length) o += '<div class="nv-riga"><span>Che cosa il cervello vuole chiarire</span>' + pianoAperteLista(R.aperte.slice(0, 6).map(d => ({ stato: d[0], l: d[1], q: d[2], perche: d[3], fatta: d[4] }))) + '</div>';
  if (R && (R.risposte || []).length) o += '<div class="nv-riga"><span>Risposte trovate</span>' + pianoRisposteLista(R.risposte.slice(0, 4).map(r => ({ stato: r[0], perche: r[1], r: r[2], f: r[3] }))) + '</div>';
  return o + '<div class="s">' + (R ? '<a href="#piano">Tutte le domande del lavoro a piano →</a> · ' : '') + 'Sul telefono: <code>python castello.py domande</code></div></div>';
}
function fermateHtml(g) {
  const f = g.filter(x => x.tipo === 'fermo'), ns = g.reduce((t, x) => t + ((x.sosp || [])[0] || 0), 0), ms = Math.round(g.reduce((t, x) => t + ((x.sosp || [])[1] || 0), 0) / 60);
  if (!f.length && !ns) return '';
  const ora = iso => { const t = Date.parse(iso || ''); return t ? new Date(t).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) : '?'; };
  return '<div class="nv-riga"><span>Fermate</span><div>' + (f.length ? '<ul class="plain">' + f.map(x => '<li>' + (x.fermo ? 'dalle ' + ora(x.fermo[0]) + ' alle ' + ora(x.fermo[1]) + ' (' + x.fermo[2] + ' minuti)' : esc(x.quando)) + ': ' + esc(x.motivo || '') + '</li>').join('') + '</ul>' : 'Nessuna fermata nelle ultime 24 ore. ') + (ns ? 'Android ha messo in pausa Termux ' + ns + (ns === 1 ? ' volta' : ' volte') + ', per ' + ms + ' minuti in tutto.' : '') + '</div><div class="s">Quando riparte dopo essere stato fermo, il programma scrive da quando a quando e il motivo più probabile. Una chiusura «di colpo» non lascia tracce: di solito è Android che ferma Termux.</div></div>';
}
function caricaPiano() {
  if (!(APP_OK || location.protocol === 'file:')) return;
  const s = document.createElement('script'); s.src = 'piano.js?v=' + Date.now();
  s.onload = () => { render(); s.remove(); }; s.onerror = () => s.remove(); document.head.appendChild(s);
}

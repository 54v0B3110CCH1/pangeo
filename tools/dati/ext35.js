
// Trentacinquesima estensione (20 novembre 2026, programma 2.24): i pezzi del puzzle che il programma trova sulla stampa
// (energia e reti, IA in campo militare, trasporti e logistica, cibo e risorse), i siti militari di ogni Stato letti da
// Wikidata uno Stato a giro (basi.js), e le tappe precedenti dei fatti che il programma ha fuso in una riga sola.
const PUZZLE_NOME = { energia: 'energia e reti', ia: 'IA in campo militare', trasporti: 'trasporti e logistica', cibo: 'cibo, acqua e risorse' };
Object.assign(QUADRO_TIPO, { energia: 'energia e reti', ia: 'IA militare', trasporti: 'trasporti e logistica', cibo: 'cibo e risorse' });
function caricaBasi() {
  if (!(APP_OK || location.protocol === 'file:')) return;
  const s = document.createElement('script'); s.src = 'basi.js?v=' + Date.now();
  s.onload = () => { basiWdIndice(); render(); s.remove(); }; s.onerror = () => s.remove(); document.head.appendChild(s);
}
// i siti che uno Stato gestisce in altri Stati: l'indice si fa una volta sola, quando arrivano i dati
function basiWdIndice() {
  const B = window.BASI_WD, E = {};
  if (B && B.stati) Object.keys(B.stati).forEach(dove => (B.stati[dove] || []).forEach(e => { if (!e.ch) (e.gs || []).forEach(g => { if (g !== dove) (E[g] = E[g] || []).push([dove, e]); }); }));
  window.BASI_WD_ESTERO = E;
}
function basiWdDi(nome) { const B = window.BASI_WD; return (B && B.stati && B.stati[nome]) || null; }
function basiWdEsteroDi(nome) { return (window.BASI_WD_ESTERO || {})[nome] || []; }
function basiWdRiga(e, dove) {
  return '<li>' + (e.w ? '<a href="' + safeU(e.w) + '" target="_blank" rel="noopener">' + esc(e.n) + '</a>' : esc(e.n)) + ' <span class="s">' + [esc(e.t || ''), dove ? stLink(dove) : '', e.l ? esc(e.l) : '', (e.g || []).length ? 'gestito da ' + e.g.map(esc).join(', ') : ''].filter(Boolean).join(' · ') + ' · <a href="https://www.wikidata.org/wiki/' + esc(e.q) + '" target="_blank" rel="noopener">Wikidata</a></span>' + (e.ch ? ' <span class="badge" style="--c:var(--muted)">risulta chiuso</span>' : '') + '</li>';
}
const BASI_WD_NOTA = 'Elenco automatico da Wikidata, che il programma legge uno Stato a giro: basi, basi aeree e navali, aree di addestramento, stazioni radar. Wikidata non sempre registra le chiusure: un sito senza l’etichetta «risulta chiuso» può non essere più in uso. Le posizioni restano a livello di città.';
function basiWdHtml(nome) {
  const B = window.BASI_WD; if (!B || !B.stati) return '';
  const l = basiWdDi(nome), letti = Object.keys(B.letti || {}).length;
  if (!l) return '<div class="item"><div class="t">Siti militari secondo Wikidata</div><div class="x">Il programma non è ancora passato da ' + esc(nome) + ': legge i siti di uno Stato a giro. Finora ne ha letti ' + letti + '.</div></div>';
  const aperti = l.filter(e => !e.ch), chiusi = l.filter(e => e.ch), altrui = aperti.filter(e => (e.gs || []).some(g => g !== nome));
  let h = '<div class="item"><div class="t">Siti militari secondo Wikidata (' + aperti.length + ')</div>';
  if (altrui.length) h += '<div class="x">Di questi, ' + altrui.length + (altrui.length === 1 ? ' è gestito' : ' sono gestiti') + ' anche o solo da un altro Stato: ' + [...new Set([].concat(...altrui.map(e => e.gs.filter(g => g !== nome))))].map(g => stLink(g)).join(', ') + '.</div>';
  h += aperti.length ? '<ul class="plain">' + aperti.map(e => basiWdRiga(e)).join('') + '</ul>' : '<div class="x">Nessun sito in uso in elenco.</div>';
  if (chiusi.length) h += '<details class="crit"><summary>Siti che risultano chiusi o storici (' + chiusi.length + ')</summary><ul class="plain">' + chiusi.map(e => basiWdRiga(e)).join('') + '</ul></details>';
  return h + '<div class="s">' + esc(BASI_WD_NOTA) + ' ' + esc(nome) + ' letto il ' + esc(pianoData((B.letti || {})[nome])) + '.</div></div>';
}
function basiWdEsteroHtml(nome) {
  const l = basiWdEsteroDi(nome); if (!l.length) return '';
  const perStato = {}; l.forEach(x => (perStato[x[0]] = perStato[x[0]] || []).push(x[1]));
  const stati = Object.keys(perStato).sort((a, b) => perStato[b].length - perStato[a].length || a.localeCompare(b, 'it'));
  const letti = Object.keys((window.BASI_WD || {}).letti || {}).length;
  return '<div class="item"><div class="t">Siti gestiti da ' + esc(nome) + ' in altri Stati, secondo Wikidata (' + l.length + ')</div><ul class="plain">' + stati.map(st => perStato[st].map(e => basiWdRiga(e, st)).join('')).join('') + '</ul><div class="s">' + esc(BASI_WD_NOTA) + ' L’elenco cresce man mano che il programma legge gli altri Stati: finora ' + letti + '.</div></div>';
}
// tappe precedenti di un fatto che il programma ha fuso in una riga sola (annuncio, trattativa, firma)
function tappeHtml(x) {
  const t = x.tappe || []; if (!t.length) return '';
  return '<details class="crit"><summary>Tappe precedenti dello stesso fatto (' + t.length + ')</summary><ul class="plain">' + t.map(y => '<li>' + [esc(pianoData(y[0])), esc(y[1] || ''), esc(y[2] || '')].filter(Boolean).join(' · ') + '</li>').join('') + '</ul></details>';
}
// puzzle: i fatti dei temi nuovi
function puzzleDi(nome, tema) { const l = pianoDi(nome, 'puzzle'); return (tema ? l.filter(x => x.tema === tema) : l).slice().sort((a, b) => ((b.r || 0) - (a.r || 0)) || String(b.d || '').localeCompare(String(a.d || ''))); }
function puzzleFatto(x, stato) {
  return '<div class="item"><div class="t"><span class="dot" style="background:var(--infra)"></span> ' + esc(x.cosa) + '</div><div class="m">' + [stato ? stLink(stato) : '', esc(pianoData(x.d)), stato ? esc(PUZZLE_NOME[x.tema] || '') : ''].filter(Boolean).join(' · ') + '</div><div class="s">' + rilBadge(x.r) + ((x.f || []).length > 1 ? 'più fonti' : 'una fonte') + ': ' + pianoFonti(x.f) + '</div>' + tappeHtml(x) + '</div>';
}
const PUZZLE_NOTA = 'Il programma cerca questi fatti a pezzi piccoli: a ogni Stato un solo tema in più, a rotazione (energia, IA militare, trasporti, cibo), poi ogni 3 ore il cervello collega i pezzi. Sono titoli di giornale, non atti ufficiali: prima di usarli vanno confermati alla fonte.';
function puzzleStatoHtml(nome, tema) {
  const l = puzzleDi(nome, tema), P = pianoDati();
  if (!P) return '';
  if (!l.length) return '<p class="note">Nessun fatto recente dalla stampa su questo tema per ' + esc(nome) + ', per ora. ' + esc(PUZZLE_NOTA) + '</p>';
  return '<h4 style="margin:16px 0 4px">Fatti recenti dalla stampa, trovati dal programma</h4>' + l.map(x => puzzleFatto(x, '')).join('') + '<p class="note">' + esc(PUZZLE_NOTA) + '</p>';
}
function puzzleSezionePiano(s) {
  const l = (s.puzzle || []).slice().sort((a, b) => String(b.d || '').localeCompare(String(a.d || '')));
  return '<h3>Puzzle: energia, IA militare, trasporti, cibo (' + l.length + ')</h3>' + (l.map(x => puzzleFatto(x, '') ).join('') || '<p class="note">' + (s.tema ? 'Nell’ultimo passaggio il tema era «' + esc(PUZZLE_NOME[s.tema] || s.tema) + '»: nessun fatto nei titoli letti.' : 'I temi del puzzle cominciano con la versione 2.24 del programma.') + '</p>');
}
function puzzleTutti(tema) {
  const P = pianoDati(), l = [];
  if (P) Object.keys(P.stati).forEach(s => (P.stati[s].puzzle || []).forEach(x => { if (!tema || x.tema === tema) l.push([s, x]); }));
  return l.sort((a, b) => ((b[1].r || 0) - (a[1].r || 0)) || String(b[1].d || '').localeCompare(String(a[1].d || '')));
}
function viewIa() {
  crumbs([['', 'IA in campo militare']]);
  const l = puzzleTutti('ia'), stati = [...new Set(l.map(x => x[0]))];
  let h = '<h2>IA in campo militare</h2><p class="note">Che cosa scrive la stampa sull’intelligenza artificiale usata dalle forze armate: sistemi adottati o provati, contratti con le aziende, regole e leggi, incidenti e critiche. Solo fatti pubblici, ognuno con la sua fonte e una rilevanza da 1 a 5. Niente dettagli tecnici su come si usano le armi.</p>';
  h += '<div class="item nv-diario"><div class="nv-tiles">' + nvTile(num(l.length), 'fatti trovati finora') + nvTile(stati.length, 'Stati con almeno un fatto') + '</div></div>';
  h += l.length ? l.slice(0, 40).map(x => puzzleFatto(x[1], x[0])).join('') + (l.length > 40 ? '<p class="note">Qui i 40 più rilevanti su ' + l.length + ': gli altri sono nelle schede degli Stati.</p>' : '') : '<div class="item"><div class="x">Ancora nessuno. Il programma cerca questo tema dalla versione 2.24, uno Stato alla volta: una domanda in inglese e una nella lingua del posto.</div></div>';
  return h + '<p class="note">' + esc(PUZZLE_NOTA) + ' I collegamenti con gli altri temi sono nel <a href="#quadro">quadro</a>.</p>';
}

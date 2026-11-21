// Quarantacinquesima estensione (programma 2.35, 21 novembre 2026): il potere, istituzionale e non. Chi guida le
// istituzioni internazionali e le banche centrali, i fondi sovrani, i grandi gestori di soldi e le grandi banche (con le
// quote nelle aziende della difesa già in PanGeo), le persone più ricche, chi gestisce porti e aeroporti, i gruppi armati
// non statali. Dati da Wikidata (potere.js, rifatti dal telefono una sezione a giro). In ogni Stato: «Chi ha il potere».
const CAR_POT = {};
function caricaPotere() { caricaJs('potere.js', 'POTERE', CAR_POT); }
const POT_ORDINE = ['istituzioni', 'banche', 'fondi', 'gestori', 'miliardari', 'porti', 'aeroporti', 'armati'];
const POT_SPIEGA = {
  istituzioni: 'Chi le guida, da quando, dove hanno sede. Le quote e i voti degli Stati nel Fondo monetario e nella Banca mondiale non sono ancora nell’archivio.',
  banche: 'Chi guida la banca centrale di ogni Stato e da quando. La Fed americana: le sue azioni le tengono per legge le banche aderenti, ma non danno il controllo come una normale proprietà.',
  fondi: 'I fondi di investimento degli Stati: di chi sono, chi li guida, quanto hanno (con l’anno del dato).',
  gestori: 'Chi muove più soldi: grandi gestori, banche, fondi di private equity. Per ognuno chi lo guida, quanto gestisce e, quando PanGeo lo sa dai documenti ufficiali, le quote nelle aziende della difesa.',
  miliardari: 'Le persone con più di 15 miliardi di dollari secondo Wikidata (il dato porta la data: i patrimoni cambiano ogni giorno). Solo persone pubbliche.',
  porti: 'Chi gestisce e chi possiede i porti (quando Wikidata lo dice).',
  aeroporti: 'Gli aeroporti con più di 10 milioni di passeggeri l’anno: chi li gestisce e chi li possiede.',
  armati: 'Gruppi armati non statali, milizie e compagnie militari private: dove operano, chi li guida oggi e da chi sono sostenuti secondo Wikidata. Le designazioni (per esempio «terroristico») non si scrivono qui: sono decisioni di singoli Stati e organizzazioni, da leggere alle fonti.'
};
// i nomi con cui i grandi gestori compaiono nelle tabelle degli azionisti (PROPR)
const POT_ALIAS = { 'BlackRock': ['BlackRock'], 'The Vanguard Group': ['Vanguard'], 'State Street Corporation': ['State Street'], 'Fidelity Investments': ['Fidelity', 'FMR'],
  'Capital Group Companies': ['Capital Research', 'Capital World', 'Capital Group'], 'Morgan Stanley': ['Morgan Stanley'], 'Goldman Sachs': ['Goldman Sachs'],
  'UBS': ['UBS'], 'Bank of America': ['Bank of America'], 'JPMorgan Chase': ['JPMorgan', 'J.P. Morgan', 'Chase Manhattan'], 'BNY': ['Bank of New York', 'BNY'],
  'Norges Bank Investment Management': ['Norges', 'Government of Norway', 'fondo sovrano norvegese'], 'Amundi': ['Amundi'], 'Invesco': ['Invesco'],
  'Allianz SE': ['Allianz'], 'Deutsche Bank': ['Deutsche Bank', 'DWS'], 'HSBC': ['HSBC'], 'Berkshire Hathaway': ['Berkshire'] };
function potQuote(nome) {
  if (typeof PROPR === 'undefined') return [];
  const chiavi = POT_ALIAS[nome] || Object.entries(POT_ALIAS).filter(([k]) => nome.includes(k) || k.includes(nome)).map(([, v]) => v).flat() || [];
  if (!chiavi.length) return [];
  const out = [];
  Object.entries(PROPR).forEach(([az, p]) => (p.q || []).forEach(r => { if (chiavi.some(c => String(r[0]).includes(c))) out.push([az, r[1], r[2]]); }));
  return out;
}
function potWd(q, n) { return q ? '<a href="https://www.wikidata.org/wiki/' + esc(q) + '" target="_blank" rel="noopener">' + esc(n) + '</a>' : esc(n); }
function potStati(l) { return (Array.isArray(l) ? l : [l]).filter(Boolean).map(n => stLink(n)).join(', '); }
function potData(d) { return d ? String(d).slice(0, 10).split('-').reverse().join('/') : ''; }
function potVoce(s, x) {
  const m = [];
  if (s === 'istituzioni' || s === 'gestori') {
    if (x.capi && x.capi.length) m.push('guida: ' + esc(x.capi.join(', ')) + (x.dal ? ' (dal ' + potData(x.dal) + ')' : ''));
    if (x.sede || x.st) m.push('sede: ' + esc(x.sede || '') + (x.st ? (x.sede ? ', ' : '') + potStati(x.st) : ''));
    if (x.nato) m.push('dal ' + esc(x.nato));
    if ((x.aum || []).length) m.push('gestisce ' + esc(x.aum[0]));
    if ((x.att || []).length) m.push('attivi ' + esc(x.att[0]));
    if ((x.prop || []).length) m.push('posseduta (in parte) da ' + esc(x.prop.join(', ')));
    let h = '<div class="item"><div class="t">' + potWd(x.q, x.n) + '</div><div class="m">' + m.join(' · ') + '</div>';
    if (s === 'gestori') {
      const qq = potQuote(x.n);
      if (qq.length) h += '<div class="s">Quote nelle aziende della difesa (documenti ufficiali raccolti da PanGeo): ' + qq.slice(0, 12).map(r => azLink(r[0]) + ' ' + esc(r[1])).join(', ') + '</div>';
    }
    if (x.sito) h += '<div class="s"><a href="' + safeU(x.sito) + '" target="_blank" rel="noopener">sito ufficiale</a></div>';
    return h + '</div>';
  }
  if (s === 'banche') return '<div class="item"><div class="t">' + potWd(x.q, x.n) + ' · ' + potStati(x.st) + '</div><div class="m">' +
    [x.capi && x.capi.length ? 'guida: ' + esc(x.capi.join(', ')) + (x.dal ? ' (dal ' + potData(x.dal) + ')' : '') : 'chi la guida: non registrato su Wikidata',
      (x.prop || []).length ? 'proprietà: ' + esc(x.prop.join(', ')) : '', x.sito ? '<a href="' + safeU(x.sito) + '" target="_blank" rel="noopener">sito</a>' : ''].filter(Boolean).join(' · ') + '</div></div>';
  if (s === 'fondi') return '<div class="item"><div class="t">' + potWd(x.q, x.n) + (x.st ? ' · ' + potStati(x.st) : '') + '</div><div class="m">' +
    [x.nato ? 'dal ' + esc(x.nato) : '', (x.att || []).length ? 'attivi ' + esc(x.att[0]) : '', (x.capi || []).length ? 'guida: ' + esc(x.capi.join(', ')) : ''].filter(Boolean).join(' · ') + '</div></div>';
  if (s === 'miliardari') return '<div class="item"><div class="t">' + potWd(x.q, x.n) + '</div><div class="m">' +
    [x.v ? Math.round(x.v / 1e9).toLocaleString('it-IT') + ' miliardi di dollari' + (x.quando ? ' (al ' + potData(x.quando) + ')' : '') : '', (x.st || []).length ? potStati(x.st) : '',
      (x.az || []).length ? 'possiede: ' + x.az.map(n => AZIENDE.find(a => a.nome === n) ? azLink(n) : esc(n)).join(', ') : ''].filter(Boolean).join(' · ') + '</div></div>';
  if (s === 'porti' || s === 'aeroporti') return '<div class="item"><div class="t">' + potWd(x.q, x.n) + (x.iata ? ' (' + esc(x.iata) + ')' : '') + ' · ' + potStati(x.st) + '</div><div class="m">' +
    [x.pax ? Math.round(x.pax / 1e6).toLocaleString('it-IT') + ' milioni di passeggeri' : '', (x.op || []).length ? 'gestisce: ' + esc(x.op.join(', ')) : '',
      (x.prop || []).length ? 'possiede: ' + esc(x.prop.join(', ')) : ''].filter(Boolean).join(' · ') + '</div></div>';
  if (s === 'armati') return '<div class="item"><div class="t">' + potWd(x.q, x.n) + '</div><div class="m">' +
    [(x.cl || []).length ? esc(x.cl.join(', ')) : '', x.nato ? 'dal ' + esc(x.nato) : '', (x.st || []).length ? 'Stato: ' + potStati(x.st) : '',
      (x.area || []).length ? 'opera in: ' + potStati(x.area) : '', (x.capi || []).length ? 'guida: ' + esc(x.capi.join(', ')) : '',
      (x.fed || []).length ? 'fedele a: ' + potStati(x.fed) : '', (x.sost || []).length ? 'sostenuto da (secondo Wikidata): ' + potStati(x.sost) : ''].filter(Boolean).join(' · ') + '</div></div>';
  return '';
}
function viewPotere(sez) {
  caricaPotere();
  const P = window.POTERE;
  crumbs(sez ? [['#potere', 'Potere'], ['', ((P && P.nomi) || {})[sez] || sez]] : [['', 'Potere']]);
  let h = '<h2>' + (sez && P ? esc(P.nomi[sez] || sez) : 'Potere, istituzionale e non') + '</h2>';
  if (!P) return h + '<p class="note">' + (CAR_POT.c === 3 ? 'Dati del potere non ancora disponibili: arrivano con il prossimo giro completo del programma.' : 'Carico…') + '</p>';
  if (!sez) {
    h += '<p class="note">Chi guida, chi possiede, chi ha soldi, porti, aeroporti e armi. Dati da Wikidata (enciclopedia aperta, da incrociare con le fonti ufficiali), rifatti dal programma ogni settimana. Ogni nome porta alla sua scheda su Wikidata con le fonti.</p><div>';
    POT_ORDINE.forEach(s => { const v = ((P.sezioni || {})[s] || {}).voci || []; h += '<a class="folder big" href="#potere/' + s + '"><b>' + esc(P.nomi[s] || s) + '</b><small>' + v.length + ' voci · ' + esc(POT_SPIEGA[s].split('. ')[0]) + '</small></a>'; });
    return h + '</div>';
  }
  const X = (P.sezioni || {})[sez] || {};
  h += '<p class="note">' + esc(POT_SPIEGA[sez] || '') + (X.quando ? ' Aggiornato il ' + potData(X.quando) + '.' : '') + '</p>';
  const v = X.voci || [];
  if (sez === 'banche' || sez === 'porti') {
    const per = {}; v.forEach(x => (per[x.st || '—'] = per[x.st || '—'] || []).push(x));
    Object.keys(per).sort((a, b) => a.localeCompare(b, 'it')).forEach(st => { h += per[st].map(x => potVoce(sez, x)).join(''); });
  } else h += (sez === 'gestori' || sez === 'istituzioni' || sez === 'fondi' ? v.slice().sort((a, b) => a.n.localeCompare(b.n, 'it')) : v).map(x => potVoce(sez, x)).join('');
  return h + '<p class="note">Fonte: Wikidata (licenza CC0). Wikidata può essere incompleta o non aggiornata: un nome che manca non vuol dire che non esista.</p>';
}
// nella pagina di uno Stato
function potereStatoHtml(n) {
  caricaPotere();
  const P = window.POTERE; if (!P || !P.sezioni) return '';
  const di = (x, campo) => { const v = x[campo]; return Array.isArray(v) ? v.includes(n) : v === n; };
  const pezzi = [];
  const sez = s => ((P.sezioni[s] || {}).voci || []);
  const banche = sez('banche').filter(x => di(x, 'st'));
  if (banche.length) pezzi.push(['Banca centrale', banche.map(x => potWd(x.q, x.n) + (x.capi && x.capi.length ? ': ' + esc(x.capi.join(', ')) + (x.dal ? ' (dal ' + potData(x.dal) + ')' : '') : '')).join('; ')]);
  const fondi = sez('fondi').filter(x => di(x, 'st'));
  if (fondi.length) pezzi.push(['Fondi sovrani', fondi.map(x => potWd(x.q, x.n) + ((x.att || []).length ? ' (' + esc(x.att[0]) + ')' : '')).join('; ')]);
  const ist = sez('istituzioni').filter(x => di(x, 'st'));
  if (ist.length) pezzi.push(['Istituzioni internazionali con sede qui', ist.map(x => potWd(x.q, x.n)).join(', ')]);
  const ges = sez('gestori').filter(x => di(x, 'st'));
  if (ges.length) pezzi.push(['Grandi banche e gestori con sede qui', ges.map(x => potWd(x.q, x.n)).join(', ')]);
  const ric = sez('miliardari').filter(x => di(x, 'st'));
  if (ric.length) pezzi.push(['Le persone più ricche', ric.slice(0, 10).map(x => potWd(x.q, x.n) + ' (' + Math.round(x.v / 1e9) + ' mld $' + (x.quando ? ', ' + String(x.quando).slice(0, 4) : '') + ')').join('; ')]);
  const porti = sez('porti').filter(x => di(x, 'st'));
  if (porti.length) pezzi.push(['Porti', porti.slice(0, 12).map(x => potWd(x.q, x.n) + ((x.op || []).length ? ' (gestisce ' + esc(x.op.join(', ')) + ')' : '')).join('; ')]);
  const aer = sez('aeroporti').filter(x => di(x, 'st'));
  if (aer.length) pezzi.push(['Aeroporti più grandi', aer.slice(0, 8).map(x => potWd(x.q, x.n) + ((x.op || []).length ? ' (gestisce ' + esc(x.op.join(', ')) + ')' : '')).join('; ')]);
  const arm = sez('armati').filter(x => di(x, 'st') || di(x, 'area'));
  if (arm.length) pezzi.push(['Gruppi armati non statali che operano qui', arm.slice(0, 12).map(x => potWd(x.q, x.n)).join(', ')]);
  const sost = sez('armati').filter(x => di(x, 'sost'));
  if (sost.length) pezzi.push(['Gruppi armati che sostiene, secondo Wikidata', sost.map(x => potWd(x.q, x.n)).join(', ')]);
  if (!pezzi.length) return '';
  return '<h3 id="st-potere"><span class="dot" style="background:var(--aziende)"></span>Chi ha il potere</h3><div class="item"><dl class="kv">' +
    pezzi.map(p => '<dt>' + esc(p[0]) + '</dt><dd>' + p[1] + '</dd>').join('') + '</dl><div class="s">Da Wikidata, aggiornato ogni settimana; può essere incompleto. <a href="#potere">Tutto il potere</a></div></div>';
}

// Trentaseiesima estensione (20 novembre 2026, programma 2.25): pagina più leggera (un solo ridisegno, i dati grossi dopo
// la prima vista, il planisfero solo quando lo apri), collegamenti dentro i testi (Stati, aziende, sistemi d'arma, ognuno
// del suo colore), le schede degli altri Stati, la sintesi di ogni Stato, i sistemi d'arma (#sistemi), le cartelle di uno
// Stato in cinque gruppi, la prima pagina in sei aree, e Documenti con i rapporti delle 12 ore e che cosa manca.

// 1. un solo ridisegno: i file arrivano uno dopo l'altro, ma la pagina si rifà una volta sola
let ridisegnoT = null;
function ridisegna() { if (ridisegnoT) return; ridisegnoT = setTimeout(() => { ridisegnoT = null; render(); }, 80); }
// i file dei dati cambiano nome ogni 10 minuti: chi riapre la pagina usa la copia già scaricata
function verDati() { return Math.floor(Date.now() / 600000); }
function caricaDopo(f) { const subito = location.hash && location.hash !== '#'; if (subito) f(); else setTimeout(f, 700); }

// 2. il planisfero si carica solo quando lo apri (circa 1 MB e la parte più pesante da disegnare sul telefono)
let brainAperto = false, brainCarico = 0;
function apriPlanisfero() {
  brainAperto = true;
  if (window.echarts && echarts.getMap && echarts.getMap('world')) { render(); return; }
  if (brainCarico) return;
  brainCarico = 1; render();
  const a = document.createElement('script'); a.src = 'https://cdn.jsdelivr.net/npm/echarts@4.9.0/dist/echarts.min.js';
  a.onload = () => { const b = document.createElement('script'); b.src = 'https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/js/world.js'; b.onload = () => { brainCarico = 2; GEOC = null; render(); }; b.onerror = () => { brainCarico = 3; render(); }; document.head.appendChild(b); };
  a.onerror = () => { brainCarico = 3; render(); };
  document.head.appendChild(a);
}

// 3. collegamenti dentro i testi: Stati (blu), aziende (viola), sistemi d'arma (verde). Si tocca e si apre la cartella.
const VARIANTI_STATI = { 'Stati Uniti': 'USA', 'Stati Uniti d’America': 'USA', 'Türkiye': 'Turchia', 'Moldova': 'Moldavia', 'Cechia': 'Repubblica Ceca', 'Gran Bretagna': 'Regno Unito', 'Federazione Russa': 'Russia', 'Olanda': 'Paesi Bassi', 'Emirati Arabi Uniti': 'Emirati Arabi', 'Birmania': 'Myanmar', 'Kazakhstan': 'Kazakistan' };
// sistemi d'arma: id (senza barre, va nell'indirizzo), nome, tipo, chi lo fa, nomi con cui compare nei testi
const SISTEMI = [
  ['f-35', 'F-35 Lightning II', 'caccia', 'Lockheed Martin', ['F-35', 'F35', 'F-35A', 'F-35B', 'F-35C', 'Lightning II']],
  ['f-16', 'F-16', 'caccia', 'Lockheed Martin', ['F-16', 'F16', 'F-16V', 'F-16 Viper']],
  ['f-15', 'F-15', 'caccia', 'Boeing', ['F-15', 'F-15EX', 'F-15E', 'F-15IA']],
  ['f-a-18', 'F/A-18 Super Hornet', 'caccia', 'Boeing', ['F/A-18', 'F-18', 'Super Hornet']],
  ['f-22', 'F-22 Raptor', 'caccia', 'Lockheed Martin', ['F-22', 'Raptor']],
  ['b-21', 'B-21 Raider', 'bombardiere', 'Northrop Grumman', ['B-21']],
  ['eurofighter', 'Eurofighter Typhoon', 'caccia', 'Eurofighter', ['Eurofighter', 'Typhoon']],
  ['rafale', 'Rafale', 'caccia', 'Dassault Aviation', ['Rafale']],
  ['gripen', 'Gripen', 'caccia', 'Saab', ['Gripen', 'JAS 39']],
  ['kf-21', 'KF-21 Boramae', 'caccia', 'KAI', ['KF-21', 'Boramae']],
  ['j-20', 'J-20', 'caccia', 'AVIC', ['J-20']], ['j-10', 'J-10', 'caccia', 'AVIC', ['J-10', 'J-10C', 'J-10CE']],
  ['jf-17', 'JF-17 Thunder', 'caccia', 'PAC / AVIC', ['JF-17']], ['tejas', 'Tejas', 'caccia', 'HAL', ['Tejas']],
  ['su-57', 'Su-57', 'caccia', 'Sukhoi', ['Su-57']], ['su-35', 'Su-35', 'caccia', 'Sukhoi', ['Su-35']], ['su-30', 'Su-30', 'caccia', 'Sukhoi', ['Su-30', 'Su-30MKI']],
  ['mig-29', 'MiG-29', 'caccia', 'MiG', ['MiG-29']],
  ['gcap', 'GCAP (Tempest)', 'caccia di sesta generazione', 'BAE Systems, Leonardo, Mitsubishi', ['GCAP', 'Tempest']],
  ['fcas', 'FCAS / SCAF', 'caccia di sesta generazione', 'Dassault, Airbus, Indra', ['FCAS', 'SCAF']],
  ['a400m', 'A400M Atlas', 'aereo da trasporto', 'Airbus', ['A400M']], ['c-390', 'C-390 Millennium', 'aereo da trasporto', 'Embraer', ['C-390', 'KC-390']],
  ['c-130', 'C-130 Hercules', 'aereo da trasporto', 'Lockheed Martin', ['C-130', 'C-130J']], ['kc-46', 'KC-46 Pegasus', 'aereo cisterna', 'Boeing', ['KC-46']],
  ['p-8', 'P-8 Poseidon', 'pattugliatore marittimo', 'Boeing', ['P-8', 'P-8A', 'Poseidon']], ['e-7', 'E-7 Wedgetail', 'radar volante', 'Boeing', ['E-7', 'Wedgetail']],
  ['mq-9', 'MQ-9 Reaper', 'drone', 'General Atomics', ['MQ-9', 'MQ-9B', 'Reaper', 'SkyGuardian', 'SeaGuardian']],
  ['tb2', 'Bayraktar TB2', 'drone', 'Baykar', ['Bayraktar', 'TB2']], ['akinci', 'Bayraktar Akıncı', 'drone', 'Baykar', ['Akıncı', 'Akinci']],
  ['shahed', 'Shahed / Geran', 'drone d’attacco', 'Iran', ['Shahed', 'Geran', 'Geran-2']],
  ['ah-64', 'AH-64 Apache', 'elicottero d’attacco', 'Boeing', ['AH-64', 'Apache']], ['uh-60', 'UH-60 Black Hawk', 'elicottero', 'Lockheed Martin (Sikorsky)', ['UH-60', 'Black Hawk']],
  ['ch-47', 'CH-47 Chinook', 'elicottero da trasporto', 'Boeing', ['CH-47', 'Chinook']], ['nh90', 'NH90', 'elicottero', 'NHIndustries', ['NH90']],
  ['aw149', 'AW149', 'elicottero', 'Leonardo', ['AW149']], ['aw101', 'AW101', 'elicottero', 'Leonardo', ['AW101']],
  ['patriot', 'Patriot', 'difesa aerea', 'RTX', ['Patriot', 'PAC-3']], ['samp-t', 'SAMP/T', 'difesa aerea', 'Eurosam (MBDA, Thales)', ['SAMP/T', 'SAMP-T']],
  ['iris-t', 'IRIS-T', 'difesa aerea', 'Diehl Defence', ['IRIS-T', 'IRIS-T SLM']], ['nasams', 'NASAMS', 'difesa aerea', 'Kongsberg, RTX', ['NASAMS']],
  ['thaad', 'THAAD', 'difesa antimissile', 'Lockheed Martin', ['THAAD']], ['iron-dome', 'Iron Dome', 'difesa aerea', 'Rafael', ['Iron Dome', 'Cupola di ferro']],
  ['arrow', 'Arrow', 'difesa antimissile', 'IAI', ['Arrow 3', 'Arrow-3', 'Arrow 4']], ['davids-sling', 'Fionda di Davide', 'difesa aerea', 'Rafael', ['David’s Sling', "David's Sling", 'Fionda di Davide']],
  ['s-400', 'S-400', 'difesa aerea', 'Almaz-Antey', ['S-400']], ['s-500', 'S-500', 'difesa aerea', 'Almaz-Antey', ['S-500']], ['s-300', 'S-300', 'difesa aerea', 'Almaz-Antey', ['S-300']],
  ['hq-9', 'HQ-9', 'difesa aerea', 'CASIC', ['HQ-9']], ['camm', 'CAMM', 'difesa aerea', 'MBDA', ['CAMM']], ['barak', 'Barak', 'difesa aerea', 'IAI', ['Barak 8', 'Barak MX']],
  ['cheongung', 'Cheongung (KM-SAM)', 'difesa aerea', 'LIG Nex1', ['Cheongung', 'KM-SAM', 'M-SAM']], ['pantsir', 'Pantsir', 'difesa aerea', 'KBP', ['Pantsir']],
  ['golden-dome', 'Golden Dome', 'difesa antimissile', 'USA', ['Golden Dome', 'Cupola d’oro']], ['essi', 'European Sky Shield', 'difesa aerea', 'iniziativa europea', ['European Sky Shield', 'ESSI']],
  ['tomahawk', 'Tomahawk', 'missile da crociera', 'RTX', ['Tomahawk']], ['storm-shadow', 'Storm Shadow / SCALP', 'missile da crociera', 'MBDA', ['Storm Shadow', 'SCALP']],
  ['taurus', 'Taurus KEPD 350', 'missile da crociera', 'Taurus Systems', ['Taurus']], ['atacms', 'ATACMS', 'missile balistico', 'Lockheed Martin', ['ATACMS']],
  ['prsm', 'PrSM', 'missile balistico', 'Lockheed Martin', ['PrSM']], ['jassm', 'JASSM', 'missile da crociera', 'Lockheed Martin', ['JASSM', 'JASSM-ER']],
  ['kalibr', 'Kalibr', 'missile da crociera', 'Russia', ['Kalibr']], ['iskander', 'Iskander', 'missile balistico', 'Russia', ['Iskander']],
  ['kinzhal', 'Kinzhal', 'missile ipersonico', 'Russia', ['Kinzhal']], ['oreshnik', 'Oreshnik', 'missile balistico', 'Russia', ['Oreshnik']], ['zircon', 'Zircon', 'missile ipersonico', 'Russia', ['Zircon', 'Tsirkon']],
  ['brahmos', 'BrahMos', 'missile da crociera', 'BrahMos Aerospace', ['BrahMos']], ['meteor', 'Meteor', 'missile aria-aria', 'MBDA', ['Meteor']],
  ['amraam', 'AMRAAM', 'missile aria-aria', 'RTX', ['AMRAAM']], ['javelin', 'Javelin', 'missile anticarro', 'RTX, Lockheed Martin', ['Javelin']],
  ['spike', 'Spike', 'missile anticarro', 'Rafael', ['Spike']], ['nlaw', 'NLAW', 'arma anticarro', 'Saab', ['NLAW']],
  ['harpoon', 'Harpoon', 'missile antinave', 'Boeing', ['Harpoon']], ['nsm', 'Naval Strike Missile', 'missile antinave', 'Kongsberg', ['Naval Strike Missile', 'NSM']],
  ['exocet', 'Exocet', 'missile antinave', 'MBDA', ['Exocet']], ['hellfire', 'Hellfire', 'missile', 'Lockheed Martin', ['Hellfire']],
  ['leopard-2', 'Leopard 2', 'carro armato', 'KNDS', ['Leopard 2', 'Leopard 2A7', 'Leopard 2A8', 'Leopard']],
  ['abrams', 'M1 Abrams', 'carro armato', 'General Dynamics', ['Abrams', 'M1A2', 'M1 Abrams']], ['k2', 'K2 Black Panther', 'carro armato', 'Hyundai Rotem', ['K2 Black Panther', 'K2PL', 'carri K2', 'carro K2']],
  ['challenger', 'Challenger', 'carro armato', 'RBSL', ['Challenger 2', 'Challenger 3']], ['leclerc', 'Leclerc', 'carro armato', 'KNDS', ['Leclerc']],
  ['t-90', 'T-90', 'carro armato', 'Uralvagonzavod', ['T-90']], ['t-72', 'T-72', 'carro armato', 'Uralvagonzavod', ['T-72']], ['merkava', 'Merkava', 'carro armato', 'Israele', ['Merkava']],
  ['boxer', 'Boxer', 'blindato', 'ARTEC (KNDS, Rheinmetall)', ['Boxer']], ['cv90', 'CV90', 'veicolo da combattimento', 'BAE Systems', ['CV90']],
  ['lynx', 'Lynx KF41', 'veicolo da combattimento', 'Rheinmetall', ['Lynx KF41', 'KF41']], ['bradley', 'M2 Bradley', 'veicolo da combattimento', 'BAE Systems', ['Bradley']],
  ['stryker', 'Stryker', 'blindato', 'General Dynamics', ['Stryker']], ['patria-amv', 'Patria AMV', 'blindato', 'Patria', ['Patria AMV', 'AMV XP']],
  ['k9', 'K9 Thunder', 'obice semovente', 'Hanwha Aerospace', ['K9 Thunder', 'obici K9', 'K9A1', 'K9A2']], ['pzh-2000', 'PzH 2000', 'obice semovente', 'KNDS', ['PzH 2000', 'PzH2000']],
  ['caesar', 'CAESAR', 'obice', 'KNDS', ['CAESAR', 'Caesar']], ['himars', 'HIMARS', 'lanciarazzi', 'Lockheed Martin', ['HIMARS', 'M142']],
  ['chunmoo', 'Chunmoo (K239)', 'lanciarazzi', 'Hanwha Aerospace', ['Chunmoo', 'K239']], ['m270', 'M270 MLRS', 'lanciarazzi', 'Lockheed Martin', ['M270', 'MLRS']],
  ['fremm', 'FREMM', 'fregata', 'Fincantieri, Naval Group', ['FREMM', 'Fremm']], ['fdi', 'FDI (Belharra)', 'fregata', 'Naval Group', ['FDI', 'Belharra']],
  ['type-26', 'Type 26', 'fregata', 'BAE Systems', ['Type 26', 'Type-26', 'classe City']], ['type-31', 'Type 31', 'fregata', 'Babcock', ['Type 31', 'Type-31']],
  ['arleigh-burke', 'Arleigh Burke', 'cacciatorpediniere', 'USA', ['Arleigh Burke']], ['constellation', 'Constellation', 'fregata', 'Fincantieri Marinette Marine', ['classe Constellation', 'fregate Constellation']],
  ['ppa', 'PPA (Thaon di Revel)', 'pattugliatore', 'Fincantieri', ['PPA', 'Thaon di Revel']], ['hobart', 'Hobart', 'cacciatorpediniere', 'Navantia', ['classe Hobart']],
  ['virginia', 'Virginia', 'sottomarino nucleare', 'General Dynamics, HII', ['classe Virginia', 'sottomarini Virginia']], ['aukus', 'AUKUS', 'patto e sottomarini', 'Australia, Regno Unito, USA', ['AUKUS']],
  ['scorpene', 'Scorpène', 'sottomarino', 'Naval Group', ['Scorpène', 'Scorpene']], ['u212', 'U212 / Type 212', 'sottomarino', 'TKMS, Fincantieri', ['U212', 'U-212', 'Type 212', 'U212NFS', '212CD']],
  ['type-214', 'Type 214', 'sottomarino', 'TKMS', ['Type 214']], ['starlink', 'Starlink', 'satelliti', 'SpaceX', ['Starlink', 'Starshield']], ['iris2', 'IRIS²', 'satelliti', 'Unione europea', ['IRIS²', 'IRIS2']]
];
const SIS = {}; SISTEMI.forEach(s => { SIS[s[0]] = { id: s[0], nome: s[1], tipo: s[2], chi: s[3], alias: s[4] }; });
let COLL = null;
function collegaIndice() {
  if (COLL && COLL.n === AZIENDE.length) return COLL;
  const voci = [];
  Object.keys(STATI).forEach(n => { if (n.length >= 4 || n === 'USA' || n === 'Iran' || n === 'Cina' || n === 'Peru' || n === 'Ciad' || n === 'Laos' || n === 'Oman' || n === 'Togo' || n === 'Cuba' || n === 'Mali' || n === 'Fiji') voci.push([n, 's', n]); });
  Object.entries(VARIANTI_STATI).forEach(([v, n]) => { if (STATI[n]) voci.push([v, 's', n]); });
  const noAz = new Set(['Leonardo', 'Patria', 'Thales']); // anche parole comuni o già sistemi: le aziende con questi nomi si collegano per intero
  AZIENDE.forEach(a => { if (a.nome.length >= 4 && !/^[A-Z]{1,3}$/.test(a.nome)) voci.push([a.nome, 'a', a.nome]); });
  ['Leonardo', 'Thales'].forEach(n => { const a = AZIENDE.find(z => z.nome === n); if (a) voci.push([n, 'a', n]); });
  SISTEMI.forEach(s => s[4].forEach(v => voci.push([v, 'w', s[0]])));
  const m = new Map(); voci.forEach(v => { if (!m.has(v[0])) m.set(v[0], v); });
  const parole = [...m.keys()].sort((a, b) => b.length - a.length).map(v => v.replace(/[.*+?^${}()|[\]\\\/]/g, '\\$&'));
  let re = null;
  try { re = new RegExp('(^|[^\\p{L}\\p{N}])(' + parole.join('|') + ')(?=$|[^\\p{L}\\p{N}])', 'gu'); } catch (e) { re = null; }
  COLL = { re, m, n: AZIENDE.length, noAz };
  return COLL;
}
function linkVoce(v, testo) {
  if (!v) return esc(testo);
  if (v[1] === 's' && STATI[v[2]]) return '<a class="cl cl-s" href="#stati/' + STATI[v[2]].slug + '">' + esc(testo) + '</a>';
  if (v[1] === 'a') { const a = AZIENDE.find(z => z.nome === v[2]); if (a) return '<a class="cl cl-a" href="#aziende/' + a.slug + '">' + esc(testo) + '</a>'; }
  if (v[1] === 'w') return '<a class="cl cl-w" href="#sistemi/' + v[2] + '">' + esc(testo) + '</a>';
  return esc(testo);
}
function collega(t) {
  t = String(t == null ? '' : t); if (!t) return '';
  const C = collegaIndice(); if (!C.re) return esc(t);
  let out = '', i = 0, mt; C.re.lastIndex = 0;
  while ((mt = C.re.exec(t))) {
    const inizio = mt.index + mt[1].length, parola = mt[2];
    out += esc(t.slice(i, inizio)) + linkVoce(C.m.get(parola), parola);
    i = inizio + parola.length; C.re.lastIndex = i;
  }
  return out + esc(t.slice(i));
}
// «Cina, USA (accordo)» → due collegamenti
function collegaNomi(t) { return collega(t); }

// 4. sistemi d'arma: dove compaiono (lavoro a piano, appalti, notizie delle schede, fatti confermati)
let SIS_IDX = null;
function sistemiIndice() {
  const firma = [(window.PIANO || {}).agg, (window.LIVE || {}).agg, Object.keys(window.MEMORIA || {}).length].join('|');
  if (SIS_IDX && SIS_IDX.firma === firma) return SIS_IDX;
  const C = collegaIndice(), I = {};
  const scorri = (testo, voce) => {
    if (!testo || !C.re) return; C.re.lastIndex = 0; let mt; const visti = new Set();
    while ((mt = C.re.exec(String(testo)))) { const v = C.m.get(mt[2]); C.re.lastIndex = mt.index + mt[1].length + mt[2].length; if (v && v[1] === 'w' && !visti.has(v[2])) { visti.add(v[2]); (I[v[2]] = I[v[2]] || []).push(voce); } }
  };
  const P = (window.PIANO || {}).stati || {};
  Object.entries(P).forEach(([st, s]) => {
    (s.accordi || []).forEach(x => scorri(x.cosa, { st, d: x.d, t: x.cosa, k: 'accordo', f: x.f, con: x.con }));
    (s.appalti || []).forEach(x => scorri(x.ogg + ' ' + (x.forn || ''), { st, d: x.d, t: x.ogg, k: 'appalto', f: x.f, forn: x.forn, val: x.val }));
    (s.intel || []).forEach(x => scorri(x.cosa, { st, d: x.d, t: x.cosa, k: 'intelligence', f: x.f }));
    (s.puzzle || []).forEach(x => scorri(x.cosa, { st, d: x.d, t: x.cosa, k: PUZZLE_NOME[x.tema] || 'risorse', f: x.f }));
  });
  (typeof APPALTI !== 'undefined' ? APPALTI : []).forEach(x => scorri(x[2], { st: x[1], d: x[0], t: x[2], k: 'appalto (tabella)', src: x[5], forn: x[3], val: x[4] }));
  Object.entries(SCHEDE).forEach(([st, s]) => (s.nz || []).forEach(r => scorri(r[1], { st, d: r[0], t: r[1], k: 'notizia', src: r[2] })));
  Object.entries(window.MEMORIA || {}).forEach(([st, l]) => (l || []).forEach(x => scorri(x[1], { st, d: x[0], t: x[1], k: 'confermato', f: [[x[2], x[4]]] })));
  SIS_IDX = { firma, I }; return SIS_IDX;
}
function sisFonti(v) {
  if (v.src) return src(v.src);
  return (v.f || []).slice(0, 3).map(f => f && f[1] ? '<a href="' + safeU(f[1]) + '" target="_blank" rel="noopener">' + esc(f[0] || 'fonte') + '</a>' : '').filter(Boolean).join(' · ');
}
function viewSistemi(id) {
  const I = sistemiIndice().I;
  if (id && SIS[id]) {
    const S = SIS[id], l = (I[id] || []).slice().sort((a, b) => String(b.d || '').localeCompare(String(a.d || '')));
    crumbs([['#sistemi', 'Sistemi d’arma'], ['', S.nome]]);
    const stati = [...new Set(l.map(v => v.st))];
    const az = AZIENDE.filter(a => S.chi.includes(a.nome));
    let h = '<h2>' + esc(S.nome) + '</h2><p class="note">' + esc(S.tipo) + ' · ' + (az.length ? az.map(a => azLink(a.nome)).join(', ') : esc(S.chi)) + '</p>';
    h += '<div class="item nv-diario"><div class="nv-tiles">' + nvTile(l.length, 'volte in cui compare nell’archivio') + nvTile(stati.length, 'Stati') + '</div></div>';
    if (!l.length) return h + '<p class="note">Per ora non compare nei fatti raccolti. L’elenco cresce con il lavoro a piano e le notizie.</p>';
    h += '<div class="members">' + stati.map(n => stLink(n)).join('') + '</div>';
    const per = {}; l.forEach(v => (per[v.st] = per[v.st] || []).push(v));
    Object.keys(per).sort((a, b) => per[b].length - per[a].length || a.localeCompare(b, 'it')).forEach(st => {
      h += '<h3>' + stLink(st) + ' <span class="s">(' + per[st].length + ')</span></h3>';
      h += per[st].slice(0, 12).map(v => '<div class="item"><div class="t">' + collega(v.t) + '</div><div class="m">' + [esc(pianoData(v.d)), esc(v.k), v.con ? 'con ' + collega(v.con) : '', v.forn ? 'fornisce ' + collega(v.forn) : '', v.val ? esc(v.val) : ''].filter(Boolean).join(' · ') + '</div><div class="s">' + sisFonti(v) + '</div></div>').join('');
    });
    return h + '<p class="note">Elenco automatico: ogni riga è un fatto già salvato da PanGeo che nomina ' + esc(S.nome) + ', con la sua fonte. Sono titoli e sintesi, da leggere alla fonte.</p>';
  }
  crumbs([['', 'Sistemi d’arma']]);
  const tipi = {}; SISTEMI.forEach(s => (tipi[s[2]] = tipi[s[2]] || []).push(s));
  let h = '<h2>Sistemi d’arma</h2><p class="note">Aerei, elicotteri, difese aeree, missili, carri, navi e satelliti: per ognuno, dove compare nei fatti raccolti, Stato per Stato. Nei testi di PanGeo i loro nomi sono in verde e si toccano.</p>';
  const ordine = Object.keys(tipi).sort((a, b) => tipi[b].reduce((n, s) => n + (I[s[0]] || []).length, 0) - tipi[a].reduce((n, s) => n + (I[s[0]] || []).length, 0));
  ordine.forEach(t => {
    h += '<h3>' + esc(t[0].toUpperCase() + t.slice(1)) + '</h3><div class="members">' + tipi[t].slice().sort((a, b) => (I[b[0]] || []).length - (I[a[0]] || []).length).map(s => '<a class="cl-w" href="#sistemi/' + s[0] + '">' + esc(s[1]) + ((I[s[0]] || []).length ? ' (' + I[s[0]].length + ')' : '') + '</a>').join('') + '</div>';
  });
  return h;
}

// 5. le schede degli altri Stati: un accordo Italia–Grecia scritto nella scheda della Grecia compare anche in quella dell'Italia
function nomeGiusto(n) { n = String(n || '').trim(); return VARIANTI_STATI[n] || n; }
function nomiIn(t) { const C = collegaIndice(); const fuori = new Set(); if (!t || !C.re) return fuori; C.re.lastIndex = 0; let mt; while ((mt = C.re.exec(String(t)))) { const v = C.m.get(mt[2]); C.re.lastIndex = mt.index + mt[1].length + mt[2].length; if (v && v[1] === 's') fuori.add(v[2]); } return fuori; }
function paroleDi(t) { return new Set(String(t || '').toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(w => w.length > 3)); }
function pianoAltri(nome, tipo) {
  const P = (window.PIANO || {}).stati || {}, mie = ((P[nome] || {})[tipo] || []).map(x => paroleDi(x.cosa || x.ogg));
  const fuori = [];
  Object.entries(P).forEach(([st, s]) => {
    if (st === nome) return;
    (s[tipo] || []).forEach(x => {
      const dove = tipo === 'accordi' ? nomiIn(x.con) : new Set([...nomiIn(x.acq), ...nomiIn(x.forn)]);
      if (!dove.has(nome)) return;
      const p = paroleDi(x.cosa || x.ogg);
      if (mie.some(q => { let c = 0; p.forEach(w => { if (q.has(w)) c++; }); return c >= 0.5 * Math.min(p.size, q.size); })) return; // c'è già nella scheda
      fuori.push([st, x]);
    });
  });
  return fuori.sort((a, b) => String(b[1].d || '').localeCompare(String(a[1].d || '')));
}
function pianoAltriHtml(nome, tipo) {
  const l = pianoAltri(nome, tipo); if (!l.length) return '';
  return '<h4 style="margin:16px 0 4px">Nelle schede di altri Stati (' + l.length + ')</h4>' + l.slice(0, 20).map(([st, x]) => (tipo === 'appalti' ? pianoAppalto(x) : pianoAccordo(x)).replace('<div class="m">', '<div class="m">dalla scheda di ' + stLink(st) + ' · ')).join('') + (l.length > 20 ? '<p class="note">Qui i 20 più recenti.</p>' : '');
}

// 6. la sintesi di ogni Stato: la scrive il cervello dai fatti già salvati, ogni frase con le sue fonti
function sintesiHtml(nome) {
  const s = (((window.PIANO || {}).stati || {})[nome] || {}).sintesi;
  if (!s || !(s.righe || []).length) return '';
  return '<section class="item sintesi"><div class="t">In breve, dai fatti raccolti</div><ul class="plain">' + s.righe.map(r => '<li><b>' + esc(r[0]) + ':</b> ' + collega(r[1]) + ((r[2] || []).length ? ' <span class="s">' + r[2].map(f => '<a href="' + safeU(f[1]) + '" target="_blank" rel="noopener">' + esc(f[0] || 'fonte') + '</a>').join(' · ') + '</span>' : '') + '</li>').join('') + '</ul><div class="s">Scritta dal programma il ' + esc(pianoOra(s.quando)) + ' da ' + (s.fatti || 0) + ' fatti con fonte (accordi, appalti, servizi, risorse, fatti confermati). Una sintesi automatica: i dettagli e le fonti sono nelle cartelle qui sotto.</div></section>';
}

// 7. le cartelle di uno Stato in cinque gruppi
const GRUPPI_SUB = [
  ['Politica e società', ['governo', 'stabilita', 'alleanze', 'trattati', 'notizie', 'storia', 'voci', 'proteste', 'societa', 'sedi', 'siti']],
  ['Difesa e sicurezza', ['numeri', 'forze', 'riserve', 'ambizioni', 'unita', 'basi', 'estero', 'conflitti', 'pmc', 'ia']],
  ['Intelligence', ['intelligence']],
  ['Risorse, energia e rotte', ['energia', 'logistica', 'cibo', 'dipendenze', 'infrastrutture', 'stretti', 'aeroporti']],
  ['Industria e appalti', ['appalti', 'aziende', 'programmi']]
];
function subOrdinati() { const ids = GRUPPI_SUB.flatMap(g => g[1]); return ids.map(id => SUB.find(u => u.id === id)).filter(Boolean).concat(SUB.filter(u => !ids.includes(u.id))); }
function subGruppiHtml(s, subs) {
  return GRUPPI_SUB.map(g => { const l = subs.filter(u => g[1].includes(u.id)); if (!l.length) return ''; return '<div class="subg"><span class="subg-t">' + esc(g[0]) + '</span><div class="sub">' + l.map(u => { const n = subCount(s, u.id); return '<a href="#stati/' + s.slug + '/' + u.id + '"><span class="dot" style="background:var(' + subCol(s, u) + ')"></span>' + esc(u.nome) + (n ? ' (' + n + ')' : '') + '</a>'; }).join('') + '</div></div>'; }).join('');
}

// 8. prima pagina in sei aree; il planisfero si apre a richiesta
const AREE_HOME = [
  ['Stati e politica', ['#stati', '#alleanze', '#live', '#temi', '#propaganda']],
  ['Difesa', ['#forze', '#sistemi', '#unita', '#sicurezza', '#ia']],
  ['Intelligence', ['#intelligence', '#quadro']],
  ['Risorse ed energia', ['#risorse']],
  ['Industria e appalti', ['#aziende', '#appalti', '#industria', '#rete', '#piano']],
  ['Documenti e fonti', ['#documenti', '#fonti']]
];
function homeAree(vecchia) {
  const tess = {}; (vecchia.match(/<a class="folder big" href="#[^"]+">[\s\S]*?<\/a>/g) || []).forEach(t => { tess[t.match(/href="(#[^"]+)"/)[1]] = t; });
  const nIdx = sistemiIndice().I, nSis = Object.keys(nIdx).length;
  tess['#sistemi'] = '<a class="folder big" href="#sistemi"><b>Sistemi d’arma</b><small>' + SISTEMI.length + ' sistemi, da F-35 a Patriot e FREMM: dove compaiono, Stato per Stato' + (nSis ? ' (' + nSis + ' già nei fatti)' : '') + '</small></a>';
  tess['#quadro'] = '<a class="folder big" href="#quadro"><b>Quadro e collegamenti</b><small>Le voci più rilevanti e i collegamenti tra i fatti, con le domande per verificarli</small></a>';
  tess['#documenti'] = '<a class="folder big" href="#documenti"><b>Documenti</b><small>Rapporti del programma ogni 12 ore, che cosa c’è e che cosa manca per ogni Stato, tabelle, archivi</small></a>';
  const usati = new Set();
  let h = '';
  AREE_HOME.forEach(([nome, hrefs]) => {
    const l = hrefs.filter(x => tess[x]); if (!l.length) return;
    l.forEach(x => usati.add(x));
    h += '<h3 class="area">' + esc(nome) + '</h3><div class="grid big">' + l.map(x => tess[x]).join('') + '</div>';
  });
  const resto = Object.keys(tess).filter(x => !usati.has(x));
  if (resto.length) h += '<h3 class="area">Altro</h3><div class="grid big">' + resto.map(x => tess[x]).join('') + '</div>';
  return h;
}
function viewHome2() {
  const v = viewHome();
  const i = v.indexOf('<section class="brain">'), j = v.indexOf('</section>', i);
  const brain = i >= 0 ? v.slice(i, j + 10) : '';
  const dopo = v.slice(v.indexOf('<div class="quick">'));
  let mappa;
  if (brainAperto && brainCarico !== 1 && brainCarico !== 3) mappa = brain;
  else mappa = '<section class="brain chiusa"><div class="item"><div class="t">Planisfero</div><div class="x">Colora i Paesi per spesa militare, alleanze o stabilità, con conflitti, rotte, basi e aziende. Si carica solo quando lo apri (circa 1 MB).</div><div class="quick"><button class="pill" id="apri-mappa">' + (brainCarico === 1 ? 'Sto caricando il planisfero…' : brainCarico === 3 ? 'Non si è caricato: riprova' : 'Apri il planisfero') + '</button></div></div></section>';
  return mappa + homeAree(v) + dopo;
}

// 9. Documenti: rapporti delle 12 ore, che cosa c'è e che cosa manca, tabelle, archivi
let RAPP_CARICO = false;
function caricaRapporti() {
  if (RAPP_CARICO || !(APP_OK || location.protocol === 'file:') || typeof fetch !== 'function') return; RAPP_CARICO = true;
  fetch('rapporti.json?v=' + verDati()).then(r => r.ok ? r.json() : null).then(d => { if (Array.isArray(d)) { window.RAPPORTI = d; ridisegna(); } }).catch(() => {});
}
function copertura() {
  const P = (window.PIANO || {}).stati || {}, B = (window.BASI_WD || {}).letti || {}, M = window.MEMORIA || {}, SA = window.SAPERE || {};
  return Object.keys(SCHEDE).sort((a, b) => a.localeCompare(b, 'it')).map(n => {
    const p = P[n] || {}, temi = new Set((p.puzzle || []).map(x => x.tema));
    const c = { 'notizie confermate': (M[n] || []).length, 'lavoro a piano': p.quando ? 1 : 0, 'accordi': (p.accordi || []).length, 'appalti': (p.appalti || []).length,
      'servizi di intelligence': ((INTEL.stati || {})[n] || {}).s ? 1 : ((INTEL.stati || {})[n] ? 1 : 0), 'fatti sui servizi': (p.intel || []).length,
      'energia': temi.has('energia') ? 1 : 0, 'IA militare': temi.has('ia') ? 1 : 0, 'trasporti': temi.has('trasporti') ? 1 : 0, 'cibo': temi.has('cibo') ? 1 : 0,
      'siti militari': B[n] ? 1 : 0, 'uomini e mezzi': FORZE[n] ? 1 : 0, 'Wikipedia': SA[n] ? 1 : 0, 'sintesi': ((p.sintesi || {}).righe || []).length ? 1 : 0 };
    return [n, c, Object.keys(c).filter(k => !c[k])];
  });
}
function viewDocumenti(parte) {
  crumbs([['#documenti', 'Documenti']]);
  caricaRapporti();
  let h = '<h2>Documenti</h2><div class="sub"><a role="button" tabindex="0" data-go="doc-rap">Rapporti</a><a role="button" tabindex="0" data-go="doc-cop">Che cosa manca</a><a role="button" tabindex="0" data-go="doc-tab">Tabelle</a><a role="button" tabindex="0" data-go="doc-arc">Archivi</a></div>';
  const R = window.RAPPORTI || [];
  h += '<h3 id="doc-rap">Rapporti del programma (ogni 12 ore)</h3>';
  if (!R.length) h += '<p class="note">Il programma scrive un rapporto alle 8 e alle 20 (dalla versione 2.25): che cosa ha fatto, quante informazioni ha, che cosa è migliorato o peggiorato rispetto al rapporto prima, telefono e costi. Arriva anche per mail.' + (APP_OK ? ' Nessun rapporto ancora su questo sito.' : '') + '</p>';
  else {
    const z = R[R.length - 1];
    h += '<div class="item"><div class="t">' + esc(z.quando) + ' · ' + esc(z.verdetto) + '</div><pre class="rap">' + collega(z.testo) + '</pre></div>';
    R.slice(0, -1).reverse().slice(0, 30).forEach(r => { h += '<details class="crit"><summary>' + esc(r.quando) + ' · ' + esc(r.verdetto) + '</summary><pre class="rap">' + collega(r.testo) + '</pre></details>'; });
  }
  const C = copertura(), tot = C.length, conta = k => C.filter(x => x[1][k]).length;
  h += '<h3 id="doc-cop">Che cosa c’è e che cosa manca, Stato per Stato</h3><div class="item nv-diario"><div class="nv-tiles">' +
    ['lavoro a piano', 'sintesi', 'siti militari', 'servizi di intelligence', 'Wikipedia', 'uomini e mezzi'].map(k => nvTile(conta(k) + '/' + tot, 'Stati con ' + k)).join('') + '</div><div class="s">Puzzle: energia ' + conta('energia') + ', IA militare ' + conta('IA militare') + ', trasporti ' + conta('trasporti') + ', cibo ' + conta('cibo') + ' Stati su ' + tot + '. Il programma lavora uno Stato alla volta: il lavoro a piano e i siti militari coprono tutti gli Stati in pochi giorni, il puzzle dà a ogni Stato un tema per passata, quindi tutti e quattro in circa quattro passate.</div></div>';
  h += '<ul class="plain">' + C.slice().sort((a, b) => b[2].length - a[2].length || a[0].localeCompare(b[0], 'it')).map(([n, c, manca]) => '<li>' + stLink(n) + ' <span class="s">— ' + (manca.length ? 'manca: ' + esc(manca.join(', ')) : 'c’è tutto') + (c['notizie confermate'] ? ' · ' + c['notizie confermate'] + ' fatti confermati' : '') + (c.accordi + c.appalti ? ' · ' + c.accordi + ' accordi, ' + c.appalti + ' appalti' : '') + '</span></li>').join('') + '</ul>';
  h += '<h3 id="doc-tab">Tabelle aperte</h3><div class="item"><a href="tabelle.html">Tutte le tabelle (CSV e JSON, con date e fonti)</a><div class="s">Stati, forze, basi, appalti, aziende e proprietà, fonti, intelligence, energia e commercio: si scaricano e si aprono con un foglio di calcolo.</div></div>';
  h += '<h3 id="doc-arc">Archivi su claude.ai</h3><p class="note">Si aprono solo con il tuo account di Claude. Li aggiornano le attività programmate (notte, mattina, mese).</p>';
  let last = '';
  DOCS.forEach(d => { if (d[0] !== last) { h += '<h4>' + esc(d[0]) + '</h4>'; last = d[0]; } h += '<div class="item"><a href="' + d[2] + '" target="_blank" rel="noopener">' + esc(d[1]) + '</a></div>'; });
  return h;
}

// 10. siti militari: la zona sulla mappa (le coordinate sono a un decimo di grado, cioè a livello di città)
const basiWdRiga0 = basiWdRiga;
basiWdRiga = function (e, dove) {
  const r = basiWdRiga0(e, dove);
  if (!e.c || e.c.length < 2) return r;
  return r.replace(/<\/li>$/, ' · <a class="s" href="https://www.google.com/maps/search/?api=1&query=' + e.c[1] + ',' + e.c[0] + '" target="_blank" rel="noopener">zona sulla mappa</a></li>');
};

(function () {
  const st = document.createElement('style');
  st.textContent = '.cl{text-decoration:none;border-bottom:1px dotted currentColor}.cl-s{color:var(--accent)}.cl-a{color:var(--aziende)}.cl-w{color:var(--numeri);font-weight:600}' +
    '.members a.cl-w{color:var(--numeri)}.subg{margin:6px 0}.subg-t{display:block;font-size:12px;color:var(--muted);margin:8px 0 2px;text-transform:uppercase;letter-spacing:.04em}' +
    '.sintesi{border-left:3px solid var(--accent)}h3.area{margin:22px 0 6px}pre.rap{white-space:pre-wrap;font:inherit;font-size:13px;line-height:1.45;margin:6px 0 0}.brain.chiusa .item{margin:0}';
  document.head.appendChild(st);
})();
document.addEventListener('click', e => { const b = e.target && e.target.closest && e.target.closest('#apri-mappa'); if (b) { e.preventDefault(); apriPlanisfero(); } });

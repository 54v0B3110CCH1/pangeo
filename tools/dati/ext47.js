// Quarantasettesima estensione (programma 2.38, 21 novembre 2026): il controllo dei dati.
// 1. Chi guida, controllato: per Stati, istituzioni, banche centrali, grandi banche e fondi il programma mette a confronto
//    Wikidata e il riquadro della voce di Wikipedia, cerca i nomi nelle notizie che ha letto e, quando Wikipedia cita il
//    sito ufficiale, guarda lì. Ogni nome porta il voto alla NATO (fonte A–F, informazione 1–6) e la data del controllo;
//    quando le fonti non concordano la pagina lo dice e mostra tutte e due (capi.js).
// 2. Armi vendute e comprate: il registro SIPRI degli ultimi dieci anni, Stato per Stato e sistema per sistema (armi.js).
// 3. I fatti dentro gli articoli: chi, che cosa, quanti, dove, quando, ognuno controllato nel testo (fatti.js).
const CAR_CAPI = {}, CAR_ARMI = {}, CAR_FATTI = {};
function caricaCapi() { caricaJs('capi.js', 'CAPI', CAR_CAPI); }
function caricaArmi() { caricaJs('armi.js', 'ARMI', CAR_ARMI); }
function caricaFatti() { caricaJs('fatti.js', 'FATTI', CAR_FATTI); }
const VOTO_INFO = { 1: 'confermato', 2: 'probabile', 3: 'una sola fonte', 4: 'fonti in disaccordo', 5: 'improbabile', 6: 'manca' };
const VOTO_INFO_LUNGO = { 1: 'confermato da una fonte indipendente (notizie lette o sito ufficiale)', 2: 'probabilmente vero (due fonti che concordano ma non sono indipendenti, o una fonte più le notizie)', 3: 'una sola fonte', 4: 'le fonti non concordano: da ricontrollare', 5: 'improbabile', 6: 'nessuna fonte lo dice' };
const VOTO_FONTE = { A: 'sito ufficiale', B: 'fonte di solito affidabile', C: 'Wikipedia e Wikidata (affidabilità media)', D: 'fonte poco affidabile', E: 'fonte non affidabile', F: 'nessuna fonte' };
function votoHtml(v) {
  if (!v) return '';
  const n = v.slice(1), cl = n <= '2' ? 'v-ok' : n === '3' ? 'v-medio' : 'v-no';
  return '<span class="voto ' + cl + '" title="' + esc((VOTO_FONTE[v[0]] || '') + ' · ' + (VOTO_INFO_LUNGO[n] || '')) + '">' + esc(v) + ' ' + esc(VOTO_INFO[n] || '') + '</span>';
}
function capiNorm(t) { return String(t || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
const CAPI_STOP = new Set(['jr', 'sr', 'of', 'bin', 'ibn', 'al', 'el', 'de', 'da', 'di', 'van', 'von', 'der', 'la', 'le', 'dos', 'das', 'del', 'the', 'sir', 'dr', 'mr', 'mrs', 'ms', 'prof', 'sheikh', 'king', 'queen', 'prince', 'emir', 'sultan', 'ii', 'iii', 'iv', 'vi', 'vii', 'x', 're', 'regina']);
function capiParole(n) { return (capiNorm(n).replace(/\(.*?\)/g, ' ').replace(/['’]/g, '').match(/[a-z]+/g) || []).filter(w => !CAPI_STOP.has(w) && !/^[ivxlcdm]{1,5}$/.test(w)); }
// la stessa parola traslitterata in modi diversi (Lukašenko e Lukashenko, Zelens'kij e Zelenskyy): come nel programma
function capiFon(w) { [['sch', 's'], ['sh', 's'], ['ch', 'c'], ['kh', 'h'], ['zh', 'z'], ['ts', 'c'], ['ks', 'x'], ['dj', 'g'], ['y', 'i'], ['j', 'i'], ['w', 'v'], ['ph', 'f'], ['ck', 'k'], ['q', 'k']].forEach(([a, b]) => { w = w.split(a).join(b); }); return w.replace(/(.)\1+/g, '$1'); }
function capiRapporto(a, b) {
  const m = [...Array(b.length + 1).keys()];
  for (let i = 1; i <= a.length; i++) { let p = m[0]; m[0] = i; for (let j = 1; j <= b.length; j++) { const t = m[j]; m[j] = Math.min(m[j] + 1, m[j - 1] + 1, p + (a[i - 1] === b[j - 1] ? 0 : 1)); p = t; } }
  return 1 - m[b.length] / Math.max(a.length, b.length, 1);
}
function capiSimili(a, b) { return [[a, b], [capiFon(a), capiFon(b)]].some(([x, y]) => x === y || (x.length >= 3 && y.length >= 3 && (x.startsWith(y) || y.startsWith(x))) || (x.length >= 4 && y.length >= 4 && capiRapporto(x, y) >= 0.8)); }
function capiStessa(a, b) {
  const x = capiParole(a), y = capiParole(b);
  if (!x.length || !y.length) return false;
  if (x.length === 1 || y.length === 1) { const [c, l] = x.length === 1 ? [x, y] : [y, x]; return l.some(w => capiSimili(c[0], w)); }
  if (x.filter(w => y.some(z => capiSimili(w, z))).length >= 2) return true;
  if (!capiSimili(x[x.length - 1], y[y.length - 1]) || x[0][0] !== y[0][0]) return false;
  return x[0].length === 1 || y[0].length === 1 || capiSimili(x[0], y[0]) || (capiFon(x[x.length - 1]) === capiFon(y[y.length - 1]) && capiRapporto(capiFon(x[0]), capiFon(y[0])) >= 0.7);
}
// una voce di Wikidata [nome, ruolo, dal, nome inglese] e un nome
function capiStessaWd(q, n) { return capiStessa(q[0], n) || (q[3] ? capiStessa(q[3], n) : false); }
// il nome compare in un testo? cognome (o due parole del nome); per i sovrani conta il nome prima di «del», «di», «of»
function capiNelTesto(nome, testo) {
  const t = ' ' + capiNorm(testo).replace(/[^a-z0-9]+/g, ' ') + ' ';
  const base = String(nome || '').split(/\s(?:del|della|di|of|de)\s/)[0];
  const p = capiParole(base).filter(w => w.length >= 3);
  if (!p.length) return true;
  const cogn = p[p.length - 1];
  if (t.includes(' ' + cogn + ' ')) {
    if (p.length === 1) return true;
    // stesso cognome, persona diversa? («Guida suprema Mojtaba Khamenei» non è Ali Khamenei): si guarda la parola prima
    const prima = [...t.matchAll(new RegExp('([a-z]{2,}) (?:[a-z] )*' + cogn + ' ', 'g'))].map(m => m[1]);
    const generiche = new Set(['governo', 'presidente', 'presidenza', 'premier', 'primo', 'ministro', 're', 'regina', 'guida', 'suprema', 'supremo', 'di', 'del', 'della', 'da', 'il', 'la', 'e', 'con', 'sig', 'signor', 'emiro', 'sultano', 'principe', 'generale', 'maresciallo', 'cancelliere', 'capo', 'leader', 'giunta', 'dal', 'dalla', 'a', 'alla', 'al']);
    if (!prima.length || prima.some(w => capiSimili(w, p[0]) || generiche.has(w) || /^[ivxlcdm]{1,5}$/.test(w))) return true;
    return false;
  }
  return p.filter(w => t.includes(' ' + w + ' ')).length >= 2;
}
function capiFonti(r) {
  const f = [];
  if ((r.wd || []).length) f.push('Wikidata');
  if ((r.wp || []).length) f.push((r.t ? '<a href="https://en.wikipedia.org/wiki/' + encodeURIComponent(r.t.replace(/ /g, '_')) + '" target="_blank" rel="noopener">Wikipedia</a>' : 'Wikipedia') + (r.wv ? ' (voce modificata il ' + potData(r.wv) + ')' : ''));
  if (r.u) f.push('sito ufficiale (' + esc(r.u) + ')');
  return f.join(', ') || 'nessuna fonte';
}
// i nomi in ordine: prima quelli di Wikipedia (con la data di Wikidata quando è la stessa persona), poi quelli solo di Wikidata
function capiNomi(r, quanti) {
  const out = [];
  (r.wp || []).slice(0, quanti).forEach(p => {
    const w = (r.wd || []).find(q => capiStessaWd(q, p[0]));
    out.push(esc(p[0]) + ' <span class="s">(' + esc(p[1] || (w && w[1]) || '') + (w && w[2] ? ', dal ' + potData(w[2]) : '') + ')</span>');
  });
  if (r.e !== 'diversi') (r.wd || []).forEach(q => { if (!(r.wp || []).some(p => capiStessaWd(q, p[0]))) out.push(esc(q[0]) + ' <span class="s">(' + esc(q[1] || '') + (q[2] ? ', dal ' + potData(q[2]) : '') + '; solo Wikidata)</span>'); });
  return out;
}
function capiDisaccordo(r) {
  if (r.e !== 'diversi') return '';
  return '<div class="s avviso-dato">⚠ ' + esc((r.p || [])[0] || 'Le fonti non concordano') + '. Wikidata: ' +
    (r.wd || []).map(q => esc(q[0]) + (q[1] ? ' (' + esc(q[1]) + (q[2] ? ', dal ' + potData(q[2]) : '') + ')' : '')).join(', ') + '.</div>';
}
// sostituisce la riga «guida» del potere (estensione 45) quando il controllo c'è
function potGuida(x) {
  caricaCapi();
  const C = window.CAPI, r = C && C.enti && x.q ? C.enti[x.q] : null;
  if (!r) return potGuidaWd(x);
  const nomi = capiNomi(r, 3);
  return (nomi.length ? 'guida: ' + nomi.join(', ') : 'chi guida: nessuna fonte lo dice') + ' ' + votoHtml(r.v) +
    ' <span class="s">controllato il ' + potData(r.d) + ' su ' + capiFonti(r) + '</span>' + capiDisaccordo(r);
}
const CAPI_RUOLI_STATO = ['presidente', 'primo ministro', 'sovrano', 'Guida suprema', 'capo di Stato', 'capo del governo', 'cancelliere', 'principe ereditario'];
// nella pagina di uno Stato, sotto «Governo»: il controllo automatico del capo di Stato e del governo
function capiStatoHtml(n, g) {
  caricaCapi();
  const C = window.CAPI, r = C && C.stati ? C.stati[n] : null;
  if (!r) return '';
  const testo = [(g && g.capo) || '', (g && g.governo) || ''].join(' ');
  const capi = [];
  (r.wd || []).forEach(q => capi.push([q[0], q[1], 'Wikidata' + (q[2] ? ', dal ' + potData(q[2]) : '')]));
  (r.wd || []).forEach((q, i) => { capi[i].push(q[3] || ''); });
  // dal riquadro di Wikipedia solo chi guida lo Stato o il governo (non i presidenti delle Camere o della Corte)
  (r.wp || []).filter(p => CAPI_RUOLI_STATO.includes(p[1])).slice(0, 2).forEach(p => { if (!capi.some(c => capiStessa(c[0], p[0]) || (c[3] && capiStessa(c[3], p[0])))) capi.push([p[0], p[1], 'Wikipedia']); });
  const mancano = testo.trim() ? capi.filter(c => !capiNelTesto(c[0], testo) && !(c[3] && capiNelTesto(c[3], testo))) : [];
  let h = '<div class="s capi-st">Controllo automatico del ' + potData(r.d) + ' ' + votoHtml(r.v) + ': ' + capiNomi(r, 2).join(', ') + ' · fonti: ' + capiFonti(r) + '.</div>';
  // chi manca secondo Wikidata, quando il testo e Wikipedia concordano su un altro nome: è Wikidata a essere indietro
  const wpTesto = (r.wp || []).filter(p => CAPI_RUOLI_STATO.includes(p[1]) && capiNelTesto(p[0], testo));
  const vecchiWd = mancano.filter(c => c[2].startsWith('Wikidata') && wpTesto.length && r.e === 'diversi' && !(r.wp || []).some(p => capiStessaWd([c[0], c[1], '', c[3]], p[0])));
  const dubbi = mancano.filter(c => !vecchiWd.includes(c));
  if (vecchiWd.length) h += '<div class="s">Wikidata indica ancora ' + vecchiWd.map(c => esc(c[0]) + ' (' + esc(c[1]) + ')').join('; ') + ': il testo qui sopra e Wikipedia concordano su ' +
    wpTesto.map(p => esc(p[0])).join(', ') + ', quindi è Wikidata a essere indietro.</div>';
  if (dubbi.length) h += '<div class="s avviso-dato">⚠ Da ricontrollare: ' + dubbi.map(c => esc(c[0]) + ' (' + esc(c[1]) + ', secondo ' + c[2] + ')').join('; ') +
    ' non compare nel testo qui sopra. Il testo può essere rimasto indietro, oppure la fonte automatica sbaglia: PanGeo lo segnala invece di scegliere.</div>';
  return h + (vecchiWd.length ? '' : capiDisaccordo(r));
}
// #potere/controllo: la salute dei dati e il modello
function capiControlloVista() {
  caricaCapi();
  const C = window.CAPI;
  let h = '<p class="note">Il modello di PanGeo per i dati che cambiano (chi guida uno Stato, un’istituzione, una banca centrale, una grande banca o un fondo):</p><ol class="plain-num">' +
    '<li>ogni dato è un’affermazione con la sua fonte, la data della fonte e la data del controllo;</li>' +
    '<li>due voti separati, come nel codice dell’Ammiragliato usato dalla NATO (AJP-2.1): la <b>fonte</b> da A (ufficiale) a F (nessuna) e l’<b>informazione</b> da 1 (confermata da una fonte indipendente) a 6 (non giudicabile). Wikidata e Wikipedia valgono C: affidabilità media;</li>' +
    '<li>due fonti che copiano l’una dall’altra contano come una: Wikidata e Wikipedia d’accordo danno al massimo 2, «probabile»; per l’1 serve una fonte indipendente (le notizie lette dal programma o il sito ufficiale);</li>' +
    '<li>ogni dato scade: si ricontrolla dopo due settimane, quelli in disaccordo dopo tre giorni;</li>' +
    '<li>quando le fonti non concordano non si sceglie in silenzio: si mostrano tutte e due, con la data;</li>' +
    '<li>quando manca, si scrive che manca e il dato passa in testa alla coda;</li>' +
    '<li>il voto vale per quella affermazione in quel momento, non per sempre: si rifà a ogni controllo.</li></ol>';
  if (!C) return h + '<p class="note">' + (CAR_CAPI.c === 3 ? 'I controlli arrivano con la versione 2.38 del programma (o con il motore nel cloud).' : 'Carico…') + '</p>';
  const S = C.salute || {}, es = S.esiti || {};
  h += '<div class="item nv-diario"><div class="nv-tiles">' + nvTile(S.totale || 0, 'voci controllate') + nvTile(es.concorde || 0, 'fonti d’accordo') +
    nvTile((es.solo_wp || 0) + (es.solo_wd || 0), 'una sola fonte') + nvTile(es.diversi || 0, 'fonti in disaccordo') + nvTile(es.manca || 0, 'nessuna fonte') + nvTile(S.vecchi || 0, 'controlli più vecchi di 30 giorni') + '</div></div>';
  const P = window.POTERE, nomi = {};
  if (P && P.sezioni) Object.keys(P.sezioni).forEach(s => ((P.sezioni[s] || {}).voci || []).forEach(x => { if (x.q) nomi[x.q] = [x.n, s]; }));
  const righe = [];
  Object.entries(C.stati || {}).forEach(([k, r]) => righe.push([stLink(k), 'Stato', r]));
  Object.entries(C.enti || {}).forEach(([q, r]) => righe.push([potWd(q, (nomi[q] || [r.t || q])[0]), ((P && P.nomi) || {})[(nomi[q] || [])[1]] || 'ente', r]));
  const gruppo = (tit, f, chiuso) => { const l = righe.filter(z => f(z[2])); if (!l.length) return ''; return (chiuso ? '<details><summary><b>' + esc(tit) + '</b> <span class="s">(' + l.length + ', tocca per aprire)</span></summary>' : '<h3>' + esc(tit) + ' <span class="s">(' + l.length + ')</span></h3>') +
    l.slice(0, 300).map(z => '<div class="item"><div class="t">' + z[0] + ' <span class="s">' + esc(z[1]) + '</span> ' + votoHtml(z[2].v) + '</div><div class="m">' +
      (capiNomi(z[2], 2).join(', ') || 'nessun nome') + ' · controllato il ' + potData(z[2].d) + '</div>' + capiDisaccordo(z[2]) +
      ((z[2].p || []).length && z[2].e !== 'diversi' ? '<div class="s">' + esc(z[2].p.join('; ')) + '</div>' : '') + '</div>').join('') + (chiuso ? '</details>' : ''); };
  h += gruppo('Fonti in disaccordo: da ricontrollare', r => r.e === 'diversi');
  h += gruppo('Nessuna fonte dice chi guida', r => r.e === 'manca', true);
  h += gruppo('Una sola fonte', r => r.e === 'solo_wp' || r.e === 'solo_wd', true);
  return h + '<p class="note">Le voci d’accordo non sono elencate qui: si vedono nelle sezioni del potere e nelle pagine degli Stati, con il loro voto.</p>';
}
// --- armi vendute e comprate (SIPRI)
const ARMI_TIPI = { 'tank': 'carro armato', 'armoured personnel carrier': 'trasporto truppe blindato', 'infantry fighting vehicle': 'veicolo da combattimento della fanteria',
  'self-propelled gun': 'obice semovente', 'self-propelled howitzer': 'obice semovente', 'towed gun': 'cannone trainato', 'multiple rocket launcher': 'lanciarazzi multiplo', 'self-propelled MRL': 'lanciarazzi multiplo semovente',
  'mortar': 'mortaio', 'self-propelled mortar': 'mortaio semovente', 'combat aircraft': 'aereo da combattimento', 'FGA aircraft': 'cacciabombardiere', 'fighter aircraft': 'caccia',
  'trainer aircraft': 'aereo addestratore', 'trainer/combat aircraft': 'addestratore e aereo da combattimento', 'transport aircraft': 'aereo da trasporto', 'tanker/transport aircraft': 'aereo cisterna e da trasporto',
  'AEW&C aircraft': 'aereo radar', 'ASW aircraft': 'aereo antisommergibile', 'MP aircraft': 'pattugliatore marittimo', 'light aircraft': 'aereo leggero', 'helicopter': 'elicottero',
  'combat helicopter': 'elicottero d’attacco', 'transport helicopter': 'elicottero da trasporto', 'light helicopter': 'elicottero leggero', 'anti-submarine helicopter': 'elicottero antisommergibile', 'ASW helicopter': 'elicottero antisommergibile',
  'UAV': 'drone', 'armed UAV': 'drone armato', 'armed drone': 'drone armato', 'loitering munition': 'munizione circuitante', 'SAM system': 'sistema antiaereo', 'surface-to-air missile': 'missile antiaereo', 'SAM': 'missile antiaereo',
  'mobile SAM system': 'sistema antiaereo mobile', 'portable SAM': 'missile antiaereo spalleggiabile', 'anti-tank missile': 'missile anticarro', 'anti-ship missile': 'missile antinave', 'BVRAAM': 'missile aria-aria a lungo raggio',
  'SRAAM': 'missile aria-aria a corto raggio', 'land-attack missile': 'missile da crociera', 'ballistic missile': 'missile balistico', 'guided bomb': 'bomba guidata', 'guided rocket': 'razzo guidato', 'anti-radar missile': 'missile antiradar',
  'air-search radar': 'radar di sorveglianza aerea', 'fire control radar': 'radar di tiro', 'combat aircraft radar': 'radar per aerei da combattimento', 'ground search radar': 'radar di sorveglianza terrestre', 'sea-search radar': 'radar di sorveglianza navale',
  'turbofan': 'motore turbofan', 'turboprop': 'motore turboelica', 'turboshaft': 'motore turboalbero', 'diesel engine': 'motore diesel', 'aircraft engine': 'motore d’aereo', 'gas turbine': 'turbina a gas',
  'frigate': 'fregata', 'corvette': 'corvetta', 'patrol craft': 'pattugliatore', 'OPV': 'pattugliatore d’altura', 'submarine': 'sottomarino', 'destroyer': 'cacciatorpediniere', 'landing ship': 'nave da sbarco',
  'aircraft carrier': 'portaerei', 'minehunter': 'cacciamine', 'support ship': 'nave d’appoggio', 'naval gun': 'cannone navale', 'anti-aircraft gun': 'cannone antiaereo', 'armoured vehicle': 'veicolo blindato',
  'APV': 'veicolo protetto',
  'long-range air-to-air missile': 'missile aria-aria a lungo raggio', 'fighter/ground-attack aircraft': 'caccia e attacco al suolo', 'surface-to-air missile system': 'sistema di missili antiaerei', 'ship engine': 'motore navale', 'vehicle engine': 'motore per veicoli', 'portable surface-to-air missile': 'missile antiaereo spalleggiabile', 'patrol boat': 'motovedetta', 'light transport aircraft': 'aereo da trasporto leggero', 'air-to-surface missile': 'missile aria-superficie', 'reconnaissance drone': 'drone da ricognizione', 'anti-ship/land-attack missile': 'missile antinave e da attacco a terra', 'anti-submarine sonar': 'sonar antisommergibile', 'guided glide bomb': 'bomba planante guidata', 'aircraft electro-optical system': 'sistema elettro-ottico per aerei', 'surface-to-surface missile': 'missile superficie-superficie', 'fire-control radar': 'radar di tiro', 'anti-ballistic missile missile': 'missile antimissile balistico', 'anti-tank/air-to-surface missile': 'missile anticarro e aria-superficie', 'patrol ship': 'nave pattugliatore', 'naval surface-to-air missile system': 'sistema antiaereo navale', 'maritime patrol aircraft radar': 'radar per pattugliatori marittimi', 'armoured recovery vehicle': 'veicolo blindato da recupero', 'anti-submarine torpedo': 'siluro antisommergibile', 'air/sea-search radar': 'radar di sorveglianza aerea e navale', '(armed) trainer aircraft': 'aereo addestratore (armato)', 'infantry fighting vehicle turret': 'torretta per veicolo da combattimento', 'short-range air-to-air missile': 'missile aria-aria a corto raggio', 'maritime patrol aircraft': 'pattugliatore marittimo', 'guided shell': 'proiettile guidato', 'one-way attack drone': 'drone d’attacco a perdere', '(armed) transport helicopter': 'elicottero da trasporto (armato)', 'artillery locating radar': 'radar controbatteria', 'anti-ship/anti-submarine torpedo': 'siluro antinave e antisommergibile', 'fire-support vehicle': 'veicolo di supporto di fuoco', 'mobile surface-to-air missile system': 'sistema antiaereo mobile', 'air refuel system': 'sistema di rifornimento in volo', 'armoured reconnaissance vehicle': 'veicolo blindato da ricognizione', '(armed) light helicopter': 'elicottero leggero (armato)', 'multi-function radar': 'radar multifunzione', 'anti-submarine aircraft': 'aereo antisommergibile', 'armoured bridgelayer': 'gettaponte blindato', 'surveillance satellite': 'satellite di sorveglianza', 'coastal defence system': 'sistema di difesa costiera', 'armoured engineer vehicle': 'veicolo blindato del genio', 'ground-attack aircraft': 'aereo da attacco al suolo', 'heavy transport aircraft': 'aereo da trasporto pesante', 'air-to-surface/surface-to-surface missile': 'missile aria-superficie e superficie-superficie', 'amphibious assault ship': 'nave d’assalto anfibio', 'armoured supply vehicle': 'veicolo blindato di rifornimento', 'missile boat': 'motocannoniera lanciamissili', 'landing craft': 'mezzo da sbarco', 'air-search/fire-control radar': 'radar di sorveglianza e di tiro', 'combat helicopter radar': 'radar per elicotteri d’attacco', 'air-to-surface/anti-ship missile': 'missile aria-superficie e antinave', 'aircraft reconnaissance system': 'sistema di ricognizione per aerei', 'airborne early-warning aircraft': 'aereo radar', 'replenishment ship': 'nave rifornitrice', 'armoured engineer/recovery vehicle': 'veicolo blindato del genio e da recupero', 'self-propelled anti-aircraft gun': 'cannone antiaereo semovente', 'air-search system': 'sistema di sorveglianza aerea', 'ground surveillance radar': 'radar di sorveglianza terrestre', 'minehunter/minesweeper': 'cacciamine e dragamine', 'ground surveillance aircraft': 'aereo di sorveglianza terrestre', 'electro-optical system': 'sistema elettro-ottico', '(armed) reconnaissance drone': 'drone da ricognizione (armato)', 'self-propelled air-defence system': 'sistema antiaereo semovente', 'airborne early-warning radar': 'radar aviotrasportato di scoperta', 'surface-to-surface missile launcher': 'lanciamissili superficie-superficie', 'tank destroyer': 'cacciacarri', 'transport ship': 'nave da trasporto', 'tank turret': 'torretta per carri', 'turbojet': 'motore turbogetto', 'signals intelligence system': 'sistema di intelligence dei segnali', 'nuclear submarine': 'sottomarino nucleare', 'anti-ballistic missile system': 'sistema antimissile balistico', 'light tank': 'carro leggero', 'bomber aircraft': 'bombardiere', 'reconnaissance aircraft': 'aereo da ricognizione', 'signals intelligence aircraft': 'aereo da intelligence dei segnali', 'training ship': 'nave scuola', 'submarine sonar': 'sonar per sottomarini', 'armoured car': 'autoblindo', 'reconnaissance satellite': 'satellite da ricognizione', 'communications satellite': 'satellite per comunicazioni', 'ASW torpedo': 'siluro antisommergibile', 'anti-ship torpedo': 'siluro' };
function armiTipo(t) { return ARMI_TIPI[t] || t || ''; }
function armiSt(n) { return STATI[n] ? stLink(n) : esc(n); }
function armiNum(v) { return v == null ? '' : Number(v).toLocaleString('it-IT', { maximumFractionDigits: v < 10 ? 1 : 0 }); }
function armiRiga(a, lato) {
  const altro = lato === 0 ? a[1] : a[0];
  const cons = a[6] ? 'consegnati ' + esc(a[6]) + (a[7] ? ' (' + esc(a[7]) + ')' : '') : 'non ancora consegnati';
  return '<div class="item"><div class="t">' + esc(a[3] || '?') + ' × ' + esc(a[4]) + ' <span class="s">' + esc(armiTipo(a[5])) + '</span></div><div class="m">' +
    [(lato === 0 ? 'da ' : lato === 1 ? 'a ' : '') + (lato === 2 ? armiSt(a[1]) + ' → ' + armiSt(a[0]) : armiSt(altro)), a[2] ? 'ordine del ' + a[2] : '', cons,
      a[8] === 'U' ? 'usati' : a[8] === 'M' ? 'usati e ammodernati' : '', a[10] ? 'volume ' + armiNum(a[10]) + ' milioni di TIV' : ''].filter(Boolean).join(' · ') + '</div>' +
    (a[9] ? '<div class="s">' + esc(a[9]) + '</div>' : '') + '</div>';
}
function armiSomme(l, i) {
  const s = {}; l.forEach(a => { s[a[i]] = (s[a[i]] || 0) + (a[11] || 0); });
  return Object.entries(s).sort((x, y) => y[1] - x[1]);
}
function armiNota(A) {
  return '<p class="note">Fonte: <a href="' + safeU(A.link) + '" target="_blank" rel="noopener">SIPRI Arms Transfers Database</a> (© SIPRI), affari attivi dal ' + A.da + ' al ' + A.anno +
    ', letti il ' + potData(A.agg) + '. Solo armi convenzionali maggiori (aerei, navi, carri, artiglieria, missili, radar, motori): niente armi leggere né munizioni. I TIV misurano il volume delle armi, non il prezzo pagato. Uso non commerciale con citazione della fonte.</p>';
}
function armiStatoHtml(n) {
  caricaArmi();
  const A = window.ARMI;
  let h = '<h3 id="st-armi"><span class="dot" style="background:var(--aziende)"></span>Armi comprate e vendute</h3>';
  if (!A) return CAR_ARMI.c === 3 ? '' : h + '<p class="note">Carico il registro SIPRI…</p>';
  const comp = A.affari.filter(a => a[0] === n), vend = A.affari.filter(a => a[1] === n);
  if (!comp.length && !vend.length) return h + '<p class="note">SIPRI non registra trasferimenti di armi maggiori da o verso questo Stato tra il ' + A.da + ' e il ' + A.anno + '.</p>';
  const somma = (l, i) => armiSomme(l, i).slice(0, 8).map(([st, v]) => armiSt(st) + ' <span class="s">' + armiNum(v) + '</span>').join(', ');
  const r = [];
  if (comp.length) r.push(['Ha comprato da', somma(comp, 1) + ' <span class="s">(milioni di TIV consegnati)</span>'], ['Ordini aperti', String(comp.filter(a => !a[6]).length) + ' non ancora consegnati']);
  if (vend.length) r.push(['Ha venduto a', somma(vend, 0)]);
  h += '<div class="item"><dl class="kv">' + r.map(x => '<dt>' + esc(x[0]) + '</dt><dd>' + x[1] + '</dd>').join('') + '</dl></div>';
  const top = l => l.slice().sort((x, y) => (y[10] || 0) - (x[10] || 0)).slice(0, 6);
  if (comp.length) h += '<div class="m">I più grandi acquisti</div>' + top(comp).map(a => armiRiga(a, 0)).join('');
  if (vend.length) h += '<div class="m">Le più grandi vendite</div>' + top(vend).map(a => armiRiga(a, 1)).join('');
  return h + '<p class="note"><a href="#armi/' + encodeURIComponent(n) + '">Tutti i ' + (comp.length + vend.length) + ' affari</a>. Fonte: SIPRI (© SIPRI), dal ' + A.da + ' al ' + A.anno + '; i TIV misurano il volume, non il prezzo.</p>';
}
function viewArmi(n) {
  caricaArmi();
  const A = window.ARMI;
  n = n ? decodeURIComponent(n) : '';
  crumbs(n ? [['#armi', 'Armi vendute e comprate'], ['', n]] : [['', 'Armi vendute e comprate']]);
  let h = '<h2>' + (n ? 'Armi vendute e comprate: ' + esc(n) : 'Armi vendute e comprate') + '</h2>';
  if (!A) return h + '<p class="note">' + (CAR_ARMI.c === 3 ? 'Il registro SIPRI arriva con la versione 2.38 del programma.' : 'Carico il registro SIPRI…') + '</p>';
  if (n) {
    const comp = A.affari.filter(a => a[0] === n), vend = A.affari.filter(a => a[1] === n);
    const ord = l => l.slice().sort((x, y) => (y[2] || 0) - (x[2] || 0) || (y[10] || 0) - (x[10] || 0));
    h += (STATI[n] ? '<p class="note">' + stLink(n) + '</p>' : '');
    if (comp.length) h += '<h3>Comprate <span class="s">(' + comp.length + ')</span></h3>' + ord(comp).map(a => armiRiga(a, 0)).join('');
    if (vend.length) h += '<h3>Vendute <span class="s">(' + vend.length + ')</span></h3>' + ord(vend).map(a => armiRiga(a, 1)).join('');
    if (!comp.length && !vend.length) h += '<p class="note">Nessun affare registrato.</p>';
    return h + armiNota(A);
  }
  const vend = armiSomme(A.affari, 1), comp = armiSomme(A.affari, 0);
  const tot = vend.reduce((s, x) => s + x[1], 0) || 1;
  const lista = (l, titolo) => '<h3>' + titolo + '</h3><div class="item">' + l.slice(0, 25).map(([st, v], i) => '<div>' + (i + 1) + '. <a href="#armi/' + encodeURIComponent(st) + '">' + esc(st) + '</a> <span class="s">' +
    armiNum(v) + ' milioni di TIV · ' + (100 * v / tot).toLocaleString('it-IT', { maximumFractionDigits: 1 }) + '%</span></div>').join('') + '</div>';
  h += '<p class="note">Chi vende che cosa a chi: ' + A.affari.length.toLocaleString('it-IT') + ' affari attivi negli ultimi dieci anni, di cui ' + A.affari.filter(a => !a[6]).length.toLocaleString('it-IT') + ' ordini non ancora consegnati.</p>';
  h += lista(vend, 'Chi vende di più (volume consegnato)') + lista(comp, 'Chi compra di più');
  const aperti = A.affari.filter(a => !a[6]).sort((x, y) => (y[10] || 0) - (x[10] || 0)).slice(0, 25);
  if (aperti.length) h += '<h3>I più grandi ordini non ancora consegnati</h3>' + aperti.map(a => armiRiga(a, 2)).join('');
  return h + armiNota(A);
}
// nella pagina di un sistema d'arma: chi l'ha comprato e da chi, secondo SIPRI (si riconosce dal nome e dagli alias)
function armiCompatto(t) { return capiNorm(t).replace(/[^a-z0-9]/g, ''); }
function armiSistemaHtml(S) {
  caricaArmi();
  const A = window.ARMI;
  if (!A || !S) return '';
  const nomi = [S.nome].concat(S.alias || []).map(armiCompatto).filter(x => x.length >= 3);
  const l = A.affari.filter(a => { const d = armiCompatto(a[4]); return nomi.some(x => x.length >= 4 ? d.includes(x) : d.startsWith(x)); });
  if (!l.length) return '';
  const per = armiSomme(l, 0);
  return '<h3>Chi lo ha comprato <span class="s">(SIPRI, ' + A.da + '–' + A.anno + ')</span></h3><div class="item"><div class="m">' + per.slice(0, 30).map(([st]) => armiSt(st)).join(', ') + '</div></div>' +
    l.slice().sort((x, y) => (y[2] || 0) - (x[2] || 0)).slice(0, 12).map(a => armiRiga(a, 2)).join('') +
    '<p class="note">Riconosciuto dal nome nel registro SIPRI (' + l.length + ' affari): un nome simile può confondere varianti diverse. Fonte: SIPRI (© SIPRI).</p>';
}
// --- i fatti dentro gli articoli
function fattiStatoHtml(n) {
  caricaFatti();
  const F = window.FATTI, l = F && F.stati ? (F.stati[n] || []) : [];
  if (!l.length) return '';
  return '<h3 id="st-fattiart"><span class="dot" style="background:var(--muted)"></span>Fatti dagli articoli <span class="s">(' + l.length + ')</span></h3>' +
    l.slice(0, 15).map(f => '<div class="item"><div class="t">' + esc(f[1]) + ': ' + esc(f[2]) + (f[3] ? ' · <b>' + esc(f[3]) + '</b>' : '') + '</div><div class="m">' +
      [potData(f[0]), f[4] ? esc(f[4]) : '', f[5] ? 'quando: ' + esc(f[5]) : '', f[7] ? '<a href="' + safeU(f[7]) + '" target="_blank" rel="noopener">' + esc(f[6] || 'fonte') + '</a>' : esc(f[6] || '')].filter(Boolean).join(' · ') + '</div></div>').join('') +
    '<p class="note">Il cervello legge gli articoli delle notizie confermate e ne tira fuori chi, che cosa, quanti, dove e quando. Ogni fatto ha la frase dell’articolo che lo dice: il programma la cerca parola per parola nel testo e scarta il fatto se non c’è o se un numero non torna. La frase resta sul telefono; qui il fatto e il link alla fonte, da leggere.</p>';
}


// Trentesima estensione (19 novembre 2026): sezione Intelligence. Solo informazioni pubbliche con la fonte: i servizi di
// ogni Stato (elenco da Wikipedia e Wikidata), le relazioni che i servizi pubblicano, le alleanze di scambio, gli archivi
// declassificati e i fatti che il programma trova sulla stampa (terzo tema del lavoro a piano, dalla 2.22).
// Mai nomi di agenti o di persone private, mai indirizzi delle sedi, mai metodi o dettagli operativi.
const INTEL = /*INTEL_JSON*/;
const INTEL_REL = [
  ['Italia', 'Sistema di informazione per la sicurezza della Repubblica (DIS)', 'Relazione annuale sulla politica dell’informazione per la sicurezza', 'https://www.sicurezzanazionale.gov.it/'],
  ['USA', 'Direttore dell’intelligence nazionale (ODNI)', 'Annual Threat Assessment, la valutazione annuale delle minacce', 'https://www.dni.gov/'],
  ['Regno Unito', 'Comitato parlamentare per l’intelligence e la sicurezza (ISC)', 'Rapporto annuale', 'https://isc.independent.gov.uk/'],
  ['Germania', 'Ufficio federale per la protezione della Costituzione (BfV)', 'Verfassungsschutzbericht, il rapporto annuale', 'https://www.verfassungsschutz.de/'],
  ['Paesi Bassi', 'Servizio generale di intelligence e sicurezza (AIVD)', 'Relazione annuale', 'https://english.aivd.nl/'],
  ['Norvegia', 'Servizio di intelligence (Etterretningstjenesten)', 'Fokus, la valutazione annuale', 'https://www.etterretningstjenesten.no/'],
  ['Norvegia', 'Servizio di sicurezza della polizia (PST)', 'Valutazione nazionale delle minacce', 'https://www.pst.no/'],
  ['Svezia', 'Servizio di sicurezza (Säpo)', 'Annuario', 'https://www.sakerhetspolisen.se/'],
  ['Danimarca', 'Servizio di intelligence della difesa (FE)', 'Udsyn, la valutazione annuale dei rischi', 'https://www.fe-ddis.dk/'],
  ['Finlandia', 'Servizio di sicurezza e intelligence (Supo)', 'Rassegna sulla sicurezza nazionale', 'https://supo.fi/'],
  ['Estonia', 'Servizio informazioni estero (Välisluureamet)', 'International Security and Estonia, rapporto annuale', 'https://www.valisluureamet.ee/'],
  ['Estonia', 'Servizio di sicurezza interna (KAPO)', 'Rassegna annuale', 'https://kapo.ee/'],
  ['Lettonia', 'Ufficio per la protezione della Costituzione (SAB)', 'Relazione annuale', 'https://www.sab.gov.lv/'],
  ['Lituania', 'Dipartimento per la sicurezza dello Stato (VSD)', 'Valutazione nazionale delle minacce', 'https://www.vsd.lt/'],
  ['Repubblica Ceca', 'Servizio informazioni di sicurezza (BIS)', 'Relazione annuale', 'https://www.bis.cz/'],
  ['Svizzera', 'Servizio delle attività informative della Confederazione (SIC)', 'La sicurezza della Svizzera, rapporto annuale', 'https://www.vbs.admin.ch/'],
  ['Belgio', 'Sicurezza dello Stato (VSSE)', 'Rapporto annuale', 'https://www.vsse.be/'],
  ['Spagna', 'Dipartimento della sicurezza nazionale (DSN)', 'Informe Anual de Seguridad Nacional', 'https://www.dsn.gob.es/'],
  ['Nuova Zelanda', 'Servizio di intelligence per la sicurezza (NZSIS)', 'Valutazione annuale delle minacce', 'https://www.nzsis.govt.nz/'],
  ['Giappone', 'Agenzia d’informazione per la pubblica sicurezza (PSIA)', 'Rassegna annuale della situazione interna ed esterna', 'https://www.moj.go.jp/psia/']
];
const INTEL_SCAMBI = [
  { n: 'Five Eyes', d: 'Nato dall’accordo UKUSA del 1946: scambio di intelligence dei segnali fra cinque Paesi di lingua inglese.', m: () => ['USA', 'Regno Unito', 'Canada', 'Australia', 'Nuova Zelanda'], u: 'https://it.wikipedia.org/wiki/Five_Eyes' },
  { n: 'Club di Berna', d: 'Tavolo informale dei servizi di sicurezza dei Paesi dell’Unione europea, con Norvegia e Svizzera. Esiste dal 1971.', m: () => ALLEANZE.UE.m.concat(['Norvegia', 'Svizzera']), u: 'https://en.wikipedia.org/wiki/Club_de_Berne' },
  { n: 'INTCEN, Unione europea', d: 'Centro di situazione e di intelligence dell’UE, dentro il Servizio europeo per l’azione esterna: analisi su fonti aperte e sui contributi dei servizi degli Stati membri.', m: () => ALLEANZE.UE.m, u: 'https://it.wikipedia.org/wiki/Centro_di_situazione_e_di_intelligence_dell%27Unione_europea' },
  { n: 'NATO', d: 'Divisione congiunta Intelligence e sicurezza del quartier generale e Centro di fusione dell’intelligence, nel Regno Unito.', m: () => ALLEANZE.NATO.m, u: 'https://en.wikipedia.org/wiki/NATO_Intelligence_Fusion_Centre' },
  { n: 'Struttura antiterrorismo della SCO', d: 'Organismo dell’Organizzazione di Shanghai, con sede a Tashkent: scambio di informazioni fra i servizi di sicurezza degli Stati membri.', m: () => ALLEANZE.SCO.m, u: 'https://en.wikipedia.org/wiki/Regional_Anti-Terrorist_Structure' }
];
const INTEL_ARCH = [
  ['CIA, sala di lettura', 'Documenti della CIA resi pubblici per legge (FOIA), cercabili per parola.', 'https://www.cia.gov/readingroom/'],
  ['Dipartimento di Stato USA, serie FRUS', 'La raccolta ufficiale dei documenti di politica estera degli Stati Uniti, declassificati dopo decenni.', 'https://history.state.gov/historicaldocuments'],
  ['National Security Archive', 'Archivio della George Washington University: documenti ottenuti con richieste di accesso agli atti.', 'https://nsarchive.gwu.edu/'],
  ['Archivi della NATO', 'Documenti dell’Alleanza resi pubblici, in rete.', 'https://archives.nato.int/'],
  ['Archivi nazionali del Regno Unito', 'Catalogo dei fascicoli pubblici, compresi quelli dei servizi versati all’archivio.', 'https://discovery.nationalarchives.gov.uk/']
];
const INTEL_TIPO = { nomina: ['nomina', '--accent'], legge: ['legge o riforma', '--st1'], relazione: ['relazione pubblica', '--st1'], espulsione: ['espulsione', '--st3'], processo: ['processo o arresto', '--st3'], accordo: ['accordo di scambio', '--b-nato'], allarme: ['allarme pubblico', '--st2'], altro: ['altro', '--muted'] };
const INTEL_REGOLE = 'Qui entrano solo informazioni pubbliche, ognuna con la sua fonte. Restano fuori i nomi di agenti e di persone private, gli indirizzi delle sedi, i metodi e i dettagli operativi.';
const INTEL_NOTA_ELENCO = 'Elenco fatto in automatico da Wikipedia e Wikidata il ' + pianoData(INTEL.agg) + ' e poi ripulito a mano: può contenere errori o lasciare fuori qualcosa. Fa fede il sito ufficiale.';
const INTEL_NOTA_FATTI = 'Sono titoli di giornale letti dal programma, non atti ufficiali. Un’accusa resta un’accusa finché non c’è una sentenza: prima di usarli vanno confermati alla fonte.';
PIANO_TIPO.intelligence = 'servizi di intelligence';
function intelDi(nome) { return INTEL.stati[nome] || []; }
function intelScambiDi(nome) { return INTEL_SCAMBI.filter(a => a.m().includes(nome)); }
function intelServizio(x) { return '<li><a href="' + safeU(x[2]) + '" target="_blank" rel="noopener">' + esc(x[0]) + '</a>' + (x[1] ? ' <span class="s">dal ' + esc(x[1]) + '</span>' : '') + (x[3] ? ' · <a href="' + safeU(x[3]) + '" target="_blank" rel="noopener">sito ufficiale</a>' : '') + '</li>'; }
function intelFatto(x, stato) { const t = INTEL_TIPO[x.tipo] || INTEL_TIPO.altro; return '<div class="item"><div class="t"><span class="dot" style="background:var(--numeri)"></span> ' + esc(x.cosa) + '</div><div class="m">' + [stato ? stLink(stato, 'intelligence') : '', esc(pianoData(x.d)), x.ente ? esc(x.ente) : ''].filter(Boolean).join(' · ') + '</div><div class="s"><span class="badge" style="--c:var(' + t[1] + ')">' + esc(t[0]) + '</span> ' + ((x.f || []).length > 1 ? 'più fonti' : 'una fonte') + ': ' + pianoFonti(x.f) + '</div></div>'; }
function intelRel(r, conStato) { return '<li>' + (conStato ? '<b>' + stLink(r[0], 'intelligence') + '</b> · ' : '') + '<a href="' + safeU(r[3]) + '" target="_blank" rel="noopener">' + esc(r[2]) + '</a> <span class="s">' + esc(r[1]) + '</span></li>'; }
function intelStatoHtml(nome) {
  const l = intelDi(nome), rel = INTEL_REL.filter(r => r[0] === nome), sc = intelScambiDi(nome), f = pianoDi(nome, 'intel'), P = pianoDati();
  let h = '';
  if (l.length) h += '<div class="item"><div class="t">Servizi di informazione e di sicurezza</div><ul class="plain">' + l.map(intelServizio).join('') + '</ul><div class="s">' + esc(INTEL_NOTA_ELENCO) + '</div></div>';
  if (rel.length) h += '<div class="item"><div class="t">Che cosa pubblicano</div><ul class="plain">' + rel.map(r => intelRel(r, false)).join('') + '</ul><div class="s">Sono documenti ufficiali: dicono ciò che il servizio sceglie di rendere pubblico.</div></div>';
  if (sc.length) h += '<div class="item"><div class="t">Scambio di informazioni con altri Stati</div><ul class="plain">' + sc.map(a => '<li><a href="' + safeU(a.u) + '" target="_blank" rel="noopener">' + esc(a.n) + '</a>: ' + esc(a.d) + '</li>').join('') + '</ul></div>';
  if (f.length) h += '<h4 style="margin:16px 0 4px">Fatti recenti dalla stampa, trovati dal programma</h4>' + f.map(x => intelFatto(x, '')).join('') + '<p class="note">' + esc(INTEL_NOTA_FATTI) + '</p>';
  else h += '<p class="note">' + (P && P.stati[nome] && P.stati[nome].intel ? 'Nei titoli letti finora il programma non ha trovato fatti sui servizi di ' + esc(nome) + '.' : 'Il programma non è ancora passato da ' + esc(nome) + ' con le domande sull’intelligence: comincia con la versione 2.22.') + '</p>';
  return h + '<p class="note">' + esc(INTEL_REGOLE) + ' <a href="#intelligence">Tutta la sezione Intelligence →</a></p>';
}
function intelFattiTutti() {
  const P = pianoDati(), l = [];
  if (P) Object.keys(P.stati).forEach(s => (P.stati[s].intel || []).forEach(x => l.push([s, x])));
  return l.sort((a, b) => String(b[1].d || '').localeCompare(String(a[1].d || '')));
}
function intelSezionePiano(s) { const l = s.intel || []; return '<h3>Intelligence (' + l.length + ')</h3>' + (l.map(x => intelFatto(x, '')).join('') || '<p class="note">' + (s.intel ? 'Nessun fatto sui servizi nei titoli letti.' : 'Le domande sull’intelligence cominciano con la versione 2.22 del programma.') + '</p>'); }
function viewIntelligence(slug) {
  const nome = slug ? Object.keys(STATI).find(n => STATI[n].slug === slug) : '';
  crumbs(nome ? [['#intelligence', 'Intelligence'], ['', nome]] : [['', 'Intelligence']]);
  if (nome) return '<h2>Intelligence: ' + esc(nome) + '</h2>' + intelStatoHtml(nome) + '<p class="note">' + stLink(nome) + '</p>';
  const stati = Object.keys(INTEL.stati).sort((a, b) => a.localeCompare(b, 'it')), nServ = stati.reduce((t, s) => t + INTEL.stati[s].length, 0), fatti = intelFattiTutti(), R = pianoRias();
  let h = '<h2>Intelligence</h2><p class="note">I servizi di informazione e di sicurezza di ogni Stato, che cosa pubblicano, con chi scambiano informazioni e che cosa ne scrive la stampa. ' + esc(INTEL_REGOLE) + '</p>';
  h += '<div class="item nv-diario"><div class="nv-tiles">' + nvTile(stati.length, 'Stati con almeno un servizio in elenco') + nvTile(num(nServ), 'servizi in elenco') + nvTile(INTEL_REL.length, 'relazioni ufficiali da leggere') + nvTile(num(fatti.length || (R && R.intel) || 0), 'fatti trovati dal programma sulla stampa') + '</div></div>';
  h += '<h3>Fatti recenti dalla stampa</h3>' + (fatti.length ? fatti.slice(0, 15).map(x => intelFatto(x[1], x[0])).join('') + '<p class="note">' + esc(INTEL_NOTA_FATTI) + (fatti.length > 15 ? ' Qui i 15 più recenti su ' + fatti.length + ': gli altri sono nelle schede degli Stati.' : '') + '</p>'
    : '<div class="item"><div class="x">' + (R && R.intel ? 'Il programma ne ha trovati ' + R.intel + ': l’elenco, Stato per Stato, è sul telefono e sul sito.' : 'Ancora nessuno. Il programma li cerca dalla versione 2.22, uno Stato alla volta dentro il lavoro a piano: per ogni Stato fa una domanda in inglese e una nella lingua del posto, legge i titoli e ne tira fuori nomine, leggi, relazioni pubblicate, espulsioni e processi, ognuno con la sua fonte.') + '</div><div class="s"><a href="#piano">Lavoro a piano →</a></div></div>');
  h += '<h3>Che cosa pubblicano i servizi</h3><div class="item"><div class="x">È l’intelligence di oggi firmata da chi la fa: valutazioni annuali delle minacce e relazioni al Parlamento. Sono documenti ufficiali, quindi dicono ciò che il servizio sceglie di rendere pubblico.</div><ul class="plain">' + INTEL_REL.map(r => intelRel(r, true)).join('') + '</ul></div>';
  h += '<h3>Con chi scambiano informazioni</h3>' + INTEL_SCAMBI.map(a => '<div class="item"><div class="t"><a href="' + safeU(a.u) + '" target="_blank" rel="noopener">' + esc(a.n) + '</a></div><div class="x">' + esc(a.d) + '</div><div class="members">' + a.m().map(s => stLink(s, 'intelligence')).join('') + '</div></div>').join('');
  h += '<h3>I servizi, Stato per Stato</h3><div class="members">' + stati.map(s => '<a href="#stati/' + (STATI[s] ? STATI[s].slug : '') + '/intelligence">' + esc(s) + ' <span class="s">' + INTEL.stati[s].length + '</span></a>').join('') + '</div><p class="note">' + esc(INTEL_NOTA_ELENCO) + ' Per gli Stati che qui mancano non c’è una voce pubblica nell’elenco di partenza.</p>';
  h += '<h3>Archivi da consultare a mano</h3><div class="item"><div class="t">Documenti resi pubblici dagli Stati</div><ul class="plain">' + INTEL_ARCH.map(a => '<li><a href="' + safeU(a[2]) + '" target="_blank" rel="noopener">' + esc(a[0]) + '</a>: ' + esc(a[1]) + '</li>').join('') + '</ul></div>';
  h += '<div class="item"><div class="t">Documenti trapelati: WikiLeaks</div><div class="x">Non sono documenti resi pubblici dagli Stati: sono stati trafugati e pubblicati senza contesto e senza replica, e contengono nomi di persone private. Quasi tutti sono vecchi di anni: servono per la storia, non per le notizie di oggi. Un documento autentico non prova che ciò che dice sia vero.</div><div class="s">Il collegamento per cercarli è nella cartella «Storia» di ogni Stato. Il programma non li legge da solo.</div></div>';
  return h;
}
function caricaDiario() {
  // sul sito pubblico i dati completi arrivano ogni 3 ore, il diario dopo ogni giro: l'avviso «fermo» guarda il diario
  if (!APP_OK || typeof fetch !== 'function') return;
  fetch('diario.json?v=' + Date.now()).then(r => r.ok ? r.json() : null).then(d => { if (Array.isArray(d) && d.length && d[d.length - 1].iso) { window.DIARIO_ULT = d[d.length - 1]; render(); } }).catch(() => {});
}

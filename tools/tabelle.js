// Esporta tutti i dati di PanGeo in tabelle aperte (CSV e JSON) con data e fonti, più una pagina tabelle.html
// che si legge senza login: sul telefono (127.0.0.1:8080/tabelle.html) e sul sito GitHub Pages.
// Uso: node tools/tabelle.js index.html cartella_uscita
const fs = require('fs'), vm = require('vm'), path = require('path');
const [, , base, dest] = process.argv;
const h = fs.readFileSync(base, 'utf8');
const s0 = h.indexOf('<script>') + 8, js = h.slice(s0, h.indexOf('</script>', s0));
const el = () => ({ innerHTML: '', value: '', style: {}, dataset: {}, addEventListener() {}, setAttribute() {}, appendChild() {}, querySelectorAll() { return []; }, classList: { add() {}, remove() {}, toggle() {} } });
const ctx = { console, setTimeout, clearTimeout, encodeURIComponent, decodeURIComponent, document: { querySelector: () => el(), getElementById: () => null, querySelectorAll: () => [], createElement: el, head: el(), body: el(), addEventListener() {} }, location: { hash: '', protocol: 'https:', hostname: 'x.org' }, navigator: {}, localStorage: { getItem() { return null; }, setItem() {} }, addEventListener() {}, scrollTo() {}, matchMedia: () => ({ matches: false, addEventListener() {} }) };
ctx.window = ctx; vm.createContext(ctx); vm.runInContext(js, ctx);
const G = n => vm.runInContext('typeof ' + n + ' !== "undefined" ? ' + n + ' : null', ctx);
const F = G('F'), oggi = new Date().toISOString().slice(0, 10);
const fonte = k => { const v = F[k]; if (!v) return ''; return Array.isArray(v) ? v[0] + ' <' + v[1] + '>' : String(v); };
const fonti = ks => (ks || []).map(k => /^https?:/.test(k) ? '<' + k + '>' : fonte(k)).filter(Boolean).join(' ; ');
const cella = v => { v = v == null ? '' : String(v).replace(/\s+/g, ' ').trim(); return /[",;\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
fs.mkdirSync(path.join(dest, 'tabelle'), { recursive: true });
const indice = [];
function tabella(nome, titolo, descr, colonne, righe) {
  if (!righe.length) return;
  const csv = '\ufeff' + [colonne, ...righe].map(r => r.map(cella).join(',')).join('\r\n') + '\r\n';
  fs.writeFileSync(path.join(dest, 'tabelle', nome + '.csv'), csv);
  fs.writeFileSync(path.join(dest, 'tabelle', nome + '.json'), JSON.stringify({ titolo, aggiornata: oggi, colonne, righe }));
  indice.push({ nome, titolo, descr, righe: righe.length, colonne });
}
const SCHEDE = G('SCHEDE'), P = G('P'), PROPR = G('PROPR') || {}, APPALTI = G('APPALTI') || [], PMC = G('PMC') || [], UNITA = G('UNITA') || [], FORZE = G('FORZE') || {}, FZ = G('FZ_CAMPI') || [], SITI = G('SITI') || {}, FONTI = G('FONTI') || [], WD = G('WD_BASI') || {}, POP = G('POPWB') || {};
const coer = n => { try { const c = vm.runInContext('coerenza(' + JSON.stringify(n) + ')', ctx); return c ? c.txt : ''; } catch (e) { return ''; } };
const STAB = { 1: 'stabile', 2: 'tensioni', 3: 'instabile', 4: 'crisi o guerra' };
tabella('stati', 'Stati: governo, stabilità, riserve', 'Una riga per Stato: capo dello Stato, governo, sistema, stabilità (1–4), riserve, trattati, fonti.',
  ['Stato', 'Capo dello Stato', 'Governo', 'Sistema', 'Stabilità (1–4)', 'Stabilità, perché', 'Riserve', 'Trattati', 'Fonti'],
  Object.entries(SCHEDE).map(([n, s]) => [n, (s.gov || {}).capo, (s.gov || {}).governo, (s.gov || {}).sistema, (s.stab || [])[0] ? (s.stab[0] + ' ' + STAB[s.stab[0]]) : '', (s.stab || [])[1], s.ris, (s.tr || []).join(' | '), fonti([...(s.f || []), ...(s.rf || [])])]));
tabella('notizie_stati', 'Notizie per Stato (datate)', 'Le notizie verificate dentro le schede degli Stati, con data e fonti.',
  ['Stato', 'Data', 'Notizia', 'Fonti'], Object.entries(SCHEDE).flatMap(([n, s]) => (s.nz || []).map(z => [n, z[0], z[1], fonti(z[2])])));
tabella('storia_stati', 'Storia militare e politica per Stato', 'Date chiave di ogni Stato.',
  ['Stato', 'Anno', 'Fatto'], Object.entries(SCHEDE).flatMap(([n, s]) => (s.st || []).map(z => [n, z[0], z[1]])));
tabella('basi', 'Basi e presenze militari (livello città)', 'Basi nazionali e straniere, solo a livello di città o regione. «Wikidata» indica se la voce è confermata anche dalla banca dati aperta Wikidata.',
  ['Stato ospite · città', 'Chi la usa', 'Nome', 'Che cosa è', 'Coordinate del centro città (lon, lat)', 'Anche in Wikidata', 'Fonti'],
  P.filter(x => x.l === 'basi').map(x => [x.p, x.o, x.n, x.t, (x.c || []).join(' '), WD[x.n] ? 'sì <https://www.wikidata.org/wiki/' + WD[x.n] + '>' : '', fonti(x.f)]));
tabella('punti_mappa', 'Conflitti, stretti, aziende, proteste sulla mappa', 'Gli altri punti del planisfero.',
  ['Tipo', 'Dove', 'Nome', 'Descrizione', 'Fonti'], P.filter(x => x.l !== 'basi').map(x => [x.l, x.p, x.n, x.t, fonti(x.f)]));
tabella('aziende_proprieta', 'Aziende della difesa: chi le possiede', 'Soci e quote, controllo e proprietà finale, con la data del dato e la fonte. Sintesi neutre, non consigli di investimento.',
  ['Azienda', 'Socio', 'Quota', 'Nota', 'Flottante', 'Controllo', 'Proprietà finale', 'Borsa', 'Data del dato', 'Da verificare', 'Fonti'],
  Object.entries(PROPR).flatMap(([n, p]) => (p.q && p.q.length ? p.q : [['', '', '']]).map(q => [n, q[0], q[1], q[2], p.fl, p.c, p.fin, p.b, p.d, p.v || '', fonti(p.f)])));
tabella('appalti', 'Appalti e contratti della difesa', 'Grandi contratti firmati o annunciati, soprattutto nel 2026. Le vendite USA «DSCA» sono autorizzazioni, non contratti firmati.',
  ['Data', 'Stato acquirente', 'Oggetto', 'Fornitore (Stato)', 'Valore', 'Fonti'], APPALTI.map(a => [a[0], a[1], a[2], a[3], a[4], fonti(a[5])]));
tabella('sicurezza_privata', 'Sicurezza privata e mercenari', 'Una riga per ogni Paese in cui opera una compagnia. Accuse sempre con la replica.',
  ['Nome', 'Tipo', 'Stato d’origine', 'Sede', 'Chi la controlla', 'Dimensione', 'Dove opera', 'Anni', 'Che cosa fa lì', 'Fonti di questa riga', 'Accuse e repliche', 'Fonti generali'],
  PMC.flatMap(x => (x.dove && x.dove.length ? x.dove : [['', '', '', []]]).map(d => [x.n, x.tipo, x.orig, x.sede, x.prop, x.dim, d[0], d[1], d[2], fonti(d[3]), (x.acc || []).map(a => a[0] + ' – Replica: ' + (a[1] || 'nessuna')).join(' | '), fonti(x.f)])));
tabella('unita', 'Guardie nazionali, forze speciali, unità d’élite', 'Quadro generale e pubblico: niente dettagli operativi.',
  ['Stato', 'Unità', 'Tipo', 'Da chi dipende', 'Compito', 'Dimensione stimata', 'Sede', 'Fonti'], UNITA.map(u => [u[0], u[1], u[2], u[3], u[4], u[5], u[6], fonti(u[7])]));
const NOMI = { att: 'Militari attivi', ris: 'Riservisti', par: 'Paramilitari', es: 'Esercito', ma: 'Marina', ae: 'Aeronautica', pop: 'Popolazione', disp: 'In età da servizio', ido: 'Idonei', leva: 'Nuovi in età militare ogni anno', aerei: 'Aerei ed elicotteri', caccia: 'Caccia', attacco: 'Aerei d’attacco', trasp: 'Aerei da trasporto', elic: 'Elicotteri', elat: 'Elicotteri d’attacco', carri: 'Carri armati', blind: 'Blindati', semov: 'Artiglieria semovente', train: 'Artiglieria trainata', mlrs: 'Lanciarazzi', navi: 'Navi', porta: 'Portaerei', portael: 'Portaelicotteri', cct: 'Cacciatorpediniere', freg: 'Fregate', corv: 'Corvette', sott: 'Sottomarini', patt: 'Pattugliatori', mine: 'Cacciamine', bil: 'Bilancio difesa ($)' };
tabella('forze', 'Uomini e mezzi per Stato (stime)', 'Stime di Global Firepower 2026 con la data di revisione della scheda, giovani maschi 15–24 anni (Banca Mondiale) e coerenza con la serie storica 2008–2020.',
  ['Stato', ...FZ.map(k => NOMI[k] || k), 'Scheda rivista il', 'Giovani maschi 15–24', 'Coerenza con i dati storici', 'Fonti'],
  Object.entries(FORZE).map(([n, a]) => [n, ...a.slice(0, FZ.length), a[FZ.length], (POP[n] || [])[2] || '', coer(n), fonte('qd_gfp') + ' ; ' + fonte('qd_wb') + ' ; scheda <https://www.globalfirepower.com/country-military-strength-detail.php?country_id=' + a[FZ.length + 1] + '>']));
tabella('siti_ufficiali', 'Siti ufficiali di forze armate e polizie', 'Indirizzi provati il 18 novembre 2026. Sono la voce dello Stato: fonti di parte.',
  ['Stato', 'Ente', 'Sito'], Object.entries(SITI).flatMap(([n, l]) => l.map(x => [n, x[0], x[1]])));
const SAP = G('SAPERE_BASE') || {};
tabella('sapere', 'Sapere: forze armate e storia da Wikipedia', 'Voci lette dal programma su Wikipedia per ogni Stato, con la data di lettura e l’indirizzo. Enciclopedia aperta (CC BY-SA): utile per orientarsi, da confermare.',
  ['Stato', 'Argomento', 'Titolo della voce', 'Inizio del testo', 'Lingua', 'Letta il', 'Indirizzo'],
  Object.entries(SAP).flatMap(([n, v]) => ['forze', 'storia'].filter(k => v[k]).map(k => [n, k === 'forze' ? 'Forze armate' : 'Storia', v[k].titolo, v[k].testo, v[k].lingua, v.data, v[k].url])));
tabella('copertura', 'Copertura: che cosa c’è per ogni Stato', 'Per ogni Stato, quante voci ci sono in ogni sezione. Zero vuol dire «ancora da fare» oppure «non esiste» (per esempio Stati senza esercito).',
  ['Stato', 'Governo', 'Notizie datate', 'Righe di storia', 'Trattati', 'Uomini e mezzi (stima)', 'Personale (Banca Mondiale)', 'Basi', 'Siti ufficiali', 'Unità', 'Appalti', 'Sicurezza privata', 'Sapere (Wikipedia)'],
  Object.entries(SCHEDE).map(([n, d]) => [n, d.gov ? 'sì' : 'no', (d.nz || []).length, (d.st || []).length, (d.tr || []).length, FORZE[n] ? 'sì' : 'no', POP[n] ? 'sì' : 'no', vm.runInContext('(STATI[' + JSON.stringify(n) + '].items.basi||[]).length', ctx), (SITI[n] || []).length, UNITA.filter(u => u[0] === n).length, vm.runInContext('appaltiDi(' + JSON.stringify(n) + ').length', ctx), vm.runInContext('pmcDi(' + JSON.stringify(n) + ').length', ctx), SAP[n] ? Object.keys(SAP[n]).length - 1 : 0]));
const DIP = G('DIPLO') || {}, SF = G('SOC_FEDI') || {}, SE = G('SOC_ETNIE') || {}, SG = G('SOC_GINI') || {};
tabella('sedi_diplomatiche', 'Ambasciate: quale Stato ha una sede in quale Stato', 'Ambasciate, alte commissioni e nunziature, una riga per coppia di Stati. Elenco aperto di Wikidata letto il 18 novembre 2026, senza le sedi segnate come chiuse; non comprende i consolati, può avere buchi e sedi sospese o chiuse da poco.',
  ['Stato che invia', 'Stato che ospita', 'Reciproca nell’elenco', 'Fonte'],
  Object.entries(DIP).flatMap(([a, d]) => d.fuori.map(b => [a, b, (DIP[b] && DIP[b].fuori.includes(a)) ? 'sì' : 'no', fonte('qh_wd_sedi')])));
tabella('societa', 'Fedi, etnie e disuguaglianze per Stato', 'Composizione religiosa ed etnica (copia d’archivio del World Factbook, con gli anni della fonte) e indice di Gini della Banca Mondiale.',
  ['Stato', 'Fedi religiose', 'Etnie e minoranze (testo originale in inglese)', 'Indice di Gini', 'Anno del Gini', 'Fonti'],
  Object.keys(SCHEDE).filter(n => SF[n] || SE[n] || SG[n]).map(n => [n, SF[n] || '', SE[n] || '', SG[n] ? SG[n][0] : '', SG[n] ? SG[n][1] : '', fonti(['qh_factbook', 'qh_gini'])]));
tabella('fonti_gratuite', 'Fonti gratuite da seguire', 'Banche dati, osservatori, centri studi, libri e corsi, con affidabilità e limiti.',
  ['Tema', 'Nome', 'Indirizzo', 'Che cosa offre', 'Come si accede', 'Affidabilità', 'Limiti'], FONTI.map(f => f.slice(0, 7)));
tabella('registro_fonti', 'Registro di tutte le fonti citate', 'Ogni chiave di fonte usata nelle altre tabelle, con descrizione e indirizzo.',
  ['Chiave', 'Chi lo dice, che cosa (data)', 'Indirizzo'], Object.entries(F).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v, Array.isArray(v) ? v[1] : '']));
fs.writeFileSync(path.join(dest, 'tabelle', 'indice.json'), JSON.stringify({ aggiornate: oggi, tabelle: indice }));
const pagina = `<!DOCTYPE html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PanGeo – Tabelle aperte</title>
<style>body{font:15px/1.45 system-ui,sans-serif;margin:0;background:#f6f5f1;color:#1d1d1b}header{background:#1f3558;color:#fff;padding:14px 16px}h1{font-size:19px;margin:0}main{padding:12px 14px;max-width:1100px;margin:auto}.t{background:#fff;border:1px solid #ddd;border-radius:10px;padding:10px 12px;margin:8px 0}.t b{font-size:16px}.s{color:#666;font-size:13px}a{color:#1f4fa0}button{font:inherit;border:1px solid #1f3558;background:#fff;border-radius:8px;padding:4px 10px;margin:4px 6px 0 0}#vista{margin-top:12px}input{font:inherit;width:100%;box-sizing:border-box;padding:8px;border:1px solid #bbb;border-radius:8px;margin:6px 0}.wrap{overflow:auto;max-height:70vh;border:1px solid #ddd;border-radius:8px;background:#fff}table{border-collapse:collapse;font-size:13px}td,th{border-bottom:1px solid #eee;padding:5px 7px;vertical-align:top;text-align:left;max-width:380px}th{position:sticky;top:0;background:#eef1f6}</style></head>
<body><header><h1>PanGeo – Tabelle aperte</h1><div class="s" style="color:#cfd8e6">Tutti i dati dell’archivio, con data e fonti. Si leggono senza account; si scaricano in CSV (Excel, Fogli Google) o JSON.</div></header>
<main><p class="s">Aggiornate il <span id="agg"></span>. Ogni riga ha le sue fonti con l’indirizzo. Basi solo a livello di città; numeri di uomini e mezzi solo come stime pubbliche.</p><div id="prog"></div><div id="elenco"></div><div id="vista"></div></main>
<script>
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const link=s=>esc(s).replace(/&lt;(https?:\\/\\/[^&\\s]+)&gt;/g,(m,u)=>'<a href="'+u+'" target="_blank" rel="noopener">fonte</a>').replace(/^(https?:\\/\\/\\S+)$/,u=>'<a href="'+u+'" target="_blank" rel="noopener">'+(u.length>70?'apri':u)+'</a>');
fetch('tabelle/indice.json').then(r=>r.json()).then(I=>{document.getElementById('agg').textContent=I.aggiornate.split('-').reverse().join('/');
document.getElementById('elenco').innerHTML=I.tabelle.map(t=>'<div class="t"><b>'+esc(t.titolo)+'</b> <span class="s">('+t.righe+' righe)</span><div class="s">'+esc(t.descr)+'</div><button onclick="apri(\\''+t.nome+'\\')">Guarda</button><a href="tabelle/'+t.nome+'.csv" download>Scarica CSV</a> · <a href="tabelle/'+t.nome+'.json">JSON</a></div>').join('');}).catch(()=>{document.getElementById('elenco').textContent='Apri questa pagina dal programma PanGeo (127.0.0.1:8080/tabelle.html) o dal sito GitHub.';});
let T=null;function apri(n){fetch('tabelle/'+n+'.json').then(r=>r.json()).then(d=>{T=d;document.getElementById('vista').innerHTML='<h2>'+esc(d.titolo)+'</h2><input id="q" placeholder="Cerca (Stato, nome, parola)…" oninput="mostra()"><div class="s" id="n"></div><div class="wrap" id="tab"></div>';mostra();location.hash=n;document.getElementById('vista').scrollIntoView();});}
function mostra(){const q=(document.getElementById('q').value||'').toLowerCase();const r=T.righe.filter(x=>!q||x.join(' ').toLowerCase().includes(q));document.getElementById('n').textContent=r.length+' righe';document.getElementById('tab').innerHTML='<table><tr>'+T.colonne.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr>'+r.slice(0,800).map(x=>'<tr>'+x.map(c=>'<td>'+link(c)+'</td>').join('')+'</tr>').join('')+'</table>'+(r.length>800?'<p class="s">Mostrate le prime 800: usa la ricerca o scarica il CSV.</p>':'');}
if(location.hash.length>1&&location.hash!=='#diario'&&location.hash!=='#memoria')setTimeout(()=>apri(location.hash.slice(1)),300);
// diario del programma e memoria dei fatti confermati: li scrive il telefono a ogni giro
const NT={temi:'ricerche per tema',stati:'rotazione degli Stati',ricerca:'ricerca autonoma',feed:'feed delle testate',telegram:'Telegram',video:'YouTube',altro:'altro'};
function vedi(d){T=d;document.getElementById('vista').innerHTML='<h2>'+esc(d.titolo)+'</h2><input id="q" placeholder="Cerca (Stato, nome, parola)…" oninput="mostra()"><div class="s" id="n"></div><div class="wrap" id="tab"></div>';mostra();document.getElementById('vista').scrollIntoView();}
let DIARIO=null;
function apriDiario(){if(!DIARIO)return;location.hash='diario';vedi({titolo:'Diario del programma: un giro per riga',colonne:['Quando','Versione','Minuti','Voci nuove','Da dove','Notizie (3 giorni)','Confermate %','Non classificate %','Stati senza notizie','Feed attivi','Feed trovati da solo','Stati studiati','Fatti in memoria','Domande di seguito (notizie)','Verifiche cercate (confermate)','Richieste ai siti','Rifiuti per troppe richieste','Avvisi','Spesa del mese $'],
righe:DIARIO.slice().reverse().map(x=>{const l=x.livelli||{},t=(l.A||0)+(l.B||0)+(l.C||0)+(l.D||0);return [x.quando,x.v,Math.round(x.durata/60),x.nuove,Object.keys(x.da||{}).map(k=>(NT[k]||k)+' '+x.da[k]).join(', '),x.live,Math.round(100*x.quota),t?Math.round(100*(l.D||0)/t):0,x.scoperti,x.fonti[0]+'/'+x.fonti[1],(x.fonti_nuove||[]).join(', '),x.sapere||0,(x.memoria||[0,0])[1],(x.seguiti||[0,0])[0]+' ('+(x.seguiti||[0,0])[1]+')',(x.verifiche||[0,0])[0]+' ('+(x.verifiche||[0,0])[1]+')',x.richieste,Object.keys(x.rifiuti||{}).map(k=>k+' '+x.rifiuti[k]).join(', '),x.errori,(x.usd_mese||0).toFixed(2)];})});}
function apriMemoria(){location.hash='memoria';const righe=[];Object.keys(window.MEMORIA||{}).sort().forEach(s=>window.MEMORIA[s].forEach(x=>righe.push([s,x[0],x[1],x[2],x[3],x[4]])));vedi({titolo:'Fatti confermati per Stato (memoria del programma)',colonne:['Stato','Data','Fatto (titolo)','Prima fonte','Numero di fonti','Indirizzo'],righe});}
fetch('diario.json?v='+Date.now()).then(r=>r.json()).then(D=>{if(!D.length)return;DIARIO=D;const z=D[D.length-1],lim=new Date(Date.parse(z.iso)-24*3600e3).toISOString(),g=D.filter(x=>x.iso>=lim),i0=D.indexOf(g[0]),a=i0>0?D[i0-1]:g[0],tot=k=>g.reduce((s,x)=>s+(x[k]||0),0);
document.getElementById('prog').insertAdjacentHTML('afterbegin','<div class="t"><b>Diario del programma</b> <span class="s">('+D.length+' giri)</span><div class="s">Ultime 24 ore: '+g.length+' giri, '+tot('nuove')+' voci nuove; notizie degli ultimi 3 giorni da '+a.live+' a '+z.live+'; confermate da più fonti dal '+Math.round(100*a.quota)+'% al '+Math.round(100*z.quota)+'%; Stati senza notizie da '+a.scoperti+' a '+z.scoperti+'; feed attivi da '+a.fonti[0]+' a '+z.fonti[0]+'. Ultimo giro: '+esc(z.quando)+', versione '+esc(z.v)+'.</div><button onclick="apriDiario()">Guarda tutti i giri</button><a href="diario.json">JSON</a></div>');
if(location.hash==='#diario')apriDiario();}).catch(()=>{});
(function(){const s=document.createElement('script');s.src='memoria.js?v='+Date.now();s.onload=()=>{const M=window.MEMORIA||{},n=Object.keys(M).reduce((t,k)=>t+M[k].length,0);
document.getElementById('prog').insertAdjacentHTML('beforeend','<div class="t"><b>Fatti confermati per Stato</b> <span class="s">('+n+' righe, '+Object.keys(M).length+' Stati)</span><div class="s">La memoria del programma: i fatti riportati da almeno due fonti, tenuti 120 giorni. Titoli di giornale con data, fonte e indirizzo.</div><button onclick="apriMemoria()">Guarda</button></div>');
if(location.hash==='#memoria')apriMemoria();};s.onerror=()=>s.remove();document.head.appendChild(s);})();
</script></body></html>`;
fs.writeFileSync(path.join(dest, 'tabelle.html'), pagina);
console.log(indice.map(t => t.nome + ' ' + t.righe).join(' | '));

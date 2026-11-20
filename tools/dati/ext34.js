
// Trentaquattresima estensione (20 novembre 2026): per ogni Stato energia, trasporti e logistica, cibo e risorse,
// dipendenze e commercio, e la spesa per settori accanto a quella militare. I dati stanno in tabelle/infra.json
// (lo costruisce tools/infra_base.py dalla copia d'archivio del CIA World Factbook): ogni numero ha il suo anno.
function caricaInfra() {
  if (!APP_OK || typeof fetch !== 'function') return;
  fetch('tabelle/infra.json').then(r => r.ok ? r.json() : null).then(d => { if (d && d.stati) { window.INFRA = d; render(); } }).catch(() => {});
}
function infraDi(nome, campo) { const s = window.INFRA && window.INFRA.stati[nome]; return (s && s[campo]) || null; }
function nf(x, dec) { return Number(x).toLocaleString('it-IT', { maximumFractionDigits: dec == null ? 1 : dec }); }
function infraAnno(v) { return v && v[1] ? ' <span class="s">(' + v[1] + ')</span>' : ''; }
function infraSoldi(x) { return x >= 1e9 ? nf(x / 1e9, x >= 1e11 ? 0 : 1) + ' miliardi di $' : x >= 1e6 ? nf(x / 1e6, 1) + ' milioni di $' : nf(x, 0) + ' $'; }
function infraQ(v, div, unita, dec) { return v ? nf(v[0] / div, dec == null ? 1 : dec) + ' ' + unita + infraAnno(v) : ''; }
function infraFonte(nome) {
  const I = window.INFRA || {}, p = (I.percorsi || {})[nome];
  return '<div class="s">Fonte: ' + (p ? '<a href="https://github.com/factbook/factbook.json/blob/master/' + esc(p) + '.json" target="_blank" rel="noopener">CIA World Factbook, copia d’archivio</a>' : 'CIA World Factbook, copia d’archivio') + '. Ogni numero ha il suo anno tra parentesi: molti sono stime e alcuni sono vecchi di anni.</div>';
}
function infraKv(righe) { righe = righe.filter(r => r && r[1]); return righe.length ? '<dl class="kv">' + righe.map(r => '<dt>' + esc(r[0]) + '</dt><dd>' + r[1] + '</dd>').join('') + '</dl>' : ''; }
// barre semplici: etichetta, barra in un solo colore, valore scritto; il massimo della scala è 100 (sono percentuali)
function infraBarre(righe, link) {
  return '<div style="display:grid;gap:5px;margin:6px 0">' + righe.map(r => '<div style="display:grid;grid-template-columns:minmax(96px,38%) 1fr 3.4em;gap:8px;align-items:center"><span>' + (link ? stLink(r[0]) : esc(r[0])) + '</span><span style="background:var(--bg);border-radius:4px;height:9px;overflow:hidden"><span style="display:block;height:9px;border-radius:4px;background:var(--accent);width:' + Math.max(1, Math.min(100, r[1] || 0)) + '%"></span></span><span style="text-align:right;font-variant-numeric:tabular-nums">' + (r[1] == null ? '' : nf(r[1], 1) + '%') + '</span></div>').join('') + '</div>';
}
const DIP_NOME = { petrolio: 'petrolio', gas: 'gas naturale', carbone: 'carbone', elettricita: 'elettricità' };
function dipTiles(d) {
  const k = Object.keys(DIP_NOME).filter(x => d[x] != null);
  return k.length ? '<div class="nv-tiles">' + k.map(x => nvTile(d[x] + '%', DIP_NOME[x] + (x === 'elettricita' ? ': importazioni nette sul consumo' : ': consumo non coperto dalla produzione interna'))).join('') + '</div>' : '';
}
const DIP_NOTA = 'Le percentuali le calcola PanGeo dai numeri del Factbook (produzione e consumo): danno l’ordine di grandezza, non sono un dato ufficiale. 0% vuol dire che lo Stato produce almeno quanto consuma; dove il Factbook non riporta alcuna produzione la dipendenza è contata al 100%. Per il petrolio si confronta la produzione totale con il consumo di prodotti raffinati.';
function energiaHtml(nome) {
  const e = infraDi(nome, 'energia'); if (!e) return '';
  let h = '';
  if (e.dipendenza && Object.keys(e.dipendenza).length) h += '<div class="item"><div class="t">Quanto dipende dall’estero</div>' + dipTiles(e.dipendenza) + '<div class="s">' + esc(DIP_NOTA) + '</div></div>';
  h += '<div class="item"><div class="t">Elettricità</div>' + infraKv([
    ['Potenza installata', infraQ(e.capacita, 1e6, 'GW')], ['Consumo in un anno', infraQ(e.consumo, 1e9, 'TWh')],
    ['Importa', infraQ(e.import, 1e9, 'TWh')], ['Esporta', infraQ(e.export, 1e9, 'TWh')],
    ['Perdite della rete', e.perdite && e.consumo && e.consumo[0] ? nf(e.perdite[0] / 1e9) + ' TWh, il ' + nf(100 * e.perdite[0] / e.consumo[0], 0) + '% del consumo' + infraAnno(e.perdite) : infraQ(e.perdite, 1e9, 'TWh')],
    ['Popolazione collegata alla rete', e.accesso ? nf(e.accesso[0]) + '%' + infraAnno(e.accesso) : ''],
    ['Energia consumata a persona', e.procapite ? 'circa ' + nf(e.procapite[0] * 1.055e-6, 0) + ' GJ l’anno' + infraAnno(e.procapite) : '']]) + '</div>';
  if ((e.fonti || []).length) h += '<div class="item"><div class="t">Da che cosa viene l’elettricità</div>' + infraBarre(e.fonti) + '<div class="s">Quote della potenza installata' + (e.fonti_anno ? ', ' + e.fonti_anno : '') + '.</div></div>';
  const n = e.nucleare;
  if (n) h += '<div class="item"><div class="t">Nucleare civile</div>' + infraKv([
    ['Reattori in funzione', n.attivi ? nf(n.attivi[0], 0) + (n.gw ? ', ' + nf(n.gw[0]) + ' GW' : '') + infraAnno(n.attivi) : ''],
    ['In costruzione', n.in_costruzione ? nf(n.in_costruzione[0], 0) + infraAnno(n.in_costruzione) : ''],
    ['Chiusi per sempre', n.chiusi ? nf(n.chiusi[0], 0) + infraAnno(n.chiusi) : ''],
    ['Quota della produzione elettrica', n.quota ? nf(n.quota[0]) + '%' + infraAnno(n.quota) : '']]) + '</div>';
  const riga = (f, div, u, dec) => f ? [['Produce', infraQ(f.prod, div, u, dec)], ['Consuma', infraQ(f.cons, div, u, dec)], ['Importa', infraQ(f.imp, div, u, dec)], ['Esporta', infraQ(f.exp, div, u, dec)]] : [];
  const p = e.petrolio, g = e.gas, c = e.carbone;
  if (p) h += '<div class="item"><div class="t">Petrolio</div>' + infraKv(riga(p, 1e3, 'mila barili al giorno', 0).concat([['Riserve stimate', infraQ(p.riserve, 1e9, 'miliardi di barili', 2)]])) + '</div>';
  if (g) h += '<div class="item"><div class="t">Gas naturale</div>' + infraKv(riga(g, 1e9, 'miliardi di m³', 2).concat([['Riserve accertate', infraQ(g.riserve, 1e9, 'miliardi di m³', 0)]])) + '</div>';
  if (c) h += '<div class="item"><div class="t">Carbone</div>' + infraKv(riga(c, 1e6, 'milioni di tonnellate', 2).concat([['Riserve accertate', infraQ(c.riserve, 1e6, 'milioni di tonnellate', 0)]])) + '</div>';
  const s = STATI[nome];
  return h + infraFonte(nome) + '<p class="note">Gasdotti, oleodotti, cavi e centrali segnati sul planisfero stanno nella cartella ' + (s && hasSub(s, 'infrastrutture') ? '<a href="#stati/' + s.slug + '/infrastrutture">Infrastrutture</a>' : '«Infrastrutture»') + '. Da chi compra energia e merci: ' + (s ? '<a href="#stati/' + s.slug + '/dipendenze">Dipendenze e commercio</a>' : 'Dipendenze e commercio') + '. <a href="#risorse">Il confronto tra tutti gli Stati →</a></p>';
}
function logisticaHtml(nome) {
  const t = infraDi(nome, 'trasporti'); if (!t) return '';
  let h = '<div class="item">' + infraKv([
    ['Aeroporti', t.aeroporti ? nf(t.aeroporti[0], 0) + infraAnno(t.aeroporti) : ''], ['Eliporti', t.eliporti ? nf(t.eliporti[0], 0) + infraAnno(t.eliporti) : ''],
    ['Ferrovie', t.ferrovie ? nf(t.ferrovie[0], 0) + ' km' + (t.ferrovie_elettr ? ', di cui ' + nf(t.ferrovie_elettr, 0) + ' elettrificati' : '') + infraAnno(t.ferrovie) : ''],
    ['Porti', t.porti ? nf(t.porti[0], 0) + (t.porti_grandi || t.porti_medi ? ': ' + [t.porti_grandi ? nf(t.porti_grandi[0], 0) + ' grandi' : '', t.porti_medi ? nf(t.porti_medi[0], 0) + ' medi' : ''].filter(Boolean).join(', ') : '') + infraAnno(t.porti) : ''],
    ['Porti con terminal petroliferi', t.porti_petrolio ? nf(t.porti_petrolio[0], 0) : ''],
    ['Porti principali', t.porti_principali ? esc(t.porti_principali) : ''],
    ['Flotta mercantile', t.flotta ? nf(t.flotta[0], 0) + ' navi' + infraAnno(t.flotta) + ((t.flotta_tipi || []).length ? ': ' + t.flotta_tipi.filter(x => x[1]).map(x => esc(x[0]) + ' ' + nf(x[1], 0)).join(', ') : '') : '']]) + '</div>';
  const s = STATI[nome];
  return h + infraFonte(nome) + '<p class="note">La flotta conta le navi che battono la bandiera dello Stato, non quelle dei suoi armatori. ' + (s && hasSub(s, 'stretti') ? 'Stretti e rotte: <a href="#stati/' + s.slug + '/stretti">apri</a>. ' : '') + (s && hasSub(s, 'aeroporti') ? 'Aeroporti principali e spazio aereo: <a href="#stati/' + s.slug + '/aeroporti">apri</a>.' : '') + '</p>';
}
const CIBO_MERCI = ['grano', 'mais', 'riso', 'soia', 'latte', 'olio di palma', 'olio di soia', 'oli di semi', 'zucchero grezzo', 'carne bovina', 'carne suina', 'pollame', 'pesce', 'generi alimentari', 'altri alimenti', 'farine di grano', 'farine di cereali', 'prodotti da forno', 'orzo', 'sorgo', 'legumi secchi', 'farina di soia', 'mangimi', 'prodotti agricoli', 'formaggio', 'burro', 'carne ovina e caprina', 'fertilizzanti'];
function ciboHtml(nome) {
  const c = infraDi(nome, 'cibo'); if (!c) return '';
  const co = infraDi(nome, 'commercio') || {}, imp = (co.import_merci || []).filter(m => CIBO_MERCI.includes(m)), exp = (co.export_merci || []).filter(m => CIBO_MERCI.includes(m));
  let h = '';
  if ((c.prodotti || []).length) h += '<div class="item"><div class="t">Che cosa produce di più</div><div class="x">' + c.prodotti.map(esc).join(', ') + '.</div><div class="s">I primi dieci prodotti agricoli per tonnellate' + (c.prodotti_anno ? ', ' + c.prodotti_anno : '') + '.</div></div>';
  h += '<div class="item">' + infraKv([
    ['Terra agricola', c.terra_agricola ? nf(c.terra_agricola[0]) + '% del territorio' + (c.arabile ? ', arabile ' + nf(c.arabile[0]) + '%' : '') + infraAnno(c.terra_agricola) : ''],
    ['Terra irrigata', c.irrigata ? nf(c.irrigata[0], 0) + ' km²' + infraAnno(c.irrigata) : ''],
    ['Spesa delle famiglie per il cibo', c.spesa_cibo ? nf(c.spesa_cibo[0]) + '% della spesa' + infraAnno(c.spesa_cibo) : ''],
    ['Acqua potabile sicura', c.acqua ? nf(c.acqua[0]) + '% della popolazione' + infraAnno(c.acqua) : ''],
    ['Tra le prime merci importate', imp.length ? imp.map(esc).join(', ') + (co.anno ? ' <span class="s">(' + co.anno + ')</span>' : '') : ''],
    ['Tra le prime merci esportate', exp.length ? exp.map(esc).join(', ') + (co.anno ? ' <span class="s">(' + co.anno + ')</span>' : '') : '']]) + '</div>';
  return h + infraFonte(nome) + '<p class="note">Una quota alta della spesa delle famiglie per il cibo vuol dire che un aumento dei prezzi pesa di più. Cibo e fertilizzanti tra le prime merci importate indicano una dipendenza dall’estero.</p>';
}
function chiDipendeDa(nome, campo, soglia) {
  const out = [], S = (window.INFRA || {}).stati || {};
  Object.keys(S).forEach(k => { if (k === nome) return; const v = ((S[k].commercio || {})[campo] || []).find(x => x[0] === nome); if (v && v[1] >= soglia) out.push([k, v[1]]); });
  return out.sort((a, b) => b[1] - a[1]);
}
function dipendenzeHtml(nome) {
  const c = infraDi(nome, 'commercio'), e = infraDi(nome, 'energia'); if (!c && !e) return '';
  let h = '';
  if (e && e.dipendenza && Object.keys(e.dipendenza).length) h += '<div class="item"><div class="t">Energia: quanto dipende dall’estero</div>' + dipTiles(e.dipendenza) + '<div class="s">' + esc(DIP_NOTA) + '</div></div>';
  if (c) {
    const an = c.anno ? ', ' + c.anno : '';
    h += '<div class="item">' + infraKv([['Importazioni', c.import ? infraSoldi(c.import[0]) + infraAnno(c.import) : ''], ['Esportazioni', c.export ? infraSoldi(c.export[0]) + infraAnno(c.export) : ''],
      ['Saldo', c.import && c.export ? (c.export[0] >= c.import[0] ? 'vende più di quanto compra: +' : 'compra più di quanto vende: −') + infraSoldi(Math.abs(c.export[0] - c.import[0])) : '']]) + '</div>';
    if ((c.import_da || []).length) h += '<div class="item"><div class="t">Da chi compra</div>' + infraBarre(c.import_da, true) + ((c.import_merci || []).length ? '<div class="x">Le prime merci importate: ' + c.import_merci.map(esc).join(', ') + '.</div>' : '') + '<div class="s">Primi cinque fornitori, quota sul valore delle importazioni' + an + '.</div></div>';
    if ((c.export_a || []).length) h += '<div class="item"><div class="t">A chi vende</div>' + infraBarre(c.export_a, true) + ((c.export_merci || []).length ? '<div class="x">Le prime merci esportate: ' + c.export_merci.map(esc).join(', ') + '.</div>' : '') + '<div class="s">Primi cinque clienti, quota sul valore delle esportazioni' + an + '.</div></div>';
  }
  const d1 = chiDipendeDa(nome, 'import_da', 10), d2 = chiDipendeDa(nome, 'export_a', 15);
  if (d1.length) h += '<div class="item"><div class="t">Chi compra molto da ' + esc(nome) + '</div>' + infraBarre(d1.slice(0, 20), true) + '<div class="s">Stati per cui ' + esc(nome) + ' è tra i primi cinque fornitori, con almeno il 10% delle loro importazioni' + (d1.length > 20 ? ' (i primi 20 su ' + d1.length + ')' : '') + '.</div></div>';
  if (d2.length) h += '<div class="item"><div class="t">Chi vende molto a ' + esc(nome) + '</div>' + infraBarre(d2.slice(0, 20), true) + '<div class="s">Stati per cui ' + esc(nome) + ' è tra i primi cinque clienti, con almeno il 15% delle loro esportazioni' + (d2.length > 20 ? ' (i primi 20 su ' + d2.length + ')' : '') + '.</div></div>';
  return h + infraFonte(nome) + '<p class="note">Una quota alta su un solo fornitore o un solo cliente è una leva: chi la tiene può usarla con dazi, blocchi o sanzioni. Qui c’è solo il commercio di merci; armi e accordi stanno nelle cartelle Appalti e Alleanze. <a href="#risorse">Il confronto tra tutti gli Stati →</a></p>';
}
function spesaSettoriHtml(nome) {
  const s = infraDi(nome, 'spesa'); if (!s) return '';
  const mil = (s.militare || [])[0], barre = [];
  if (mil) barre.push(['Difesa (' + mil[0] + ')', mil[1]]);
  if (s.sanita) barre.push(['Sanità (' + (s.sanita[1] || '?') + ')', s.sanita[0]]);
  if (s.istruzione) barre.push(['Istruzione (' + (s.istruzione[1] || '?') + ')', s.istruzione[0]]);
  let h = '';
  if (barre.length) {
    const max = Math.max.apply(null, barre.map(b => b[1])), scala = max > 0 ? 100 / max : 1;
    h += '<div class="item"><div class="t">La spesa per settori, in % del PIL</div><div style="display:grid;gap:5px;margin:6px 0">' + barre.map(b => '<div style="display:grid;grid-template-columns:minmax(96px,38%) 1fr 3.4em;gap:8px;align-items:center"><span>' + esc(b[0]) + '</span><span style="background:var(--bg);border-radius:4px;height:9px;overflow:hidden"><span style="display:block;height:9px;border-radius:4px;background:var(--accent);width:' + Math.max(1, b[1] * scala) + '%"></span></span><span style="text-align:right;font-variant-numeric:tabular-nums">' + nf(b[1], 1) + '%</span></div>').join('') + '</div>' +
      ((s.militare || []).length > 1 ? '<div class="x">Difesa negli anni: ' + s.militare.map(m => m[0] + ' ' + nf(m[1], 1) + '%').join(' · ') + '.</div>' : '') +
      '<div class="s">La sanità qui è tutta la spesa sanitaria del Paese, pubblica e privata; difesa e istruzione sono spesa pubblica. Gli anni sono diversi: il confronto dà l’ordine di grandezza. Per la difesa questo è il dato del Factbook: può differire di qualche decimo da quello del SIPRI scritto sopra.</div></div>';
  }
  h += '<div class="item"><div class="t">Bilancio dello Stato</div>' + infraKv([
    ['Entrate', s.entrate ? infraSoldi(s.entrate[0]) + infraAnno(s.entrate) : ''], ['Uscite', s.uscite ? infraSoldi(s.uscite[0]) + infraAnno(s.uscite) : ''],
    ['Saldo', s.entrate && s.uscite ? (s.entrate[0] >= s.uscite[0] ? 'avanzo di ' : 'disavanzo di ') + infraSoldi(Math.abs(s.entrate[0] - s.uscite[0])) : ''],
    ['Sanità sul bilancio dello Stato', s.sanita_bilancio ? nf(s.sanita_bilancio[0]) + '%' + infraAnno(s.sanita_bilancio) : ''],
    ['Istruzione sul bilancio dello Stato', s.istruzione_bilancio ? nf(s.istruzione_bilancio[0]) + '%' + infraAnno(s.istruzione_bilancio) : ''],
    ['Entrate fiscali', s.tasse ? nf(s.tasse[0]) + '% del PIL' + infraAnno(s.tasse) : ''],
    ['Debito pubblico', s.debito ? nf(s.debito[0]) + '% del PIL' + infraAnno(s.debito) : ''],
    ['PIL', s.pil ? infraSoldi(s.pil[0]) + infraAnno(s.pil) : '']]) + '</div>';
  return h + infraFonte(nome);
}
// confronto tra tutti gli Stati: dipendenza energetica e primo fornitore
let risorseOrd = 'gas';
function viewRisorse() {
  crumbs([['', 'Energia, risorse e dipendenze']]);
  const S = (window.INFRA || {}).stati;
  if (!S) return '<h2>Energia, risorse e dipendenze</h2><p class="note">I dati si caricano dal sito pubblico e dal programma sul telefono. Su claude.ai questa pagina è un’istantanea e non li contiene.</p>';
  const righe = Object.keys(S).filter(n => STATI[n]).map(n => { const d = (S[n].energia || {}).dipendenza || {}, f = ((S[n].commercio || {}).import_da || [])[0], c = (S[n].cibo || {}).spesa_cibo; return { n, petrolio: d.petrolio, gas: d.gas, carbone: d.carbone, elettricita: d.elettricita, forn: f, cibo: c ? c[0] : null }; });
  const val = r => risorseOrd === 'forn' ? (r.forn ? r.forn[1] : null) : r[risorseOrd];
  righe.sort((a, b) => (val(b) == null ? -1 : val(b)) - (val(a) == null ? -1 : val(a)) || a.n.localeCompare(b.n, 'it'));
  const col = [['petrolio', 'Petrolio'], ['gas', 'Gas'], ['carbone', 'Carbone'], ['elettricita', 'Elettricità'], ['forn', 'Primo fornitore'], ['cibo', 'Cibo']];
  const pc = v => v == null ? '<span class="s">–</span>' : v + '%';
  return '<h2>Energia, risorse e dipendenze</h2><p class="note">Quanto ogni Stato dipende dall’estero. Per petrolio, gas e carbone è la parte del consumo non coperta dalla produzione interna; per l’elettricità sono le importazioni nette sul consumo; «primo fornitore» è lo Stato da cui compra di più e la sua quota sulle importazioni; «cibo» è la quota della spesa delle famiglie che va in cibo. ' + esc(DIP_NOTA) + '</p>' +
    '<div class="fchips" role="group" aria-label="Ordina per">' + col.map(c => '<button class="fchip ris-ord" data-o="' + c[0] + '" aria-pressed="' + (risorseOrd === c[0]) + '">' + c[1] + '</button>').join('') + '</div>' +
    '<div style="overflow-x:auto"><table class="nv-giri" style="width:100%"><tr><th style="text-align:left">Stato</th>' + col.map(c => '<th>' + c[1] + '</th>').join('') + '</tr>' +
    righe.map(r => '<tr><td style="text-align:left"><a href="#stati/' + STATI[r.n].slug + '/dipendenze">' + esc(r.n) + '</a></td><td>' + pc(r.petrolio) + '</td><td>' + pc(r.gas) + '</td><td>' + pc(r.carbone) + '</td><td>' + pc(r.elettricita) + '</td><td>' + (r.forn ? esc(r.forn[0]) + (r.forn[1] != null ? ' ' + nf(r.forn[1], 0) + '%' : '') : '<span class="s">–</span>') + '</td><td>' + (r.cibo == null ? '<span class="s">–</span>' : nf(r.cibo, 0) + '%') + '</td></tr>').join('') + '</table></div>' +
    '<p class="note">Fonte: CIA World Factbook, copia d’archivio; dati quasi tutti del 2023. Tocca uno Stato per il dettaglio. «–» vuol dire che il Factbook non dà il numero.</p>';
}

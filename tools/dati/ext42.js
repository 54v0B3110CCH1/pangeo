// Quarantaduesima estensione (21 novembre 2026): il riquadro delle novità diviso in «Ha scoperto», «Ha aggiunto»,
// «Ha aggiornato» e «Intoppi», su richiesta di Savino.
function novitaHtml() {
  const D = liveOk() ? diarioFresco(window.LIVE) : []; if (!D.length) return '';
  let giri = VISTO_PRIMA ? D.filter(x => x.iso > VISTO_PRIMA) : D.slice(-8), recap = ''; const z = D[D.length - 1];
  const quando = VISTO_PRIMA ? new Date(VISTO_PRIMA).toLocaleString('it-IT', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }) : '';
  // il programma si è fermato? Sul telefono ci si aspetta un giro all'ora (dalla 2.14), sul sito i dati arrivano ogni 3 ore
  const zu = (window.DIARIO_ULT && window.DIARIO_ULT.iso > z.iso) ? window.DIARIO_ULT : z;
  const sulTelefono = /^(localhost|127\.0\.0\.1)$/.test(location.hostname), minuti = Math.round((Date.now() - Date.parse(zu.iso)) / 60000);
  const durata = m => m < 120 ? m + ' minuti' : Math.floor(m / 60) + ' ore' + (m % 60 >= 10 ? ' e ' + (m % 60) + ' minuti' : '');
  const fermo = APP_OK && minuti > (sulTelefono ? (zu.tipo ? 45 : 200) : 75) ? '<section class="nv nv-fermo" role="status"><div class="nv-top"><b>' + (sulTelefono ? 'Il programma è fermo da ' : 'Questo sito non riceve dati da ') + durata(minuti) + '</b><span>' + (sulTelefono ? 'L’ultimo giro è del ' + esc(zu.quando) + '. Per farlo ripartire apri Termux e lancia <code>bash avvia.sh</code>, poi lascia Termux aperto in sottofondo, con la batteria su «Senza restrizioni».' : 'L’ultimo giro arrivato qui è del ' + esc(zu.quando) + '. Le cause possibili sono tre. Il telefono è senza internet: aspetta, appena la rete torna il programma fa da solo un giro completo e manda i dati. Il programma è fermo: in Termux lancia <code>bash avvia.sh</code>. Oppure gira ma non è più collegato a GitHub: in Termux lancia <code>bash github.sh</code>. Sul telefono la pagina sempre aggiornata è <code>http://127.0.0.1:8080/</code>.') + '</span></div></section>' : '';
  const R = window.LIVE.rete, gd = R && R.giu_dal ? new Date(R.giu_dal) : null;
  const senzaRete = gd && !isNaN(gd) ? '<section class="nv nv-fermo" role="status"><div class="nv-top"><b>Il telefono è senza rete</b><span>Dal ' + esc(gd.toLocaleString('it-IT', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })) + ' il programma non raggiunge internet. Non è fermo: rilegge l’archivio, cerca conferme tra le notizie che ha già e riprova ogni minuto; appena la rete torna fa subito un giro completo.</span></div></section>' : '';
  const inPausa = z.tipo === 'pausa' ? '<section class="nv nv-fermo" role="status"><div class="nv-top"><b>Il programma è in pausa</b><span>' + esc(z.motivo || '') + ' (' + esc(z.quando) + '). Riparte da solo appena il telefono si raffredda o va sotto carica.</span></div></section>' : '';
  const dove = !APP_OK ? ' Su claude.ai questa è un’istantanea: i dati dal vivo sono sul telefono e sul sito.' : sulTelefono ? (z.tipo ? ' Il prossimo giro arriva entro ' + (z.v >= '2.17' ? 'mezz’ora.' : 'un’ora.') : ' Il prossimo giro arriva entro 3 ore.') : ' Sul sito il diario dei giri arriva dopo ogni giro, le notizie complete ogni 3 ore.';
  if (!giri.length) { recap = 'Dalla tua visita del ' + esc(quando) + ' non c’è ancora stato un giro nuovo: l’ultimo è del ' + esc(z.quando) + '.' + dove + ' Intanto, ecco che cosa ha raccolto nelle ultime 24 ore.'; giri = D.filter(x => Date.parse(x.iso) > Date.now() - 864e5); if (!giri.length) giri = D.slice(-8); }
  const i0 = D.indexOf(giri[0]), prima = i0 > 0 ? D[i0 - 1] : giri[0], N = nvDati(D, giri, prima);
  let o = (fermo || senzaRete || inPausa) + '<section class="nv" aria-label="Novità"><div class="nv-top"><b>' + (recap ? 'Nelle ultime 24 ore' : VISTO_PRIMA ? 'Dall’ultima volta che sei entrato' : 'Che cosa ha aggiunto il programma') + '</b><span>' + (recap || (giri.length === 1 ? (VISTO_PRIMA ? 'Dal ' + esc(quando) + ': un giro del programma, il ' : 'Nell’ultimo giro del programma, il ') : (VISTO_PRIMA ? 'Dal ' + esc(quando) + ': ' : 'Negli ultimi ') + giri.length + ' giri del programma, l’ultimo il ') + esc(z.quando) + (VISTO_PRIMA && D[0].iso > VISTO_PRIMA ? ' (qui si vedono gli ultimi ' + D.length + ' giri)' : '')) + '</span></div>';
  // dalla 42 (21 novembre 2026): tre parti chiare. Ha scoperto (cose nuove trovate da solo), ha aggiunto (dati nuovi
  // entrati nell'archivio), ha aggiornato (dati che c'erano già, controllati o rinnovati); poi gli eventuali intoppi.
  const somA = (k, i) => giri.reduce((s, x) => s + (((x[k] || [])[i]) || 0), 0);
  const ultimoA = (k, i) => { for (let j = giri.length - 1; j >= 0; j--) { const v = (giri[j][k] || [])[i]; if (v != null) return v; } return null; };
  const voce = (n, t, link) => n ? '<li><b>' + num(n) + '</b> ' + t + (link ? ' <a href="' + link + '">apri</a>' : '') + '</li>' : '';
  const blocco = (titolo, sotto, righe) => righe.filter(Boolean).length ? '<div class="nv-riga nv-blocco"><span>' + titolo + '</span><div class="s">' + sotto + '</div><ul class="plain">' + righe.filter(Boolean).join('') + '</ul></div>' : '';
  o += '<div class="nv-tiles">' + nvTile(num(N.som('nuove')), 'voci nuove raccolte') + nvTile(num(somA('articoli', 0)), 'articoli letti') + nvTile(num(N.fonti.length + N.tg.length + N.coperti.length), 'scoperte (fonti, canali, Stati)') + nvTile(num(N.som('memoria', 0)), 'fatti confermati in memoria') + '</div>';
  // 1. ha scoperto
  let sc = '';
  if (N.coperti.length) sc += '<li>Stati che prima erano senza notizie: ' + nvChips(N.coperti, 8, s => '<a class="nv-chip" href="#live/' + encodeURIComponent(s) + '">' + esc(s) + '</a>') + '</li>';
  if (N.fonti.length) sc += '<li>Fonti nuove trovate da solo, da valutare: ' + nvChips(N.fonti, 4, f => '<span class="nv-chip">' + esc(f) + '</span>') + '</li>';
  if (N.tg.length) sc += '<li>Canali Telegram nuovi: ' + nvChips(N.tg, 4, c => '<span class="nv-chip">' + esc(c) + '</span>') + '</li>';
  const scoperte = [sc, voce(somA('x229', 1), 'avvisi su fatti gravi o insoliti', '#avvisi'), voce(N.som('intel', 0), 'fatti pubblici sui servizi segreti', '#intelligence'),
    voce(N.som('quadro', 1), 'collegamenti nuovi tra i fatti', '#quadro'), voce(N.som('puzzle', 0), 'pezzi nuovi del puzzle (energia, IA militare, trasporti, cibo)')];
  o += blocco('Ha scoperto', 'cose nuove trovate da solo', scoperte);
  // 2. ha aggiunto
  const da = Object.keys(N.da).sort((p, q) => N.da[q] - N.da[p]).slice(0, 3).map(k => (TAPPE_NOME[k] || k).toLowerCase() + ' ' + num(N.da[k])).join(', ');
  o += blocco('Ha aggiunto', 'dati nuovi entrati nell’archivio', [
    voce(N.som('nuove'), 'voci nuove raccolte' + (da ? ' <span class="s">(' + esc(da) + ')</span>' : '')),
    voce(N.som('attesa', 0), 'titoli di testate locali, nella loro lingua e tradotti'),
    voce(somA('articoli', 0), 'articoli aperti e letti (il testo va nella ricerca)'),
    voce(somA('x229', 0), 'fatti messi in schede', '#fatti'),
    voce(somA('storia', 0), 'cronologie storiche scritte o riscritte', '#storia'),
    N.som('piano', 1) || N.som('piano', 2) ? '<li><b>' + num(N.som('piano', 1)) + '</b> accordi e <b>' + num(N.som('piano', 2)) + '</b> appalti trovati dal lavoro a piano <a href="#piano">apri</a></li>' : '']);
  // 3. ha aggiornato
  const agg = [voce(N.som('memoria', 0), 'fatti confermati da più fonti messi in memoria'),
    N.som('verifiche', 0) ? '<li><b>' + num(N.som('verifiche', 0)) + '</b> notizie verificate, <b>' + num(N.som('verifiche', 1)) + '</b> confermate da una fonte affidabile</li>' : '',
    voce(N.som('seguiti', 0), 'domande di seguito sui fatti più confermati'),
    (z.sapere || 0) > (prima.sapere || 0) ? voce((z.sapere || 0) - (prima.sapere || 0), 'Stati ristudiati su Wikipedia') : '',
    ultimoA('x229', 2) ? '<li>indice di ricerca: <b>' + num(ultimoA('x229', 2)) + '</b> testi</li>' : '',
    ultimoA('storia', 1) ? '<li>storia: <b>' + num(ultimoA('storia', 1)) + '</b> Stati con la cronologia su 198</li>' : '',
    z.v !== prima.v ? '<li>programma aggiornato alla versione <b>' + esc(z.v) + '</b></li>' : ''];
  o += blocco('Ha aggiornato', 'dati che c’erano già, controllati o rinnovati', agg);
  // 4. intoppi
  const intoppi = [];
  const npausa = giri.filter(x => x.tipo === 'pausa').length; if (npausa) intoppi.push(npausa + (npausa === 1 ? ' pausa' : ' pause') + ' per proteggere il telefono (' + esc((giri.filter(x => x.tipo === 'pausa').pop() || {}).motivo || '') + ')');
  const nfuori = giri.filter(x => x.tipo === 'senza rete').length; if (nfuori) intoppi.push(nfuori + (nfuori === 1 ? ' giro' : ' giri') + ' senza rete (archivio riletto)');
  const nferme = giri.filter(x => x.tipo === 'fermo'); if (nferme.length) intoppi.push('si è fermato ' + (nferme.length === 1 ? 'una volta' : nferme.length + ' volte') + ' (' + nferme.reduce((t, x) => t + ((x.fermo || [])[2] || 0), 0) + ' minuti): ' + esc(nferme[nferme.length - 1].motivo || ''));
  const err = N.som('errori'); if (err) intoppi.push(num(err) + ' siti che non hanno risposto o hanno rifiutato');
  if (intoppi.length) o += '<div class="nv-riga"><span>Intoppi</span><div>' + intoppi.join(' · ') + '</div></div>';
  return o + totaliHtml(D) + '<div class="s"><a href="#live">Apri Live</a> per il diario completo e le notizie.</div></section>';
}
// Totali (programma 2.33.7): da sempre, questo mese, oggi, ultime 24 ore. «Da sempre» e i mesi vengono da totali.js
// (il programma li tiene per sempre); le ultime 24 ore dal diario dei giri.
const CAR_TOT = {};
const TOT_VOCI = [['voci', 'voci nuove raccolte'], ['tradotti', 'titoli locali tradotti'], ['articoli', 'articoli letti'], ['schede', 'fatti in schede'],
  ['memoria', 'fatti confermati in memoria'], ['avvisi', 'avvisi'], ['fonti', 'fonti trovate da solo'], ['verifiche', 'notizie verificate'],
  ['accordi', 'accordi trovati'], ['appalti', 'appalti trovati'], ['intel', 'fatti sui servizi segreti'], ['cronologie', 'cronologie storiche'],
  ['giri', 'giri del programma'], ['mb', 'MB scaricati']];
function totDi(r) {
  if (r.tipo === 'pausa' || r.tipo === 'fermo') return {};
  const g = (k, i) => ((r[k] || [])[i]) || 0;
  return { voci: r.nuove || 0, tradotti: g('attesa', 0), articoli: g('articoli', 0), schede: g('x229', 0), memoria: g('memoria', 0), avvisi: g('x229', 1),
    fonti: (r.fonti_nuove || []).length, verifiche: g('verifiche', 0), accordi: g('piano', 1), appalti: g('piano', 2), intel: g('intel', 0), cronologie: g('storia', 0), giri: 1, mb: r.mb || 0 };
}
function totaliHtml(D) {
  caricaJs('totali.js', 'TOTALI', CAR_TOT);
  const T = window.TOTALI; if (!T || !T.sempre) return '';
  const oggi = new Date().toLocaleDateString('sv-SE'), mese = oggi.slice(0, 7), M = (T.mesi || {})[mese] || {}, G = (T.giorni || {})[oggi] || {};
  const u24 = {}; (D || []).filter(x => Date.parse(x.iso) > Date.now() - 864e5).forEach(x => { const v = totDi(x); Object.keys(v).forEach(k => { u24[k] = (u24[k] || 0) + v[k]; }); });
  const n = v => v == null ? '—' : num(Math.round(v));
  const da = new Date(T.da).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });
  const righe = TOT_VOCI.filter(([k]) => T.sempre[k]).map(([k, t]) => '<tr><td>' + esc(t) + '</td><td>' + n(T.sempre[k]) + '</td><td>' + n(M[k] || 0) + '</td><td>' + n(G[k] || 0) + '</td><td>' + n(u24[k] || 0) + '</td></tr>');
  const S = T.spesa || {}, sm = (S.mesi || {})[mese], sg = (S.giorni || {})[oggi];
  if (S.totale != null) righe.push('<tr><td>spesa del cervello</td><td>' + (S.totale || 0).toFixed(2) + ' $</td><td>' + (sm != null ? sm.toFixed(2) + ' $' : '—') + '</td><td>' + (sg != null ? sg.toFixed(2) + ' $' : '—') + '</td><td>—</td></tr>');
  const mesi = Object.keys(T.mesi || {}).sort();
  const perMese = mesi.length > 1 ? '<div class="s">Mese per mese: ' + mesi.map(m => esc(m.slice(5) + '/' + m.slice(0, 4)) + ' ' + n((T.mesi[m] || {}).voci) + ' voci' + ((S.mesi || {})[m] != null ? ', ' + S.mesi[m].toFixed(2) + ' $' : '')).join(' · ') + '</div>' : '';
  const O = T.ora || {};
  const ora = [O.notizie != null ? num(O.notizie) + ' notizie nell’archivio dal vivo' : '', O.memoria != null ? num(O.memoria) + ' fatti in memoria' : '', O.indice != null ? num(O.indice) + ' testi nella ricerca' : '',
    O.cronologie != null ? O.cronologie + ' Stati con la cronologia' : '', O.fonti != null ? O.fonti + ' fonti attive' : '', O.stati_coperti != null ? O.stati_coperti + ' Stati con notizie' : ''].filter(Boolean).join(' · ');
  return '<div class="nv-riga"><span>In numeri</span><div class="tab-wrap"><table class="nv-giri nv-tot"><tr><th></th><th>Da sempre<br><span class="s">dal ' + esc(da) + '</span></th><th>Questo mese</th><th>Oggi</th><th>Ultime 24 ore</th></tr>' + righe.join('') + '</table></div>' +
    perMese + (ora ? '<div class="s">Adesso: ' + ora + '.</div>' : '') + '<div class="s">«Da sempre» parte dal primo diario dei giri (18 novembre 2026). Fino al 19 novembre le voci nuove erano contate in eccesso (le notizie vecchie entravano e uscivano a ogni giro).</div></div>';
}

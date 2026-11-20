// Trentanovesima estensione (programma 2.30, 20 novembre 2026): economia (Banca Mondiale, titoli di Stato, valute,
// materie prime, commercio e armi dalle dogane ONU) e canali trovati da soli.
const CAR_ECO = {};
function caricaEconomia() { caricaJs('economia.js', 'ECONOMIA', CAR_ECO); }
function soldi(v) {
  if (v == null) return '—';
  const a = Math.abs(v);
  if (a >= 1e12) return (v / 1e12).toLocaleString('it-IT', { maximumFractionDigits: 2 }) + ' mila mld $';
  if (a >= 1e9) return (v / 1e9).toLocaleString('it-IT', { maximumFractionDigits: 1 }) + ' mld $';
  if (a >= 1e6) return (v / 1e6).toLocaleString('it-IT', { maximumFractionDigits: 0 }) + ' mln $';
  return Math.round(v).toLocaleString('it-IT') + ' $';
}
function num1(v) { return v == null ? '—' : Number(v).toLocaleString('it-IT', { maximumFractionDigits: 1 }); }
function miniLinea(titolo, punti, colore, unita) {
  const p = (punti || []).filter(x => x && x[1] != null);
  if (p.length < 2) return '';
  const W = 340, H = 64, base = H - 14, vs = p.map(x => x[1]), mn = Math.min(...vs), mx = Math.max(...vs), r = (mx - mn) || 1;
  const xy = p.map((x, i) => [(i * (W - 8) / (p.length - 1) + 4), (base - 4 - (x[1] - mn) / r * (base - 12))]);
  const ult = p[p.length - 1];
  return '<div class="mini-t">' + esc(titolo) + ' · ultimo ' + num1(ult[1]) + unita + ' (' + esc(ult[0]) + ') · da ' + num1(mn) + ' a ' + num1(mx) + unita + '</div>' +
    '<svg viewBox="0 0 ' + W + ' ' + H + '" class="mini" role="img" aria-label="' + esc(titolo) + '"><polyline fill="none" stroke="var(' + colore + ')" stroke-width="2" stroke-linejoin="round" points="' +
    xy.map(q => q[0].toFixed(1) + ',' + q[1].toFixed(1)).join(' ') + '"/>' + xy.map((q, i) => '<circle cx="' + q[0].toFixed(1) + '" cy="' + q[1].toFixed(1) + '" r="5" fill="transparent"><title>' +
    esc(p[i][0] + ': ' + num1(p[i][1]) + unita) + '</title></circle>').join('') + '<circle cx="' + xy[xy.length - 1][0].toFixed(1) + '" cy="' + xy[xy.length - 1][1].toFixed(1) + '" r="3" fill="var(' + colore + ')"/>' +
    '<text x="0" y="' + (H - 2) + '" font-size="9" fill="var(--muted)">' + esc(p[0][0]) + '</text><text x="' + W + '" y="' + (H - 2) + '" font-size="9" text-anchor="end" fill="var(--muted)">' + esc(ult[0]) + '</text></svg>';
}
function varHtml(v, suf) { return v == null ? '—' : '<b style="color:var(' + (v < 0 ? '--conf-g' : '--st1') + ')">' + (v > 0 ? '+' : '') + num1(v) + '%</b>' + (suf || ''); }
function partnerHtml(l, tot, max) {
  if (!l || !l.length) return '<span class="s">nessun dato</span>';
  return '<ul class="plain">' + l.slice(0, max || 6).map(x => '<li>' + (STATI[x[0]] ? stLink(x[0]) : esc(x[0])) + ' · ' + soldi(x[1]) + (tot ? ' (' + Math.round(100 * x[1] / tot) + '%)' : '') + '</li>').join('') + '</ul>';
}
function spreadDi(n) {
  const E = window.ECONOMIA; if (!E) return null;
  const t = (E.stati[n] || {}).tasso, de = (E.stati['Germania'] || {}).tasso;
  if (!t || !de || n === 'Germania') return null;
  const u = t[t.length - 1], d = de.find(x => x[0] === u[0]) || de[de.length - 1];
  return Math.round((u[1] - d[1]) * 100);
}
function economiaStatoHtml(n) {
  caricaEconomia();
  const E = window.ECONOMIA;
  if (!E) return '';
  const S = E.stati[n]; if (!S) return '';
  const b = S.bm || {}, N = E.nomi || {};
  const righe = [['pil', soldi], ['import', soldi], ['export', soldi], ['ide', soldi], ['debito_pil', v => num1(v) + '%'], ['debito_estero', soldi],
    ['mil_pil', v => num1(v) + '%'], ['mil', soldi], ['inflazione', v => num1(v) + '%'], ['conto_corrente', v => num1(v) + '%']].filter(r => b[r[0]]);
  let h = '<h3>Economia</h3><div class="item">';
  if (righe.length) h += '<ul class="plain">' + righe.map(([k, f]) => '<li>' + esc(N[k] || k) + ': <b>' + f(b[k][1]) + '</b> <span class="s">(' + b[k][0] + ')</span></li>').join('') + '</ul>';
  if (S.valuta) h += '<div class="x" style="margin-top:6px">Moneta: <b>' + esc(S.valuta[0]) + '</b> · ' + num1(S.valuta[1]) + ' per un dollaro · in 7 giorni ' + varHtml(S.valuta[2]) +
    ', in 30 giorni ' + varHtml(S.valuta[3]) + ', in un anno ' + varHtml(S.valuta[4]) + ' <span class="s">(+ la moneta si rafforza, − si indebolisce)</span></div>';
  if (S.tasso) {
    const sp = spreadDi(n);
    h += miniLinea('Titoli di Stato a 10 anni', S.tasso, '--accent', '%') + (sp != null ? '<div class="s">Differenza con la Germania (spread): ' + sp + ' punti base.</div>' : '');
  }
  if (S.serie && S.serie.mil_pil && S.serie.mil_pil.length > 1) h += miniLinea('Spesa militare, % del PIL', S.serie.mil_pil.map(x => [String(x[0]), x[1]]), '--conf-g', '%');
  if (S.serie && S.serie.debito_pil && S.serie.debito_pil.length > 1) h += miniLinea('Debito del governo centrale, % del PIL', S.serie.debito_pil.map(x => [String(x[0]), x[1]]), '--numeri', '%');
  h += '</div>';
  const C = S.commercio;
  if (C) {
    h += '<div class="item"><div class="t">Commercio ' + C.anno + ' (dogane ONU)</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">' +
      '<div><div class="s">Importa da' + (C.M_tot ? ' · ' + soldi(C.M_tot) : '') + '</div>' + partnerHtml(C.M, C.M_tot) + '</div>' +
      '<div><div class="s">Esporta verso' + (C.X_tot ? ' · ' + soldi(C.X_tot) : '') + '</div>' + partnerHtml(C.X, C.X_tot) + '</div></div>';
    if ((C.M93 || []).length || (C.X93 || []).length) h += '<div class="t" style="margin-top:8px">Armi e munizioni (capitolo 93 delle dogane)</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">' +
      '<div><div class="s">Compra da' + (C.M93_tot ? ' · ' + soldi(C.M93_tot) : '') + '</div>' + partnerHtml(C.M93, C.M93_tot) + '</div>' +
      '<div><div class="s">Vende a' + (C.X93_tot ? ' · ' + soldi(C.X93_tot) : '') + '</div>' + partnerHtml(C.X93, C.X93_tot) + '</div></div>' +
      '<div class="s">Il capitolo 93 sono armi leggere, munizioni e parti dichiarate in dogana: non comprende aerei, navi e carri, che hanno altri capitoli, e molti Stati non dichiarano tutto.</div>';
    h += '</div>';
  }
  return h + '<p class="note">Fonti: ' + esc(Object.values(E.fonti || {}).join(' · ')) + '. Aggiornato al ' + esc(E.agg) + '. <a href="#economia">Economia di tutti gli Stati →</a></p>';
}
function viewEconomia() {
  crumbs([['#economia', 'Economia']]);
  caricaEconomia();
  const E = window.ECONOMIA;
  let h = '<h2>Economia</h2><p class="note">Titoli di Stato, valute, materie prime, commercio e armi dalle dogane, dati della Banca Mondiale: tutti pubblici e gratuiti, raccolti dal programma sul telefono un pezzo alla volta. Ogni Stato ha i suoi numeri nella sua scheda.</p>';
  if (!E) return h + attesaHtml(CAR_ECO, 'L’economia');
  const S = E.stati || {};
  h += '<h3>Materie prime</h3><div class="item">' + Object.values(E.materie || {}).map(m => miniLinea(m.nome, (m.s || []).slice(-120).map(x => [pianoData(x[0]), x[1]]), '--conf-f', '')).join('') + '</div>';
  const tas = Object.entries(S).filter(([n, x]) => x.tasso).map(([n, x]) => { const t = x.tasso, u = t[t.length - 1], p = t[t.length - 2]; return [n, u[1], p ? u[1] - p[1] : null, spreadDi(n), u[0]]; }).sort((a, b) => b[1] - a[1]);
  if (tas.length) h += '<h3>Titoli di Stato a 10 anni (' + tas.length + ' Stati)</h3><div class="item tab-wrap"><table class="fatti"><thead><tr><th>Stato</th><th>Tasso</th><th>In un mese</th><th>Spread con la Germania</th><th>Mese</th></tr></thead><tbody>' +
    tas.map(r => '<tr><td>' + stLink(r[0]) + '</td><td><b>' + num1(r[1]) + '%</b></td><td>' + (r[2] == null ? '—' : (r[2] > 0 ? '+' : '') + r[2].toFixed(2).replace('.', ',')) + '</td><td>' + (r[3] == null ? '—' : r[3] + ' pb') + '</td><td>' + esc(r[4]) + '</td></tr>').join('') + '</tbody></table></div>';
  const val = Object.entries(S).filter(([n, x]) => x.valuta && x.valuta[3] != null);
  if (val.length) {
    const deb = val.slice().sort((a, b) => a[1].valuta[3] - b[1].valuta[3]).slice(0, 12), forti = val.slice().sort((a, b) => b[1].valuta[3] - a[1].valuta[3]).slice(0, 8);
    h += '<h3>Monete: le più deboli e le più forti negli ultimi 30 giorni (contro il dollaro)</h3><div class="item"><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div><div class="s">Si indeboliscono</div><ul class="plain">' +
      deb.map(([n, x]) => '<li>' + stLink(n) + ' (' + esc(x.valuta[0]) + ') ' + varHtml(x.valuta[3]) + '</li>').join('') + '</ul></div><div><div class="s">Si rafforzano</div><ul class="plain">' +
      forti.map(([n, x]) => '<li>' + stLink(n) + ' (' + esc(x.valuta[0]) + ') ' + varHtml(x.valuta[3]) + '</li>').join('') + '</ul></div></div><div class="s">Una moneta che crolla in pochi giorni può voler dire crisi, sanzioni o guerra: va letta con le notizie.</div></div>';
  } else if (Object.values(S).some(x => x.valuta)) h += '<p class="note">Monete: servono almeno 30 giorni di storia per il confronto (il programma la raccoglie dal 20 novembre 2026).</p>';
  const flussi = [];
  Object.entries(S).forEach(([n, x]) => ((x.commercio || {}).M93 || []).forEach(p => flussi.push([p[0], n, p[1], x.commercio.anno])));
  flussi.sort((a, b) => b[2] - a[2]);
  if (flussi.length) h += '<h3>Armi e munizioni dalle dogane: i flussi più grandi</h3><div class="item"><ul class="plain">' + flussi.slice(0, 25).map(f => '<li>' + (STATI[f[0]] ? stLink(f[0]) : esc(f[0])) + ' → ' + stLink(f[1]) + ' · ' + soldi(f[2]) + ' (' + f[3] + ')</li>').join('') +
    '</ul><div class="s">Dichiarati da chi compra (capitolo 93: armi leggere, munizioni, parti). Gli Stati arrivano uno alla volta: ' + Object.values(S).filter(x => x.commercio).length + ' su 198 finora.</div></div>';
  const mil = Object.entries(S).filter(([n, x]) => (x.bm || {}).mil_pil).sort((a, b) => b[1].bm.mil_pil[1] - a[1].bm.mil_pil[1]).slice(0, 25);
  if (mil.length) h += '<h3>Spesa militare in rapporto al PIL (Banca Mondiale, da SIPRI)</h3><div class="item"><ul class="plain">' + mil.map(([n, x]) => '<li>' + stLink(n) + ' · ' + num1(x.bm.mil_pil[1]) + '% (' + x.bm.mil_pil[0] + ')<div class="barra" style="width:' +
    Math.round(100 * x.bm.mil_pil[1] / mil[0][1].bm.mil_pil[1]) + '%;background:var(--conf-g)"></div></li>').join('') + '</ul></div>';
  return h + '<p class="note">Fonti: ' + esc(Object.values(E.fonti || {}).join(' · ')) + '. Aggiornato al ' + esc(E.agg) + '.</p>';
}
function canaliHtml() {
  const C = (window.LIVE || {}).canali;
  if (!C) return '';
  let h = '<h3 id="doc-can">Canali seguiti e trovati da soli</h3><div class="item"><div class="x">Telegram: ' + C.telegram + ' canali · YouTube: ' + C.youtube + ' canali.</div>';
  if ((C.tg_trovati || []).length) h += '<details class="crit"><summary>Telegram trovati da soli (' + C.tg_trovati.length + ')</summary><ul class="plain">' + C.tg_trovati.slice().reverse().map(x => '<li><a href="https://t.me/s/' + encodeURIComponent(x[0]) + '" target="_blank" rel="noopener">' + esc(x[0]) + '</a>' + (x[1] ? ' · dal ' + esc(pianoData(x[1])) : '') + '</li>').join('') + '</ul></details>';
  if ((C.yt_trovati || []).length) h += '<details class="crit"><summary>YouTube trovati da soli (' + C.yt_trovati.length + ')</summary><ul class="plain">' + C.yt_trovati.slice().reverse().map(x => '<li><a href="https://www.youtube.com/channel/' + encodeURIComponent(x[2]) + '" target="_blank" rel="noopener">' + esc(x[0]) + '</a>' + (x[1] ? ' · dal ' + esc(pianoData(x[1])) : '') + '</li>').join('') + '</ul></details>';
  if ((C.spenti || []).length) h += '<div class="s">Spenti perché non rispondono (si riprovano una volta al giorno): ' + esc(C.spenti.map(x => x.split(':').slice(1).join(':')).join(', ')) + '.</div>';
  return h + '<div class="s">I canali trovati da soli entrano «da valutare»: li citano almeno due canali già seguiti. Sono voci, non conferme.</div></div>';
}

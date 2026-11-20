// Trentottesima estensione (programma 2.29, 20 novembre 2026): rete dei legami (accordi e forniture di armi), andamento
// per Stato giorno per giorno, fatti in schede, avvisi e ricerca per significato sul telefono.
(function () {
  const st = document.createElement('style');
  st.textContent = '.leg-svg{width:100%;max-width:460px;height:auto;display:block;margin:4px auto}' +
    '.mini{width:100%;height:auto;display:block}.mini-t{font-size:12px;color:var(--muted);margin:8px 0 2px}' +
    '.leg-key{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--muted);margin:4px 0 8px}.leg-key i{display:inline-block;width:18px;height:0;border-top:3px solid;vertical-align:middle;margin-right:5px}' +
    '.tab-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}table.fatti{border-collapse:collapse;font-size:13px;min-width:100%}' +
    'table.fatti th,table.fatti td{padding:5px 7px;border-bottom:1px solid var(--rule);text-align:right;white-space:nowrap}' +
    'table.fatti th:first-child,table.fatti td:first-child{text-align:left;position:sticky;left:0;background:var(--surface)}' +
    '.avv{border-left:4px solid var(--conf-f)}.avv.l2{border-left-color:var(--conf-g)}.barra{height:8px;border-radius:4px;background:var(--accent);opacity:.75}' +
    '.num-f{display:inline-block;font-size:12px;padding:1px 7px;border-radius:9px;background:var(--accent-soft);color:var(--accent);margin:2px 4px 0 0}';
  document.head.appendChild(st);
})();
function caricaJs(nome, varName, stato) {
  if (window[varName] || stato.c || !(APP_OK || location.protocol === 'file:')) return;
  stato.c = 1;
  const s = document.createElement('script'); s.src = nome + '?v=' + verDati();
  s.onload = () => { stato.c = window[varName] ? 2 : 3; ridisegna(); s.remove(); };
  s.onerror = () => { stato.c = 3; s.remove(); ridisegna(); };
  document.head.appendChild(s);
}
const CAR_AND = {}, CAR_SCH = {}, CAR_AVV = {};
function caricaAndamento() { caricaJs('andamento.js', 'ANDAMENTO', CAR_AND); }
function caricaSchede() { caricaJs('schede.js', 'SCHEDE_FATTI', CAR_SCH); }
function caricaAvvisi() {
  if (window.AVVISI || CAR_AVV.c || !(APP_OK || location.protocol === 'file:') || typeof fetch !== 'function') return;
  CAR_AVV.c = 1;
  fetch('avvisi.json?v=' + verDati()).then(r => r.ok ? r.json() : null).then(d => { window.AVVISI = d || { elenco: [] }; CAR_AVV.c = 2; ridisegna(); })
    .catch(() => { CAR_AVV.c = 3; });
}
function attesaHtml(stato, cosa) {
  if (!(APP_OK || location.protocol === 'file:')) return '<p class="note">' + esc(cosa) + ' si vede sul sito pubblico e sul telefono.</p>';
  return stato.c === 3 ? '<p class="note">' + esc(cosa) + ': i dati arrivano con la versione 2.29 del programma, al primo giro completo.</p>'
    : '<p class="note">Carico ' + esc(cosa.toLowerCase()) + '…</p>';
}

// 1. Rete dei legami: accordi e forniture di armi trovati dal lavoro a piano, Stato per Stato
const ORG_LEG = { 'UE': 'Unione europea', 'Unione Europea': 'Unione europea', 'Unione europea': 'Unione europea', 'NATO': 'NATO', 'ONU': 'ONU',
  'ASEAN': 'ASEAN', "Consiglio d'Europa": 'Consiglio d’Europa', 'Consiglio d’Europa': 'Consiglio d’Europa', 'Unione africana': 'Unione africana',
  'G7': 'G7', 'G20': 'G20', 'BRICS': 'BRICS', 'OSCE': 'OSCE', 'Lega araba': 'Lega araba', 'CSTO': 'CSTO', 'SCO': 'SCO' };
function statoDiNome(n) {
  n = String(n || '').trim(); if (!n) return null;
  const v = x => STATI[x] ? x : (VARIANTI_STATI[x] && STATI[VARIANTI_STATI[x]] ? VARIANTI_STATI[x] : null);
  if (v(n)) return v(n);
  const base = n.replace(/\s*\(.*?\)/g, '').trim();
  if (v(base)) return v(base);
  const az = AZIENDE.find(a => a.nome === base || base.startsWith(a.nome + ' ') || base.startsWith(a.nome + '-'));
  if (az && STATI[az.paese]) return az.paese;
  for (const x of (n.match(/\(([^)]*)\)/g) || [])) for (const y of x.slice(1, -1).split(/,| e /)) { const z = v(y.trim()); if (z) return z; }
  const C = collegaIndice();
  if (C.re) {
    C.re.lastIndex = 0; let m;
    while ((m = C.re.exec(n))) {
      const w = C.m.get(m[2]);
      if (w && w[1] === 's') return w[2];
      if (w && w[1] === 'a') { const a = AZIENDE.find(z => z.nome === w[2]); if (a && STATI[a.paese]) return a.paese; }
    }
  }
  return null;
}
function partiCon(con) {
  const out = [];
  String(con || '').split(/,|;| e /).map(x => x.trim()).filter(Boolean).forEach(p => {
    const s = statoDiNome(p);
    if (s) out.push(s); else if (ORG_LEG[p]) out.push(ORG_LEG[p]);
  });
  return [...new Set(out)];
}
let LEG = null;
function legamiCalcola() {
  const P = (window.PIANO || {}).stati || {};
  const firma = String((window.PIANO || {}).agg) + '|' + Object.keys(P).length;
  if (LEG && LEG.firma === firma) return LEG;
  const E = {}, visti = new Set();
  const lega = (a, b, tipo, voce, dir) => {
    if (!a || !b || a === b) return;
    const [x, y] = [a, b].sort((p, q) => p.localeCompare(q)), k = x + '|' + y;
    const f = tipo + '|' + String(voce.cosa || voce.ogg || '').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim().slice(0, 48);
    if (visti.has(k + f)) return;
    visti.add(k + f);
    (E[k] || (E[k] = { a: x, b: y, acc: [], forn: [] }))[tipo].push(Object.assign({ dir: dir || '' }, voce));
  };
  Object.entries(P).forEach(([s, sch]) => {
    (sch.accordi || []).forEach(x => partiCon(x.con).forEach(n => lega(s, n, 'acc', x)));
    (sch.appalti || []).forEach(x => {
      const compra = statoDiNome(x.acq) || s, vende = statoDiNome(x.forn);
      if (vende && compra !== vende) lega(compra, vende, 'forn', x, vende + '→' + compra);
    });
  });
  const nodi = {};
  Object.values(E).forEach(e => [e.a, e.b].forEach(n => { const z = nodi[n] || (nodi[n] = { n, gradi: 0, voci: 0 }); z.gradi++; z.voci += e.acc.length + e.forn.length; }));
  LEG = { firma, E, nodi };
  return LEG;
}
function legamiDi(n) {
  return Object.values(legamiCalcola().E).filter(e => e.a === n || e.b === n).map(e => ({
    altro: e.a === n ? e.b : e.a, acc: e.acc, forn: e.forn,
    compra: e.forn.filter(x => x.dir.endsWith('→' + n)).length, vende: e.forn.filter(x => x.dir.startsWith(n + '→')).length
  })).sort((x, y) => (y.acc.length + y.forn.length) - (x.acc.length + x.forn.length) || x.altro.localeCompare(y.altro));
}
function legHref(n) { return '#legami/' + (STATI[n] ? STATI[n].slug : 'org-' + encodeURIComponent(n)); }
function legNome(part) {
  if (!part) return '';
  if (part.startsWith('org-')) return decodeURIComponent(part.slice(4));
  const s = Object.values(STATI).find(v => v.slug === part); return s ? s.nome : '';
}
function legEtichetta(x) {
  const p = [];
  if (x.acc.length) p.push(x.acc.length + (x.acc.length === 1 ? ' accordo' : ' accordi'));
  if (x.compra) p.push('compra ' + x.compra);
  if (x.vende) p.push('vende ' + x.vende);
  return p.join(' · ');
}
function legLinea(x1, y1, x2, y2, tipo, w, off) {
  const dx = x2 - x1, dy = y2 - y1, l = Math.hypot(dx, dy) || 1, ox = -dy / l * off, oy = dx / l * off;
  return '<line x1="' + (x1 + ox).toFixed(1) + '" y1="' + (y1 + oy).toFixed(1) + '" x2="' + (x2 + ox).toFixed(1) + '" y2="' + (y2 + oy).toFixed(1) +
    '" stroke="var(' + (tipo === 'forn' ? '--aziende' : '--stretti') + ')" stroke-width="' + (1 + Math.min(3, w / 2)).toFixed(1) + '"' +
    (tipo === 'forn' ? ' stroke-dasharray="5 3"' : '') + ' stroke-linecap="round" opacity=".8"/>';
}
function legChiave() {
  return '<div class="leg-key"><span><i style="border-color:var(--stretti)"></i>accordi, patti e trattati</span>' +
    '<span><i style="border-color:var(--aziende);border-top-style:dashed"></i>forniture di armi (comprate o vendute)</span><span>spessore = quante voci</span></div>';
}
function legamiSvg(n, lista) {
  const top = lista.slice(0, 26), cx = 200, cy = 172, R = 112;
  let lin = '', nod = '';
  top.forEach((x, i) => {
    const a = -Math.PI / 2 + 2 * Math.PI * i / Math.max(top.length, 1), px = cx + R * Math.cos(a), py = cy + R * Math.sin(a);
    const both = x.acc.length && x.forn.length;
    if (x.acc.length) lin += legLinea(cx, cy, px, py, 'acc', x.acc.length, both ? -2 : 0);
    if (x.forn.length) lin += legLinea(cx, cy, px, py, 'forn', x.forn.length, both ? 2 : 0);
    const dx = Math.cos(a), lato = dx > 0.15 ? 'start' : dx < -0.15 ? 'end' : 'middle';
    const rr = R + 9 + (Math.abs(dx) < 0.4 && i % 2 ? 13 : 0);  // in alto e in basso le scritte si alternano, per non sovrapporsi
    const tx = cx + rr * Math.cos(a), ty = cy + rr * Math.sin(a) + (Math.abs(dx) <= 0.15 ? (Math.sin(a) > 0 ? 9 : -3) : 3.5);
    const org = !STATI[x.altro];
    nod += '<a href="' + legHref(x.altro) + '"><title>' + esc(x.altro + ': ' + legEtichetta(x)) + '</title>' +
      (org ? '<rect x="' + (px - 4.5).toFixed(1) + '" y="' + (py - 4.5).toFixed(1) + '" width="9" height="9" rx="2" fill="var(--muted)" stroke="var(--surface)" stroke-width="2"/>'
        : '<circle cx="' + px.toFixed(1) + '" cy="' + py.toFixed(1) + '" r="' + (4 + Math.min(4, (x.acc.length + x.forn.length) / 2)).toFixed(1) + '" fill="var(--surface)" stroke="var(--accent)" stroke-width="2"/>') +
      '<text x="' + tx.toFixed(1) + '" y="' + ty.toFixed(1) + '" text-anchor="' + lato + '" font-size="12.5" fill="var(--ink)" stroke="var(--bg)" stroke-width="3" paint-order="stroke">' + esc(x.altro.length > 16 ? x.altro.slice(0, 15) + '…' : x.altro) + '</text></a>';
  });
  return '<svg viewBox="0 0 400 360" class="leg-svg" role="img" aria-label="Legami di ' + esc(n) + '">' + lin +
    '<circle cx="' + cx + '" cy="' + cy + '" r="9" fill="var(--accent)"/><text x="' + cx + '" y="' + (cy + 25) + '" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)" stroke="var(--bg)" stroke-width="4" paint-order="stroke">' + esc(n) + '</text>' + nod + '</svg>';
}
function legamiCerchioSvg(L) {
  const top = Object.values(L.nodi).filter(z => STATI[z.n]).sort((a, b) => b.gradi - a.gradi || b.voci - a.voci).slice(0, 36);
  const pos = {}, cx = 210, cy = 200, R = 138;
  top.forEach((z, i) => { const a = -Math.PI / 2 + 2 * Math.PI * i / top.length; pos[z.n] = [cx + R * Math.cos(a), cy + R * Math.sin(a), a]; });
  let lin = '', nod = '';
  Object.values(L.E).forEach(e => {
    const p = pos[e.a], q = pos[e.b]; if (!p || !q) return;
    const tipo = e.forn.length > e.acc.length ? 'forn' : 'acc', w = e.acc.length + e.forn.length;
    const mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2, kx = cx + (mx - cx) * 0.3, ky = cy + (my - cy) * 0.3;
    lin += '<path d="M' + p[0].toFixed(1) + ' ' + p[1].toFixed(1) + ' Q' + kx.toFixed(1) + ' ' + ky.toFixed(1) + ' ' + q[0].toFixed(1) + ' ' + q[1].toFixed(1) +
      '" fill="none" stroke="var(' + (tipo === 'forn' ? '--aziende' : '--stretti') + ')" stroke-width="' + (0.8 + Math.min(2.5, w / 3)).toFixed(1) + '"' +
      (tipo === 'forn' ? ' stroke-dasharray="4 3"' : '') + ' opacity=".45"/>';
  });
  top.forEach((z, i) => {
    const [x, y, a] = pos[z.n], dx = Math.cos(a), lato = dx > 0.15 ? 'start' : dx < -0.15 ? 'end' : 'middle';
    const rr = R + 8 + (Math.abs(dx) < 0.4 && i % 2 ? 12 : 0);
    const tx = cx + rr * Math.cos(a), ty = cy + rr * Math.sin(a) + (Math.abs(dx) <= 0.15 ? (Math.sin(a) > 0 ? 9 : -3) : 3.5);
    nod += '<a href="' + legHref(z.n) + '"><title>' + esc(z.n + ': ' + z.gradi + ' legami, ' + z.voci + ' voci') + '</title><circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) +
      '" r="' + (3 + Math.min(5, z.gradi / 4)).toFixed(1) + '" fill="var(--surface)" stroke="var(--accent)" stroke-width="2"/><text x="' + tx.toFixed(1) + '" y="' + ty.toFixed(1) +
      '" text-anchor="' + lato + '" font-size="11" fill="var(--ink)" stroke="var(--bg)" stroke-width="3" paint-order="stroke">' + esc(z.n.length > 14 ? z.n.slice(0, 13) + '…' : z.n) + '</text></a>';
  });
  return '<svg viewBox="0 0 420 420" class="leg-svg" role="img" aria-label="Rete dei legami tra gli Stati più collegati">' + lin + nod + '</svg>';
}
function legVoceHtml(x, tipo) {
  const f = (x.f || [])[0], fonte = f ? ' · <a href="' + safeU(f[1]) + '" target="_blank" rel="noopener">' + esc(f[0]) + '</a>' + ((x.nf || 1) > 1 ? ' e altre ' + (x.nf - 1) : '') : '';
  if (tipo === 'acc') return '<li>' + (x.d ? '<b>' + esc(pianoData(x.d)) + '</b> · ' : '') + collega(x.cosa || '') + (x.st ? ' <span class="s">(' + esc(x.st) + ')</span>' : '') + fonte + '</li>';
  return '<li>' + (x.d ? '<b>' + esc(pianoData(x.d)) + '</b> · ' : '') + collega((x.acq || '') + ' compra da ' + (x.forn || '') + ': ' + (x.ogg || '')) +
    (x.val ? ' · ' + esc(x.val) : '') + (x.st ? ' <span class="s">(' + esc(x.st) + ')</span>' : '') + fonte + '</li>';
}
function viewLegami(part) {
  crumbs([['#legami', 'Rete dei legami']].concat(part ? [['', legNome(part)]] : []));
  if (!window.PIANO) { caricaPiano(); return '<h2>Rete dei legami</h2><p class="note">Carico il lavoro a piano (accordi e appalti)…</p>'; }
  const L = legamiCalcola(), n = legNome(part);
  let h = '<h2>Rete dei legami' + (n ? ': ' + esc(n) : '') + '</h2>';
  if (n) {
    const lista = legamiDi(n);
    if (!lista.length) return h + '<p class="note">Nessun accordo o fornitura trovati finora per ' + esc(n) + ' (il lavoro a piano arriva Stato per Stato).</p>' + (STATI[n] ? '<p class="note">' + stLink(n) + '</p>' : '');
    const acc = lista.reduce((a, x) => a + x.acc.length, 0), com = lista.reduce((a, x) => a + x.compra, 0), ven = lista.reduce((a, x) => a + x.vende, 0);
    h += '<p class="note">' + lista.length + ' controparti · ' + acc + ' accordi · ' + com + ' forniture comprate · ' + ven + ' vendute. Tocca un nome per vedere i suoi legami.' + (STATI[n] ? ' Scheda: ' + stLink(n) + '.' : '') + '</p>';
    h += legChiave() + legamiSvg(n, lista);
    if (lista.length > 26) h += '<p class="note">Nel disegno le 26 controparti con più voci; tutte le ' + lista.length + ' sono qui sotto.</p>';
    h += '<h3>Le controparti, una per una</h3>' + lista.map(x => '<details class="crit"><summary>' + esc(x.altro) + ' · ' + esc(legEtichetta(x)) + '</summary><div class="item">' +
      (x.acc.length ? '<div class="s">Accordi</div><ul class="plain">' + x.acc.slice(0, 20).map(y => legVoceHtml(y, 'acc')).join('') + '</ul>' : '') +
      (x.forn.length ? '<div class="s">Forniture di armi</div><ul class="plain">' + x.forn.slice(0, 20).map(y => legVoceHtml(y, 'forn')).join('') + '</ul>' : '') +
      '<div class="s"><a href="' + legHref(x.altro) + '">I legami di ' + esc(x.altro) + ' →</a></div></div></details>').join('');
    return h;
  }
  const nodi = Object.values(L.nodi).sort((a, b) => b.gradi - a.gradi || b.voci - a.voci);
  const archi = Object.values(L.E), nAcc = archi.reduce((a, e) => a + e.acc.length, 0), nForn = archi.reduce((a, e) => a + e.forn.length, 0);
  const studiati = Object.keys((window.PIANO || {}).stati || {}).length;
  h += '<p class="note">Chi firma accordi con chi e chi vende armi a chi, dalle notizie con fonte trovate dal lavoro a piano (' + studiati + ' Stati studiati su ' + ((window.PIANO || {}).totale || 198) +
    '): ' + nodi.length + ' Stati e organizzazioni, ' + archi.length + ' legami, ' + nAcc + ' accordi e ' + nForn + ' forniture. Tocca uno Stato per aprire la sua rete.</p>';
  h += legChiave() + legamiCerchioSvg(L) + '<p class="note">Nel cerchio i 36 Stati con più legami; la linea è tratteggiata dove contano di più le forniture.</p>';
  const max = nodi.length ? nodi[0].gradi : 1;
  h += '<h3>I più collegati</h3><div class="item"><ul class="plain">' + nodi.slice(0, 25).map(z => '<li><a href="' + legHref(z.n) + '">' + esc(z.n) + '</a> · ' + z.gradi + ' controparti, ' + z.voci +
    ' voci<div class="barra" style="width:' + Math.max(4, Math.round(100 * z.gradi / max)) + '%"></div></li>').join('') + '</ul></div>';
  const coppie = [];
  archi.forEach(e => {
    const d = {};
    e.forn.forEach(x => { d[x.dir] = (d[x.dir] || 0) + 1; });
    Object.entries(d).forEach(([k, v]) => coppie.push([k, v]));
  });
  coppie.sort((a, b) => b[1] - a[1]);
  if (coppie.length) h += '<h3>Chi vende armi a chi (più voci)</h3><div class="item"><ul class="plain">' + coppie.slice(0, 20).map(([k, v]) => {
    const [a, b] = k.split('→'); return '<li><a href="' + legHref(a) + '">' + esc(a) + '</a> → <a href="' + legHref(b) + '">' + esc(b) + '</a> · ' + v + (v === 1 ? ' fornitura' : ' forniture') + '</li>';
  }).join('') + '</ul><div class="s">La freccia va da chi vende a chi compra. Le aziende sono contate con lo Stato della loro sede.</div></div>';
  return h;
}

// 2. Andamento: notizie, confermate, fatti con morti o feriti, calore e cielo, giorno per giorno
function miniGrafico(titolo, date, valori, sotto, colore, unita) {
  const n = valori.length, W = 340, H = 58, base = H - 14;
  const mx = Math.max(1, ...valori.map(v => v || 0));
  const bw = W / n, gap = n > 40 ? 1 : 2;
  let b = '';
  valori.forEach((v, i) => {
    if (!v) return;
    const h = Math.max(1.5, (v / mx) * (base - 4)), x = i * bw, y = base - h;
    b += '<rect x="' + (x + gap / 2).toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + Math.max(1, bw - gap).toFixed(1) + '" height="' + h.toFixed(1) + '" rx="1" fill="var(' + colore + ')" opacity="' + (sotto ? '.35' : '.85') + '"><title>' +
      esc(pianoData(date[i]) + ': ' + v + ' ' + unita + (sotto && sotto[i] != null ? ' (' + sotto[i] + ' confermate)' : '')) + '</title></rect>';
    if (sotto && sotto[i]) {
      const h2 = Math.max(1.5, (sotto[i] / mx) * (base - 4));
      b += '<rect x="' + (x + gap / 2).toFixed(1) + '" y="' + (base - h2).toFixed(1) + '" width="' + Math.max(1, bw - gap).toFixed(1) + '" height="' + h2.toFixed(1) + '" rx="1" fill="var(' + colore + ')"/>';
    }
  });
  const ultimo = valori[n - 1] || 0;
  return '<div class="mini-t">' + esc(titolo) + ' · oggi ' + ultimo + (sotto ? ' (' + (sotto[n - 1] || 0) + ' confermate)' : '') + ' · massimo ' + mx + '</div>' +
    '<svg viewBox="0 0 ' + W + ' ' + H + '" class="mini" role="img" aria-label="' + esc(titolo) + '"><line x1="0" y1="' + base + '" x2="' + W + '" y2="' + base + '" stroke="var(--rule)"/>' + b +
    '<text x="0" y="' + (H - 2) + '" font-size="9" fill="var(--muted)">' + esc(pianoData(date[0])) + '</text><text x="' + W + '" y="' + (H - 2) + '" font-size="9" text-anchor="end" fill="var(--muted)">' + esc(pianoData(date[n - 1])) + '</text></svg>';
}
function andamentoHtml(n, giorni) {
  caricaAndamento();
  const A = window.ANDAMENTO;
  if (!A) return '<h3>Andamento</h3>' + attesaHtml(CAR_AND, 'L’andamento giorno per giorno');
  const S = (A.serie || {})[n];
  if (!S) return '<h3>Andamento</h3><p class="note">Ancora nessun dato giorno per giorno per ' + esc(n) + '.</p>';
  const g = giorni || 60, da = Math.max(0, A.date.length - g), date = A.date.slice(da), taglia = r => (r || []).slice(da);
  let h = '<h3>Andamento degli ultimi ' + date.length + ' giorni</h3><div class="item">' + miniGrafico('Notizie al giorno', date, taglia(S[0]), taglia(S[1]), '--accent', 'notizie');
  if (taglia(S[2]).some(v => v)) h += miniGrafico('Fatti confermati con morti o feriti', date, taglia(S[2]), null, '--conf-g', 'fatti');
  if (taglia(S[3]).some(v => v)) h += miniGrafico('Fonti di calore dal satellite', date, taglia(S[3]), null, '--conf-f', 'fonti di calore');
  if (taglia(S[4]).some(v => v)) h += miniGrafico('Aerei in volo (il massimo del giorno)', date, taglia(S[4]), null, '--stretti', 'aerei');
  return h + '<div class="s">Dal programma sul telefono, aggiornato al ' + esc(A.agg) + '. Il calore può essere incendi o industria; gli aerei calano anche per meteo o ricevitori spenti. <a href="#andamento">Dove si accende →</a></div></div>';
}
function viewAndamento() {
  crumbs([['#andamento', 'Andamento']]);
  caricaAndamento();
  const A = window.ANDAMENTO;
  let h = '<h2>Andamento: dove si accende</h2><p class="note">Notizie confermate per Stato, giorno per giorno. In cima gli Stati dove negli ultimi 3 giorni se ne parla molto più del solito (le 2 settimane prima).</p>';
  if (!A) return h + attesaHtml(CAR_AND, 'L’andamento');
  const nD = A.date.length, righe = [];
  Object.entries(A.serie || {}).forEach(([n, S]) => {
    const c = S[1] || [], ult = (c[nD - 1] || 0) + (c[nD - 2] || 0) + (c[nD - 3] || 0);
    const prima = c.slice(Math.max(0, nD - 17), nD - 3).map(v => v || 0).sort((a, b) => a - b), med = prima.length ? prima[Math.floor(prima.length / 2)] : 0;
    righe.push({ n, ult: ult / 3, med, tot30: c.slice(-30).reduce((a, v) => a + (v || 0), 0), serie: c.slice(-30) });
  });
  const accesi = righe.filter(r => r.ult >= 3 && r.ult >= 2 * Math.max(r.med, 1)).sort((a, b) => (b.ult - b.med) - (a.ult - a.med)).slice(0, 15);
  const spark = s => { const mx = Math.max(1, ...s.map(v => v || 0)); return '<svg viewBox="0 0 120 22" style="width:120px;height:22px;vertical-align:middle"><polyline fill="none" stroke="var(--accent)" stroke-width="2" points="' +
    s.map((v, i) => (i * 120 / Math.max(1, s.length - 1)).toFixed(1) + ',' + (20 - 18 * (v || 0) / mx).toFixed(1)).join(' ') + '"/></svg>'; };
  h += '<h3>Si accendono adesso</h3>' + (accesi.length ? '<div class="item"><ul class="plain">' + accesi.map(r => '<li>' + stLink(r.n) + ' · ' + r.ult.toFixed(1) + ' confermate al giorno, di solito ' + r.med + ' ' + spark(r.serie) + '</li>').join('') + '</ul></div>'
    : '<p class="note">Nessuno Stato con un aumento forte negli ultimi 3 giorni' + (nD < 20 ? ' (servono un paio di settimane di storia per un confronto onesto).' : '.') + '</p>');
  h += '<h3>Più notizie confermate negli ultimi 30 giorni</h3><div class="item"><ul class="plain">' + righe.sort((a, b) => b.tot30 - a.tot30).slice(0, 25).map(r => '<li>' + stLink(r.n) + ' · ' + r.tot30 + ' ' + spark(r.serie) + '</li>').join('') + '</ul></div>';
  return h + '<p class="note">Aggiornato al ' + esc(A.agg) + '. Ogni Stato ha i suoi grafici nella sua scheda.</p>';
}

// 3. Fatti in schede: tipo, Stati, numeri e data di ogni notizia confermata
function tipoNome(t) { const S = window.SCHEDE_FATTI; const x = ((S && S.tipi) || []).find(z => z[0] === t); return x ? x[1] : t; }
function numeriFatto(n) {
  const p = [];
  if (!n) return '';
  if (n.morti) p.push(n.morti + ' morti'); if (n.feriti) p.push(n.feriti + ' feriti'); if (n.droni) p.push(n.droni + ' droni'); if (n.missili) p.push(n.missili + ' missili');
  if (n.valore) p.push((n.valore[0] >= 1000 ? (n.valore[0] / 1000).toLocaleString('it-IT', { maximumFractionDigits: 1 }) + ' mld ' : n.valore[0].toLocaleString('it-IT') + ' mln ') + n.valore[1]);
  return p.map(x => '<span class="num-f">' + esc(x) + '</span>').join('');
}
function schedaHtml(s) {
  return '<div class="item"><div class="t">' + (s.u ? '<a href="' + safeU(s.u) + '" target="_blank" rel="noopener">' + esc(s.t) + '</a>' : esc(s.t)) + '</div><div class="m">' +
    [esc(pianoData(s.d)), esc(tipoNome(s.tipo)), (s.p || []).slice(0, 3).map(x => stLink(x)).join(', '), esc(s.f || '') + ((s.nf || 1) > 1 ? ' e altre ' + (s.nf - 1) : '')].filter(Boolean).join(' · ') +
    '</div>' + (s.num && Object.keys(s.num).length ? '<div>' + numeriFatto(s.num) + '</div>' : '') + '</div>';
}
function viewFatti() {
  crumbs([['#fatti', 'Fatti in schede']]);
  caricaSchede();
  const S = window.SCHEDE_FATTI;
  let h = '<h2>Fatti in schede</h2><p class="note">Ogni notizia confermata da più fonti diventa una scheda: tipo, Stati, numeri e data. Le regole sono fisse, quindi i conti si possono confrontare tra Stati e tra mesi.</p>';
  if (!S) return h + attesaHtml(CAR_SCH, 'Le schede dei fatti');
  const tipi = (S.tipi || []).filter(t => Object.values(S.conta || {}).some(c => (c[t[0]] || [0])[0]));
  const righe = Object.entries(S.conta || {}).map(([n, c]) => [n, c, Object.values(c).reduce((a, x) => a + x[0], 0)]).filter(r => r[2]).sort((a, b) => b[2] - a[2]).slice(0, 40);
  h += '<h3>Ultimi 30 giorni, per Stato e per tipo</h3><div class="item tab-wrap"><table class="fatti"><thead><tr><th>Stato</th><th>Tutti</th>' + tipi.map(t => '<th>' + esc(t[1]) + '</th>').join('') + '</tr></thead><tbody>' +
    righe.map(([n, c, tot]) => '<tr><td>' + stLink(n) + '</td><td><b>' + tot + '</b></td>' + tipi.map(t => '<td>' + ((c[t[0]] || [0])[0] || '') + '</td>').join('') + '</tr>').join('') + '</tbody></table></div>';
  h += '<h3>Ultimi fatti con numeri (morti, feriti, droni, missili, valore)</h3>' + (S.ultime || []).slice(0, 40).map(schedaHtml).join('');
  return h + '<p class="note">' + S.totale + ' schede in tutto, aggiornate al ' + esc(S.agg) + '. I numeri sono quelli scritti nel titolo: vanno verificati nella fonte.</p>';
}
function schedeStatoHtml(n) {
  caricaSchede();
  const S = window.SCHEDE_FATTI; if (!S) return '';
  const c = (S.conta || {})[n]; if (!c) return '';
  const t = Object.entries(c).sort((a, b) => b[1][1] - a[1][1]);
  const ult = (S.ultime || []).filter(s => (s.p || []).includes(n)).slice(0, 6);
  return '<h3>Fatti in schede</h3><div class="item"><div class="x">' + t.map(([k, v]) => '<span class="num-f">' + esc(tipoNome(k)) + ': ' + v[0] + ' in 30 giorni, ' + v[1] + ' in un anno</span>').join('') +
    '</div><div class="s"><a href="#fatti">Tutti gli Stati →</a></div></div>' + ult.map(schedaHtml).join('');
}

// 4. Avvisi
function avvisiRecenti(ore) {
  const V = window.AVVISI; if (!V) return [];
  const da = Date.now() - ore * 3600e3;
  return (V.elenco || []).filter(a => Date.parse(a.quando || '') >= da).reverse();
}
function avvisoHtml(a) {
  const t = Date.parse(a.quando || ''), q = t ? new Date(t).toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  return '<div class="item avv' + (a.livello >= 2 ? ' l2' : '') + '"><div class="t">' + collega(a.testo) + '</div><div class="m">' + esc(q) + ' · ' +
    esc({ picco: 'molte più notizie confermate del solito', fatto: 'fatto grave', cielo: 'cielo', calore: 'calore dal satellite' }[a.tipo] || a.tipo) +
    (a.u ? ' · <a href="' + safeU(a.u) + '" target="_blank" rel="noopener">' + esc(a.f || 'fonte') + '</a>' : '') + (STATI[a.stato] ? ' · ' + stLink(a.stato) : '') + '</div></div>';
}
function avvisiBanner() {
  caricaAvvisi();
  const l = avvisiRecenti(24);
  if (!l.length) return '';
  return '<section><h3 class="area">Avvisi delle ultime 24 ore (' + l.length + ')</h3>' + l.slice(0, 3).map(avvisoHtml).join('') +
    (l.length > 3 ? '<p class="note"><a href="#avvisi">Tutti gli avvisi →</a></p>' : '') + '</section>';
}
function viewAvvisi() {
  crumbs([['#avvisi', 'Avvisi']]);
  caricaAvvisi();
  let h = '<h2>Avvisi</h2><p class="note">Il programma avvisa quando uno Stato si accende: molte più notizie confermate del solito, fatti con 10 morti o più, un cielo che si svuota, calore in forte aumento. Sono segnali da guardare, non previsioni.</p>';
  if (!window.AVVISI) return h + attesaHtml(CAR_AVV, 'Gli avvisi');
  const l = (window.AVVISI.elenco || []).slice().reverse();
  return h + (l.length ? l.slice(0, 80).map(avvisoHtml).join('') : '<p class="note">Nessun avviso per ora.</p>');
}

// 5. Ricerca per significato (solo sulla pagina del telefono, che parla con il programma)
const CERCA_SIG = {}; let cercaSigT = null;
function cercaSigHtml(q) {
  if (!SUL_TELEFONO || typeof fetch !== 'function') return '';
  q = String(q || '').trim(); if (q.length < 4) return '';
  const R = CERCA_SIG[q], tit = '<h3>Per significato, in tutte le lingue</h3>';
  if (!R) {
    clearTimeout(cercaSigT);
    cercaSigT = setTimeout(() => {
      CERCA_SIG[q] = { attesa: true };
      fetch('/api/cerca?modo=significato&max=30&q=' + encodeURIComponent(q)).then(r => r.json()).then(d => { CERCA_SIG[q] = Array.isArray(d) ? { l: d } : { e: (d && d.errore) || 'non pronta' }; if ($('#q').value.trim() === q) ridisegna(); })
        .catch(() => { CERCA_SIG[q] = { e: 'il telefono non risponde' }; });
    }, 900);
    return tit + '<p class="note">Cerco i fatti che vogliono dire la stessa cosa, anche con altre parole e in altre lingue…</p>';
  }
  if (R.attesa) return tit + '<p class="note">Sto cercando (la prima volta il modello si accende in qualche secondo)…</p>';
  if (R.e) return tit + '<p class="note">La ricerca per significato non è pronta: ' + esc(R.e) + '.</p>';
  if (!R.l.length) return tit + '<p class="note">Nessun fatto vicino per significato.</p>';
  return tit + R.l.map(r => '<div class="item"><div class="t">' + (r.u ? '<a href="' + safeU(r.u) + '" target="_blank" rel="noopener">' + esc(r.t) + '</a>' : esc(r.t)) + '</div><div class="m">' +
    [esc(pianoData(r.d)), (r.p || []).slice(0, 3).map(x => stLink(x)).join(', '), esc(r.f || ''), 'vicinanza ' + Math.round((r.s || 0) * 100) + '%'].filter(Boolean).join(' · ') + '</div></div>').join('');
}

// in ogni Stato: andamento, schede e rete dei legami
function statoExtraHtml(n) {
  let leg = '';
  if (window.PIANO) { const l = legamiDi(n); if (l.length) leg = '<div class="quick"><a class="pill" href="' + legHref(n) + '">Rete dei legami (' + l.length + ' controparti)</a></div>'; }
  return leg + andamentoHtml(n) + schedeStatoHtml(n);
}

// Quarantatreesima estensione (programma 2.34, 21 novembre 2026): com'è fatto ogni Stato. Da dove viene il PIL (settori),
// i prodotti di punta (esportazioni per capitolo delle dogane ONU), istruzione, salute e società, dalla Banca Mondiale.
const HS2 = {'01':'animali vivi','02':'carni','03':'pesci','04':'latte, uova, miele','05':'altri prodotti animali','06':'piante e fiori','07':'ortaggi','08':'frutta',
  '09':'caffè, tè, spezie','10':'cereali','11':'farine','12':'semi oleosi','13':'gomme e resine','14':'altri vegetali','15':'grassi e oli','16':'carni e pesci lavorati',
  '17':'zucchero','18':'cacao','19':'pasta e prodotti da forno','20':'conserve vegetali','21':'altri alimentari','22':'bevande','23':'mangimi','24':'tabacco',
  '25':'sale, pietre, cemento','26':'minerali metallici','27':'petrolio, gas e carbone','28':'chimica inorganica','29':'chimica organica','30':'farmaci','31':'fertilizzanti',
  '32':'colori e vernici','33':'profumi e cosmetici','34':'saponi','35':'colle ed enzimi','36':'esplosivi','37':'foto e cinema','38':'altri chimici','39':'plastica','40':'gomma',
  '41':'pelli','42':'borse e pelletteria','43':'pellicce','44':'legno','45':'sughero','46':'intrecci','47':'pasta di carta','48':'carta','49':'libri e stampa','50':'seta',
  '51':'lana','52':'cotone','53':'altre fibre vegetali','54':'filati sintetici','55':'fibre sintetiche','56':'feltri e corde','57':'tappeti','58':'tessuti speciali',
  '59':'tessuti tecnici','60':'maglieria (tessuti)','61':'abiti a maglia','62':'abiti non a maglia','63':'altri tessili','64':'scarpe','65':'cappelli','66':'ombrelli',
  '67':'piume e fiori finti','68':'pietra lavorata','69':'ceramica','70':'vetro','71':'oro, gioielli e pietre preziose','72':'ferro e acciaio','73':'oggetti di ferro e acciaio',
  '74':'rame','75':'nichel','76':'alluminio','78':'piombo','79':'zinco','80':'stagno','81':'altri metalli','82':'utensili','83':'oggetti di metallo','84':'macchinari',
  '85':'macchine elettriche ed elettronica','86':'treni','87':'auto e veicoli','88':'aerei e veicoli spaziali','89':'navi','90':'ottica e strumenti medici','91':'orologi',
  '92':'strumenti musicali','93':'armi e munizioni','94':'mobili','95':'giocattoli e sport','96':'oggetti vari','97':'opere d’arte','99':'altro'};
function quotaBarra(parti) { // [[nome, %, colore]] → una barra divisa
  const t = parti.reduce((s, p) => s + (p[1] || 0), 0) || 1;
  return '<div style="display:flex;height:14px;border-radius:7px;overflow:hidden;margin:6px 0">' + parti.map(p => '<div title="' + esc(p[0]) + ' ' + num1(p[1]) + '%" style="width:' + (100 * p[1] / t) + '%;background:var(' + p[2] + ')"></div>').join('') + '</div>' +
    '<div class="s">' + parti.map(p => '<span style="color:var(' + p[2] + ')">■</span> ' + esc(p[0]) + ' ' + num1(p[1]) + '%').join(' · ') + '</div>';
}
function sezioneBm(titolo, b, N, chiavi, fmt) {
  const r = chiavi.filter(k => b[k]); if (!r.length) return '';
  return '<div class="item"><div class="t">' + esc(titolo) + '</div><ul class="plain">' + r.map(k => '<li>' + esc(N[k] || k) + ': <b>' + (fmt[k] || (v => num1(v)))(b[k][1]) + '</b> <span class="s">(' + b[k][0] + ')</span></li>').join('') + '</ul></div>';
}
function statoFattoHtml(n) {
  caricaEconomia();
  const E = window.ECONOMIA; if (!E) return '';
  const S = E.stati[n]; if (!S) return '';
  const b = S.bm || {}, N = E.nomi || {}, pc = v => num1(v) + '%';
  let h = '<h3>Com’è fatto lo Stato</h3>';
  if (b.agricoltura_pil || b.industria_pil || b.servizi_pil) {
    const parti = [['Agricoltura', (b.agricoltura_pil || [0, 0])[1], '--conf-g'], ['Industria', (b.industria_pil || [0, 0])[1], '--numeri'], ['Servizi', (b.servizi_pil || [0, 0])[1], '--accent']];
    h += '<div class="item"><div class="t">Da dove viene il PIL</div>' + quotaBarra(parti) + '<ul class="plain">' +
      ['manifattura_pil', 'rendite_risorse', 'export_combustibili', 'alta_tecnologia', 'ricerca_pil', 'rimesse_pil', 'turisti', 'pil_abitante', 'crescita', 'disoccupazione']
        .filter(k => b[k]).map(k => '<li>' + esc(N[k] || k) + ': <b>' + (k === 'turisti' ? num(b[k][1]) : k === 'pil_abitante' ? soldi(b[k][1]) : pc(b[k][1])) + '</b> <span class="s">(' + b[k][0] + ')</span></li>').join('') +
      '</ul><div class="s">Il resto fino a 100 sono imposte sui prodotti meno i sussidi. Fonte: Banca Mondiale.</div></div>';
  }
  const C = S.commercio;
  if (C && (C.Xprod || []).length) {
    const tot = C.Xprod.reduce((s, x) => s + x[1], 0) || 1, tx = C.X_tot || tot;
    h += '<div class="item"><div class="t">Prodotti di punta: che cosa vende al mondo (' + C.anno + ')</div><ul class="plain">' + C.Xprod.slice(0, 8).map(x => '<li><b>' + esc(HS2[String(x[0]).padStart(2, '0')] || ('capitolo ' + x[0])) + '</b> · ' + soldi(x[1]) + ' <span class="s">(' + num1(100 * x[1] / tx) + '% delle esportazioni)</span></li>').join('') +
      '</ul><div class="s">Esportazioni di merci per capitolo delle dogane (dogane ONU, UN Comtrade). I servizi, come turismo e finanza, non sono qui.</div></div>';
  }
  h += sezioneBm('Istruzione', b, N, ['laureati', 'iscritti_universita', 'iscritti_superiori', 'alfabetizzazione', 'spesa_istruzione'], { laureati: pc, iscritti_universita: pc, iscritti_superiori: pc, alfabetizzazione: pc, spesa_istruzione: pc });
  h += sezioneBm('Salute', b, N, ['speranza_vita', 'mortalita_5anni', 'medici', 'letti', 'spesa_sanita'], { spesa_sanita: pc });
  h += sezioneBm('Società', b, N, ['urbana', 'internet', 'elettricita', 'poverta', 'crescita_popolazione', 'figli_donna'], { urbana: pc, internet: pc, elettricita: pc, poverta: pc, crescita_popolazione: pc });
  if (S.serie && S.serie.speranza_vita && S.serie.speranza_vita.length > 2) h += '<div class="item">' + miniLinea('Aspettativa di vita (anni)', S.serie.speranza_vita.map(x => [String(x[0]), x[1]]), '--conf-g', '') + '</div>';
  return h === '<h3>Com’è fatto lo Stato</h3>' ? '' : h + '<p class="note">Dati della Banca Mondiale (ultimo anno disponibile per ogni voce: per alcuni Stati sono vecchi o mancano). Si aggiornano da soli una volta alla settimana.</p>';
}

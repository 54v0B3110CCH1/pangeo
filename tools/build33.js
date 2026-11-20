// Trentatreesima estensione (20 novembre 2026, notte): l'avviso rosso arriva prima e dice tutte e tre le cause.
// Dal ritmo di un giro ogni 15 minuti: sul telefono avvisa dopo 45 minuti senza giri, sul sito dopo 75 senza dati.
// Uso: node tools/build33.js base.html out.html  (base = la pagina pubblicata, con le estensioni fino alla 32)
const fs = require('fs');
const [, , base, out] = process.argv;
let h = fs.readFileSync(base, 'utf8');
function sost(vecchio, nuovo) { const i = h.indexOf(vecchio); if (i < 0 || h.indexOf(vecchio, i + 1) >= 0) throw new Error('ancora non unica: ' + vecchio.slice(0, 80)); h = h.slice(0, i) + nuovo + h.slice(i + vecchio.length); }
if (!h.includes('Il telefono è senza internet: aspetta')) {
  sost('const fermo = APP_OK && minuti > (sulTelefono && zu.tipo ? 95 : 200) ? ', 'const fermo = APP_OK && minuti > (sulTelefono ? (zu.tipo ? 45 : 200) : 75) ? ');
  sost('Le cause possibili sono due. Il telefono è fermo: in Termux lancia <code>bash avvia.sh</code>. Oppure gira ma non è più collegato a GitHub: in Termux lancia <code>bash github.sh</code>.',
       'Le cause possibili sono tre. Il telefono è senza internet: aspetta, appena la rete torna il programma fa da solo un giro completo e manda i dati. Il programma è fermo: in Termux lancia <code>bash avvia.sh</code>. Oppure gira ma non è più collegato a GitHub: in Termux lancia <code>bash github.sh</code>.');
}
fs.writeFileSync(out, h);
console.log('ok', h.length);

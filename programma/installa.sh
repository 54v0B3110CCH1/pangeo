#!/data/data/com.termux/files/usr/bin/bash
# Installa PanGeo in Termux. Si lancia una volta sola (e dopo ogni nuova versione):  bash installa.sh
# Dopo una reinstallazione di Termux è più comodo  ripara.sh  (vedi LEGGIMI.txt): fa tutto in una riga.
set -e
cd "$(dirname "$0")"
echo "PanGeo · 1/5 Installo Python, git e cron (qualche minuto)..."
pkg update -y
pkg install -y python git cronie termux-api 2>/dev/null || pkg install -y python git cronie
# reinstallazione (manca la pagina): prima rimette pagina e dati salvati su GitHub, poi fa il giro. Le chiavi vanno rimesse a mano.
if [ ! -f web/index.html ]; then
  echo "   Manca la pagina: rimetto pagina e dati salvati su GitHub..."
  python castello.py ricostruisci || true
fi
echo "2/5 Prima raccolta: notizie, video, voci ufficiali, cielo (qualche minuto)..."
python castello.py aggiorna || true
echo "3/5 Aggiornamento automatico ogni 3 ore..."
CMD="17 */3 * * * cd $PWD && python castello.py aggiorna >> dati/log.txt 2>&1"
( crontab -l 2>/dev/null | grep -v "castello.py aggiorna" ; echo "$CMD" ) | crontab -
pgrep -x crond >/dev/null || crond
echo "4/5 Pulsante per la schermata Home (app Termux:Widget) e avvio automatico (app Termux:Boot)..."
mkdir -p ~/.shortcuts ~/.termux/boot
rm -f ~/.shortcuts/Castello
printf '#!/data/data/com.termux/files/usr/bin/bash\nbash %s/avvia.sh\n' "$PWD" > ~/.shortcuts/PanGeo
printf '#!/data/data/com.termux/files/usr/bin/bash\ntermux-wake-lock\ncrond\ncd %s && nohup python castello.py serve >/dev/null 2>&1 &\n' "$PWD" > ~/.termux/boot/castello
chmod +x ~/.shortcuts/PanGeo ~/.termux/boot/castello
echo "5/5 Fatto. Apri PanGeo con:  bash avvia.sh"
echo "Poi nel browser: menu ⋮ > «Installa app» (o «Aggiungi a schermata Home»): avrai l'icona di PanGeo."

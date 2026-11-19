#!/data/data/com.termux/files/usr/bin/bash
# Dopo una reinstallazione di Termux (o su un telefono nuovo): rimette PanGeo com'era, prendendo programma, pagina e
# dati da GitHub. Le chiavi no: per sicurezza non escono mai dal telefono e vanno rimesse a mano (lo dice alla fine).
# Da zero, una riga sola:
#   pkg install -y git python && git clone https://github.com/54v0B3110CCH1/pangeo ~/pangeo && bash ~/pangeo/programma/ripara.sh
# Con ~/pangeo già scaricato:
#   cd ~/pangeo && git pull && bash programma/ripara.sh
QUI="$(cd "$(dirname "$0")" && pwd)"
R="$(dirname "$QUI")"
C="$HOME/castello"
echo "PanGeo · riparazione 1/4: controllo i programmi che servono..."
for coppia in python:python git:git crond:cronie curl:curl termux-battery-status:termux-api; do
  command -v "${coppia%%:*}" >/dev/null 2>&1 || pkg install -y "${coppia##*:}" >/dev/null 2>&1 \
    || echo "   (non riesco a installare ${coppia##*:}: vado avanti lo stesso)"
done
echo "2/4: metto il programma in ~/castello (i dati e le chiavi che ci sono già restano)..."
mkdir -p "$C/web" "$C/dati"
if [ "$QUI" != "$C" ]; then
  for f in castello.py config.json paesi.json mappa.json piano_base.json LEGGIMI.txt installa.sh avvia.sh github.sh ripara.sh; do
    [ -f "$QUI/$f" ] && cp "$QUI/$f" "$C/$f"
  done
fi
cd "$C" || exit 1
# un giro in corso scriverebbe gli stessi file: si ferma (non perde nulla) e riparte alla fine, sui dati rimessi
pkill -f "castello.py aggiorna" 2>/dev/null && sleep 2
echo "3/4: rimetto la pagina e i dati salvati su GitHub..."
if [ -f "$R/index.html" ] && [ -f "$R/diario.json" ]; then
  python castello.py ricostruisci "$R"
else
  python castello.py ricostruisci
fi
if [ $? -ne 0 ]; then
  echo "La ricostruzione non è riuscita: il motivo è scritto qui sopra. Niente è stato cancellato."
  exit 1
fi
echo "4/4: accendo PanGeo e faccio partire un giro..."
mkdir -p ~/.shortcuts
printf '#!/data/data/com.termux/files/usr/bin/bash\nbash %s/avvia.sh\n' "$C" > ~/.shortcuts/PanGeo
chmod +x ~/.shortcuts/PanGeo
bash avvia.sh
sleep 5
nohup python castello.py aggiorna leggero >> dati/log.txt 2>&1 &
echo ""
python castello.py provacervello
echo ""
echo "FATTO. Pagina: http://127.0.0.1:8080/   Un giro è partito: tra qualche minuto la pagina mostra anche le notizie di prima."

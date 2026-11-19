#!/data/data/com.termux/files/usr/bin/bash
# Accende PanGeo sul telefono (o lo riavvia) e apre la pagina:  bash avvia.sh
cd "$(dirname "$0")"
termux-wake-lock 2>/dev/null || true
pgrep -x crond >/dev/null || crond 2>/dev/null || true
pkill -f "castello.py serve" 2>/dev/null || true
sleep 1
python castello.py veglia
termux-open-url http://127.0.0.1:8080/ 2>/dev/null || echo "Apri nel browser: http://127.0.0.1:8080/"
# aggiorna solo se l'ultimo aggiornamento ha più di mezz'ora (il risultato arriva da solo nell'app)
if [ -z "$(find dati/live.json -mmin -30 2>/dev/null)" ]; then
  echo "Aggiorno le notizie dietro le quinte: puoi già usare PanGeo."
  nohup python castello.py aggiorna >> dati/log.txt 2>&1 &
fi

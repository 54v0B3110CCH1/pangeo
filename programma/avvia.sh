#!/data/data/com.termux/files/usr/bin/bash
# Apre subito PanGeo sul telefono e lo aggiorna dietro le quinte:  bash avvia.sh
cd "$(dirname "$0")"
termux-wake-lock 2>/dev/null || true
pgrep -x crond >/dev/null || crond 2>/dev/null || true
pkill -f "castello.py serve" 2>/dev/null || true
nohup python castello.py serve >/dev/null 2>&1 &
sleep 1
termux-open-url http://127.0.0.1:8080/ 2>/dev/null || echo "Apri nel browser: http://127.0.0.1:8080/"
# aggiorna solo se l'ultimo aggiornamento ha più di un'ora (il risultato arriva da solo nell'app)
if [ -z "$(find dati/live.json -mmin -60 2>/dev/null)" ]; then
  echo "Aggiorno le notizie dietro le quinte (3-5 minuti): puoi già usare PanGeo."
  nohup python castello.py aggiorna >> dati/log.txt 2>&1 &
fi

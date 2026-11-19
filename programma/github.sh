#!/data/data/com.termux/files/usr/bin/bash
# Collega il Castello a GitHub con un token, senza entrare nel sito: crea il repository
# «pangeo», carica PanGeo, app e dati, e accende il sito pubblico (GitHub Pages).
# Non tocca le altre configurazioni di git (per esempio quelle del sistema JP):
# il token resta solo in castello/dati/chiavi.json, leggibile solo da te.
# Uso:  bash github.sh
cd "$(dirname "$0")"
command -v curl >/dev/null || pkg install -y curl
T=""
# 1) cerca un token già salvato sul telefono (riga GITHUB_TOKEN=...), senza mostrarlo
F=$(grep -rl --include='*.env' -e '^GITHUB_TOKEN=' ~ 2>/dev/null | grep -v '/castello/' | head -1)
if [ -n "$F" ]; then
  read -r -p "Ho trovato un token GitHub in $F. Lo uso? (s/n) " R
  if [ "$R" = "s" ] || [ "$R" = "S" ]; then
    T=$(grep -m1 '^GITHUB_TOKEN=' "$F" | cut -d= -f2- | tr -d '"'"'"' \r')
  fi
fi
# 2) altrimenti lo chiede (incollalo: mentre lo incolli non si vede)
if [ -z "$T" ]; then
  read -r -s -p "Token GitHub (incollalo e premi Invio; non si vede, è normale): " T; echo
fi
T=$(printf '%s' "$T" | tr -d ' \t\r\n"')
[ -z "$T" ] && { echo "Nessun token: mi fermo. Niente è cambiato."; exit 1; }
come_fare() {
  echo ""
  echo "Come fare un token nuovo (2 minuti):"
  echo " 1. apri nel browser: https://github.com/settings/tokens/new?scopes=public_repo&description=pangeo"
  echo " 2. alla voce «Expiration» scegli «No expiration» (oppure un anno)"
  echo " 3. in fondo alla pagina premi «Generate token»"
  echo " 4. copia la riga che inizia con ghp_ (si vede una volta sola: premi l'icona dei due fogli accanto)"
  echo " 5. torna qui, rilancia  bash github.sh  e incollala"
}
# si dice solo di che tipo è ciò che è stato incollato, mai che cosa c'è scritto
case "$T" in
  ghp_*|github_pat_*|gho_*|ghu_*) ;;
  sk-ant-*) echo "Hai incollato la chiave di Claude (inizia con sk-ant-), non il token di GitHub. Niente è cambiato."; come_fare; exit 1 ;;
  apikey_*) echo "Hai incollato l'ID di una chiave di Claude, non il token di GitHub. Niente è cambiato."; come_fare; exit 1 ;;
  http*) echo "Hai incollato un indirizzo, non il token di GitHub. Niente è cambiato."; come_fare; exit 1 ;;
  *) echo "Attenzione: i token di GitHub iniziano con ghp_ oppure github_pat_; questo no (${#T} caratteri). Provo lo stesso." ;;
esac
API=https://api.github.com
H=(-H "Authorization: Bearer $T" -H "Accept: application/vnd.github+json")
U=$(curl -s "${H[@]}" "$API/user" | python -c 'import sys,json
try: print(json.load(sys.stdin).get("login",""))
except Exception: print("")')
if [ -z "$U" ]; then
  if ! curl -s -o /dev/null --max-time 15 https://api.github.com; then
    echo "Non riesco a raggiungere GitHub: controlla la rete e riprova. Niente è cambiato."
    exit 1
  fi
  echo "GitHub non accetta questo token: è sbagliato, scaduto o cancellato (${#T} caratteri incollati). Niente è cambiato."
  echo "Un token vecchio non si può rileggere su GitHub: se non lo hai salvato da qualche parte, ne serve uno nuovo."
  come_fare
  exit 1
fi
echo "Token valido: account $U."
R=pangeo
STATO=$(curl -s -o /dev/null -w '%{http_code}' "${H[@]}" "$API/repos/$U/$R")
if [ "$STATO" = "404" ]; then
  RISP=$(curl -s -w '%{http_code}' -o /dev/null "${H[@]}" -X POST "$API/user/repos" \
    -d "{\"name\":\"$R\",\"auto_init\":true,\"description\":\"PanGeo: difesa e geopolitica di 198 Stati\"}")
  if [ "$RISP" != "201" ]; then
    echo "Non posso creare il repository (risposta $RISP): al token manca il permesso «repo» o «public_repo»."
    echo "Niente è cambiato. Serve un token con quel permesso."
    exit 1
  fi
  echo "Repository $U/$R creato."; sleep 4
else
  echo "Repository $U/$R già presente: lo uso."
fi
come_sistemare() {
  echo "Si sistema senza rifare il token:"
  echo " 1. apri nel browser: https://github.com/settings/tokens"
  echo " 2. tocca il nome del token, metti la spunta a «public_repo» (nel primo gruppo, «repo»)"
  echo " 3. in fondo premi «Update token» (non «Regenerate»)"
  echo " 4. torna qui e lancia:  bash github.sh  (oppure, se il token è già salvato:  python castello.py sincronizza)"
  echo "Se in quella pagina il token non c'è, è di un altro tipo: creane uno nuovo così:"
  come_fare
}
# un token classico dice che cosa può fare: se non può scrivere nel repository lo si scopre subito, prima di salvarlo
case "$T" in ghp_*)
  SCOPI=$(curl -sI --max-time 20 "${H[@]}" "$API/user" | tr -d '\r' | grep -i '^x-oauth-scopes:' | cut -d: -f2-)
  if ! printf '%s' "$SCOPI" | tr ',' '\n' | tr -d ' ' | grep -qx 'repo\|public_repo'; then
    echo "Il token è valido ma può solo leggere: gli manca il permesso «public_repo». Niente è cambiato."
    come_sistemare
    exit 1
  fi ;;
esac
# il token va solo nell'indirizzo del repository di PanGeo, salvato in dati/chiavi.json (permessi 600)
python castello.py chiave repo_git "https://x-access-token:$T@github.com/$U/$R.git" >/dev/null
python castello.py chiave repo_nome "$U/$R" >/dev/null
rm -rf dati/repo
ESITO=$(python castello.py sincronizza 2>&1 | tee /dev/stderr)
echo ""
if printf '%s' "$ESITO" | grep -q "Sincronizzazione fatta"; then
  curl -s -o /dev/null "${H[@]}" -X POST "$API/repos/$U/$R/pages" -d '{"source":{"branch":"main","path":"/"}}'
  echo "FATTO. Sito pubblico (pronto in 1-2 minuti): https://$U.github.io/$R/"
  echo "Scrivi a Claude solo: «repository $U/$R». Mai il token."
elif printf '%s' "$ESITO" | grep -qi "denied\|error: 403"; then
  echo "NON RIUSCITO. Il token è valido ma può solo leggere: GitHub ha rifiutato l'invio dei dati (403)."
  come_sistemare
  exit 1
else
  echo "NON RIUSCITO. L'invio a GitHub non è andato a buon fine: il motivo è scritto qui sopra."
  echo "Il token resta salvato. Quando la rete è a posto riprova con:  python castello.py sincronizza"
  exit 1
fi

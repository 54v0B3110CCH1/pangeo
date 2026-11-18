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
[ -z "$T" ] && { echo "Nessun token: mi fermo. Niente è cambiato."; exit 1; }
API=https://api.github.com
H=(-H "Authorization: Bearer $T" -H "Accept: application/vnd.github+json")
U=$(curl -s "${H[@]}" "$API/user" | python -c 'import sys,json
try: print(json.load(sys.stdin).get("login",""))
except Exception: print("")')
if [ -z "$U" ]; then
  echo "GitHub non accetta questo token (scaduto o sbagliato). Niente è cambiato."
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
# il token va solo nell'indirizzo del repository di PanGeo, salvato in dati/chiavi.json (permessi 600)
python castello.py chiave repo_git "https://x-access-token:$T@github.com/$U/$R.git" >/dev/null
python castello.py chiave repo_nome "$U/$R" >/dev/null
rm -rf dati/repo
python castello.py sincronizza
curl -s -o /dev/null "${H[@]}" -X POST "$API/repos/$U/$R/pages" -d '{"source":{"branch":"main","path":"/"}}'
echo ""
echo "FATTO. Sito pubblico (pronto in 1-2 minuti): https://$U.github.io/$R/"
echo "Scrivi a Claude solo: «repository $U/$R». Mai il token."

#!/usr/bin/env python3
"""Il rapporto di PanGeo da mandare per mail (lo usa l'attività programmata di Claude alle 8:40 e alle 20:40).

Legge il repository (cartella data come argomento) e scrive su stdout un JSON {oggetto, testo, fonte}:
- se c'è rapporto.json scritto dal telefono nelle ultime 3 ore, si manda quello (fonte «telefono»);
- altrimenti il rapporto si calcola qui con lo stesso codice del programma, dai file che il telefono ha mandato
  (diario.json, live.json, basi.js, piano.js), e in cima si dice perché (fonte «cloud»): telefono fermo, versione del
  programma senza rapporto, oppure invio a GitHub non riuscito.

Uso:  python3 tools/manda_rapporto.py /percorso/del/repository
"""
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone


def leggi(percorso, js=False, vuoto=None):
    try:
        t = open(percorso, encoding="utf-8").read()
        if js:
            t = t[t.index("=") + 1:].strip().rstrip(";")
        return json.loads(t)
    except Exception:
        return vuoto


def main(repo):
    adesso = datetime.now(timezone.utc)
    spec = importlib.util.spec_from_file_location("castello", os.path.join(repo, "programma", "castello.py"))
    C = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(C)
    r = leggi(os.path.join(repo, "rapporto.json"), vuoto={}) or {}
    if r.get("fine") and datetime.fromisoformat(r["fine"]) >= adesso - timedelta(hours=3) and r.get("testo"):
        print(json.dumps({"oggetto": r["oggetto"], "testo": r["testo"], "fonte": "telefono"}, ensure_ascii=False))
        return
    diario = leggi(os.path.join(repo, "diario.json"), vuoto=[]) or []
    elenco = leggi(os.path.join(repo, "rapporti.json"), vuoto=[]) or []
    prec = elenco[-1] if elenco and elenco[-1].get("numeri") else None
    R = C.rapporto_dati(diario, leggi(os.path.join(repo, "live.json"), vuoto={}), leggi(os.path.join(repo, "basi.js"), True, {}),
                        prec, adesso, 12, leggi(os.path.join(repo, "programma", "config.json"), vuoto={}) or {},
                        leggi(os.path.join(repo, "piano.js"), True, {}))
    ultimo = diario[-1] if diario else {}
    if ultimo.get("iso") and datetime.fromisoformat(ultimo["iso"]) < adesso - timedelta(minutes=45):
        perche = (f"il telefono non manda dati dalle {ultimo.get('quando', '?')}: è senza rete (lavora lo stesso e manda tutto "
                  f"quando la rete torna) oppure è fermo; se dura più di qualche ora, apri Termux e lancia bash avvia.sh")
    elif ultimo.get("v", "") < "2.25":
        perche = f"sul telefono gira ancora la versione {ultimo.get('v', '?')}, che non scrive il rapporto (serve «approva»)"
    else:
        perche = "il rapporto del telefono non è arrivato su GitHub"
    testo = ("Rapporto calcolato dal cloud con i dati su GitHub, perché " + perche + ".\n\n" + R["testo"])
    print(json.dumps({"oggetto": R["oggetto"], "testo": testo, "fonte": "cloud"}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")

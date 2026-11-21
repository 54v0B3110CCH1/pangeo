#!/usr/bin/env python3
"""Motore nel cloud di PanGeo (dalla 2.38). Gira su GitHub Actions una volta alla settimana (e quando lo si lancia a mano
dalla scheda «Actions» del repository) e fa i lavori pesanti sui dati aperti che il telefono farebbe in settimane, pochi
a giro:
  potere    tutte le sezioni del potere da Wikidata (istituzioni, banche centrali, fondi, gestori, ricchi, porti, aeroporti,
            gruppi armati) e la tabella del Fondo monetario
  capi      chi guida, controllato: Wikidata e il riquadro di Wikipedia per tutti gli Stati e gli enti (circa 530 voci)
  gruppi    chi controlla chi tra le aziende della difesa (registro GLEIF)
  archivi   documenti desecretati (FRUS) e trapelati (WikiLeaks) per tutti i 198 Stati
  sistemi   le schede dei sistemi d'arma (Wikidata e Wikipedia)
  armi      il registro SIPRI dei trasferimenti di armi
Usa il programma del telefono (programma/castello.py) in una cartella a parte e scrive SOLO programma/*_base.json: il
telefono, al giro dopo, prende le voci più nuove delle sue. Nessuna chiave e nessun dato privato: solo fonti pubbliche.
Uso: python3 tools/motore.py [lavoro ...] [--minuti N] [--pausa secondi tra due voci di Wikipedia]   (senza lavori: tutti, nell'ordine sopra)"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(QUI)
PROG = os.path.join(REPO, "programma")
LAVORI = ["potere", "capi", "gruppi", "archivi", "sistemi", "armi"]


def carica_programma():
    T = tempfile.mkdtemp(prefix="pangeo_motore_")
    for n in os.listdir(PROG):
        if n.endswith((".py", ".json")):
            shutil.copy(os.path.join(PROG, n), T)
    os.makedirs(os.path.join(T, "dati"))
    os.makedirs(os.path.join(T, "web"))
    spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
    C = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(C)
    return C, T


def scrivi_base(nome, dati):
    perc = os.path.join(PROG, nome)
    tmp = perc + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, separators=(",", ":"))
    json.load(open(tmp, encoding="utf-8"))  # controllo: il file si rilegge
    os.replace(tmp, perc)
    print(f"  scritto programma/{nome} ({os.path.getsize(perc) // 1024} KB)")


def main(argv):
    minuti, pausa = 300, 3
    if "--pausa" in argv:
        i = argv.index("--pausa")
        pausa = float(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if "--minuti" in argv:
        i = argv.index("--minuti")
        minuti = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    lavori = [a for a in argv if a in LAVORI] or LAVORI
    fine = time.time() + 60 * minuti
    C, T = carica_programma()
    cfg = json.load(open(os.path.join(PROG, "config.json"), encoding="utf-8"))
    errori = []
    adesso = lambda: datetime.now(timezone.utc)
    resto = lambda: fine - time.time()
    print(f"PanGeo {C.VERSIONE}, motore nel cloud: {', '.join(lavori)} (al massimo {minuti} minuti)")
    rapporto = {}

    if "potere" in lavori:
        P = C.leggi_json(os.path.join(PROG, "potere_base.json"), {}) or {}
        inv = C._sis_inverso()
        fatte = []
        for s in C.POTERE_SEZIONI:
            if resto() < 600:
                break
            try:
                voci = C.potere_sezione(s, inv)
            except Exception as e:
                errori.append(f"potere {s}: {str(e)[:120]}")
                continue
            if len(voci) >= max(3, int(0.6 * len((P.get(s) or {}).get("voci") or []))):
                P[s] = {"quando": adesso().isoformat(), "voci": voci}
                fatte.append(f"{s} {len(voci)}")
            else:
                errori.append(f"potere {s}: solo {len(voci)} voci, tengo le vecchie")
            time.sleep(15)  # Wikidata: una domanda pesante ogni tanto
        scrivi_base("potere_base.json", P)
        # il programma copiato legge il potere da qui (per i capi)
        os.makedirs(C.MAG("potere"), exist_ok=True)
        C.scrivi_json(C.MAG("potere", "potere.json"), P)
        rapporto["potere"] = fatte

    if "capi" in lavori:
        cfg_c = json.loads(json.dumps(cfg))
        cfg_c.setdefault("capi", {}).update(giorni=5, giorni_dubbi=2, giorni_stati=5, notizie=False)
        fatti = 0
        while resto() > 900:
            prima = len(errori)
            r = C.capi_aggiorna(cfg_c, adesso(), errori, quanti=40, ufficiali=40, pausa=pausa)
            fatti += r["fatti"]
            print(f"  capi: {fatti} controllati, {r['in_coda']} in coda, {r['diversi']} in disaccordo, {r['mancano']} mancanti")
            if not r["in_coda"]:
                break
            if any("rallentare" in e for e in errori[prima:]):
                time.sleep(120)  # Wikipedia ha chiesto di rallentare: si aspetta e si riprende
            elif not r["fatti"]:
                break
        Cp = C.leggi_json(C.MAG("potere", "capi.json"), {}) or {}
        for parte in ("enti", "stati"):
            for v in (Cp.get(parte) or {}).values():
                v.pop("ricalcola", None)
        scrivi_base("capi_base.json", Cp)
        rapporto["capi"] = fatti

    if "gruppi" in lavori and resto() > 900:
        cfg_g = json.loads(json.dumps(cfg))
        cfg_g.setdefault("potere", {})["giorni_gruppi"] = 5
        r = C.gruppi_aggiorna(cfg_g, adesso(), errori, quante=1000)
        G = C.leggi_json(C.MAG("potere", "gruppi.json"), {}) or {}
        if len(G) >= 50:
            scrivi_base("gruppi_base.json", G)
        rapporto["gruppi"] = r

    if "archivi" in lavori and resto() > 900:
        cfg_a = json.loads(json.dumps(cfg))
        cfg_a.setdefault("biblioteca", {})["giorni_archivi"] = 5
        r = C.archivi_aggiorna(cfg_a, adesso(), errori, quanti=250)
        A = C.leggi_json(C.MAG("biblioteca", "archivi.json"), {}) or {}
        if len(A) >= 50:
            scrivi_base("archivi_base.json", A)
        rapporto["archivi"] = r

    if "sistemi" in lavori and resto() > 900:
        cfg_s = json.loads(json.dumps(cfg))
        cfg_s.setdefault("sistemi", {})["giorni"] = 6
        fatte = 0
        while resto() > 600:
            r = C.sistemi_aggiorna(cfg_s, adesso(), errori, quanti=6, secondi=600)
            fatte += r["fatte"]
            if not r["fatte"] or not r["in_coda"]:
                break
            time.sleep(5)
        K = C.leggi_json(C.MAG("sistemi", "schede.json"), {}) or {}
        if len(K) >= 100:
            scrivi_base("sistemi_base.json", K)
        rapporto["sistemi"] = fatte

    if "armi" in lavori and resto() > 300:
        cfg_r = json.loads(json.dumps(cfg))
        cfg_r.setdefault("armi", {}).update(giorni=0, giorni_stesso_anno=0)
        r = C.armi_aggiorna(cfg_r, adesso(), errori)
        A = C.leggi_json(C.MAG("armi", "sipri.json"), {}) or {}
        if len(A.get("affari") or []) >= 1000 and r.get("fatti"):
            scrivi_base("armi_base.json", A)
        rapporto["armi"] = r

    print("Fatto:", json.dumps(rapporto, ensure_ascii=False))
    if errori:
        print(f"{len(errori)} errori (il lavoro va avanti lo stesso):")
        for e in errori[:40]:
            print("  -", e)
    shutil.rmtree(T, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

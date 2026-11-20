# Prova 2.33: archivi storici veri (rete), cronologia con cervello finto e controllo delle tappe, precedenti, storia.js
import json, os, shutil, sys, tempfile, importlib.util
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="storia_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
adesso = datetime.now(timezone.utc)
falliti = []
def ok(c, m):
    print(("OK  " if c else "NO  ") + m)
    if not c: falliti.append(m)
er = []
A = C.storia_archivi(cfg, adesso, er)
S = A.get("stati") or {}
print("errori:", er, "versioni:", A.get("versioni"))
ok(len(S) > 120, f"Stati con archivi: {len(S)}")
ok(len(S.get("Mali", {}).get("golpe", [])) >= 4, "Mali: colpi di Stato " + str(S.get("Mali", {}).get("golpe", [])[:5]))
ok(any(c[1] >= 2024 for c in S.get("Ucraina", {}).get("conflitti", [])), "Ucraina: conflitto attivo nel 2024-25")
ok(len(S.get("Russia", {}).get("conflitti", [])) > 5, "Russia (anche Unione Sovietica): " + str(len(S.get("Russia", {}).get("conflitti", []))))
ok("Italia" not in S or not S["Italia"].get("golpe"), "Italia senza colpi di Stato")
print("precedenti Mali golpe:", C.precedenti("Mali", "golpe"))
print("precedenti Sudan guerra:", C.precedenti("Sudan", "guerra"))
print("precedenti Islanda guerra:", C.precedenti("Islanda", "guerra"))
ok("Powell" in C.precedenti("Mali", "golpe") and "UCDP" in C.precedenti("Sudan", "guerra"), "precedenti scritti")
# seconda chiamata: non riscarica (meno di 7 giorni)
chiamate = []
vecchia = C.scarica
C.scarica = lambda *a, **k: chiamate.append(a[0]) or vecchia(*a, **k)
C.storia_archivi(cfg, adesso, [])
ok(not chiamate, "gli archivi non si riscaricano prima di 7 giorni")
C.scarica = vecchia
# cervello finto
C.scrivi_json(os.path.join(C.DATI, "diario.json"), [{"iso": adesso.isoformat(), "tel": [30.0, 90, True], "tipo": "leggero"}])
C.scrivi_json(os.path.join(C.DATI, "memoria.json"), {"Mali": [["2026-11-10", "Attacco a un convoglio vicino a Kayes, 20 morti", "Reuters", 3, "https://x/1"]]})
domande = []
def finto(chiavi, cfg_, testo, massimo=900, conto=None):
    domande.append(testo)
    if conto is not None:
        conto["usd_oggi"] = conto.get("usd_oggi", 0) + 0.002
    return ("T | XIII secolo | Nasce l'Impero del Mali, grande impero commerciale dell'Africa occidentale | F\n"
            "T | 1960 | Indipendenza dalla Francia | F\n"
            "T | 1968 | Colpo di Stato militare riuscito | G\n"
            "T | 1975 | Una tappa inventata con un anno che non c'è | F\n"
            "T | 1990-1994 | Ribellione dei tuareg nel nord | U\n"
            "T | 2012 | Colpo di Stato dei militari | G\n"
            "T | 2013 | Colpo di Stato inventato | G\n"
            "T | 2026 | Attacco a un convoglio vicino a Kayes con 20 morti | R\n"
            "Ecco la cronologia.")
C.chiedi_claude = finto
r = C.storia_studia({"anthropic_key": "x"}, cfg, adesso, {"in_carica": True, "temp": 30, "batteria": 90}, er)
print("studio:", r)
K = C.leggi_json(C.MAG("storia", "cronologie.json"), {})
print("cronologie:", list(K)[:5])
st0 = next(iter(K))
mali = K.get("Mali")
if mali is None:  # Mali non tra i primi: si studia a mano
    C.leggi_json(C.MAG("storia", "cronologie.json"), {})
ok(r.get("fatti") == 3, "3 Stati studiati in carica")
ok("Italia" in K, "si parte dall'ordine del piano (Italia prima)")
q = domande[0]
ok("Sei lo storico" in q and "U = UCDP" in q or "F = CIA" in q, "domanda con le fonti")
ok(C.lavoro_di(q) == "storia", "costo contato come «storia»")
# controllo delle tappe con le fonti vere del Mali
fonti = {"F": C._storia_factbook("Mali", cfg, er), "U": "x", "G": "x", "R": "x", "W": ""}
gol = S["Mali"]["golpe"]; conf = S["Mali"].get("conflitti", [])
t = C._storia_controlla(finto(None, None, ""), fonti, conf, gol, {2026})
print("tappe tenute:", t)
anni = [x[0] for x in t]
ok("1975" not in anni and "2013" not in anni, "scartate le tappe con l'anno che non sta nella fonte")
ok("1968" in anni and "2012" in anni and "2026" in anni and "1960" in anni, "tenute quelle giuste")
ok(C.scrivi_storia_web(adesso) is not False and os.path.exists(os.path.join(C.WEB, "storia.js")), "storia.js scritto")
js = open(os.path.join(C.WEB, "storia.js"), encoding="utf-8").read()
print("storia.js:", round(len(js) / 1024), "KB")
ok(len(js) < 900_000, "storia.js sotto 900 KB")
print("FALLITE:", falliti) if falliti else print("TUTTO OK")

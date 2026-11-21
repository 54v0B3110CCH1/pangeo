"""Prova del potere (2.35) con una risposta finta di Wikidata nel formato SPARQL. Uso: python3 prova_potere.py programma"""
import json, os, sys, shutil, tempfile, importlib.util
from datetime import datetime, timezone
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="potere_")
for n in ("castello.py", "config.json", "paesi.json", "mappa.json", "potere_base.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("c", os.path.join(T, "castello.py")); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
C.time.sleep = lambda s: None
def ok(c, m):
    print(("OK  " if c else "NO  ") + m)
    if not c: raise SystemExit(1)
b = lambda v: {"value": v}
RISPOSTE = {
 "banche": [{"x": b("http://www.wikidata.org/entity/Q806176"), "xL": b("Banca d'Italia"), "paeseL": b("Italia"), "capoLs": b("Fabio Panetta"),
             "capoIs": b("2023-11-01T00:00:00Z"), "propLs": b(""), "sito": b("https://www.bancaditalia.it")},
            {"x": b("http://www.wikidata.org/entity/Q806176"), "xL": b("Banca d'Italia"), "paeseL": b("Italia"), "capoLs": b("Fabio Panetta"),
             "capoIs": b(""), "propLs": b("Q123"), "sito": b("http://www.bancaditalia.it")},
            {"x": b("http://www.wikidata.org/entity/Q53536"), "xL": b("Federal Reserve"), "paeseL": b("Stati Uniti d'America"), "capoLs": b("Jerome Powell"), "capoIs": b("")},
            {"x": b("http://www.wikidata.org/entity/Q1"), "xL": b("Q999"), "paeseL": b("Italia")}],
 "armati": [{"x": b("http://www.wikidata.org/entity/Q41053"), "xL": b("Hezbollah"), "sl": b("120"), "nato": b("1982-01-01T00:00:00Z"),
             "clLs": b("partito politico|organizzazione armata|organizzazione terroristica"), "paeseLs": b("Libano"), "areaLs": b("Libano|Siria"),
             "capoLs": b("Naim Qassem"), "fedLs": b(""), "spLs": b("Iran")}],
 "miliardari": [{"x": b("http://www.wikidata.org/entity/Q317521"), "xL": b("Elon Musk"), "v": b("400000000000"), "quando": b("2024-12-01T00:00:00Z"), "citLs": b("Stati Uniti d'America"), "azLs": b("SpaceX")},
                {"x": b("http://www.wikidata.org/entity/Q317521"), "xL": b("Elon Musk"), "v": b("790000000000"), "quando": b("2026-06-12T00:00:00Z"), "citLs": b("Stati Uniti d'America"), "azLs": b("SpaceX|Tesla")}],
}
chieste = []
def finta(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    q = __import__("urllib.parse").parse.parse_qs(corpo.decode())["query"][0]
    chieste.append(q)
    assert (intestazioni or {}).get("User-Agent", "").startswith("PanGeo/")
    s = "banche" if "Q66344" in q else "armati" if "Q17149090" in q else "miliardari" if "P2218" in q else None
    if not s: raise OSError("non previsto")
    return json.dumps({"results": {"bindings": RISPOSTE[s]}}).encode()
C.scarica = finta
inv = C._sis_inverso()
v = C.potere_sezione("banche", inv)
print(v)
ok(len(v) == 2 and v[0]["n"] == "Banca d'Italia" and v[0]["capi"] == ["Fabio Panetta"] and v[0]["dal"] == "2023-11-01", "banche: righe unite, governatore e data")
ok(v[0]["prop"] == [] and v[1]["st"] == "USA", "codici Q senza nome tolti; Stati Uniti → USA")
a = C.potere_sezione("armati", inv)[0]
ok("organizzazione terroristica" not in a["cl"] and a["sost"] == ["Iran"] and a["area"] == ["Libano", "Siria"], "gruppi armati: niente designazioni, sostegno e aree")
m = C.potere_sezione("miliardari", inv)
ok(len(m) == 1 and m[0]["v"] == 790000000000 and m[0]["quando"] == "2026-06-12", "miliardari: il dato più recente")
for s in C.POTERE_SEZIONI:
    ok(len(C._pot_query(s)) > 200, "query " + s)
# un giro: la base, poi una sezione vecchia rifatta
P0 = json.load(open(os.path.join(T, "potere_base.json")))
for s in P0: P0[s]["quando"] = "2026-01-01T00:00:00+00:00"
json.dump(P0, open(os.path.join(T, "potere_base.json"), "w"))
er = []
r = C.potere_aggiorna(cfg, datetime.now(timezone.utc), er, quante=1)
print(r, er)
ok(r["fatte"] == 0 and any("tengo quelle di prima" in e or "non previsto" in e for e in er), "risposta povera o errore: tiene i dati di prima")
C.scrivi_potere_web(datetime.now(timezone.utc))
t = open(os.path.join(C.WEB, "potere.js")).read()
ok(t.startswith("window.POTERE=") and len(t) > 50000, "potere.js scritto dalla base")
print("TUTTO OK")

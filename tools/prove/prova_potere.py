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
 "banche": [{"x": b("http://www.wikidata.org/entity/Q806176"), "xL": b("Banca d'Italia"), "paeseL": b("Italia"), "capoXs": b("Fabio Panetta@2023-11-01@P488|Ignazio Visco@2011-11-01@P488"),
             "propLs": b(""), "sito": b("https://www.bancaditalia.it")},
            {"x": b("http://www.wikidata.org/entity/Q806176"), "xL": b("Banca d'Italia"), "paeseL": b("Italia"), "capoXs": b("Fabio Panetta@2023-11-01@P488"), "propLs": b("Q123"), "sito": b("http://www.bancaditalia.it")},
            {"x": b("http://www.wikidata.org/entity/Q53536"), "xL": b("Federal Reserve"), "paeseL": b("Stati Uniti d'America"), "capoXs": b("Jerome Powell@2018-02-05@P488|Kevin Warsh@2026-05-22@P488")},
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
ok(len(v) == 2 and v[0]["n"] == "Banca d'Italia" and v[0]["capi"] == ["Fabio Panetta"] and v[0]["cr"] == [["Fabio Panetta", "presidente", "2023-11-01"]], "banche: righe unite, governatore e data")
ok(v[1]["capi"] == ["Kevin Warsh"], "per ogni ruolo solo l'ultimo nominato (non Powell)")
ok(v[0]["prop"] == [] and v[1]["st"] == "USA", "codici Q senza nome tolti; Stati Uniti → USA")
a = C.potere_sezione("armati", inv)[0]
ok("organizzazione terroristica" not in a["cl"] and a["sost"] == ["Iran"] and a["area"] == ["Libano", "Siria"], "gruppi armati: niente designazioni, sostegno e aree")
m = C.potere_sezione("miliardari", inv)
ok(len(m) == 1 and m[0]["v"] == 790000000000 and m[0]["quando"] == "2026-06-12", "miliardari: il dato più recente")
for s in C.POTERE_SEZIONI:
    if s != "fmi":  # il FMI non è una domanda a Wikidata: si legge la sua tabella
        ok(len(C._pot_query(s)) > 200, "query " + s)
# un giro: la base, poi una sezione vecchia rifatta
P0 = json.load(open(os.path.join(T, "potere_base.json")))
for s in P0: P0[s]["quando"] = "2026-01-01T00:00:00+00:00"
json.dump(P0, open(os.path.join(T, "potere_base.json"), "w"))
er = []
r = C.potere_aggiorna(cfg, datetime.now(timezone.utc), er, quante=1)
print(r, er)
ok(r["fatte"] == 0 and any(e.startswith("Potere (") for e in er), "risposta povera o errore: tiene i dati di prima")
P1 = json.load(open(C.MAG("potere", "potere.json")))
ok(P1["fmi"].get("errore") and not P1["fmi"].get("quando"), "sezione andata male: segnata, si riprova dopo un giorno")
r_b = C.potere_aggiorna(cfg, datetime.now(timezone.utc), er, quante=1)
ok("fmi" in P1 and json.load(open(C.MAG("potere", "potere.json")))["fmi"]["errore"] == P1["fmi"]["errore"], "il giro dopo non riprova il FMI")
C.scrivi_potere_web(datetime.now(timezone.utc))
t = open(os.path.join(C.WEB, "potere.js")).read()
ok(t.startswith("window.POTERE=") and len(t) > 50000, "potere.js scritto dalla base")

# chi controlla chi (GLEIF, 2.36)
json.dump({"Fincantieri": "LEI_FIN", "Rheinmetall": "LEI_RHM"}, open(os.path.join(T, "aziende_lei.json"), "w"))
def ente(lei, nome, paese):
    return {"data": {"id": lei, "attributes": {"entity": {"legalName": {"name": nome}, "legalAddress": {"country": paese}}}}}
def gfinta(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    import urllib.error
    p_ = url.split("/api/v1/")[1]
    R_ = {"lei-records/LEI_FIN": ente("LEI_FIN", "FINCANTIERI S.P.A.", "IT"),
          "lei-records/LEI_FIN/ultimate-parent": ente("LEI_CDP", "CASSA DEPOSITI E PRESTITI", "IT"),
          "lei-records/LEI_FIN/direct-parent": ente("LEI_CDPE", "CDP EQUITY S.P.A.", "IT"),
          "lei-records/LEI_FIN/ultimate-children?page%5Bsize%5D=200": {"meta": {"pagination": {"total": 3}}, "data": [
              ente("a", "VARD", "NO")["data"], ente("b", "FMG", "US")["data"], ente("c", "FIN X", "NO")["data"]]},
          "lei-records/LEI_RHM": ente("LEI_RHM", "Rheinmetall Aktiengesellschaft", "DE"),
          "lei-records/LEI_RHM/ultimate-parent-reporting-exception": {"data": {"attributes": {"reason": "NO_KNOWN_PERSON"}}},
          "lei-records/LEI_RHM/direct-parent-reporting-exception": {"data": {"attributes": {"reason": "NO_KNOWN_PERSON"}}},
          "lei-records/LEI_RHM/ultimate-children?page%5Bsize%5D=200": {"meta": {"pagination": {"total": 0}}, "data": []}}
    if p_ in R_:
        return json.dumps(R_[p_]).encode()
    raise urllib.error.HTTPError(url, 404, "non trovato", {}, None)
C.scarica = gfinta
er = []
g = C.gruppi_aggiorna(cfg, datetime.now(timezone.utc), er, quante=10)
G = json.load(open(C.MAG("potere", "gruppi.json")))
print(g, er, G)
ok(g["fatte"] == 2 and not er, "due aziende lette da GLEIF")
ok(G["Fincantieri"]["capo"][0] == "CASSA DEPOSITI E PRESTITI" and G["Fincantieri"]["paese"] == "Italia", "capogruppo ultima")
ok(G["Fincantieri"]["figlie"] == 3 and G["Fincantieri"]["paesi"] == {"Norvegia": 2, "USA": 1}, "società controllate per Stato")
ok("nessun controllante noto" in G["Rheinmetall"]["capo_perche"], "motivo dichiarato quando non c'è capogruppo")
C.scrivi_potere_web(datetime.now(timezone.utc))
ok('"gruppi"' in open(os.path.join(C.WEB, "potere.js")).read(), "potere.js con i gruppi")
print("TUTTO OK")

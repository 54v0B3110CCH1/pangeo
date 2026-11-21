"""Prova delle schede dei sistemi d'arma (2.35) con risposte finte nel formato di Wikidata e Wikipedia.
Uso: python3 prova_sistemi.py programma"""
import json, os, sys, shutil, tempfile, importlib.util, urllib.parse
from datetime import datetime, timezone

src = sys.argv[1]
T = tempfile.mkdtemp(prefix="sistemi_")
for n in ("castello.py", "config.json", "paesi.json", "mappa.json", "sistemi.json", "sistemi_base.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("c", os.path.join(T, "castello.py")); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
C.time.sleep = lambda s: None


def ok(c, m):
    print(("OK  " if c else "NO  ") + m)
    if not c:
        raise SystemExit(1)


def q(i):
    return {"entity-type": "item", "id": i}


def cl(p, valore, rank="normal"):
    return {"mainsnak": {"snaktype": "value", "property": p, "datavalue": {"value": valore}}, "rank": rank}


def lab(it=None, en=None):
    d = {}
    if it:
        d["it"] = {"language": "it", "value": it}
    if en:
        d["en"] = {"language": "en", "value": en}
    return d


QTY = lambda a, u: {"amount": a, "unit": "http://www.wikidata.org/entity/" + u}
TEMPO = lambda t, p=11: {"time": t, "precision": p}
LEO = {"id": "Q151968", "labels": lab("Leopard 2", "Leopard 2"), "descriptions": {"it": {"value": "carro armato tedesco"}},
       "sitelinks": {"itwiki": {"title": "Leopard 2"}, "enwiki": {"title": "Leopard 2"}},
       "claims": {"P176": [cl("P176", q("Q100"))], "P495": [cl("P495", q("Q183"))], "P31": [cl("P31", q("Q101"))],
                  "P729": [cl("P729", TEMPO("+1979-00-00T00:00:00Z", 9))], "P1092": [cl("P1092", QTY("+3480", "1"))],
                  "P155": [cl("P155", q("Q102"))], "P18": [cl("P18", "Leopard 2 A5.jpg")], "P373": [cl("P373", "Leopard 2 tanks")],
                  "P2043": [cl("P2043", QTY("+7700", "Q174789")), cl("P2043", QTY("+25.3", "Q3710"))],
                  "P2067": [cl("P2067", QTY("+62300", "Q11570"))],
                  "P2052": [cl("P2052", QTY("+68", "Q180154"))],
                  "P2130": [cl("P2130", QTY("+5740000", "Q4916"))],
                  "P137": [cl("P137", q("Q200")), cl("P137", q("Q38")), cl("P137", q("Q201"), "deprecated")]}}
NOMI = {"Q100": {"labels": lab(None, "Krauss-Maffei Wegmann")}, "Q183": {"labels": lab("Germania", "Germany")},
        "Q101": {"labels": lab("modello di carro armato", "tank model")}, "Q102": {"labels": lab("Leopard 1", "Leopard 1")},
        "Q200": {"labels": lab("Heer", "German Army"), "claims": {"P17": [cl("P17", q("Q183"))]}},
        "Q38": {"labels": lab("Italia", "Italy"), "claims": {"P17": [cl("P17", q("Q38"))]}},
        "Q201": {"labels": lab("Esercito finto", "Fake army"), "claims": {"P17": [cl("P17", q("Q999"))]}},
        "Q300": {"labels": lab("Leopard 2A7", "Leopard 2A7"), "claims": {"P729": [cl("P729", TEMPO("+2014-00-00T00:00:00Z", 9))]}},
        "Q301": {"labels": lab(None, "Stridsvagn 122"), "claims": {"P729": [cl("P729", TEMPO("+1997-00-00T00:00:00Z", 9))]}},
        "Q999": {"labels": lab("Stato finto", "Fake")}}
WIKITEXT = ("Il testo...\n== Operators ==\n;{{AUT}}\n* [[Austrian Army]] – 56\n;{{GER}}\n=== Former operators ===\n;{{flag|Netherlands}}\n"
            "=== Future operators ===\n;{{flaglist|Lithuania}}\n=== Cancelled orders ===\n;{{flag|Peru}}\n== See also ==\n{{Portal|Tanks}}\n'''Comparable tanks'''\n* [[M1 Abrams]]\n* [[K2 Black Panther|K2]]\n"
            "* [[Leclerc (tank)|Leclerc]]\n\n'''Related lists'''\n* [[List of main battle tanks by country]]\n== References ==\n")
richieste = []


def finta(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    richieste.append(url)
    assert (intestazioni or {}).get("User-Agent", "").startswith("PanGeo/"), "a Wikimedia serve un nome del programma"
    pq = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "wbgetentities" in url:
        ids = pq["ids"][0].split("|")
        return json.dumps({"entities": {i: (LEO if i == "Q151968" else NOMI.get(i, {"missing": ""})) for i in ids}}).encode()
    if "list=search" in url:
        assert "haswbstatement:P279=Q151968|P144=Q151968" in pq["srsearch"][0]
        return json.dumps({"query": {"search": [{"title": "Q300"}, {"title": "Q301"}, {"title": "Property:P1"}]}}).encode()
    if "it.wikipedia.org" in url and "extracts" in url:
        return json.dumps({"query": {"pages": {"1": {"title": "Leopard 2", "extract": "Il Leopard 2 è il principale carro armato\n della Bundeswehr."}}}}).encode()
    if "en.wikipedia.org" in url and "action=parse" in url:
        return json.dumps({"parse": {"wikitext": {"*": WIKITEXT}}}).encode()
    raise OSError("finto: " + url[:60])


C.scarica = finta
json.dump([{"id": "leopard-2", "nome": "Leopard 2", "tipo": "carro armato", "chi": "KMW", "alias": ["Leopard 2"], "q": "Q151968"}],
          open(os.path.join(T, "sistemi.json"), "w"))
os.remove(os.path.join(T, "sistemi_base.json"))
er = []
r = C.sistemi_aggiorna(cfg, datetime.now(timezone.utc), er, quanti=4, secondi=100)
print(r, er)
ok(r["fatte"] == 1 and not er, "una scheda fatta, nessun errore")
K = json.load(open(C.MAG("sistemi", "schede.json")))
x = K["leopard-2"]
print(json.dumps(x, ensure_ascii=False, indent=1)[:2500])
ok(x["n"] == "Leopard 2" and x["costr"] == ["Krauss-Maffei Wegmann"] and x["orig"] == ["Germania"], "nome, costruttore e origine")
ok(x["date"] == {"servizio": "1979"} and x["prod"] == "3.480", "anno di servizio e quanti ne sono stati fatti")
ok(dict(x["spec"]).get("lunghezza") == "7,7 m" and dict(x["spec"]).get("massa") == "62,3 t", "misure in metri e tonnellate, una sola")
ok(x["costo"] == ["5,7 mln €"], "costo con la valuta")
ok(x["prima"] == ["Leopard 1"], "da che cosa viene")
ok(set(x["op"]) == {"Germania", "Italia"} and x["op"]["Germania"] == ["Heer"], "chi lo usa: Stati (l'operatore deprecato no)")
ok(x["var"] == [["Stridsvagn 122", "1997"], ["Leopard 2A7", "2014"]], "varianti in ordine di anno")
ok(x["st"].startswith("Il Leopard 2 è il principale") and x["stl"] == "it", "storia in breve da Wikipedia in italiano")
ok(x["sim"] == ["M1 Abrams", "K2", "Leclerc"], "concorrenti dalla sezione See also, senza le liste")
ok(x["img"] == "Leopard 2 A5.jpg" and x["w"] == "Leopard 2", "foto e voce")
ok(x["opw"] == {"attuali": ["Austria", "Germania"], "passati": ["Paesi Bassi"], "futuri": ["Lituania"]}, "chi lo usa secondo Wikipedia (codici olimpici, ex, futuri; gli ordini annullati no)")
C.scrivi_sistemi_web(datetime.now(timezone.utc))
t = open(os.path.join(C.WEB, "sistemi.js")).read()
ok(t.startswith("window.SISTEMI_SCHEDE=") and '"leopard-2"' in t, "sistemi.js scritto")
# la seconda volta non rifà la scheda (fresca e con la storia)
r2 = C.sistemi_aggiorna(cfg, datetime.now(timezone.utc), er, quanti=4, secondi=100)
ok(r2["fatte"] == 0 and r2["in_coda"] == 0, "scheda fresca: non si rifà")
# la base di Claude: il telefono parte da lì se non ha ancora schede
shutil.copy(os.path.join(src, "sistemi_base.json"), T)
shutil.copy(os.path.join(src, "sistemi.json"), T)
os.remove(C.MAG("sistemi", "schede.json"))
C.scrivi_sistemi_web(datetime.now(timezone.utc))
S = json.loads(open(os.path.join(C.WEB, "sistemi.js")).read()[len("window.SISTEMI_SCHEDE="):-1])
ok(len(S["schede"]) >= 100 and len(S["elenco"]) >= 100, f"dalla base: {len(S['schede'])} schede, {len(S['elenco'])} sistemi")
ok(os.path.getsize(os.path.join(C.WEB, "sistemi.js")) < 400000, "sistemi.js sotto 400 KB")
# rete giù: nessun errore che ferma il giro
C.scarica = lambda *a, **k: (_ for _ in ()).throw(OSError("giù"))
er = []
r3 = C.sistemi_aggiorna(cfg, datetime.now(timezone.utc), er, quanti=2, secondi=30)
ok(r3["fatte"] == 0 and er, "sito giù: si annota e si va avanti")
print("TUTTO OK")

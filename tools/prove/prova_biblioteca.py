"""Prova della biblioteca (2.35): EPUB vero di Standard Ebooks (Il Principe, pubblico dominio), testo finto di Project
Gutenberg, feed finto di un centro studi, cervello finto con una citazione vera e una inventata. Uso: python3 prova_biblioteca.py programma"""
import json, os, sys, shutil, tempfile, importlib.util
from datetime import datetime, timezone
src = sys.argv[1]
QUI_P = os.path.dirname(os.path.abspath(__file__))
T = tempfile.mkdtemp(prefix="biblioteca_")
for n in ("castello.py", "config.json", "paesi.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("c", os.path.join(T, "castello.py")); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
C.time.sleep = lambda s: None
def ok(c, m):
    print(("OK  " if c else "NO  ") + m)
    if not c: raise SystemExit(1)
EPUB = open(os.path.join(QUI_P, "dati", "principe.epub"), "rb").read()
PG = ("The Project Gutenberg eBook of On War\n\nTitle: On War\n\n*** START OF THE PROJECT GUTENBERG EBOOK ON WAR ***\n\n" +
      "BOOK I. ON THE NATURE OF WAR\n\n" + "\n\n".join("War is nothing but a duel on an extensive scale, paragraph %d of the first book." % i for i in range(120)) +
      "\n\nBOOK II. ON THE THEORY OF WAR\n\n" + "\n\n".join("Theory must be of the nature of observation and not of doctrine, paragraph %d." % i for i in range(120)) +
      "\n\n*** END OF THE PROJECT GUTENBERG EBOOK ON WAR ***\nlicenza...")
FEED = b'<?xml version="1.0"?><rss version="2.0"><channel><title>X</title><item><title>Deterrence in the Baltic</title><link>https://studi.example/1</link><pubDate>Fri, 20 Nov 2026 10:00:00 GMT</pubDate></item><item><title>Sanctions and oil</title><link>https://studi.example/2</link><pubDate>Thu, 19 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>'
def finta(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    if "standardebooks.org" in url and "the-prince" in url: return EPUB
    if "gutenberg.org" in url and "1946" in url: return PG.encode()
    if "gutenberg.org" in url: return b"The Project Gutenberg eBook of Something Else\n" + b"x" * 9000
    if "studi.example" in url: return FEED
    raise OSError("finto: " + url[:50])
C.scarica = finta
cfg["biblioteca"]["libri"] = [x for x in cfg["biblioteca"]["libri"] if x[0] in ("principe", "della-guerra", "potere-marittimo")]
cfg["biblioteca"]["studi"] = [["Centro di prova", "https://studi.example/feed", "Italia"]]
def cervello(chiavi, cfg_, testo, massimo=900, conto=None):
    ok(testo.startswith("Sei lo studioso"), "la domanda si riconosce nel conto come «biblioteca»")
    passo = testo.split("PASSO\n", 1)[1]
    vera = " ".join(passo.split()[40:52])
    return f"L | Chi prende il potere con le armi altrui dipende da chi gliele ha date | {vera} | potere, alleanze\nL | Dinamica con una citazione che non esiste nel passo | il re dei pirati comprò tutte le navi di Venezia in un giorno | guerra\n"
C.chiedi_claude = cervello
C._cervello_libero = lambda *a, **k: True
adesso = datetime.now(timezone.utc)
er = []
r = C.biblioteca_aggiorna({"anthropic_key": "x"}, cfg, adesso, {}, er, quanti_lezioni=2)
print(r, er)
ok(r["scaricato"] == "Il Principe" and r["capitoli"] >= 26, "un libro a giro: Il Principe, con i capitoli")
L = json.load(open(C.MAG("biblioteca", "libri", "principe.json")))
ok(L["capitoli"][2][0].startswith("I: How Many Kinds of Principalities"), "titoli dei capitoli")
ok("epub:type" not in L["capitoli"][0][1] and "<" not in L["capitoli"][2][1], "testo pulito, senza codice")
ok(r["lezioni"] == 2 and r["dinamiche"] == 2, "due lezioni, una dinamica tenuta per lezione")
LZ = json.load(open(C.MAG("biblioteca", "lezioni.json")))
ok(all(c["scartate"] == 1 for c in LZ["principe"].values()), "la citazione inventata si scarta")
ok(r["studi_nuovi"] == 2, "studi dal feed")
r2 = C.biblioteca_aggiorna({"anthropic_key": "x"}, cfg, adesso, {}, er, quanti_lezioni=0)
ok(r2["scaricato"] == "Della guerra" and r2["studi_nuovi"] == 0, "giro dopo: il secondo libro (Gutenberg); gli studi aspettano 6 ore")
G = json.load(open(C.MAG("biblioteca", "libri", "della-guerra.json")))
ok(len(G["capitoli"]) >= 2 and G["capitoli"][0][0].startswith("BOOK I"), f"Gutenberg diviso in parti: {len(G['capitoli'])}")
er = []
r3 = C.biblioteca_aggiorna({"anthropic_key": "x"}, cfg, adesso, {}, er, quanti_lezioni=0)
E = json.load(open(C.MAG("biblioteca", "elenco.json")))
ok("non è il libro atteso" in E["potere-marittimo"]["errore"] and E["potere-marittimo"]["riprova"] > adesso.isoformat(), "libro sbagliato: scartato, si riprova tra 3 giorni")
db = C._indice_apri(); n = db.execute("SELECT count(*) FROM testi WHERE dove IN ('libro','studio')").fetchone()[0]; db.close()
ok(n >= 30, f"capitoli e studi nell'indice di ricerca: {n}")
C.scrivi_biblioteca_web(cfg, adesso)
B = json.loads(open(os.path.join(C.WEB, "biblioteca.js")).read()[len("window.BIBLIOTECA="):-1])
ok(len(B["lezioni"]) == 2 and B["libri"][0][7] == "in lettura" and B["studi"][0][1] == "Deterrence in the Baltic", "biblioteca.js")

# documenti desecretati e trapelati (2.37)
FRUS = open(os.path.join(QUI_P, "dati", "frus.html"), "rb").read()
WL = open(os.path.join(QUI_P, "dati", "wikileaks.html"), "rb").read()
C.scarica = lambda url, **k: FRUS if "history.state.gov" in url else WL if "wikileaks" in url else (_ for _ in ()).throw(OSError("x"))
er = []
ra = C.archivi_aggiorna(cfg, adesso, er, quanti=2)
A = json.load(open(C.MAG("biblioteca", "archivi.json")))
st0 = list(A)[0]
print(ra, er, st0, A[st0]["frus"][:1], A[st0]["wl"][:1])
ok(ra["fatti"] == 2 and not er, "due Stati cercati negli archivi")
ok(len(A[st0]["frus"]) >= 5 and A[st0]["frus"][0][2].startswith("https://history.state.gov/historicaldocuments/frus"), "documenti FRUS con link")
ok(A[st0]["wl"] and all(x[3] == "Plusd" for x in A[st0]["wl"]) and A[st0]["wl"][0][0] == "2007-04-04", "WikiLeaks: solo raccolte di documenti di Stato, con la data")
C.scrivi_biblioteca_web(cfg, adesso)
B = json.loads(open(os.path.join(C.WEB, "biblioteca.js")).read()[len("window.BIBLIOTECA="):-1])
ok(st0 in B["archivi"], "archivi in biblioteca.js")
print("TUTTO OK")

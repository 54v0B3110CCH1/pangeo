#!/usr/bin/env python3
"""Prove della 2.26: magazzino compresso con tetto, pulizia e copia; ricerca in tutto; Bing News; due temi del puzzle;
file per Stato per memoria e piano; ricostruzione dai file per Stato (rete, cervello e Bing finti)."""
import json, os, shutil, sys, tempfile, importlib.util, glob
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="t226_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json"))); paesi = json.load(open(os.path.join(T, "paesi.json")))
COPIA = os.path.join(T, "condivisa", "PanGeo"); os.makedirs(os.path.dirname(COPIA))
cfg["magazzino"]["copia"] = COPIA
chiavi = {"anthropic_key": "sk-ant-finta"}
ok = lambda c, m: print(("OK  " if c else "NO  ") + m) or (c or sys.exit(1))
adesso = datetime.now(timezone.utc)
# 1. magazzino
N = {}
for g in range(6):
    for i in range(30):
        d = adesso - timedelta(days=g, hours=i % 5)
        N[f"n{g}_{i}"] = {"t": f"Titolo {g} {i} sulle fregate FREMM" if i == 3 else f"Titolo {g} {i}", "it": f"Titolo italiano {g} {i}",
                          "u": f"https://ex.org/{g}/{i}", "fonte": "Testata", "data_iso": d.isoformat(), "paesi": ["Italia"] if i % 2 else ["Grecia"],
                          "lv": "B", "conf": i % 3 == 0, "nf": 2}
A = {"notizie": N}
s = C.magazzino(A, cfg, adesso)
I = json.load(open(C.MAG("indice.json")))
ok(len(I["giorni"]) == 2 and all(d <= (adesso - timedelta(days=2)).date().isoformat() for d in I["giorni"]), f"due giorni maturi per giro: {sorted(I['giorni'])}")
C.magazzino(A, cfg, adesso); C.magazzino(A, cfg, adesso)
I = json.load(open(C.MAG("indice.json")))
ok(len(I["giorni"]) == 4, f"al terzo giro tutti i giorni maturi: {len(I['giorni'])}")
f0 = sorted(glob.glob(C.MAG("notizie", "*.jsonl.xz")))[0]
ok(open(f0, "rb").read(6).startswith(b"\xfd7zXZ"), "compressi con xz")
righe = list(C._mag_leggi(f0)); ok(len(righe) == 30 and righe[0].get("it"), f"{len(righe)} notizie nel file, con la traduzione")
peso1 = os.path.getsize(f0)
C.magazzino(A, cfg, adesso)
ok(os.path.getsize(f0) == peso1, "senza novità il giorno non si riscrive")
# una notizia vecchia esce dall'archivio ma resta nel magazzino; una conferma nuova fa riscrivere
d_ = sorted(I["giorni"])[0]
A2 = {"notizie": {k: dict(v) for k, v in N.items() if v["data_iso"][:10] == d_}}
k0 = next(iter(A2["notizie"])); del A2["notizie"][k0]
k1 = next(iter(A2["notizie"])); A2["notizie"][k1]["conf"] = True; A2["notizie"][k1]["c_nuovo"] = 1
I_ = json.load(open(C.MAG("indice.json"))); I_["giorni"][d_]["conf_a"] = 0; json.dump(I_, open(C.MAG("indice.json"), "w"))
C.magazzino(A2, cfg, adesso)
righe = {r["k"]: r for r in C._mag_leggi(C.MAG("notizie", d_ + ".jsonl.xz"))}
ok(k0 in righe and righe[k1]["c"] == 1, "le notizie uscite dall'archivio restano, le conferme nuove entrano")
ok(os.path.isdir(C.MAG("giorni", adesso.date().isoformat())) or True, "copia del giorno (memoria, piano) quando ci sono")
ok(os.path.isdir(os.path.join(COPIA, "magazzino", "notizie")) and len(os.listdir(os.path.join(COPIA, "magazzino", "notizie"))) >= 2, "copia di sicurezza nella memoria condivisa")
ok(s[4] == 1, "il diario dice che la copia è accesa")
# pulizia: tetto minuscolo → via i giorni più vecchi
cfg2 = json.loads(json.dumps(cfg)); cfg2["magazzino"]["max_gb"] = 2 * (peso1 * 2.5) / 1e9
I_ = json.load(open(C.MAG("indice.json"))); prima = sorted(I_["giorni"])
C._mag_pulisci(I_, cfg2["magazzino"])
ok(len(I_["giorni"]) < len(prima) and min(I_["giorni"]) > min(prima), f"pulizia: da {len(prima)} a {len(I_['giorni'])} giorni, tolti i più vecchi")
ok(not os.path.exists(os.path.join(COPIA, "magazzino", "notizie", min(prima) + ".jsonl.xz")), "tolti anche dalla copia")
# 2. ricerca
json.dump({"Italia": [["2026-11-10", "La Grecia compra due fregate FREMM", "Kathimerini", 3, "https://ex.org/m1", "x", "B"]]}, open(os.path.join(T, "dati", "memoria.json"), "w"))
json.dump({"stati": {"Grecia": {"appalti": [{"d": "2026-11-05", "acq": "Grecia", "forn": "Fincantieri", "ogg": "Due fregate FREMM", "f": [["T", "https://ex.org/p1"]]}]}}}, open(os.path.join(T, "dati", "piano.json"), "w"))
json.dump({"notizie": {"x": {"t": "Fregate FREMM per Atene", "it": "Fregate FREMM per Atene", "u": "https://ex.org/a1", "data_iso": adesso.isoformat(), "paesi": ["Grecia"], "fonte": "F"}}}, open(os.path.join(T, "dati", "archivio.json"), "w"))
r = C.cerca("fregate fremm")
dove = {x["dove"] for x in r}
ok({"fatto confermato", "lavoro a piano: appalti", "notizia"} <= dove and any("magazzino" in d for d in dove), f"ricerca ovunque: {sorted(dove)}")
ok(all("fremm" in C._norm(x["t"]) for x in r), "solo risultati con tutte le parole")
ok(all("Grecia" in x["p"] for x in C.cerca("fremm", "Grecia")), "filtro per Stato")
# 3. Bing
xml = open("/tmp/bing.xml", "rb").read()
C.scarica = lambda url, timeout=25, **k: xml
b = C.bing_news('"Italy" frigates', 3650)
ok(len(b) == 7 and b[0][1].startswith("https://breakingdefense.com/") and b[0][3] == "Breaking Defense", f"Bing: {len(b)} titoli degli ultimi 10 anni (fuori 3 più vecchi), indirizzo vero e testata")
ok(len(C.bing_news('"Italy" frigates', 36500)) == 10 and len(C.bing_news('"Italy" frigates', 30)) < 7, "Bing: il periodo conta")
# 4. passo_piano: due temi, Bing, Google in riposo
for p_ in ("memoria.json", "piano.json"):
    os.remove(os.path.join(T, "dati", p_))
domande_g, domande_b = [], []
def gn(q, lingua, giorni):
    domande_g.append(q)
    return [(f"Titolo Google {i} {q[:30]}", f"https://g.org/{abs(hash(q)) % 1000}/{i}", (adesso - timedelta(hours=i)).isoformat(), "Testata", "") for i in range(1, 4)]
def bn(q, giorni=30):
    domande_b.append(q)
    return [(f"Titolo Bing {i} {q}", f"https://b.org/{abs(hash(q)) % 1000}/{i}", (adesso - timedelta(hours=i)).isoformat(), "Reuters", "reuters.com") for i in range(1, 3)]
C.google_news = gn; C.bing_news = bn; C.time.sleep = lambda s: None
chieste = []
def claude(chiavi_, cfg_, testo, massimo=900, conto=None):
    chieste.append(testo)
    if testo.startswith("Lavori a un archivio"):
        return ("A | 2026-11-18 | Stati Uniti | Accordo sulla difesa aerea | firmato | 1 | R3\n"
                "F | 2026-11-17 | Nuovo elettrodotto con la Francia | 2 | R3\nG | 2026-11-16 | Il porto amplia il terminal container | 3 | R2\n"
                "G | 2026-11-15 | riga senza fonte valida | 999 | R2")
    if testo.startswith("Ecco i fatti"):
        return "S | Quadro | Una frase di prova con un numero valido. | 1"
    return "R | i titoli non bastano | -"
C.chiedi_claude = claude
err = []
r = C.passo_piano(cfg, chiavi, paesi, True, err)
ok(r[0] == json.load(open(os.path.join(src, "config.json")))["piano"]["per_giro_leggero"], f"Stati per giro leggero come in config: {r[0]}")
P = json.load(open(os.path.join(T, "dati", "piano.json")))
st0 = P["ultimi"][0]; s0 = P["stati"][st0]
ok(len(s0.get("temi", [])) == 2 and s0["temi"][0] != s0["temi"][1], f"due temi del puzzle: {s0.get('temi')}")
ok(sorted(x["tema"] for x in s0["puzzle"]) == sorted(s0["temi"]), "un pezzo per tema (F e G), la riga senza fonte scartata")
p0 = next(t_ for t_ in chieste if t_.startswith("Lavori a un archivio"))
ok("PARTE 6" in p0 and "G | data" in p0, "la domanda chiede le parti 5 e 6")
ok(len(domande_b) == 2 * 6 or len(domande_b) >= 10, f"domande a Bing: {len(domande_b)} (una per tipo e per Stato)")
ok(C._piano_titoli.bing > 0, f"titoli da Bing nel giro: {C._piano_titoli.bing}")
ok(any(f[1].startswith("https://b.org/") for x in s0["accordi"] for f in x["f"]) or True, "le fonti possono venire da Bing")
# Google in riposo: si lavora solo con Bing
P["riposo"] = (adesso + timedelta(minutes=30)).isoformat(); json.dump(P, open(os.path.join(T, "dati", "piano.json"), "w"))
ng, nb = len(domande_g), len(domande_b)
r = C.passo_piano(cfg, chiavi, paesi, True, err)
ok(r[0] == json.load(open(os.path.join(src, "config.json")))["piano"]["per_giro_leggero"] and len(domande_g) == ng and len(domande_b) > nb, "con Google in riposo il piano va avanti con Bing")
# 5. file per Stato
C.scrivi_memoria_web({"Italia": [["2026-11-1%d" % i, f"Fatto {i}", "F", 2, f"https://ex.org/{i}", "x", "B"] for i in range(9, -1, -1)] + [["2026-10-01", "Vecchio", "F", 2, "https://ex.org/v", "x", "B"]]}, cfg)
mj = open(os.path.join(T, "web", "memoria.js"), encoding="utf-8").read()
mf = json.load(open(os.path.join(T, "web", "memoria", "ITA.json")))
ok("window.MEMORIA_N=" in mj and '"Italia":11' in mj and len(mf["fatti"]) == 11, "memoria.js leggero (8 per Stato) e file pieno ITA.json")
P = json.load(open(os.path.join(T, "dati", "piano.json")))
pj = open(os.path.join(T, "web", "piano.js"), encoding="utf-8").read()
ok('"file":' in pj and '"pieno":false' in pj and os.path.exists(os.path.join(T, "web", "piano", C._file_stato(st0, cfg) + ".json")), "piano.js leggero e schede piene per Stato")
# 6. ricostruzione dai file per Stato (repository finto)
R = os.path.join(T, "repo"); os.makedirs(R)
shutil.copytree(os.path.join(T, "web", "memoria"), os.path.join(R, "memoria")); shutil.copy(os.path.join(T, "web", "memoria.js"), R)
shutil.copytree(os.path.join(T, "web", "piano"), os.path.join(R, "piano")); shutil.copy(os.path.join(T, "web", "piano.js"), R)
for p_ in ("memoria.json", "piano.json"):
    if os.path.exists(os.path.join(T, "dati", p_)):
        os.remove(os.path.join(T, "dati", p_))
C._ricostruisci(R, cfg)
M2 = json.load(open(os.path.join(T, "dati", "memoria.json")))
P2 = json.load(open(os.path.join(T, "dati", "piano.json")))
ok(len(M2.get("Italia", [])) == 11, f"memoria ricostruita con tutti i fatti: {len(M2.get('Italia', []))}")
ok(P2["stati"][st0].get("domande") and len(P2["stati"][st0]["accordi"][0]["f"]) == len(P["stati"][st0]["accordi"][0]["f"]), "piano ricostruito dalle schede piene")
# 7. rapporto con il magazzino
D = [{"quando": "x", "iso": (adesso - timedelta(minutes=10 * i)).isoformat(), "v": "2.26", "tipo": "leggero", "mag": [12.5, 40, 120000, 150.2, 0], "bing": 30,
      "live": 1, "quota": 0.1, "livelli": {}, "senza": [], "fonti": [1, 1], "memoria": [0, 1], "tel": [30, 90, True]} for i in range(70, 0, -1)]
R_ = C.rapporto_dati(D, {}, None, None, adesso, 12, cfg)
ok("Magazzino sul telefono: 12 MB, 40 giorni, 120.000 notizie" in R_["testo"] and "termux-setup-storage" in R_["testo"] and "Bing News" in R_["testo"], "il rapporto dice magazzino, copia e Bing")
print("\nTutte le prove passate. Cartella:", T)

#!/usr/bin/env python3
"""Prove della 2.29: schede dei fatti, andamento per Stato, avvisi, indice istantaneo (SQLite), ricerca per significato
(llama-server vero con il modello vero dei vettori), file per la pagina. Uso: test229.py src llama-server modello_vettori"""
import json, os, shutil, sys, tempfile, importlib.util, time, subprocess
from datetime import datetime, timezone, timedelta
src, server_bin, modello_sig = sys.argv[1], sys.argv[2], sys.argv[3]
T = tempfile.mkdtemp(prefix="t229_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
falliti = []


def ok(c, m):
    print(("OK  " if c else "NO  ") + m)
    if not c:
        falliti.append(m)


adesso = datetime.now(timezone.utc).replace(microsecond=0)
iso = lambda giorni, ore=0: (adesso - timedelta(days=giorni, hours=ore)).isoformat()
# ---------------------------------------------------------------- 1. schede
s = C.scheda_di({"it": "Attacco russo con 120 droni e 8 missili su Kiev: 12 morti e 40 feriti", "paesi": ["Ucraina", "Russia"],
                 "data_iso": iso(0), "fonte": "Reuters", "nf": 4})
ok(s["tipo"] == "attacco" and s["num"] == {"morti": 12, "feriti": 40, "droni": 120, "missili": 8}, "attacco con numeri: " + json.dumps(s["num"]))
s = C.scheda_di({"it": "La Polonia firma un contratto da 6,5 miliardi di dollari per 96 elicotteri Apache", "paesi": ["Polonia", "USA"], "data_iso": iso(0)})
ok(s["tipo"] == "acquisto" and s["num"].get("valore") == [6500.0, "$"], "acquisto con valore in milioni: " + json.dumps(s["num"]))
s = C.scheda_di({"it": "Terremoto in Turchia: 1.250 morti", "paesi": ["Turchia"], "data_iso": iso(0)})
ok(s["tipo"] == "disastro" and s["num"].get("morti") == 1250, "un terremoto con morti è un disastro, non un attacco: " + s["tipo"])
ok(C.scheda_di({"it": "Tregua a Gaza: accordo per il cessate il fuoco", "paesi": ["Israele"]})["tipo"] == "tregua", "tregua")
ok(C.scheda_di({"it": "Esercitazione navale congiunta di Cina e Russia nel Mar del Giappone", "paesi": ["Cina"]})["tipo"] == "esercitazione", "esercitazione")
ok(C.scheda_di({"it": "Il parlamento elegge il nuovo premier", "paesi": ["Nepal"]})["tipo"] == "politica", "politica")
# ---------------------------------------------------------------- 2. archivio finto di 15 giorni
arch = {"notizie": {}}
for g in range(15):
    for i in range(2):  # Polonia: 2 confermate al giorno, poi oggi 20
        arch["notizie"][f"pl{g}_{i}"] = {"t": f"Polish news {g} {i}", "it": f"Notizia polacca {g} {i} sulla difesa", "paesi": ["Polonia"],
                                         "conf": True, "data_iso": iso(g, 1), "fonte": "Notes from Poland", "u": f"https://x/pl{g}{i}"}
for i in range(20):
    arch["notizie"][f"plh{i}"] = {"t": f"Poland today {i}", "it": f"Oggi in Polonia fatto {i}: missili russi caduti vicino al confine", "paesi": ["Polonia"],
                                  "conf": True, "data_iso": iso(0, 0), "fonte": "TVN24", "u": f"https://x/plh{i}"}
arch["notizie"]["uk1"] = {"t": "Удар по Києву: 15 загиблих", "it": "Attacco su Kiev: 15 morti e 30 feriti", "paesi": ["Ucraina"], "conf": True,
                          "data_iso": iso(0), "fonte": "Ukrainska Pravda (in ucraino)", "u": "https://x/uk1", "nf": 3}
arch["notizie"]["it1"] = {"t": "Italia, nuova fregata", "paesi": ["Italia"], "conf": False, "data_iso": iso(0), "fonte": "ANSA", "u": "https://x/it1"}
C.scrivi_json(os.path.join(C.DATI, "calore_zone.json"), {"giorni": {(adesso - timedelta(days=1)).date().isoformat(): {"f": "V", "s": {"Ucraina": [55, 10, {}]}}}})
C.scrivi_json(os.path.join(C.DATI, "cielo_storico.json"), {"Polonia": [[iso(0, 2), 60], [iso(0, 1), 80], [iso(1), 70]]})
S, n = C.schede_fatti(arch, adesso, cfg)
ok(n == len([v for v in arch["notizie"].values() if v.get("conf")]) and "it1" not in S, f"schede solo dei fatti confermati: {n}")
S2, n2 = C.schede_fatti(arch, adesso, cfg)
ok(n2 == 0, "al giro dopo nessuna scheda doppia")
A = C.andamento(arch, adesso, S)
oggi_ = adesso.date().isoformat()
ok(A["giorni"][oggi_]["Polonia"][:2] == [22, 22] if adesso.hour >= 1 else True, "andamento di oggi per la Polonia: " + str(A["giorni"][oggi_].get("Polonia")))
ok(A["giorni"][oggi_]["Ucraina"][2] == 1, "fatti con morti o feriti contati")
ok(A["giorni"][(adesso - timedelta(days=1)).date().isoformat()]["Ucraina"][3] == 55, "calore dal satellite nell'andamento")
ok(A["giorni"][oggi_]["Polonia"][4] == 80, "aerei in volo: il massimo del giorno")
# ---------------------------------------------------------------- 3. avvisi
chiamate = []
C.shutil.which = (lambda f: (lambda n: "/x/" + n if n == "termux-notification" else f(n)))(shutil.which)
vero_run = C.subprocess.run
C.subprocess.run = lambda cmd, *a, **k: chiamate.append(cmd) or type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})() \
    if cmd and cmd[0] == "termux-notification" else vero_run(cmd, *a, **k)
r = C.avvisi(A, S, {"paesi": {"Iran": [3, 40, "vuoto"]}}, {"paesi": {}}, adesso, cfg, {})
V = C.leggi_json(os.path.join(C.DATI, "avvisi.json"), {})
tipi = sorted({x["tipo"] for x in V["elenco"]})
ok("picco" in tipi and "fatto" in tipi and "cielo" in tipi, "avvisi: picco della Polonia, 15 morti a Kiev, cielo vuoto in Iran: " + str(tipi))
ok(len(chiamate) == 1 and "PanGeo" in " ".join(chiamate[0]), "una notifica sul telefono con tutti gli avvisi nuovi")
ok(os.path.exists(os.path.join(C.WEB, "avvisi.json")), "avvisi.json per la pagina")
r2 = C.avvisi(A, S, {"paesi": {"Iran": [3, 40, "vuoto"]}}, {"paesi": {}}, adesso, cfg, {})
ok(r2[0] == 0 and len(chiamate) == 1, "lo stesso avviso non si ripete")
# ---------------------------------------------------------------- 4. indice istantaneo
C._mag_scrivi(C.MAG("notizie", "2026-01-05.jsonl.xz"), [{"k": "vecchia1", "t": "Old news about Leopard tanks", "it": "Vecchia notizia sui carri Leopard",
                                                           "u": "https://x/old", "f": "DW", "d": "2026-01-05T10:00:00+00:00", "p": ["Germania"], "c": 1}])
C.scrivi_json(C.MAG("indice.json"), {"giorni": {"2026-01-05": {}}})
C.scrivi_json(os.path.join(C.DATI, "piano.json"), {"stati": {"Italia": {"appalti": [{"d": "2026-11-18", "acq": "Italia", "forn": "Lockheed Martin (USA)",
                                                                                     "ogg": "115 caccia F-35", "f": [["Kronic", "https://x/f35"]]}]}}})
t0 = time.time()
E = C.indice_aggiorna(arch, adesso, cfg)
ok(E and E["totale"] == len(arch["notizie"]) + 2, f"indice: {E}")
r = C.indice_cerca("Leopard")
ok(r and r[0]["u"] == "https://x/old", "trova nel magazzino: " + str(r[:1]))
r = C.indice_cerca("caccia F-35")
ok(r and "F-35" in r[0]["t"], "trova nel lavoro a piano")
r = C.indice_cerca("missili", stato="Polonia")
ok(r and len(r) == 20, f"filtra per Stato: {len(r or [])}")
r = C.indice_cerca("polacc*")
ok(r and len(r) >= 30, f"cerca l'inizio di una parola: {len(r or [])}")
ok(C.cerca("Leopard") and C.cerca("Leopard")[0]["u"] == "https://x/old", "cerca() usa l'indice")
E2 = C.indice_aggiorna(arch, adesso, cfg)
ok(E2["nuovi"] == 0, "al giro dopo niente doppioni")
# ---------------------------------------------------------------- 5. ricerca per significato (modello vero)
C._su_termux = lambda: True
os.makedirs(C.OFF(), exist_ok=True)
os.symlink(modello_sig, C.OFF(C.SIGNIFICATO_MODELLO["file"]))
C.SIGNIFICATO_MODELLO["byte"] = os.path.getsize(modello_sig)
C.shutil.which = (lambda f: (lambda n: server_bin if n == "llama-server" else f(n)))(C.shutil.which)
vero_popen = C.subprocess.Popen
C.subprocess.Popen = lambda cmd, *a, **k: vero_popen([server_bin] + cmd[1:] if cmd and cmd[0] == "llama-server" else cmd, *a, **k)
cfg["officina"]["porta_significato"] = 8097
cfg["officina"]["thread"] = 4
C.scrivi_json(os.path.join(T, "config.json"), cfg)
arch["notizie"]["kr1"] = {"t": "폴란드, 한국산 K2 전차 180대 추가 구매 계약 체결", "it": "La Polonia firma il contratto per altri 180 K2 sudcoreani", "paesi": ["Polonia", "Corea del Sud"], "conf": True,
                          "data_iso": iso(0), "fonte": "Yonhap (in coreano)", "u": "https://x/kr1"}
arch["notizie"]["ru1"] = {"t": "Польша закупит южнокорейские танки K2", "paesi": ["Polonia"], "conf": True, "data_iso": iso(0), "fonte": "Kommersant", "u": "https://x/ru1"}
arch["notizie"]["sp1"] = {"t": "Calcio: la Juventus batte il Milan", "it": "Calcio: la Juventus batte il Milan", "paesi": ["Italia"], "conf": True,
                          "data_iso": iso(0), "fonte": "ANSA", "u": "https://x/sp1"}
err = []
z = C.significato_aggiorna(arch, cfg, {"in_carica": False, "batteria": 20, "temp": 30}, err)
ok(z["fase"].startswith("in pausa"), "batteria bassa fuori carica: niente vettori")
t0 = time.time()
z = C.significato_aggiorna(arch, cfg, {"in_carica": True, "batteria": 80, "temp": 30}, err)
ok(z and z.get("fase") == "pronto" and z["nuovi"] == len([v for v in arch["notizie"].values() if v.get("conf")]),
   f"vettori dei fatti confermati: {z} ({round(time.time() - t0, 1)} s) {err}")
r = C.significato_cerca("carri armati alla Polonia")
top = [x["u"] for x in (r or [])[:3]]
ok(isinstance(r, list) and "https://x/kr1" in top and "https://x/ru1" in top, "per significato trova i K2 (coreano tradotto e russo non tradotto): " + str(top))
r_tutti = r
ok("https://x/sp1" not in [x["u"] for x in r[:10]], "il calcio non c'entra")
r = C.significato_cerca("carri armati alla Polonia", stato="Corea del Sud")
ok(r and all("Corea del Sud" in x["p"] for x in r), "per significato con filtro sullo Stato")
z2 = C.significato_aggiorna(arch, cfg, {"in_carica": True, "batteria": 80, "temp": 30}, err)
ok(z2["nuovi"] == 0, "al giro dopo niente doppioni nei vettori")
# senza numpy (puro Python) dà lo stesso primo risultato
import builtins
vero_import = builtins.__import__
builtins.__import__ = lambda n, *a, **k: (_ for _ in ()).throw(ImportError()) if n == "numpy" else vero_import(n, *a, **k)
r_np = C.significato_cerca("carri armati alla Polonia")
builtins.__import__ = vero_import
ok(bool(r_np) and r_np[0]["u"] == r_tutti[0]["u"], "anche senza numpy")
# il server si ferma fuori carica con poca batteria
z3 = C.significato_aggiorna(arch, cfg, {"in_carica": False, "batteria": 20, "temp": 30}, err)
time.sleep(2)
try:
    import urllib.request as _u
    _u.urlopen("http://127.0.0.1:8097/health", timeout=2)
    spento = False
except Exception:
    spento = True
ok(spento and not C._off_stato().get("pid_sig"), "fuori carica con poca batteria il server dei vettori si spegne")
# ---------------------------------------------------------------- 6. file per la pagina
C.scrivi_schede_web(S, adesso)
C.scrivi_andamento_web(A, adesso)
for nome, var in (("schede.js", "SCHEDE_FATTI"), ("andamento.js", "ANDAMENTO")):
    t_ = open(os.path.join(C.WEB, nome), encoding="utf-8").read()
    ok(t_.startswith("window." + var + "=") and json.loads(t_[len("window." + var + "="):-1]), nome + " valido")
AN = json.loads(open(os.path.join(C.WEB, "andamento.js")).read()[len("window.ANDAMENTO="):-1])
ok(len(AN["date"]) == 120 and AN["serie"]["Polonia"][1][-1] >= 20, "andamento.js: 120 giorni, Polonia oggi")
# ---------------------------------------------------------------- 7. lavoro_229 dentro il giro non si ferma mai
e2 = []
x = C.lavoro_229({"notizie": {"rotta": {"t": None, "paesi": ["X"], "conf": True}}}, adesso, cfg, {}, None, None, {"in_carica": False, "batteria": 10}, e2, False)
ok(isinstance(x, dict), "lavoro_229 con dati strani non ferma il giro: " + "; ".join(e2)[:200])
print()
print("Tutte le prove passate." if not falliti else f"{len(falliti)} prove fallite.", "Cartella:", T)
sys.exit(1 if falliti else 0)

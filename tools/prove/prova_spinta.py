# Prova 2.32: download dei feed in parallelo (stessi risultati, meno tempo), spinta, thread dei vettori. Mai il repo vero.
import json, os, shutil, sys, tempfile, importlib.util, time, threading, urllib.error
from datetime import datetime, timezone, timedelta
src = sys.argv[1]

def prepara(par, carica):
    T = tempfile.mkdtemp(prefix="spinta_")
    for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
        shutil.copy(os.path.join(src, n), T)
    cfg = json.load(open(os.path.join(T, "config.json")))
    cfg["repo_pubblico"] = ""; cfg["repo_git"] = ""
    cfg["cielo"] = False; cfg["cervello"]["attivo"] = False
    cfg["spinta"]["paralleli_carica"] = par; cfg["spinta"]["paralleli"] = par
    json.dump(cfg, open(os.path.join(T, "config.json"), "w"), ensure_ascii=False)
    os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
    spec = importlib.util.spec_from_file_location("castello_" + str(par), os.path.join(T, "castello.py"))
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
    adesso = datetime.now(timezone.utc)
    C.scrivi_json(os.path.join(C.DATI, "diario.json"), [{"iso": adesso.isoformat(), "tel": [30.0, 90, carica], "tipo": "leggero"}])
    return C

def finta_scarica(C, conta, attivi, massimo):
    def f(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
        d_ = C.urllib.parse.urlparse(url).netloc
        with C._LUCCHETTO:
            C.RICHIESTE[d_] = C.RICHIESTE.get(d_, 0) + 1
        attivi[0] += 1; massimo[0] = max(massimo[0], attivi[0])
        try:
            time.sleep(0.15)
            conta.append(url)
            h = abs(hash(url)) % 10
            if h == 0:
                raise urllib.error.HTTPError(url, 304, "Not Modified", {}, None)
            if h == 1:
                raise OSError("sito giù (finto)")
            if risposta is not None:
                risposta["etag"], risposta["lm"] = "e1", ""
            dd = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
            voci = "".join(f"<item><title>Notizia {i} da {d_} sulla difesa in Polonia</title><link>https://{d_}/a{abs(hash(url))%9999}_{i}</link><pubDate>{dd}</pubDate></item>" for i in range(3))
            return f"<rss><channel>{voci}</channel></rss>".encode()
        finally:
            attivi[0] -= 1
    return f

risultati = {}
for par in (1, 8):
    C = prepara(par, True)
    C.rete_ok = lambda *a, **k: True
    conta, attivi, massimo = [], [0], [0]
    C.scarica = finta_scarica(C, conta, attivi, massimo)
    C._ULTIMA.clear()
    t0 = time.time()
    try:
        C.aggiorna("leggero")
    except SystemExit:
        pass
    d = C.leggi_json(os.path.join(C.DATI, "diario.json"), [])[-1]
    risultati[par] = (round(time.time() - t0, 1), d.get("spinta"), d.get("nuove"), len(conta), massimo[0], d.get("invariate"))
    open("/home/claude/q16/esito.txt", "a").write(f"paralleli {par}: {risultati[par]}\n")
    print("paralleli", par, "→ durata", risultati[par][0], "s · spinta", d.get("spinta"), "· nuove", d.get("nuove"),
          "· richieste", len(conta), "· contemporanee max", massimo[0], "· invariate (304)", d.get("invariate"))
    assert d.get("v", "").startswith("2.32")
assert risultati[1][2] == risultati[8][2], "le voci nuove devono essere le stesse"
assert risultati[8][1][3] < risultati[1][1][3], "in parallelo i feed devono durare meno"
assert risultati[8][4] > 1 and risultati[1][4] == 1

# spinta e thread
C = prepara(8, True)
sp = C.spinta(json.load(open(os.path.join(C.QUI, "config.json"))))
print("spinta in carica:", sp); assert sp["piena"] and sp["paralleli"] == 8 and sp["ogni_minuti"] == 10
sp2 = C.spinta(json.load(open(os.path.join(C.QUI, "config.json"))), {"in_carica": False, "temp": 30, "batteria": 80})
print("spinta fuori carica:", sp2); assert not sp2["piena"] and sp2["paralleli"] == 8  # la prova mette 8 anche fuori carica
sp3 = C.spinta(json.load(open(os.path.join(C.QUI, "config.json"))), {"in_carica": True, "temp": 38.5, "batteria": 80})
assert not sp3["piena"] and "caldo" in sp3["perche"]
imp = {"thread": 4}
C.os.cpu_count = lambda: 8
assert C._sig_thread(imp, {"in_carica": True, "temp": 30}) == 4
S = C._off_stato(); S["sig_thread"] = 4; C._off_salva(S)
C._sig_misura(96, 40); C._sig_misura(96, 40)
assert C._sig_thread(imp, {"in_carica": True, "temp": 30}) == 6, "dopo 2 misure con 4 si prova 6"
S = C._off_stato(); S["sig_thread"] = 6; C._off_salva(S); C._sig_misura(96, 30); C._sig_misura(96, 30)
assert C._sig_thread(imp, {"in_carica": True, "temp": 30}) == 8
S = C._off_stato(); S["sig_thread"] = 8; C._off_salva(S); C._sig_misura(96, 35); C._sig_misura(96, 35)
print("velocità:", C._off_stato()["sig_velocita"])
assert C._sig_thread(imp, {"in_carica": True, "temp": 30}) == 6, "si sceglie il più veloce (6)"
assert C._sig_thread(imp, {"in_carica": False, "temp": 30, "batteria": 80}) == 4, "fuori carica: 4"
S = C._off_stato(); S["sig_velocita"]["6"]["quando"] = "2020-01-01"; C._off_salva(S)
assert C._sig_thread(imp, {"in_carica": True, "temp": 30}) == 6, "misura vecchia: si rifà"
print("TUTTO OK"); open("/home/claude/q16/esito.txt", "a").write("TUTTO OK\n")

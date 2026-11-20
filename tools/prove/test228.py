#!/usr/bin/env python3
"""Prove della 2.28: conferme tra lingue e per testata; scaricatore nel cuore (ripresa, pausa, blocco); filtro che impara
dalla sala d'attesa (non si accende con esempi a caso, si accende con esempi chiari, controlli, ordine della coda)."""
import json, os, re, shutil, sys, tempfile, importlib.util, threading, time, random, http.server, socketserver
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="t228_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
falliti = []


def ok(cond, msg):
    print(("OK  " if cond else "NO  ") + msg)
    if not cond:
        falliti.append(msg)


# ---------------------------------------------------------------- 1. conferme tra lingue e per testata
iso = lambda m: (datetime(2026, 11, 20, 10, tzinfo=timezone.utc) + timedelta(minutes=m)).isoformat()
voci = {
    "a": {"t": "Два российских ракеты упали на территорию Польши", "it": "Due missili russi sono caduti sul territorio polacco, dice il ministero della Difesa",
          "fonte": "Kommersant (Russia)", "lv": "B", "data_iso": iso(0)},
    "b": {"t": "2 Russian missiles fall on Polish territory, defence ministry says", "it": "Due missili russi caduti sul territorio polacco, dice il ministero della Difesa",
          "fonte": "BBC World", "lv": "B", "data_iso": iso(10)},
    "c": {"t": "صاروخان روسيان يسقطان في الأراضي البولندية", "it": "Due missili russi caduti nel territorio polacco, secondo il ministero della Difesa",
          "fonte": "BBC in arabo", "lv": "B", "data_iso": iso(20)},
    "d": {"t": "L'UE stanzia 7,9 miliardi per l'Ucraina", "fonte": "Ukrainska Pravda (in inglese)", "lv": "B", "data_iso": iso(30),
          "it": "L'UE stanzia 7,9 miliardi di euro per l'Ucraina in un'unica tranche"},
    "e": {"t": "ЄС виділив 7,9 млрд євро Україні", "fonte": "Ukrainska Pravda (in ucraino)", "lv": "B", "data_iso": iso(35),
          "it": "L'UE ha stanziato 7,9 miliardi di euro all'Ucraina in un'unica tranche"},
}
g, e = C.raggruppa(voci)
ok(e["a"] == e["b"] == e["c"], "russo, inglese e arabo sullo stesso fatto finiscono nello stesso gruppo")
ok(C.confermata(g[e["a"]]["fonti"], voci["a"]["fonte"]), "il titolo russo è confermato dalla BBC")
ok(len(g[e["b"]]["fonti"]) == 2, "BBC World e BBC in arabo contano come una testata sola: " + str(g[e["b"]]["fonti"]))
ok(e["d"] == e["e"] and not C.confermata(g[e["d"]]["fonti"], voci["d"]["fonte"]),
   "Ukrainska Pravda in inglese e in ucraino non si confermano a vicenda")
ok(C.famiglia_fonte("Telegram · Meduza, testata russa indipendente in esilio") == C.famiglia_fonte("Meduza (in russo)") == "meduza",
   "il canale Telegram di Meduza e il sito sono la stessa testata")
ok(C.famiglia_fonte("Times of Malta") != C.famiglia_fonte("Times of Israel"), "Times of Malta e Times of Israel restano testate diverse")
ok(C.famiglia_fonte("Kyiv Post") != C.famiglia_fonte("Kyiv Independent"), "Kyiv Post e Kyiv Independent restano diverse")

# ---------------------------------------------------------------- 2. scaricatore
DATI = C.DATI
os.makedirs(C.OFF(), exist_ok=True)
contenuto = bytes(random.Random(1).getrandbits(8) for _ in range(3_000_000))


class Lento(http.server.BaseHTTPRequestHandler):
    ritardo = 0.0

    def do_GET(self):
        inizio = 0
        m = re.match(r"bytes=(\d+)-", self.headers.get("Range", ""))
        if m:
            inizio = int(m.group(1))
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {inizio}-{len(contenuto) - 1}/{len(contenuto)}")
        else:
            self.send_response(200)
        self.send_header("Content-Length", str(len(contenuto) - inizio))
        self.end_headers()
        for i in range(inizio, len(contenuto), 65536):
            try:
                self.wfile.write(contenuto[i:i + 65536])
            except OSError:
                return
            time.sleep(Lento.ritardo)

    def log_message(self, *a):
        pass


srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Lento)
srv.daemon_threads = True
threading.Thread(target=srv.serve_forever, daemon=True).start()
C.OFFICINA_MODELLO = dict(C.OFFICINA_MODELLO, url=f"http://127.0.0.1:{srv.server_address[1]}/m.gguf", byte=len(contenuto))
C._wifi = lambda: True


def diario_tel(temp, batt, carica, minuti_fa=1):
    C.scrivi_json(os.path.join(DATI, "diario.json"), [{"iso": (datetime.now(timezone.utc) - timedelta(minutes=minuti_fa)).isoformat(),
                                                       "tel": [temp, batt, carica], "tipo": "leggero"}])


imp = {"attivo": True, "temp_max": 38}
diario_tel(30, 20, False)
p_ = C.scarica_modello(imp)
sc = C.leggi_json(C.OFF("scarico.json"), {})
ok(p_ == 300 and "fuori carica" in sc.get("stato", "") and not os.path.exists(C.OFF("modello.gguf.part")),
   "fuori carica non scarica e lo scrive: " + sc.get("stato", ""))
diario_tel(30, 80, True, minuti_fa=90)
C.scarica_modello(imp)
ok("prossimo giro" in C.leggi_json(C.OFF("scarico.json"), {}).get("stato", ""), "diario vecchio: aspetta il giro dopo")
diario_tel(41, 80, True)
C.scarica_modello(imp)
ok("caldo" in C.leggi_json(C.OFF("scarico.json"), {}).get("stato", ""), "telefono caldo: aspetta")
diario_tel(30, 80, True)
Lento.ritardo = 0.02
p_ = C.scarica_modello(imp, max_secondi=0.3)
mezzo = os.path.getsize(C.OFF("modello.gguf.part")) if os.path.exists(C.OFF("modello.gguf.part")) else 0
ok(p_ == 1 and 0 < mezzo < len(contenuto), f"si ferma a metà ({mezzo} byte) senza perdere nulla")
# un secondo scaricatore non parte mentre il primo tiene il blocco
b_ = C._blocco_scarico()
ok(C.scarica_modello(imp) == 120, "con il blocco preso da un altro, aspetta")
b_.close()
# curl della versione di prima ancora vivo: aspetta
S_ = C._off_stato(); S_["pid_curl"] = os.getpid(); C._off_salva(S_)
ok(C.scarica_modello(imp) == 120, "con il curl di prima ancora vivo, aspetta")
S_.pop("pid_curl"); C._off_salva(S_)
Lento.ritardo = 0
p_ = C.scarica_modello(imp)
fatto_ = open(C.OFF("modello.gguf"), "rb").read() if os.path.exists(C.OFF("modello.gguf")) else b""
ok(fatto_ == contenuto and not os.path.exists(C.OFF("modello.gguf.part")), "riprende da metà e il file finale è identico")
ok(C.leggi_json(C.OFF("scarico.json"), {}).get("stato") == "finito", "stato: finito")
ok(C.scarica_modello(imp) == 1800, "modello già completo: non fa nulla")
# l'officina legge lo stato scritto dal cuore
os.remove(C.OFF("modello.gguf"))
open(C.OFF("modello.gguf.part"), "wb").write(contenuto[:1_000_000])
C._scarico_scrivi(stato="scarico", mb=1, vel=2.5)
C.shutil.which = (lambda f: (lambda n: "/x/" + n if n == "llama-server" else f(n)))(shutil.which)
C._su_termux = lambda: True
cfg_t = C.leggi_json(os.path.join(T, "config.json"), {}); cfg_t["officina"]["traduttore"] = True
S2 = C.officina(cfg_t, {"in_carica": True, "temp": 30, "batteria": 80}, {}, [],
                datetime.now(timezone.utc))
ok("1 MB su 3" in (S2 or {}).get("fase", "") and "2.5 MB/s" in S2["fase"] and not S2.get("pid_curl"),
   "l'officina mostra i MB scritti dal cuore e non lancia curl: " + (S2 or {}).get("fase", ""))

# ---------------------------------------------------------------- 3. filtro che impara
os.remove(C.OFF("modello.gguf.part"))
R = random.Random(7)
paesi = ["Polonia", "Russia", "Ucraina", "Iran", "Israele", "Cina", "Taiwan", "Sudan", "Mali", "Turchia", "Serbia", "India"]
utili = ["{p}: il ministro della Difesa annuncia l'acquisto di {n} carri armati", "{p} e {q} firmano un accordo di difesa",
         "Attacco con droni nel nord di {p}, {n} morti", "{p} richiama l'ambasciatore da {q}", "Esercitazione militare di {p} vicino al confine",
         "Sanzioni di {q} contro {p} sul petrolio", "Colpo di Stato in {p}: i militari prendono il potere", "{p}: {n} soldati alla frontiera con {q}",
         "Missile lanciato da {p} cade in mare", "Il parlamento di {p} vota la leva obbligatoria", "Tregua tra {p} e {q}: negoziati a Ginevra"]
inutili = ["Calcio: {s} batte {t} {n}-1 e vola in testa", "Meteo: weekend di sole e caldo a {c}", "Il cantante {v} annuncia il nuovo album",
           "Ricetta della torta di mele della nonna", "Tennis, {v} vince il torneo di {c}", "Oroscopo di oggi: ottima giornata per i Leoni",
           "Incidente stradale a {c}: due feriti lievi", "Festival del cinema di {c}: tutti i vincitori", "Basket: {s} perde in casa contro {t}",
           "Saldi di stagione, le offerte migliori a {c}", "Gossip: {v} paparazzato in vacanza a {c}"]
squadre = ["Juventus", "Ajax", "Benfica", "Galatasaray", "Partizan", "Celtic", "Olympiacos"]
citta = ["Milano", "Lisbona", "Atene", "Varsavia", "Belgrado", "Ankara", "Lione", "Porto"]
vip = ["Rossi", "Garcia", "Novak", "Kowalski", "Yilmaz", "Petrovic", "Dubois"]


def titolo(utile):
    m = R.choice(utili if utile else inutili)
    return m.format(p=R.choice(paesi), q=R.choice(paesi), n=R.randint(2, 90), s=R.choice(squadre), t=R.choice(squadre),
                    c=R.choice(citta), v=R.choice(vip))


fonti_ = ["Daily Trust (Nigeria)", "Hürriyet (Turchia)", "Digi24 (Romania)", "Clarín (Argentina)"]
cfg = C.leggi_json(os.path.join(T, "config.json"), {})
imp_f = cfg["cervello"]["filtro"]
# a) esempi a caso: il filtro non deve accendersi
with open(C.ESEMPI_FILE(), "w", encoding="utf-8") as f:
    for i in range(3000):
        f.write(json.dumps([f"Titolo qualunque numero {i} {R.random()}", R.random() < 0.3, R.choice(fonti_)]) + "\n")
F = C.filtro_addestra(imp_f, forza=True)
ok(not F.get("attivo"), "con scelte a caso il filtro non scarta da solo: " + (F.get("perche") or ""))
# b) pochi esempi: impara ancora
with open(C.ESEMPI_FILE(), "w", encoding="utf-8") as f:
    for i in range(150):
        u = i % 3 == 0
        f.write(json.dumps([titolo(u) + f" ({i})", 1 if u else 0, R.choice(fonti_)]) + "\n")
F = C.filtro_addestra(imp_f, forza=True)
ok(not F.get("attivo") and "pochi esempi" in F.get("perche", ""), "con pochi esempi aspetta: " + F.get("perche", ""))
# c) primi esempi dall'archivio (scelte già fatte dal cervello), poi esempi chiari
os.remove(C.ESEMPI_FILE())
arch = {"attesa": {}, "notizie": {}}
for i in range(4000):
    u = R.random() < 0.3
    t_ = titolo(u) + f" · {i}"
    k = f"k{i}"
    if u:
        arch["notizie"][k] = {"t": t_, "fonte": R.choice(fonti_)}
        arch["attesa"][k] = {"no": True, "t": "", "u": ""}
    else:
        arch["attesa"][k] = {"no": True, "t": t_, "u": "x", "fonte": R.choice(fonti_)}
arch["attesa"]["kf"] = {"no": True, "filtro": True, "t": "scartato dal filtro: non è un esempio", "u": "x"}
n0 = C.filtro_primi_esempi(arch)
ok(n0 == 4000, f"i primi esempi vengono dall'archivio: {n0} (gli scarti del filtro stesso no)")
ok(C.filtro_primi_esempi(arch) == 0, "solo la prima volta")
t0 = time.time()
F = C.filtro_addestra(imp_f, forza=True)
dur = time.time() - t0
ok(F.get("attivo") and F.get("errore") is not None and F["errore"] <= 0.01 and F.get("copre", 0) > 0.5,
   f"con esempi chiari impara: copre {F.get('copre')}, errore {F.get('errore')} ({round(dur, 1)} s per imparare)")
# d) la coda: scarta i sicuramente inutili, tiene gli utili, mette in testa quelli che interessano
coda = []
for i in range(400):
    u = i % 4 == 0
    coda.append((f"q{i}", {"t": titolo(u) + f" ~{i}", "fonte": R.choice(fonti_), "data_iso": iso(i), "utile": u}))
tenuti, via = C.filtro_attesa(list(coda), cfg, [])
persi = sum(1 for k, v in coda if v["utile"] and v.get("filtro"))
ok(via > 150 and persi == 0, f"scarta {via} titoli inutili su 300 senza perdere quelli utili (persi: {persi})")
ok(all(v["utile"] for k, v in tenuti[:100]), "in testa alla coda ci sono i titoli che interessano")
ctrl_ = [v for k, v in tenuti if v.get("ctrl")]
ok(0 < len(ctrl_) < 40, f"alcuni titoli da scartare vanno comunque al cervello come controllo ({len(ctrl_)})")
F = C.leggi_json(C.FILTRO_FILE(), {})
ok(F.get("scartati_oggi") == via, "conta i titoli risparmiati di oggi")
# e) i controlli sbagliati spengono il filtro
for _ in range(25):
    C.filtro_esempio("controllo giusto", False, "x", True)
for _ in range(6):
    C.filtro_esempio("controllo sbagliato", True, "x", True)
tenuti2, via2 = C.filtro_attesa([(f"z{i}", {"t": titolo(False) + f" !{i}", "fonte": "x", "data_iso": iso(i)}) for i in range(50)], cfg, [])
ok(via2 == 0 and not C.leggi_json(C.FILTRO_FILE(), {}).get("attivo"), "troppi errori nei controlli: il filtro si spegne")
# f) senza filtro in config: nessun cambiamento
cfg_off = json.loads(json.dumps(cfg)); cfg_off["cervello"]["filtro"]["attivo"] = False
co_ = [("a", {"t": "x"}), ("b", {"t": "y"})]
ok(C.filtro_attesa(co_, cfg_off, []) == (co_, 0), "filtro spento in config.json: la coda resta com'era")
# g) il rapporto lo racconta
live = {"officina": {"fase": "pronta", "filtro": {"esempi": 4000, "attivo": True, "copre": 0.8, "errore": 0.004, "scartati_oggi": 230, "controlli": [25, 0]}}}
righe_ = [r for r in C.rapporto_dati([{"iso": iso(0), "v": "2.28", "tipo": "leggero"}], live, {}, None,
                                      datetime(2026, 11, 20, 12, tzinfo=timezone.utc), 12, cfg, {})["testo"].splitlines() if "Filtro" in r]
ok(righe_ and "80%" in righe_[0] and "230" in righe_[0], "il rapporto dice quanto scarta il filtro: " + (righe_[0] if righe_ else "niente"))

print()
print("Tutte le prove passate." if not falliti else f"{len(falliti)} prove fallite.", "Cartella:", T)
sys.exit(1 if falliti else 0)

#!/usr/bin/env python3
"""Prove della 2.27: spesa per lavoro, officina con il traduttore del telefono (llama-server vero, modello vero)."""
import json, os, shutil, sys, tempfile, importlib.util, time
from datetime import datetime, timezone, timedelta
src, server_bin, modello = sys.argv[1], sys.argv[2], sys.argv[3]
T = tempfile.mkdtemp(prefix="t227_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json"))); paesi = json.load(open(os.path.join(T, "paesi.json")))
cfg.setdefault("officina", {}).update({"attivo": True, "porta": 8093, "thread": 2, "secondi_per_giro": 400})
ok = lambda c, m: print(("OK  " if c else "NO  ") + m) or (c or sys.exit(1))
adesso = datetime.now(timezone.utc)
# 1. spesa per lavoro
ok(C.lavoro_di("Traduci in italiano questi titoli di notizie") == "traduzioni" and C.lavoro_di("Sono titoli di giornali e") == "sala d'attesa"
   and C.lavoro_di("Lavori a un archivio pubblico") == "lavoro a piano" and C.lavoro_di("Ecco i fatti che") == "sintesi", "riconosce i lavori")
# 2. officina: niente fuori carica
C._su_termux = lambda: True
os.makedirs(C.OFF(), exist_ok=True)
os.symlink(modello, C.OFF("modello.gguf"))
C.OFFICINA_MODELLO["byte"] = os.path.getsize(modello)
vero_which = shutil.which
C.shutil.which = lambda n: server_bin if n == "llama-server" else vero_which(n)
orig_popen = C.subprocess.Popen
def popen(cmd, *a, **k):
    if cmd and cmd[0] == "llama-server":
        cmd = [server_bin] + cmd[1:]
    return orig_popen(cmd, *a, **k)
C.subprocess.Popen = popen
err = []
S = C.officina(cfg, {"in_carica": False, "temp": 30, "batteria": 30}, {}, err, adesso)
ok(S["ok_tel"] is False and not S.get("pid_server"), "fuori carica con poca batteria: niente traduttore")
S = C.officina(cfg, {"in_carica": True, "temp": 41, "batteria": 80}, {}, err, adesso)
ok(S["ok_tel"] is False, "a 41 gradi: niente traduttore")
tel = {"in_carica": True, "temp": 30, "batteria": 80}
S = C.officina(cfg, tel, {}, err, adesso)
ok(S["fase"] == "accendo il traduttore" and S.get("pid_server"), "in carica e al fresco: accende il server " + str(S.get("fase")))
for _ in range(60):
    if C._off_server_su(S, 8093): break
    time.sleep(2)
ok(C._off_server_su(S, 8093), "server pronto")
titoli = [("ru", "Минобороны России заявило о перехвате 40 беспилотников над Брянской областью", "Il ministero della Difesa russo ha dichiarato di aver intercettato 40 droni sulla regione di Bryansk"),
          ("ru", "Путин провел совещание с членами Совета безопасности", "Putin ha tenuto una riunione con i membri del Consiglio di sicurezza"),
          ("fr", "La France va livrer de nouveaux avions Rafale à l'Inde", "La Francia consegnerà nuovi aerei Rafale all'India"),
          ("fr", "Le ministre des Armées annonce une hausse du budget de la défense", "Il ministro delle Forze armate annuncia un aumento del bilancio della difesa"),
          ("es", "El Gobierno aprueba la compra de 25 helicópteros para el Ejército", "Il governo approva l'acquisto di 25 elicotteri per l'Esercito"),
          ("es", "Marruecos y España firman un acuerdo de cooperación militar", "Marocco e Spagna firmano un accordo di cooperazione militare"),
          ("ar", "مصر والسعودية توقعان اتفاقية للتعاون العسكري", "Egitto e Arabia Saudita firmano un accordo di cooperazione militare"),
          ("ar", "الجيش اللبناني ينتشر في الجنوب بعد انسحاب القوات الإسرائيلية", "L'esercito libanese si schiera nel sud dopo il ritiro delle forze israeliane"),
          ("id", "TNI AL terima kapal perang baru dari galangan PT PAL", "La Marina indonesiana riceve una nuova nave da guerra dal cantiere PT PAL"),
          ("id", "Indonesia dan Prancis sepakati pembelian kapal selam Scorpene", "Indonesia e Francia concordano l'acquisto di sottomarini Scorpène"),
          ("tr", "Türkiye, Endonezya'ya 48 adet KAAN savaş uçağı satacak", "La Turchia venderà all'Indonesia 48 caccia KAAN"),
          ("tr", "Milli Savunma Bakanlığı yeni tatbikat duyurdu", "Il ministero della Difesa nazionale ha annunciato una nuova esercitazione")]
A = {"notizie": {f"n{i}": {"t": t, "it": it, "lg": lg, "data_iso": (adesso - timedelta(hours=i)).isoformat(), "paesi": []} for i, (lg, t, it) in enumerate(titoli)}}
t0 = time.time()
S = C.officina(cfg, tel, A, err, adesso)
pr = S.get("prova") or {}
print("   prova:", json.dumps(pr, ensure_ascii=False), f"({time.time() - t0:.0f} s)")
ok(pr.get("titoli") == len(titoli), f"prova fatta su {pr.get('titoli')} titoli")
ok(S["fase"] in ("attivo", "provato: non abbastanza buono"), "fase dopo la prova: " + S["fase"])
# 3. traduzioni del telefono prima del cervello
class R:
    def trova(self, t): return [p for p in ("Russia", "India", "Francia") if p.lower()[:4] in t.lower()]
nuovi = [{"t": "Россия и Индия подписали соглашение о поставках оружия", "lg": "ru", "paesi": []},
         {"t": "La France et l'Inde signent un accord sur les sous-marins", "lg": "fr", "paesi": []},
         {"t": "Un titolo in una lingua che non ha passato la prova", "lg": "xx", "paesi": []}]
resto = C.officina_traduci(list(nuovi), cfg, R(), err)
fatti = [v for v in nuovi if v.get("tr") == "telefono"]
for v in nuovi: print("   ", v.get("lg"), "→", v.get("it"))
ok(len(resto) + len(fatti) == 3 and nuovi[2] in resto, f"{len(fatti)} tradotti dal telefono, {len(resto)} lasciati al cervello")
ok(all(v.get("it") for v in fatti), "le traduzioni del telefono ci sono")
# 4. fuori carica il server si spegne
S = C.officina(cfg, {"in_carica": False, "temp": 30, "batteria": 80}, A, err, adesso)
ok(S.get("ok_tel") and C._off_server_su(S, 8093), "dalla 2.28.2, staccato il caricatore con batteria buona, il traduttore continua")
S = C.officina(cfg, {"in_carica": False, "temp": 30, "batteria": 30}, A, err, adesso)
time.sleep(2)
ok(not C._off_server_su(S, 8093), "fuori carica con batteria sotto il 35%, il traduttore si spegne")
print("errori:", err)
print("\nTutte le prove passate. Cartella:", T)
# 5. senza rete: l'officina traduce a ogni giro
C.telefono = lambda: {"in_carica": True, "temp": 30, "batteria": 80}
S = C.officina(cfg, tel, A, err, adesso)  # riaccende il server
for _ in range(60):
    if C._off_server_su(S, 8093): break
    time.sleep(2)
A2 = {"notizie": {"z1": {"t": "Россия и Китай проведут совместные учения", "lg": "ru", "data_iso": adesso.isoformat(), "paesi": []},
                  "z2": {"t": "Le Maroc commande des drones turcs", "lg": "fr", "data_iso": adesso.isoformat(), "paesi": []}}}
json.dump(A2, open(os.path.join(T, "dati", "archivio.json"), "w"))
json.dump(cfg, open(os.path.join(T, "config.json"), "w"))
f = C._offline_locale(adesso)
A3 = json.load(open(os.path.join(T, "dati", "archivio.json")))
print("   senza rete:", f, [v.get("it") for v in A3["notizie"].values()])
ok(f.get("tradotti", 0) >= 1 and any(v.get("tr") == "telefono" for v in A3["notizie"].values()), "senza rete il telefono traduce lo stesso")
C._off_ferma(C._off_stato())
print("Tutte le prove 2.27.2 passate.")

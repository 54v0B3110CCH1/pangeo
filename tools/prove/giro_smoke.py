import json, os, shutil, sys, tempfile, importlib.util, time
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="giro229_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json", "sistemi.json", "sistemi_base.json", "potere_base.json", "aziende_lei.json", "gruppi_base.json"):
    shutil.copy(os.path.join(src, n), T)
cfg = json.load(open(os.path.join(T, "config.json")))
cfg["repo_pubblico"] = ""; cfg["repo_git"] = ""   # MAI verso il repository vero
cfg["cielo"] = False; cfg["cervello"]["attivo"] = False
json.dump(cfg, open(os.path.join(T, "config.json"), "w"), ensure_ascii=False)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
adesso = datetime.now(timezone.utc)
# archivio con notizie confermate di 3 giorni
arch = {"notizie": {}, "video": {}}
for g in range(3):
    for i in range(5):
        arch["notizie"][f"k{g}{i}"] = {"t": f"Attacco con 12 droni in Ucraina {g}{i}", "it": f"Attacco con 12 droni in Ucraina: 3 morti ({g}{i})",
                                      "paesi": ["Ucraina"], "conf": True, "data_iso": (adesso - timedelta(days=g)).isoformat(), "fonte": "Reuters",
                                      "lv": "A", "u": f"https://x/{g}{i}"}
C.scrivi_json(os.path.join(C.DATI, "archivio.json"), arch)
C.rete_ok = lambda *a, **k: True
def finta(*a, **k):
    raise OSError("rete finta per la prova")
C.scarica = finta
C.urllib.request.urlopen = finta
t0 = time.time()
try:
    C.aggiorna("")
except SystemExit:
    pass
d = C.leggi_json(os.path.join(C.DATI, "diario.json"), [])
print("durata", round(time.time() - t0, 1), "s; righe diario", len(d), "x229", d[-1].get("x229") if d else None, "tipo", d[-1].get("tipo") if d else None)
print("web:", sorted(os.listdir(C.WEB)))
print("errori 229:", [e for e in (C.leggi_json(os.path.join(C.DATI, "live.json"), {}) or {}).get("errori", []) if "2.29" in e or "Schede" in e or "Andamento" in e or "Avvisi" in e or "Indice" in e])

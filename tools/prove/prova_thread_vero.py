import json, os, shutil, sys, tempfile, importlib.util, time
from datetime import datetime, timezone
src, bin_dir, modello = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ["PATH"] = bin_dir + ":" + os.environ["PATH"]
T = tempfile.mkdtemp(prefix="thr_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
C._su_termux = lambda: True
C.os.cpu_count = lambda: 8
os.makedirs(os.path.dirname(C.OFF(C.SIGNIFICATO_MODELLO["file"])), exist_ok=True)
os.symlink(modello, C.OFF(C.SIGNIFICATO_MODELLO["file"]))
cfg = json.load(open(os.path.join(T, "config.json"))); imp = dict(cfg["officina"], porta_significato=8097)
cfg["officina"] = imp; json.dump(cfg, open(os.path.join(T, "config.json"), "w"))
adesso = datetime.now(timezone.utc)
C.scrivi_json(os.path.join(C.DATI, "diario.json"), [{"iso": adesso.isoformat(), "tel": [30.0, 90, True], "tipo": "leggero"}])
def cmd(pid):
    return open(f"/proc/{pid}/cmdline").read().replace("\0", " ")
try:
    p = C._sig_server(imp)
    S = C._off_stato(); print("acceso:", p, "thread", S["sig_thread"], "|", cmd(S["pid_sig"])[-12:])
    assert p and S["sig_thread"] == 4
    arch = {"notizie": {f"k{i}": {"it": f"La Polonia compra carri armati numero {i}", "conf": True, "data_iso": adesso.isoformat()} for i in range(70)}}
    r = C.significato_aggiorna(arch, cfg, {"in_carica": True, "temp": 30, "batteria": 90}, [], secondi=600, tutte=True, misura=True)
    print("lavoro:", r)
    C._sig_misura(70, 25); C._sig_misura(70, 25)  # due misure come quelle del telefono
    print("misure:", C._off_stato().get("sig_velocita"))
    p2 = C._sig_server(imp)
    S = C._off_stato(); print("dopo la misura con 4:", p2, "thread", S["sig_thread"], "|", cmd(S["pid_sig"])[-12:])
    assert p2 and S["sig_thread"] == 6 and " -t 6" in cmd(S["pid_sig"])
    p3 = C._sig_server(imp, tel={"in_carica": False, "temp": 30, "batteria": 80})
    S = C._off_stato(); print("fuori carica:", p3, "thread", S["sig_thread"])
    assert S["sig_thread"] == 4
    print("TUTTO OK")
finally:
    C._sig_ferma()

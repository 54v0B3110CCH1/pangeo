import json, os, shutil, sys, tempfile, importlib.util, time
from datetime import datetime, timezone
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="eco230_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
cfg["economia"]["comtrade_per_giro"] = 2
adesso = datetime.now(timezone.utc)
for giro in range(3):
    err = []
    r = C.economia(cfg, adesso, err, secondi=120)
    print("giro", giro, r, err[:3])
E = C.leggi_json(os.path.join(C.DATI, "economia.json"), {})
print("bm", {k: len(v) for k, v in E["bm"].items()})
print("Italia pil", E["bm"].get("pil", {}).get("Italia", [])[-2:])
print("tassi", {k: (v.get("s") or [None])[-1] for k, v in E["tassi"].items()}, {k: v.get("manca") for k, v in E["tassi"].items() if v.get("manca")})
print("valute EUR", list(E["valute"]["storia"].values())[-1].get("EUR"), len(list(E["valute"]["storia"].values())[-1]))
print("materie", {k: (v.get("s") or [None])[-1] for k, v in E["materie"].items()})
for k, v in E["comtrade"].items():
    print("comtrade", k, v.get("anno"), "M", v.get("M", [])[:3], "M93", v.get("M93", [])[:3], "X93", v.get("X93", [])[:3], v.get("errore"))
C.scrivi_economia_web(cfg, adesso)
t = open(os.path.join(C.WEB, "economia.js"), encoding="utf-8").read()
d = json.loads(t[len("window.ECONOMIA="):-1]); print("economia.js", len(t), "stati", len(d["stati"]), d["stati"].get("Italia", {}).keys())
print("avvisi eco", C.avvisi_economia(cfg, adesso)[:3])

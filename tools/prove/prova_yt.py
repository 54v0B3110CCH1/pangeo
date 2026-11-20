import json, os, shutil, sys, tempfile, importlib.util
from datetime import datetime, timezone
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="yt230_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
yt, tgc = {}, {}
for c in ["nexta_tv", "UkraineNow", "gerashchenko_en", "ukrpravda_news", "Tsaplienko", "bbcrussian", "astrapress", "QudsN", "intelslava", "rybar"]:
    try:
        n = len(C.telegram(c, tgc, yt))
        print(c, n, "messaggi")
    except Exception as e:
        print(c, "errore", e)
print("citazioni YouTube:", len(yt), sorted(((k, len(v)) for k, v in yt.items()), key=lambda x: -x[1])[:8])
auto = {}
nuovi = C.scopri_youtube(auto, yt, dict(cfg, scoperta_youtube={"attiva": True, "video_per_giro": 8, "min_citazioni": 1, "max_canali": 60}), datetime.now(timezone.utc), [])
print("canali trovati (con 1 citazione, solo per la prova):", nuovi)
print("citati:", [(v["nome"], v["da"]) for v in auto.get("youtube_citati", {}).values()][:8])
# salute
a2 = {}
for i in range(12):
    C.canale_esito(a2, "tg:prova", False, cfg, datetime.now(timezone.utc))
print("spento dopo 12 errori:", not C.canale_ok(a2, "tg:prova", cfg), a2)
C.canale_esito(a2, "tg:prova", True, cfg, datetime.now(timezone.utc)); print("riacceso dopo un ok:", C.canale_ok(a2, "tg:prova", cfg))
print(C.canali_stato(cfg, {}, auto, datetime.now(timezone.utc))["yt_trovati"][:5])

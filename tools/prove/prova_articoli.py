import json, os, shutil, sys, tempfile, importlib.util, time
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="art_")
for n in ("castello.py", "config.json", "paesi.json", "piano_base.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("castello", os.path.join(T, "castello.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
adesso = datetime.now(timezone.utc)
pagina = ("<html><head><meta charset='utf-8'><script>var x='<p>script finto</p>'</script></head><body><nav><p>Menu menu menu menu menu menu menu menu menu menu menu menu</p></nav>"
          "<article><h1>Titolo</h1>" + "".join(f"<p>Il ministro della Difesa ha annunciato l&#39;acquisto di {i} nuovi elicotteri per l'esercito, secondo il comunicato ufficiale.</p>" for i in range(30)) +
          "<p>Accetta i cookie per continuare a leggere questo sito e le sue pagine</p></article></body></html>").encode()
breve = b"<html><body><p>Abbonati per leggere l'articolo completo su questo sito web.</p></body></html>"
t = C.testo_articolo(pagina)
assert "elicotteri" in t and "script finto" not in t and "Menu" not in t and "cookie" not in t and "l'acquisto" in t, t[:300]
print("estrazione ok:", len(t), "caratteri")
arch = {"notizie": {}}
for i in range(40):
    arch["notizie"][f"k{i}"] = {"t": f"News {i}", "it": f"Notizia {i}", "conf": i % 4 != 3, "nf": 5 - i % 5, "gr": f"g{i // 5}",
                               "u": ("https://news.google.com/x" if i == 0 else f"https://sito{i % 7}.example/a{i}"),
                               "data_iso": (adesso - timedelta(hours=i)).isoformat(), "paesi": ["Polonia"], "fonte": "Prova"}
aperti = []
def finta(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    aperti.append(url); time.sleep(0.1)
    if url.endswith("a5"):
        raise OSError("sito giù")
    return breve if url.endswith("a6") else pagina
C.scarica = finta
C.scrivi_json(os.path.join(C.DATI, "diario.json"), [{"iso": adesso.isoformat(), "tel": [30.0, 90, True], "tipo": "leggero"}])
r = C.leggi_articoli(arch, adesso, cfg, None, [])
print("in carica:", r, "aperti", len(aperti))
assert r["provati"] == 12 and "https://news.google.com/x" not in aperti
assert r["poco_testo"] >= 1 and r["letti"] >= 9
gr = {}
for u in aperti:
    k = "k" + u.rsplit("a", 1)[1]; gr[arch["notizie"][k]["gr"]] = gr.get(arch["notizie"][k]["gr"], 0) + 1
assert max(gr.values()) <= 2, gr
r2 = C.leggi_articoli(arch, adesso, cfg, {"in_carica": False, "temp": 30, "batteria": 70}, [])
print("fuori carica:", r2)
assert r2["provati"] == 4 and not (set(aperti[12:]) & set(aperti[:12])), "non riapre le stesse pagine"
res = C.indice_cerca("elicotteri")
print("ricerca 'elicotteri':", len(res), res[0] if res else None)
assert res and res[0]["dove"] == "articolo letto"
print("TUTTO OK")

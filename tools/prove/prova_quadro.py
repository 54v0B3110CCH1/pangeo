"""Prova del controllo della scaletta (2.34): numeri sbagliati, codici giusti, eco del titolo."""
import json, os, sys, tempfile, importlib.util, shutil
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="quadro_")
for n in ("castello.py", "config.json", "paesi.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati"))
spec = importlib.util.spec_from_file_location("c", os.path.join(T, "castello.py")); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
voci = [{"tipo": "notizia", "t": t, "u": f"https://x/{i}", "fonte": "F", "d": "2026-11-20", "paesi": p, "nf": 30 - i}
        for i, (t, p) in enumerate([
            ("Genocidio dei Rohingya: la Corte internazionale di giustizia conferma la sentenza", ["Myanmar"]),
            ("Trump: Putin vuole porre fine alla guerra. Nuovi raid su Kiev e Leopoli", ["Ucraina"]),
            ("Sciopero generale: manifestazioni in tutto il Veneto", []),
            ("Il parlamento danese vota 109 a 0 il patto di difesa tra Stati Uniti e Groenlandia", ["Danimarca", "Groenlandia", "USA"]),
            ("Gli Stati Uniti chiedono al vertice di eliminare la clausola sull'Ucraina", ["Ucraina", "USA"]),
            ("Haiti: forti combattimenti tra esercito e bande per un corridoio chiave", ["Haiti"]),
            ("Bukele registra la candidatura alle presidenziali di El Salvador", ["El Salvador"]),
            ("Qatar e Turchia firmano a Istanbul un patto di difesa reciproca", ["Qatar", "Turchia"]),
            ("Il Pakistan estende il divieto di spazio aereo per i voli indiani", ["Pakistan", "India"]),
            ("Accordi militari USA con il Venezuela annunciati a Caracas", ["Venezuela", "USA"]),
        ])]
C._quadro_voci = lambda *a, **k: voci
risposte = []
C.chiedi_claude = lambda chiavi, cfg_, testo, massimo=900, conto=None: risposte.pop(0)
C._cervello_libero = lambda *a, **k: True
C.scarica = lambda *a, **k: (_ for _ in ()).throw(OSError("niente rete"))
perc = os.path.join(C.DATI, "quadro.json")


def giro(testo):
    if os.path.exists(perc):
        os.remove(perc)
    risposte.append(testo)
    er = []
    C.quadro({"anthropic_key": "x"}, cfg, {"notizie": {}}, False, er)
    return json.load(open(perc)), er


# 1. il difetto del 21 novembre: classifica 1, 2, 3 al posto del numero, senza eco
Q, er = giro("R | 1 | 5 | La Corte internazionale riconosce il genocidio dei Rohingya in Myanmar\n"
             "R | 2 | 5 | Gli Stati Uniti chiedono di eliminare la clausola sull'Ucraina dalla dichiarazione di pace\n"
             "R | 3 | 4 | Il parlamento danese approva il patto di difesa USA-Groenlandia\n"
             "R | 4 | 4 | Raid russi su Kiev e Leopoli mentre Trump dice che Putin vuole la fine della guerra\n")
t = [(x["t"][:20], x["perche"][:25]) for x in Q["scaletta"]]
print("1.", t, Q.get("scartate"))
assert not any("Sciopero" in x["t"] for x in Q["scaletta"]), "lo sciopero non deve prendere il perché dell'Ucraina"
for x in Q["scaletta"]:
    assert C._quadro_punti(x, x["perche"]) >= 2, x
assert len(Q["scaletta"]) == 4
# 2. formato nuovo: codice giusto ed eco
Q, er = giro("R | V4 | 5 | Il parlamento danese vota 109 | Patto di difesa approvato all'unanimità\n"
             "R | V8 | 4 | Qatar e Turchia firmano | Rafforza la rete di difesa reciproca nel Golfo\n"
             "K | V4, V10 | USA, Groenlandia, Venezuela | Gli accordi militari USA con Groenlandia e Venezuela mostrano la stessa strategia | US military agreements Venezuela Greenland | en | Quali motivazioni?\n")
print("2.", [x["t"][:25] for x in Q["scaletta"]], [[v["t"][:20] for v in c["voci"]] for c in Q["collegamenti"]])
assert [x["u"] for x in Q["scaletta"]] == ["https://x/3", "https://x/7"]
assert [v["u"] for v in Q["collegamenti"][0]["voci"]] == ["https://x/3", "https://x/9"]
# 3. codice sbagliato ma eco giusto: si prende la voce dell'eco; voci sbagliate nel collegamento: si tolgono e si cercano
Q, er = giro("R | V3 | 5 | Gli Stati Uniti chiedono al vertice | Possibile cambio di posizione sull'Ucraina\n"
             "R | V9 | 2 | Nessun titolo così | Una frase che non parla di nessuna voce precisa davvero\n"
             "K | V1, V6, V3 | USA, Danimarca, Groenlandia, Venezuela | Gli accordi militari USA con Groenlandia e Venezuela mostrano la stessa strategia | US military Venezuela Greenland | en | Quali motivazioni?\n")
print("3.", [x["t"][:25] for x in Q["scaletta"]], Q.get("scartate"), [[v["t"][:20] for v in c["voci"]] for c in Q["collegamenti"]])
assert [x["u"] for x in Q["scaletta"]] == ["https://x/4"]
assert Q["scartate"] == 1
assert sorted(v["u"] for v in Q["collegamenti"][0]["voci"]) == ["https://x/3", "https://x/9"]
# 4. pulizia una volta sola del quadro vecchio sul telefono
vecchio = {"iso": "2026-11-21T02:59:00+00:00", "scaletta": [dict(voci[2], r=5, perche="Gli Stati Uniti chiedono di eliminare la clausola sull'Ucraina dalla dichiarazione"),
                                                            dict(voci[4], r=4, perche="Il raid massiccio russo su Kiev e Leopoli mentre Trump parla di pace")],
           "collegamenti": [{"testo": "Gli accordi USA con Groenlandia e Venezuela", "stati": "USA, Groenlandia, Venezuela",
                             "voci": [voci[0], voci[2], voci[3]]}]}
json.dump(vecchio, open(perc, "w"))
risposte.append("niente")
C.quadro({"anthropic_key": "x"}, cfg, {"notizie": {}}, False, [])
Q = json.load(open(perc))
print("4.", [(x["t"][:20], x["perche"][:20]) for x in Q["scaletta"]], [[v["t"][:20] for v in c["voci"]] for c in Q["collegamenti"]], Q.get("ripulito"))
assert Q["ripulito"] == "2.34"
assert [x["u"] for x in Q["scaletta"]] == ["https://x/4"]  # il perché dell'Ucraina passa sotto la voce giusta, lo sciopero esce
assert [v["u"] for v in Q["collegamenti"][0]["voci"]] == ["https://x/3"]
print("Prova del quadro passata.")

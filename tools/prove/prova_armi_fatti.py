"""Prova delle armi SIPRI e dei fatti dagli articoli (2.38), con risposte finte. Uso: python3 prova_armi_fatti.py programma"""
import base64, json, os, sys, shutil, tempfile, importlib.util
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
T = tempfile.mkdtemp(prefix="armi_")
for n in ("castello.py", "config.json", "paesi.json", "mappa.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("c", os.path.join(T, "castello.py")); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
C.time.sleep = lambda s: None
def ok(c, m):
    print(("OK  " if c else "NO  ") + m)
    if not c: raise SystemExit(1)
# --- SIPRI
INTEST = ("Transfers of major conventional arms from All countries to All countries .\nSource: SIPRI Arms Transfers Database (c) SIPRI.\n"
          "Recipient,Supplier,Year of order, ,Number ordered, ,Weapon designation,Weapon description,Deliveries in the Year Range, ,Year(s) of delivery,status,Comments,SIPRI TIV per unit,SIPRI TIV for total order,SIPRI TIV of delivered weapons\n")
RIGHE = ['Poland,United States,2022,,250,,M-1A2 SEPv-3 Abrams,tank,117,,2025,New,USD4.8 b deal; delivery planned 2025-2026,5.2,1300,608.4',
         'Poland,Turkiye,2021,,24,,Bayraktar TB-2,armed drone,24,,2022; 2023; 2024,New,$268 m deal,2.4,57.6,57.6',
         'Viet Nam,Russia,2019,?,12,?,Yak-130,trainer/combat aircraft,12,?,2021; 2023,New,,10,120,120',
         'Houthi rebels (Yemen)*,unknown supplier(s),2020,?,10,?,Qasef-2K,armed UAV,10,?,2021,New,Probably from Iran,0.1,1,1',
         'Albania,France,2025,,1,,Ground Master-400,air-search radar,,,,New,Delivery planned 2026,13,13,0']
TESTO = INTEST + "\n".join(RIGHE) + "\n"
aff = C.sipri_righe(TESTO, C._sis_inverso())
ok(len(aff) == 5, "cinque affari letti")
ok(aff[0][:3] == ["Polonia", "USA", 2022] and aff[0][7] == "2025" and aff[0][11] == 608.4, "Polonia compra Abrams dagli USA, con i TIV")
ok(aff[1][1] == "Turchia" and aff[1][7] == "2022-2024", "Turkiye → Turchia; anni di consegna compressi")
ok(aff[2][0] == "Vietnam" and aff[2][3] == "12?" and aff[2][6] == "12?", "Viet Nam → Vietnam; i dati incerti restano con «?»")
ok(aff[3][0] == "Houthi (Yemen)" and aff[3][1] == "venditore sconosciuto", "gruppi non statali e venditori sconosciuti con il loro nome")
ok(aff[4][6] == "" and aff[4][7] == "", "ordine non ancora consegnato")
chieste = []
def finta(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    chieste.append(url)
    assert url.startswith(C.SIPRI_API)
    if url.endswith("/trades/getMaxYear"):
        return b"2025"
    if "trade-register-csv" in url:
        f = json.loads(corpo.decode())["filters"]
        assert f[0]["field"] == "activePrograms" and f[0]["value1"] == 2016 and f[0]["value2"] == 2025
        return json.dumps({"bytes": base64.b64encode((INTEST + "\n".join(RIGHE * 220)).encode()).decode()}).encode()
    raise OSError(url)
C.scarica = finta
adesso = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)
err = []
r = C.armi_aggiorna(cfg, adesso, err)
ok(r["fatti"] == 1 and r["affari"] == 1100 and r["anno"] == 2025 and not err, "registro scaricato (una richiesta)")
ok(C.scrivi_armi_web(adesso) and "SIPRI" in open(os.path.join(C.WEB, "armi.js")).read(), "armi.js per la pagina, con la fonte")
n = len(chieste)
r = C.armi_aggiorna(cfg, adesso + timedelta(days=5), err)
ok(r["fatti"] == 0 and len(chieste) == n, "dopo 5 giorni non si richiede niente")
def poche(url, **k):
    if "trade-register" in url:
        return json.dumps({"bytes": base64.b64encode(TESTO.encode()).decode()}).encode()
    return finta(url, **k)
C.scarica = poche
cfg["armi"]["giorni_stesso_anno"] = 0
r = C.armi_aggiorna(cfg, adesso + timedelta(days=40), err)
ok(r["affari"] == 1100 and any("tengo quelli di prima" in e for e in err), "una risposta monca non cancella il registro buono")
# base del motore nel cloud più nuova: il telefono la prende
B = dict(C.leggi_json(C.MAG("armi", "sipri.json"), {}), quando="2027-01-01T00:00:00+00:00")
C.scrivi_json(os.path.join(T, "armi_base.json"), B)
ok(C.armi_aggiorna(cfg, adesso + timedelta(days=41), [])["affari"] == 1100 and C.leggi_json(C.MAG("armi", "sipri.json"), {})["quando"].startswith("2027"), "base del cloud presa")
# --- fatti
testo = ("The Polish defence ministry said on Tuesday it had signed a contract for 96 AH-64E Apache helicopters worth $10 billion. "
         "Deliveries will start in 2028, minister Wladyslaw Kosiniak-Kamysz told reporters in Warsaw.")
ok(C.fatto_verificato("it had signed a contract for 96 AH-64E Apache helicopters", testo), "frase trovata nel testo")
ok(C.fatto_verificato("«It had signed a contract for 96 AH-64E Apache helicopters»", testo), "virgolette e maiuscole non contano")
ok(not C.fatto_verificato("it had signed a contract for 120 Apache helicopters", testo), "frase inventata: scartata")
risp = ("F | Ministero della Difesa polacco | firmato il contratto per elicotteri Apache | 96 elicotteri, 10 miliardi di dollari | Varsavia | martedì | "
        "it had signed a contract for 96 AH-64E Apache helicopters worth $10 billion\n"
        "F | Polonia | consegne dal 2028 | - | - | 2028 | Deliveries will start in 2028\n"
        "F | Polonia | comprati 200 carri | 200 carri | - | - | it had signed a contract for 96 AH-64E Apache helicopters\n"
        "F | Polonia | comprati droni | 50 droni | - | - | the ministry bought fifty drones from Turkey\n")
tenuti, scartati = C.fatti_leggi_risposta(risp, testo)
ok(len(tenuti) == 2 and scartati == 2, "due fatti tenuti; scartati quello con un numero che non c'è e quello con la frase inventata")
ok(tenuti[0]["quanti"] == "96 elicotteri, 10 miliardi di dollari" and tenuti[1]["quanti"] == "", "i numeri restano")
C.fatti_in_coda("k1", {"it": "Polonia: contratto per 96 Apache", "data_iso": "2026-11-21T08:00:00+00:00", "paesi": ["Polonia", "USA"], "fonte": "Reuters", "u": "https://r/1", "nf": 4}, testo)
C.fatti_in_coda("k1", {"it": "doppione"}, testo)
ok(len(C.leggi_json(os.path.join(C.DATI, "fatti_coda.json"), [])) == 1, "coda dei fatti senza doppioni")
domande = []
def cervello(chiavi, cfg_, t, massimo=900, conto=None):
    domande.append(t)
    return risp
C.chiedi_claude = cervello
r = C.fatti_aggiorna({"anthropic_key": "sk-ant-finta"}, cfg, adesso, [], quanti=3)
ok(r["articoli"] == 1 and r["fatti"] == 2 and r["scartati"] == 2 and r["in_coda"] == 0, "un articolo letto dal cervello: 2 fatti")
ok(domande[0].startswith("Sei l'estrattore") and C.lavoro_di(domande[0]) == "fatti dagli articoli", "la spesa va sotto «fatti dagli articoli»")
ok(C.scrivi_fatti_web(adesso), "fatti.js")
W = open(os.path.join(C.WEB, "fatti.js")).read()
ok("Polonia" in W and "Apache" in W and "it had signed" not in W, "sul sito il fatto e il link, non la frase dell'articolo")
F = C.leggi_json(C.MAG("fatti", "fatti.json"), {})
ok(F["fatti"]["k1"]["fatti"][0]["cit"].startswith("it had signed"), "la frase resta sul telefono")
r = C.fatti_aggiorna({"anthropic_key": "sk-ant-finta"}, cfg, adesso, [], quanti=3)
ok(r["articoli"] == 0 and len(domande) == 1, "lo stesso articolo non si rilegge")
r = C.fatti_aggiorna({}, cfg, adesso, [], quanti=3)
ok(r["articoli"] == 0, "senza chiave il cervello non lavora")
print("tutto bene")

"""Prova di «chi guida, controllato» (2.38): il riquadro di Wikipedia (estratti veri in dati/riquadri.json), il confronto dei
nomi, il voto alla NATO, il giro completo con Wikidata, Wikipedia e notizie finte, la base del motore nel cloud rivalutata
con le notizie del telefono. Uso: python3 prova_capi.py programma"""
import json, os, sys, shutil, tempfile, importlib.util, urllib.parse
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
QUI = os.path.dirname(os.path.abspath(__file__))
T = tempfile.mkdtemp(prefix="capi_")
for n in ("castello.py", "config.json", "paesi.json", "mappa.json", "potere_base.json"):
    shutil.copy(os.path.join(src, n), T)
os.makedirs(os.path.join(T, "dati")); os.makedirs(os.path.join(T, "web"))
spec = importlib.util.spec_from_file_location("c", os.path.join(T, "castello.py")); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
cfg = json.load(open(os.path.join(T, "config.json")))
C.time.sleep = lambda s: None
def ok(c, m):
    print(("OK  " if c else "NO  ") + m)
    if not c: raise SystemExit(1)
R = json.load(open(os.path.join(QUI, "dati", "riquadri.json")))
paesi = json.load(open(os.path.join(T, "paesi.json")))
stati = {C._capi_testo(s) for s in paesi} | {C._capi_testo(a) for l in paesi.values() for a in (l or [])[:3]}
def capi(t): return [(a, b) for a, b, c, d in C.capi_dal_riquadro(R[t], stati)]
ok(capi("Bank for International Settlements")[0] == ("Pablo Hernández de Cos", "direttore generale"), "BRI: il direttore generale che Wikidata non ha")
ok(capi("Asian Infrastructure Investment Bank")[0] == ("Zou Jiayi", "presidente"), "AIIB: la presidente nuova (key_people)")
osce = capi("Organization for Security and Co-operation in Europe")
ok(("Feridun Sinirlioğlu", "segretario generale") in osce, "OSCE: il segretario generale")
ok(capi("NATO")[0] == ("Mark Rutte", "segretario generale"), "NATO")
ok(capi("Federal Reserve")[0] == ("Kevin Warsh", "presidente"), "Fed: chi la presiede (lista con <br>)")
ok(capi("BlackRock")[0] == ("Larry Fink", "amministratore delegato"), "BlackRock: {{Unbulleted list}} con il ruolo nella riga dopo")
ok(capi("Italy")[:2] == [("Sergio Mattarella", "presidente"), ("Giorgia Meloni", "primo ministro")], "Italia: capo di Stato e del governo")
ok(capi("Iran")[0] == ("Mojtaba Khamenei", "Guida suprema"), "Iran: la Guida suprema")
ok(capi("Saudi Arabia")[0][0] == "Salman of Saudi Arabia", "Arabia Saudita: il nome intero dal collegamento")
ok(capi("International Atomic Energy Agency") == [("Rafael Grossi", "direttore generale")], "AIEA: il ruolo scritto sopra il nome")
ue = capi("European Union")
ok(all("Ireland" not in a and "Irlanda" not in a for a, b in ue) and ("António Costa", "presidente del Consiglio europeo") in ue, "UE: la presidenza a turno (uno Stato) non è una persona")
ok(("Lucas Philippe", "presidente") in capi("Interpol"), "Interpol: chief1_name/chief1_position")
ok(capi("People's Bank of China")[0] == ("Pan Gongsheng", "governatore"), "Banca Popolare Cinese: nome, ruolo dopo la virgola")
ok(capi("Bank of Italy") == [("Fabio Panetta", "governatore")], "Banca d'Italia: president con leader_title")
ok(capi("World Trade Organization")[0] == ("Ngozi Okonjo-Iweala", "direttore generale"), "OMC: «(since 2021)» non è un ruolo")
# stessa persona
sp = C.stessa_persona
ok(not sp("Ali Khamenei", "Mojtaba Khamenei"), "padre e figlio non sono la stessa persona")
ok(sp("Ajay Banga", "Ajaypal Singh Banga") and sp("Nabil Fahmi", "Nabil Fahmy") and sp("Yūji Iwasawa", "Yuji Iwasawa"), "stessa persona scritta in modi diversi")
ok(not sp("Jin Liqun", "Zou Jiayi") and not sp("Jerome Powell", "Kevin Warsh"), "persone diverse")
# voto
v = C.capi_valuta([["Jin Liqun", "presidente", ""]], [["Zou Jiayi", "presidente", ""]], [3, "2026-11-10"], [0, ""])
ok(v[0] == "diversi" and v[1] == "C2" and "Wikidata è probabilmente vecchio" in v[2][0], "disaccordo risolto dalle notizie: C2")
ok(C.capi_valuta([["A B", "", ""]], [["C D", "", ""]], [0, ""], [0, ""])[1] == "C4", "disaccordo senza notizie: C4, da ricontrollare")
ok(C.capi_valuta([["Christine Lagarde", "", ""]], [["Christine Lagarde", "", ""]], [0, ""], [0, ""])[1] == "C2", "due fonti non indipendenti d'accordo: C2, non C1")
ok(C.capi_valuta([["Christine Lagarde", "", ""]], [["Christine Lagarde", "", ""]], [2, "2026-11-01"], [0, ""])[1] == "C1", "con le notizie: C1")
ok(C.capi_valuta([], [["Mark Rutte", "", "x"]], [0, ""], [0, ""], "nato.int")[1] == "A2", "sito ufficiale: A")
ok(C.capi_valuta([], [], [0, ""], [0, ""])[:2] == ("manca", "F6"), "niente: F6")
# il giro con fonti finte
P = {"istituzioni": {"quando": "2026-11-21T00:00:00+00:00", "voci": [
        {"q": "Q309195", "n": "Banca dei Regolamenti Internazionali", "st": "Svizzera", "capi": [], "cr": [], "sito": "https://www.bis.org/"},
        {"q": "Q18109843", "n": "Banca Asiatica d'Investimento per le infrastrutture", "st": "Cina", "capi": ["Jin Liqun"], "cr": [["Jin Liqun", "presidente", ""]], "sito": "https://www.aiib.org"},
        {"q": "Q7184", "n": "NATO", "st": "Belgio", "capi": ["Mark Rutte"], "cr": [["Mark Rutte", "alla guida", "2024-10-01"]], "sito": "https://www.nato.int"}]},
     "banche": {"quando": "2026-11-21T00:00:00+00:00", "voci": [{"q": "Q806176", "n": "Banca d'Italia", "st": "Italia", "capi": ["Fabio Panetta"], "cr": [["Fabio Panetta", "presidente", "2023-11-01"]]}]}}
os.makedirs(C.MAG("potere"), exist_ok=True)
C.scrivi_json(C.MAG("potere", "potere.json"), P)
TIT = {"Q309195": "Bank for International Settlements", "Q18109843": "Asian Infrastructure Investment Bank", "Q7184": "NATO", "Q806176": "Bank of Italy"}
chieste = []
def finta(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    assert (intestazioni or {}).get("User-Agent", "").startswith("PanGeo/")
    chieste.append(url)
    if "query.wikidata.org" in url:
        q = urllib.parse.parse_qs(corpo.decode())["query"][0]
        if "P298" in q:  # gli Stati
            b = lambda v: {"value": v}
            return json.dumps({"results": {"bindings": [
                {"iso": b("ITA"), "x": b("http://www.wikidata.org/entity/Q38"), "t": b("Italy"), "pr": b("P35"), "capoL": b("Sergio Mattarella"), "ci": b("2015-02-03T00:00:00Z")},
                {"iso": b("ITA"), "x": b("http://www.wikidata.org/entity/Q38"), "t": b("Italy"), "pr": b("P6"), "capoL": b("Giorgia Meloni"), "ci": b("2022-10-22T00:00:00Z")},
                {"iso": b("IRN"), "x": b("http://www.wikidata.org/entity/Q794"), "t": b("Iran"), "pr": b("P35"), "capoL": b("Ali Khamenei"), "ci": b("1989-06-04T00:00:00Z")}]}}).encode()
        return json.dumps({"results": {"bindings": [{"x": {"value": "http://www.wikidata.org/entity/" + q_}, "t": {"value": t_}} for q_, t_ in TIT.items()]}}).encode()
    if "en.wikipedia.org/w/api.php" in url:
        tit = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["titles"][0].split("|")
        assert len(tit) <= 20
        pagine = [{"title": t, "revisions": [{"timestamp": "2026-11-20T10:00:00Z", "slots": {"main": {"content": R[t]}}}]} for t in tit if t in R]
        return json.dumps({"query": {"pages": pagine}}).encode()
    if "nato.int" in url:
        return b"<html><body><p>Secretary General Mark Rutte took office on 1 October 2024.</p></body></html>"
    raise OSError("non previsto: " + url)
C.scarica = finta
# notizie lette dal telefono (indice istantaneo): Zou Jiayi con la AIIB, Khamenei figlio con l'Iran
db = C._indice_apri()
for k, t, d, p in (("1", "Zou Jiayi, presidente della AIIB, firma un prestito · The AIIB president Zou Jiayi said", "2026-11-10", "Cina"),
                   ("2", "Iran: la Guida suprema Mojtaba Khamenei parla ai pasdaran", "2026-11-12", "Iran"),
                   ("3", "Mojtaba Khamenei e il governo dell'Iran", "2026-11-15", "Iran")):
    db.execute("INSERT INTO testi (testo, d, p, f, u, dove, c) VALUES (?,?,?,?,?,?,?)", (t, d, p, "Reuters", "https://x/" + k, "notizia", 1))
db.commit(); db.close()
adesso = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)
cfg["capi"]["per_giro"] = 10
err = []
r = C.capi_aggiorna(cfg, adesso, err, quanti=300, ufficiali=3)
print(r, err)
Cp = C.leggi_json(C.MAG("potere", "capi.json"), {})
E, S = Cp["enti"], Cp["stati"]
ok(E["Q309195"]["esito"] == "solo_wp" and E["Q309195"]["wp"][0][0] == "Pablo Hernández de Cos", "BRI: il nome che mancava, da Wikipedia")
ok(E["Q18109843"]["esito"] == "diversi" and E["Q18109843"]["voto"] == "C2" and E["Q18109843"]["not"][0][0] >= 1, "AIIB: Wikidata vecchio, le notizie danno ragione a Wikipedia")
ok(E["Q7184"]["esito"] == "concorde", "NATO: d'accordo")
ok(E["Q806176"]["esito"] == "concorde" and E["Q806176"]["wpv"] == "2026-11-20", "Banca d'Italia: d'accordo, con la data della voce")
ok(S["Italia"]["esito"] == "concorde", "Italia: d'accordo")
ok(S["Iran"]["esito"] == "diversi" and S["Iran"]["voto"] == "C2", "Iran: Wikidata dice ancora Ali Khamenei; notizie e Wikipedia dicono Mojtaba")
nw = [u for u in chieste if "en.wikipedia.org" in u]
ok(len(nw) <= 3 + (len(paesi) // 20) + 2, f"Wikipedia a gruppi di 20 voci per richiesta ({len(nw)} richieste)")
ok(any("nato.int" in u for u in chieste) is False, "il sito ufficiale si apre solo per i dubbi")
ok(C.scrivi_capi_web(adesso) and "window.CAPI=" in open(os.path.join(C.WEB, "capi.js")).read(), "capi.js per la pagina")
# il secondo giro non rifà niente (tutto fresco); i dubbi tornano dopo i giorni_dubbi
r2 = C.capi_aggiorna(cfg, adesso + timedelta(hours=1), err, quanti=300)
ok(r2["fatti"] == 0, "giro dopo: niente da rifare")
r3 = C.capi_aggiorna(cfg, adesso + timedelta(days=4), err, quanti=300)
ok(r3["fatti"] >= 1 and r3["fatti"] < len(paesi), "dopo 4 giorni si ricontrollano i dubbi (voto 4 e 6), non tutto")
# 429: si smette per il giro e non si scrivono voci vuote
def no429(url, **k):
    if "en.wikipedia.org" in url:
        raise C.urllib.error.HTTPError(url, 429, "Too Many", {"Retry-After": "1"}, None)
    return finta(url, **k)
C.scarica = no429
prima = json.dumps(C.leggi_json(C.MAG("potere", "capi.json"), {})["stati"]["Italia"])
err = []
C.capi_aggiorna(cfg, adesso + timedelta(days=20), err, quanti=30)
ok(any("rallentare" in e for e in err), "429: si riprende al prossimo giro")
ok(json.dumps(C.leggi_json(C.MAG("potere", "capi.json"), {})["stati"]["Italia"]) == prima, "429: le voci di prima restano")
# la base del motore nel cloud: più nuova, senza notizie → il telefono rifà il voto con le sue notizie
B = {"enti": {"Q18109843": dict(E["Q18109843"], quando="2026-12-30T00:00:00+00:00", voto="C4", esito="diversi", **{"not": [[0, ""], [0, ""]]})}, "stati": {}}
C.scrivi_json(os.path.join(T, "capi_base.json"), B)
C.scarica = finta
C.capi_aggiorna(cfg, adesso + timedelta(days=1), [], quanti=1)
ok(C.leggi_json(C.MAG("potere", "capi.json"), {})["enti"]["Q18109843"]["voto"] == "C2", "base del cloud presa e rivalutata con le notizie del telefono")
# i modelli che Wikipedia riempie da sola ({{Current leader|…}}): si espandono in una richiesta
USA = "{{Infobox country\n| leader_title1 = [[President of the United States|President]]\n| leader_name1 = {{Current leader|United States|President}}\n| leader_title2 = [[Vice President of the United States|Vice President]]\n| leader_name2 = {{Incumbent VPOTUS}}\n}}"
def espandi(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    q = urllib.parse.parse_qs(corpo.decode())
    assert q["action"] == ["expandtemplates"]
    return json.dumps({"expandtemplates": {"wikitext": "[[Donald Trump]]<span style=\"display:none\"></span>\n@@@PANGEO@@@\n[[JD Vance]]"}}).encode()
C.scarica = espandi
tt = {"United States": (USA, "2026-11-20")}
ok(C._capi_espandi(tt) == 2 and [a for a, *_ in C.capi_dal_riquadro(tt["United States"][0], stati)] == ["Donald Trump", "JD Vance"], "Stati Uniti: {{Current leader}} espanso, il nome c'è")
print("tutto bene")

#!/usr/bin/env python3
"""Costruisce l'elenco dei servizi di intelligence per Stato (tools/dati/intel.json), per la sezione Intelligence della pagina.

Fonti, tutte pubbliche: le voci collegate dall'elenco «List of intelligence agencies» di Wikipedia in inglese e le voci
che Wikidata classifica come servizi di intelligence. Da Wikidata arrivano anche anno di nascita, sito ufficiale e voce di
Wikipedia in italiano. Le voci sciolte o sostituite escono. Resta un elenco fatto in automatico e poi ripulito con le
liste qui sotto: può contenere errori o lasciare fuori qualcosa, e nella pagina è scritto.

Uso (serve la rete):  python3 tools/intel_base.py            scarica da Wikidata e riscrive tools/dati/intel.json
                      python3 tools/intel_base.py --siti     in più prova i siti ufficiali e toglie quelli che non rispondono
"""
import collections
import json
import os
import re
import subprocess
import sys
from datetime import date

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
UA = "PanGeo/2.22 (archivio pubblico; https://github.com/54v0B3110CCH1/pangeo)"

CAMPI = """?a ?aLabel ?iso ?site ?inizio ?fine ?sost ?link ?itwiki ?enwiki"""
CORPO = """
  ?a wdt:P17|wdt:P1001 ?c . ?c wdt:P298 ?iso .
  OPTIONAL { ?a wdt:P856 ?site }
  OPTIONAL { ?a wdt:P571 ?inizio }
  OPTIONAL { ?a wdt:P576 ?fine }
  OPTIONAL { ?a wdt:P1366 ?sost }
  ?a wikibase:sitelinks ?link .
  OPTIONAL { ?itwiki schema:about ?a ; schema:isPartOf <https://it.wikipedia.org/> }
  OPTIONAL { ?enwiki schema:about ?a ; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
"""
Q_CLASSE = "SELECT " + CAMPI + " WHERE { ?a wdt:P31/wdt:P279* wd:Q47913 . " + CORPO + " FILTER(?link >= 3) }"
Q_ELENCO = ("SELECT " + CAMPI + """ (GROUP_CONCAT(DISTINCT ?cl; separator="|") AS ?classi) WHERE {
  SERVICE wikibase:mwapi {
    bd:serviceParam wikibase:endpoint "en.wikipedia.org"; wikibase:api "Generator"; mwapi:generator "links";
      mwapi:titles "List of intelligence agencies"; mwapi:gpllimit "max"; mwapi:gplnamespace "0"; mwapi:redirects "1"; wikibase:limit 5000 .
    ?a wikibase:apiOutputItem mwapi:item .
  }
  FILTER(BOUND(?a))
  ?a wdt:P31 ?classe . ?classe rdfs:label ?cl . FILTER(LANG(?cl) = "en")
""" + CORPO + "} GROUP BY " + CAMPI)

# classi di Wikidata che dicono «è un servizio»
CORE = {"intelligence agency", "security agency", "military intelligence agency", "foreign intelligence service", "secret service",
        "secret police", "signals intelligence agency", "domestic intelligence agency", "counterintelligence agency"}
# classi che dicono «non è un ente» (Stati, persone, partiti, pagine di servizio)
NON_ENTE = {"country", "sovereign state", "successor state", "unitary state", "landlocked country", "mediterranean country",
            "island country", "republic", "federal republic", "kingdom", "constitutional monarchy", "human",
            "wikimedia disambiguation page", "political party", "communist party", "city", "big city", "capital city",
            "special administrative region", "historical country", "state", "federation", "position", "public office"}
NOME = re.compile(r"intel+i[gj]|inform|securit|sicurezza|rensei|nachricht|verfassungsschutz|razved|istihbarat|mukhabarat|seguridad|"
                  r"segurança|sécurité|veiligheid|inlichting|underrättelse|efterretning|etterretning|tiedustelu|suojelu|wywiad|"
                  r"bezpiecze|bezpečnost|sigurnos|siguri|drošīb|saugumo|kaitse|biztons|bezbedn", re.I)
FUORI = re.compile(r"financ|finanz|money|laundering|\btax|revenue|narcot|\bdrug|corruption|corrupc|customs|aduan|douani|gendarm|border|"
                   r"coast guard|party|partito|comitato centrale|flotilla|\bbase\b|brigade|battalion|regiment|special operations|spetsnaz|"
                   r"ministry|ministero|ministerio|ministère|cabinet secretariat|prime minister|attorney|\bcourt|commission|commissione|"
                   r"investigation|investigaz|investigativa|\bcrime|criminal|judici|fraud|ballistic|transaction|accountability|"
                   r"enforcement|communit|activity abroad|spionaggio in|intelligence agencies|egmont|satellit|stato maggiore|"
                   r"general staff|deep-sea|extremism|military-political|territorial army|fishery|main rouge|agency 114|ottoman|impero|"
                   r"landesamt|bayerisches|saxony|united front|safeguarding national security of|cyber|electronic security|"
                   r"information technology|informationstechnik|network security|special communications|telecomunic|telecommunication|"
                   r"comunicazione e informazione|special programs|protezione$|protection service|federal government|geospatial information|"
                   r"polic(e|ía|ia)\b|polizia|polizei|politie|guardia|security forces|security services$|security council|"
                   r"sicurezza pubblica popolare|^MI\d+$|detective|surveillance unit|body ?guard|^station |^y-service", re.I)
TIENI = re.compile(r"security service|security and intelligence|intelligence service|police security|säkerhetspolisen|suojelupoliisi|"
                   r"public security intelligence|d'informazione per la pubblica sicurezza|direzione degli agenti di pubblica sicurezza", re.I)
# aggiunte a mano: enti veri che le regole scarterebbero (per il nome o per come sono classificati)
SI = {"Q8333", "Q1068951", "Q2497240", "Q303976", "Q3799334", "Q1480245", "Q6867472", "Q3029599", "Q1227126", "Q854461", "Q330666",
      "Q399639", "Q210175", "Q184560", "Q220798"}
# tolte a mano: storiche senza data di fine, reparti, programmi, enti che non sono servizi, regimi caduti
NO = {"Q434371", "Q217386", "Q130879", "Q762201", "Q158363", "Q3298064", "Q2510824", "Q7574715", "Q96376368", "Q2790089", "Q3374614",
      "Q6043857", "Q2346285", "Q138515", "Q15934151", "Q12579935", "Q3029464", "Q905830", "Q7813959", "Q6978334", "Q7574492",
      "Q4504195", "Q12473190", "Q271110", "Q7574524", "Q5522137", "Q4393617", "Q2903292", "Q24909019", "Q22080502", "Q10302518",
      "Q201747", "Q2212723", "Q15826059", "Q7251339", "Q120598147", "Q5295116", "Q943607", "Q1717958", "Q11231", "Q2817257",
      "Q1105642", "Q7928541", "Q1501755", "Q1537850", "Q2975622", "Q1962501", "Q690196", "Q3962189", "Q7016181", "Q4388247",
      "Q4431136", "Q786878", "Q131832106", "Q2910691", "Q6897661", "Q1154057"}
# nomi più leggibili per i servizi più noti (sigla e nome)
NOMI = {"Q58792": "FSB – Servizio federale di sicurezza", "Q115782": "GRU – intelligence militare (Direzione principale dello Stato maggiore)",
        "Q863254": "SVR – Servizio informazioni estero", "Q37230": "CIA – Central Intelligence Agency",
        "Q121194": "NSA – National Security Agency", "Q8333": "FBI – Federal Bureau of Investigation (sicurezza interna e controspionaggio)",
        "Q184560": "MI6 – Secret Intelligence Service", "Q210175": "MI5 – Security Service", "Q220798": "GCHQ – intelligence dei segnali",
        "Q335827": "DGSE – Direction générale de la Sécurité extérieure", "Q167079": "DGSI – Direction générale de la Sécurité intérieure",
        "Q3029491": "DRSD – Direction du renseignement et de la sécurité de la défense",
        "Q272969": "BND – Bundesnachrichtendienst", "Q310522": "BfV – Bundesamt für Verfassungsschutz",
        "Q480220": "MAD – Militärischer Abschirmdienst", "Q392910": "AISE – Agenzia informazioni e sicurezza esterna",
        "Q392916": "AISI – Agenzia informazioni e sicurezza interna", "Q1227126": "DIS – Dipartimento delle informazioni per la sicurezza",
        "Q34216": "Mossad", "Q380238": "Shin Bet (Shabak) – sicurezza interna", "Q453558": "Aman – intelligence militare",
        "Q478481": "MİT – Millî İstihbarat Teşkilatı", "Q1068951": "MSS – Ministero per la sicurezza dello Stato",
        "Q2092054": "RAW – Research and Analysis Wing", "Q274564": "ISI – Inter-Services Intelligence",
        "Q916449": "CNI – Centro Nacional de Inteligencia", "Q1365657": "VAJA – Ministero dell’intelligence",
        "Q615811": "SBU – Servizio di sicurezza dell’Ucraina", "Q2497240": "HUR – intelligence militare (Ministero della difesa)",
        "Q2625535": "SZRU – Servizio informazioni esterne", "Q303976": "EYP – Servizio nazionale di informazioni",
        "Q3799334": "Servizio di intelligence militare (Forze di difesa)", "Q1480245": "FRA – intelligence dei segnali",
        "Q6867472": "Ministero della pubblica sicurezza (comprende i servizi di sicurezza)",
        "Q399639": "ABIN – Agência Brasileira de Inteligência", "Q1721811": "KAPO – Servizio di sicurezza interna",
        "Q12376592": "Välisluureamet – Servizio informazioni estero", "Q549972": "Supo – Servizio di sicurezza e intelligence",
        "Q1331110": "Säpo – Säkerhetspolisen", "Q854461": "BIS – Servizio informazioni di sicurezza",
        "Q330666": "ÚZSI – Ufficio per le relazioni estere e le informazioni", "Q485566": "NIS – National Intelligence Service",
        "Q1032405": "CSIS – Canadian Security Intelligence Service", "Q782740": "ASIO – Australian Security Intelligence Organisation",
        "Q181694": "ASIS – Australian Secret Intelligence Service", "Q392540": "ABW – Agenzia per la sicurezza interna",
        "Q601940": "AW – Agenzia di intelligence", "Q1329608": "KGB della Bielorussia"}
# enti veri a cui su Wikidata manca lo Stato (o che risultano «sostituiti» per errore): lo Stato si mette a mano
A_MANO = {"Q1866011": "Paesi Bassi", "Q2426814": "India", "Q3153003": "Pakistan", "Q15911311": "Kenya", "Q3026771": "Bangladesh",
          "Q3161571": "Libano", "Q22222677": "USA"}
NOMI.update({"Q1866011": "AIVD – Servizio generale di intelligence e sicurezza", "Q2426814": "IB – Intelligence Bureau (sicurezza interna)",
             "Q3153003": "IB – Intelligence Bureau (sicurezza interna)", "Q15911311": "NIS – National Intelligence Service",
             "Q3026771": "DGFI – intelligence militare", "Q3161571": "Sûreté générale – Direzione generale della sicurezza generale",
             "Q22222677": "ODNI – Ufficio del Direttore dell’intelligence nazionale"})
Q_A_MANO = ("SELECT ?a ?aLabel ?site ?inizio ?link ?itwiki ?enwiki WHERE { VALUES ?a { %s } OPTIONAL { ?a wdt:P856 ?site } "
            "OPTIONAL { ?a wdt:P571 ?inizio } ?a wikibase:sitelinks ?link . "
            "OPTIONAL { ?itwiki schema:about ?a ; schema:isPartOf <https://it.wikipedia.org/> } "
            "OPTIONAL { ?enwiki schema:about ?a ; schema:isPartOf <https://en.wikipedia.org/> } "
            'SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }' % " ".join("wd:" + q for q in A_MANO))
# nome inglese dello Stato su Wikidata → nome in PanGeo, dove non coincidono con tools/dati/en.json
STATI_A_MANO = {"united states": "USA", "people's republic of china": "Cina", "czech republic": "Repubblica Ceca", "czechia": "Repubblica Ceca",
                "türkiye": "Turchia", "turkey": "Turchia", "the gambia": "Gambia", "kingdom of the netherlands": "Paesi Bassi",
                "netherlands": "Paesi Bassi", "republic of ireland": "Irlanda", "state of palestine": "Palestina",
                "occupied palestinian territory": "Palestina", "democratic republic of the congo": "RD Congo",
                "republic of the congo": "Congo", "ivory coast": "Costa d'Avorio", "east timor": "Timor Est",
                "federated states of micronesia": "Micronesia", "kingdom of denmark": "Danimarca", "vatican city": "Vaticano"}


def sparql(query):
    r = subprocess.run(["curl", "-s", "-m", "170", "-G", "https://query.wikidata.org/sparql", "--data-urlencode", "query=" + query,
                        "-H", "Accept: application/sparql-results+json", "-H", "User-Agent: " + UA], capture_output=True, text=True)
    return json.loads(r.stdout)["results"]["bindings"]


def carica(righe):
    E = {}
    for r in righe:
        q = r["a"]["value"].rsplit("/", 1)[1]
        e = E.setdefault(q, {"q": q, "nome": r["aLabel"]["value"], "iso": set(), "site": "", "inizio": "", "fine": False,
                             "link": int(r["link"]["value"]), "it": "", "en": "", "classi": set()})
        e["iso"].add(r["iso"]["value"])
        if "classi" in r:
            e["classi"] |= {c.lower() for c in r["classi"]["value"].split("|")}
        for k, src in (("site", "site"), ("it", "itwiki"), ("en", "enwiki")):
            if src in r and not e[k]:
                e[k] = r[src]["value"]
        if "inizio" in r:
            e["inizio"] = r["inizio"]["value"][:4].lstrip("-+")
        if "fine" in r or "sost" in r:
            e["fine"] = True
    return E


def main():
    paesi = json.load(open(os.path.join(RADICE, "programma", "paesi.json"), encoding="utf-8"))
    en = json.load(open(os.path.join(QUI, "dati", "en.json"), encoding="utf-8"))
    E = carica(sparql(Q_ELENCO))
    for q, e in carica(sparql(Q_CLASSE)).items():
        if q in E:
            E[q]["classi"].add("intelligence agency")
        else:
            e["classi"] = {"intelligence agency"}
            E[q] = e
    isos = sorted({i for e in E.values() for i in e["iso"]})
    nomi_iso = collections.defaultdict(list)
    for r in sparql('SELECT ?iso ?l WHERE { VALUES ?iso { %s } ?c wdt:P298 ?iso ; rdfs:label ?l . FILTER(LANG(?l)="en") }'
                    % " ".join('"%s"' % i for i in isos)):
        nomi_iso[r["iso"]["value"]].append(r["l"]["value"].lower())
    da_inglese = {v.lower(): k for k, v in en.items()}
    iso_it = {}
    for iso, nomi in nomi_iso.items():
        s = next((STATI_A_MANO.get(n) or da_inglese.get(n) for n in nomi if (STATI_A_MANO.get(n) or da_inglese.get(n)) in paesi), None)
        if s:
            iso_it[iso] = s
    per = collections.defaultdict(list)
    for q, e in E.items():
        if q in NO or e["fine"] or e["classi"] & NON_ENTE:
            continue
        if not (q in SI or ((e["classi"] & CORE or NOME.search(e["nome"])) and (not FUORI.search(e["nome"]) or TIENI.search(e["nome"])))):
            continue
        for iso in e["iso"]:
            if iso in iso_it:
                per[iso_it[iso]].append(e)
    for r in sparql(Q_A_MANO):
        q = r["a"]["value"].rsplit("/", 1)[1]
        if A_MANO.get(q) in paesi and not any(e["q"] == q for e in per[A_MANO[q]]):
            per[A_MANO[q]].append({"q": q, "nome": r["aLabel"]["value"], "site": r.get("site", {}).get("value", ""),
                                   "inizio": r.get("inizio", {}).get("value", "")[:4], "link": int(r["link"]["value"]),
                                   "it": r.get("itwiki", {}).get("value", ""), "en": r.get("enwiki", {}).get("value", "")})
    fuori = {}
    for st, voci in per.items():
        voci.sort(key=lambda e: (-(e["q"] in SI or e["q"] in NOMI or e["q"] in A_MANO), -e["link"]))
        fuori[st] = [[NOMI.get(e["q"], e["nome"]), e["inizio"], e["it"] or e["en"], e["site"], e["q"]] for e in voci[:6]
                     if e["it"] or e["en"]]
    fuori = {st: v for st, v in sorted(fuori.items()) if v}
    if "--siti" in sys.argv:  # un sito ufficiale che non risponde più viene tolto: resta la voce di Wikipedia
        siti = sorted({x[3] for v in fuori.values() for x in v if x[3]})
        prova = subprocess.run(["xargs", "-P", "16", "-I", "{}", "curl", "-s", "-o", "/dev/null", "-m", "20", "-L", "-A", UA, "-w",
                                "%{http_code} {}\\n", "{}"], input="\n".join(siti), capture_output=True, text=True).stdout
        morti = {riga.split(" ", 1)[1] for riga in prova.splitlines() if riga.startswith("000 ")}
        print("siti provati:", len(siti), "| senza risposta (tolti):", len(morti))
        for v in fuori.values():
            for x in v:
                if x[3] in morti:
                    x[3] = ""
    esito = {"agg": date.today().isoformat(),
             "fonte": "Wikipedia in inglese (voci collegate da «List of intelligence agencies») e Wikidata",
             "stati": fuori}
    with open(os.path.join(QUI, "dati", "intel.json"), "w", encoding="utf-8") as f:
        json.dump(esito, f, ensure_ascii=False, indent=0, separators=(",", ":"))
    print("Stati con almeno un servizio:", len(fuori), "| servizi:", sum(len(v) for v in fuori.values()))
    return fuori


if __name__ == "__main__":
    main()

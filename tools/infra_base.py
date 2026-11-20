#!/usr/bin/env python3
"""Costruisce tabelle/infra.json: per ogni Stato energia, trasporti e logistica, cibo e terra, commercio e dipendenze,
spesa per settori. Lo legge la pagina (cartelle «Energia», «Trasporti e logistica», «Cibo e risorse», «Dipendenze»
e il confronto della spesa nella cartella dei numeri).

Fonte unica: la copia d'archivio del CIA World Factbook (github.com/factbook/factbook.json), la stessa che il programma
usa per forze armate e sicurezza. Ogni numero porta il suo anno. Le percentuali di dipendenza le calcola questo script
dai numeri del Factbook (produzione e consumo): danno l'ordine di grandezza, non un dato ufficiale.

Uso (serve la rete):  python3 tools/infra_base.py            scarica e riscrive tabelle/infra.json
                      python3 tools/infra_base.py cartella   usa i file già scaricati in «cartella» (uno per Stato)
"""
import concurrent.futures as cf
import html
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
BASE = "https://raw.githubusercontent.com/factbook/factbook.json/master/"

MERCI = {
    "additive manufacturing machines": "macchine per la stampa 3D", "agricultural products": "prodotti agricoli", "aircraft": "aerei",
    "aircraft parts": "parti di aerei", "alcohols": "alcoli", "aluminum": "alluminio", "aluminum ore": "minerale di alluminio",
    "aluminum oxide": "ossido di alluminio", "aluminum wire": "filo di alluminio", "ammonia": "ammoniaca", "animal food": "mangimi",
    "animal meal": "farine animali", "antimony": "antimonio", "aqueous paints": "vernici all’acqua", "artwork": "opere d’arte",
    "baked goods": "prodotti da forno", "bananas": "banane", "base metal watches": "orologi in metallo comune",
    "bedding": "biancheria da letto", "beef": "carne bovina", "beer": "birra", "broadcasting equipment": "apparecchi per le trasmissioni",
    "building plastics": "plastiche per l’edilizia", "building stone": "pietra da costruzione", "butter": "burro",
    "carbon-based electronics": "elettronica a base di carbonio", "carbonates": "carbonati", "cars": "automobili",
    "cars and vehicle parts": "automobili e parti di veicoli", "cassava": "manioca", "cattle": "bovini", "cement": "cemento",
    "centrifuges": "centrifughe", "cereal flours": "farine di cereali", "cheese": "formaggio", "chromium ore": "minerale di cromo",
    "cigars": "sigari", "cloves": "chiodi di garofano", "coal": "carbone", "coal tar oil": "olio di catrame di carbone",
    "cobalt": "cobalto", "cocoa beans": "fave di cacao", "cocoa paste": "pasta di cacao", "coconut oil": "olio di cocco",
    "coconuts/brazil nuts/cashews": "noci di cocco, noci del Brasile e anacardi", "coffee": "caffè", "computers": "computer",
    "connectors for audio and video": "connettori audio e video", "construction vehicles": "veicoli da cantiere",
    "copper ore": "minerale di rame", "copra": "copra", "corn": "mais", "cotton": "cotone", "cotton fabric": "tessuti di cotone",
    "cotton yarn": "filati di cotone", "crude petroleum": "petrolio greggio", "cut flowers": "fiori recisi",
    "dental products": "prodotti dentali", "diamonds": "diamanti", "dolomite": "dolomite", "dried legumes": "legumi secchi",
    "electric batteries": "batterie elettriche", "electric generating sets": "gruppi elettrogeni", "electric motors": "motori elettrici",
    "electrical capacitors": "condensatori elettrici", "electrical control boards": "quadri elettrici",
    "electrical transformers": "trasformatori elettrici", "electricity": "elettricità", "energy products": "prodotti energetici",
    "essential oils": "oli essenziali", "excavation machinery": "macchine per lo scavo", "fabric": "tessuti", "fake hair": "capelli finti",
    "fertilizers": "fertilizzanti", "fish": "pesce", "fish oil": "olio di pesce", "flat-rolled iron": "laminati piatti di ferro",
    "flavored water": "bevande aromatizzate", "foodstuffs": "generi alimentari", "footwear": "calzature", "forage crops": "foraggi",
    "frozen fruits and nuts": "frutta e frutta secca surgelate", "furniture": "mobili", "garments": "abbigliamento",
    "gas turbines": "turbine a gas", "gold": "oro", "granite": "granito", "grapes": "uva", "gravel and crushed stone": "ghiaia e pietrisco",
    "ground nuts": "arachidi", "gum resins": "gommoresine", "hand tools": "utensili a mano", "hardware": "ferramenta",
    "harvesting machinery": "macchine per la raccolta", "hormones": "ormoni", "hydrocarbons": "idrocarburi",
    "industrial acids/oils/alcohols": "acidi, oli e alcoli industriali", "insulated wire": "cavi isolati",
    "integrated circuits": "circuiti integrati", "iron alloys": "ferroleghe", "iron bars": "barre di ferro", "iron blocks": "blocchi di ferro",
    "iron ore": "minerale di ferro", "iron pipes": "tubi di ferro", "iron reductions": "ferro di riduzione", "iron rods": "tondini di ferro",
    "iron structures": "strutture in ferro", "jewelry": "gioielli", "knotted carpets": "tappeti annodati",
    "laboratory ceramic ware": "ceramica da laboratorio", "lead ore": "minerale di piombo", "lignite": "lignite", "liquor": "liquori",
    "machine parts": "parti di macchine", "machinery": "macchinari", "malt extract": "estratto di malto",
    "manganese ore": "minerale di manganese", "margarine": "margarina", "mattress materials": "materiali per materassi",
    "measuring instruments": "strumenti di misura", "medical instruments": "strumenti medici", "metal goods": "prodotti in metallo",
    "metal piping": "tubature in metallo", "milk": "latte", "minerals": "minerali", "motor vehicles": "autoveicoli",
    "motorcycles and cycles": "moto e biciclette", "natural gas": "gas naturale", "nickel": "nichel",
    "nitrogen compounds": "composti azotati", "nutmeg/cardamons": "noce moscata e cardamomo", "oil seeds": "semi oleosi",
    "olive oil": "olio d’oliva", "orthopedic appliances": "apparecchi ortopedici", "other animals": "altri animali",
    "other foods": "altri alimenti", "other nuts": "altra frutta a guscio", "packaged medicine": "medicinali confezionati",
    "packaged medicines": "medicinali confezionati", "paintings": "dipinti", "palm oil": "olio di palma", "paper": "carta",
    "paper containers": "contenitori di carta", "parts for motor vehicles": "parti di autoveicoli", "perfume plants": "piante da profumo",
    "perfumes": "profumi", "pesticides": "pesticidi", "petroleum coke": "coke di petrolio", "phosphates": "fosfati",
    "phosphoric acid": "acido fosforico", "pitted fruits": "frutta a nocciolo", "plastic products": "prodotti in plastica",
    "plastics": "materie plastiche", "platinum": "platino", "pork": "carne suina", "postage stamps/documents": "francobolli e documenti",
    "poultry": "pollame", "power equipment": "apparecchiature elettriche", "precious metal ore": "minerali di metalli preziosi",
    "precious stones": "pietre preziose", "prefabricated buildings": "edifici prefabbricati", "prepared meat": "carne lavorata",
    "processed crustaceans": "crostacei lavorati", "processed fruits and nuts": "frutta e frutta secca lavorate",
    "processed hair": "capelli lavorati", "radioactive chemicals": "sostanze chimiche radioattive",
    "railway cargo containers": "container ferroviari", "rapeseed oil": "olio di colza", "rare earth ores": "minerali di terre rare",
    "rare-earth metal compounds": "composti di terre rare", "raw copper": "rame grezzo", "raw materials": "materie prime",
    "raw sugar": "zucchero grezzo", "reaction and catalytic products": "prodotti di reazione e catalizzatori",
    "recreational boats": "imbarcazioni da diporto", "refined copper": "rame raffinato", "refined petroleum": "petrolio raffinato",
    "rice": "riso", "rubber": "gomma", "rubber products": "prodotti in gomma", "rubber tires": "pneumatici",
    "scented mixtures": "miscele profumate", "scrap iron": "rottami di ferro", "seats": "sedili", "seed oils": "oli di semi",
    "semi-finished iron": "semilavorati di ferro", "semiconductors": "semiconduttori", "sheep and goat meat": "carne ovina e caprina",
    "sheep and goats": "ovini e caprini", "shellfish": "molluschi e crostacei", "ships": "navi",
    "small specialty machinery": "piccole macchine speciali", "soap": "sapone", "sorghum": "sorgo", "soybean meal": "farina di soia",
    "soybean oil": "olio di soia", "soybeans": "soia", "spice seeds": "semi di spezie", "steel": "acciaio",
    "stone processing machines": "macchine per la lavorazione della pietra", "sulphur": "zolfo", "synthetic fabric": "tessuti sintetici",
    "synthetic fibers": "fibre sintetiche", "tanks and armored vehicles": "carri armati e veicoli blindati", "tea": "tè",
    "telephones": "telefoni", "textiles": "tessili", "tin ores": "minerali di stagno", "titanium ore": "minerale di titanio",
    "tobacco": "tabacco", "toilet paper": "carta igienica", "tomatoes": "pomodori", "tractors": "trattori", "trailers": "rimorchi",
    "tropical fruits": "frutta tropicale", "trucks": "camion", "trunks and cases": "bauli e valigie",
    "tungsten ore": "minerale di tungsteno", "unpackaged medicine": "medicinali sfusi", "uranium and thorium ore": "minerali di uranio e torio",
    "used rubber tires": "pneumatici usati", "vaccines": "vaccini", "valves": "valvole", "vanilla": "vaniglia",
    "vehicle bodies": "carrozzerie", "vehicle parts/accessories": "parti e accessori di veicoli", "video displays": "schermi",
    "washing and bottling machines": "macchine per lavare e imbottigliare", "watches": "orologi", "water": "acqua", "wheat": "grano",
    "wheat flours": "farine di grano", "wine": "vino", "wood": "legname", "wood pulp": "pasta di legno",
    "woodworking machines": "macchine per la lavorazione del legno", "wool": "lana", "zinc ore": "minerale di zinco",
}
AGRICOLI = {
    "apples": "mele", "apricots": "albicocche", "areca nuts": "noci di areca", "avocados": "avocado", "bananas": "banane",
    "barley": "orzo", "beans": "fagioli", "beef": "carne bovina", "beef offal": "frattaglie bovine", "berries": "frutti di bosco",
    "betel nuts": "noci di betel", "bison milk": "latte di bufala", "breadfruit": "frutto dell’albero del pane", "cabbages": "cavoli",
    "calamansi": "calamansi", "camel meat": "carne di cammello", "camel milk": "latte di cammella", "cantaloupes/melons": "meloni",
    "carrots/turnips": "carote e rape", "cashews": "anacardi", "cassava": "manioca", "cattle": "bovini",
    "cauliflower/broccoli": "cavolfiori e broccoli", "cereals": "cereali", "cheese": "formaggio", "chestnuts": "castagne",
    "chicken": "carne di pollo", "chickens": "polli", "chillies/peppers": "peperoncini e peperoni", "citrus fruits": "agrumi",
    "cocoa beans": "fave di cacao", "coconuts": "noci di cocco", "coffee": "caffè", "corn": "mais", "cotton": "cotone",
    "cowpeas": "fagioli dall’occhio", "cucumbers": "cetrioli", "cucumbers/gherkins": "cetrioli e cetriolini",
    "dairy products": "latticini", "dates": "datteri", "duck": "anatra", "eggplant": "melanzane", "eggplants": "melanzane",
    "eggs": "uova", "fiber crops": "piante da fibra", "figs": "fichi", "fish": "pesce", "fonio": "fonio", "fruit; dairy": "frutta e latticini",
    "fruits": "frutta", "game meat": "selvaggina", "ginger": "zenzero", "goat meat": "carne di capra", "goat milk": "latte di capra",
    "gourds": "zucche", "grapefruits": "pompelmi", "grapes": "uva", "green onions": "cipollotti", "groundnuts": "arachidi",
    "guava": "guava", "hides": "pelli", "horse meat": "carne di cavallo", "horses": "cavalli", "jute": "iuta",
    "kangkong": "kangkong (spinacio d’acqua)", "kiwifruit": "kiwi", "lamb/mutton": "carne ovina", "lemons/limes": "limoni e lime",
    "lentils": "lenticchie", "lettuce": "lattuga", "livestock; fish": "bestiame e pesce", "maize": "mais", "mangoes": "manghi",
    "mangoes/guavas": "manghi e guave", "melons": "meloni", "milk": "latte", "millet": "miglio", "none": "nessuno", "noni": "noni",
    "nuts": "frutta a guscio", "oats": "avena", "oil palm fruit": "frutti della palma da olio", "okra": "gombo", "olives": "olive",
    "olives; cattle": "olive e bovini", "onions": "cipolle", "oranges": "arance", "other meats": "altre carni", "papaya": "papaie",
    "papayas": "papaie", "peaches/nectarines": "pesche e nettarine", "pears": "pere", "peas": "piselli", "peppers": "peperoni",
    "pigeon peas": "caiano (pisello d’Angola)", "pigs": "suini", "pineapples": "ananas", "plantains": "platani", "plums": "prugne",
    "polynesian almonds": "mandorle polinesiane", "polynesian chestnuts": "castagne polinesiane", "pork": "carne suina",
    "pork fat": "grasso di maiale", "pork offal": "frattaglie suine", "potatoes": "patate", "potatoes; livestock": "patate e bestiame",
    "poultry": "pollame", "pulses": "legumi", "pumpkins/squash": "zucche", "radishes": "ravanelli", "rapeseed": "colza",
    "reindeer": "renne", "rice": "riso", "root vegetables": "radici e tuberi", "rubber": "gomma", "rye": "segale",
    "sesame seeds": "semi di sesamo", "sheep": "ovini", "sheep milk": "latte di pecora", "sheep offal": "frattaglie ovine",
    "sheepskins": "pelli di pecora", "shellfish": "molluschi e crostacei", "small quantities of rye": "piccole quantità di segale",
    "sorghum": "sorgo", "soursop": "graviola", "soybeans": "soia", "spices": "spezie", "spinach": "spinaci", "squash/pumpkins": "zucche",
    "sugar beets": "barbabietole da zucchero", "sugarcane": "canna da zucchero", "sunflower seeds": "semi di girasole",
    "sweet potatoes": "patate dolci", "sweet potatoes; fish": "patate dolci e pesce", "tangerines/mandarins": "mandarini",
    "taro": "taro", "tea": "tè", "tobacco": "tabacco", "tomatoes": "pomodori", "triticale": "triticale",
    "tropical fruits": "frutta tropicale", "vegetables": "ortaggi", "watermelons": "angurie", "wheat": "grano", "wool": "lana",
    "yams": "igname", "yautia": "yautia (malanga)",
}
# nomi dei partner commerciali come li scrive il Factbook → nome dello Stato in PanGeo (o nome italiano, se non è tra i 198)
PARTNER = {
    "American Samoa": "Samoa Americane", "Bermuda": "Bermuda", "Hong Kong": "Hong Kong", "Antigua & Barbuda": "Antigua e Barbuda", "Azerbaijan": "Azerbaigian", "Belgium": "Belgio",
    "Bosnia & Herzegovina": "Bosnia ed Erzegovina", "Brazil": "Brasile", "Cambodia": "Cambogia", "Cameroon": "Camerun",
    "Cayman Islands": "Isole Cayman", "Chile": "Cile", "China": "Cina", "Cote d'Ivoire": "Costa d’Avorio", "Croatia": "Croazia",
    "Cyprus": "Cipro", "Czechia": "Repubblica Ceca", "DRC": "RD Congo", "Denmark": "Danimarca", "Djibouti": "Gibuti",
    "Dominican Republic": "Repubblica Dominicana", "Egypt": "Egitto", "Ethiopia": "Etiopia", "Fiji": "Figi", "Finland": "Finlandia",
    "France": "Francia", "Germany": "Germania", "Greece": "Grecia", "Hungary": "Ungheria", "Iceland": "Islanda", "Ireland": "Irlanda",
    "Israel": "Israele", "Italy": "Italia", "Jamaica": "Giamaica", "Japan": "Giappone", "Jordan": "Giordania",
    "Kazakhstan": "Kazakistan", "Kyrgyzstan": "Kirghizistan", "Latvia": "Lettonia", "Lebanon": "Libano", "Libya": "Libia",
    "Lithuania": "Lituania", "Malaysia": "Malesia", "Marshall Islands": "Isole Marshall", "Mexico": "Messico", "Morocco": "Marocco",
    "Mozambique": "Mozambico", "NZ": "Nuova Zelanda", "Netherlands": "Paesi Bassi", "North Macedonia": "Macedonia del Nord",
    "Norway": "Norvegia", "Peru": "Perù", "Philippines": "Filippine", "Poland": "Polonia", "Portugal": "Portogallo",
    "S. Korea": "Corea del Sud", "Saudi Arabia": "Arabia Saudita", "Slovakia": "Slovacchia", "South Africa": "Sudafrica",
    "South Sudan": "Sud Sudan", "Spain": "Spagna", "St. Kitts & Nevis": "Saint Kitts e Nevis", "St. Lucia": "Saint Lucia",
    "St. Vincent & the Grenadines": "Saint Vincent e Grenadine", "Sweden": "Svezia", "Switzerland": "Svizzera",
    "Thailand": "Thailandia", "Trinidad & Tobago": "Trinidad e Tobago", "Turkey": "Turchia", "UAE": "Emirati Arabi", "UK": "Regno Unito",
    "United Kingdom": "Regno Unito", "United States": "USA", "Ukraine": "Ucraina",
}
FONTI_EL = {"fossil fuels": "combustibili fossili", "nuclear": "nucleare", "solar": "solare", "wind": "eolico",
            "hydroelectricity": "idroelettrico", "geothermal": "geotermico", "biomass and waste": "biomasse e rifiuti",
            "tide and wave": "maree e onde"}
NAVI = {"bulk carrier": "portarinfuse", "container ship": "portacontainer", "general cargo": "carico generale",
        "oil tanker": "petroliere", "other": "altre"}
MOLT = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
mancanti = set()


def testo(v):
    if isinstance(v, dict):
        v = v.get("text", "")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(v or "")))).strip()


def numero(v):
    """«128.692 million kW (2023 est.)» → [128692000.0, 2023]; «56% of …» → [56.0, 2023]. None se non c'è un numero."""
    t = testo(v)
    m = re.match(r"^[^\d\-]{0,3}(-?[\d,]*\.?\d+)\s*(thousand|million|billion|trillion)?", t)
    if not m or t[:2].upper() == "NA":
        return None
    try:
        x = float(m.group(1).replace(",", "")) * MOLT.get(m.group(2) or "", 1)
    except ValueError:
        return None
    a = re.search(r"\((?:FY)?(\d{4})", t) or re.search(r"\b(19|20)\d\d\b", t[m.end():])
    anno = int(a.group(1)) if a and len(a.group(1)) == 4 else (int(a.group(0)) if a else None)
    return [round(x, 3) if x < 1000 else round(x), anno]


def ultimo(d, prefisso):
    """Il valore più recente tra chiavi tipo «Imports 2024», «Imports 2023»."""
    voci = sorted(((k, v) for k, v in (d or {}).items() if k.startswith(prefisso) and re.search(r"\d{4}$", k)), reverse=True)
    for _, v in voci:
        n = numero(v)
        if n:
            return n
    return numero(d) if isinstance(d, dict) and "text" in d else None


def elenco(v, dizionario):
    """«milk, wheat, grapes (2023)» → (["latte", "grano", "uva"], 2023)"""
    t = testo(v)
    a = re.search(r"\((\d{4})", t)
    voci = []
    for w in re.sub(r"\(.*?\)", "", t).split(","):
        w = w.strip().lower()
        if not w or w == "na":
            continue
        if w not in dizionario:
            mancanti.add(w)
        voci.append(dizionario.get(w, w))
    return voci, (int(a.group(1)) if a else None)


def partner(v, stati):
    t = testo(v).replace("Congo, Republic of the", "Congo").replace("Congo, Democratic Republic of the", "DRC")
    t = re.sub(r", The\b", "", t)
    a = re.search(r"\((\d{4})", t)
    voci = []
    for w in re.sub(r"\(.*?\)", "", t).split(","):
        w = w.strip()
        m = re.match(r"^(.*?)\s*([\d.]+)%$", w)
        nome, quota = (m.group(1).strip(), float(m.group(2))) if m else (w, None)
        if not nome or nome.upper() == "NA":
            continue
        it = PARTNER.get(nome, nome)
        if it not in stati and nome not in PARTNER:
            mancanti.add("partner: " + nome)
        voci.append([it, quota])
    return voci, (int(a.group(1)) if a else None)


def quota(prod, cons, imp=None, minimo=0):
    """Quanta parte del consumo NON è coperta dalla produzione interna, in % (0–100). None se i numeri non bastano
    o se il consumo è così piccolo (sotto «minimo») che la percentuale direbbe poco."""
    if not cons or not cons[0] or cons[0] < minimo:
        return None
    if prod:
        return max(0, min(100, round(100 * (cons[0] - prod[0]) / cons[0])))
    return 100  # il Factbook non scrive mai «0»: dove la produzione è nulla la voce manca. Consumo senza produzione = tutto da fuori


def scheda(d, stati):
    E, T, EC, PS, G, M = (d.get(k, {}) for k in ("Energy", "Transportation", "Economy", "People and Society", "Geography",
                                                 "Military and Security"))
    s = {}
    # --- energia
    el, gas, pet, carb, nuc = (E.get(k, {}) for k in ("Electricity", "Natural gas", "Petroleum", "Coal", "Nuclear energy"))
    en = {
        "accesso": numero((E.get("Electricity access") or {}).get("electrification - total population")),
        "capacita": numero(el.get("installed generating capacity")), "consumo": numero(el.get("consumption")),
        "import": numero(el.get("imports")), "export": numero(el.get("exports")),
        "perdite": numero(el.get("transmission/distribution losses")),
        "fonti": sorted(([FONTI_EL.get(k, k), numero(v)[0]] for k, v in (E.get("Electricity generation sources") or {}).items()
                         if numero(v) and numero(v)[0] > 0), key=lambda x: -x[1]),
        "fonti_anno": next((numero(v)[1] for v in (E.get("Electricity generation sources") or {}).values() if numero(v)), None),
        "nucleare": {k2: numero(nuc.get(k1)) for k1, k2 in (("Number of operational nuclear reactors", "attivi"),
                                                               ("Number of nuclear reactors under construction", "in_costruzione"),
                                                               ("Number of nuclear reactors permanently shut down", "chiusi"),
                                                               ("Percent of total electricity production", "quota"),
                                                               ("Net capacity of operational nuclear reactors", "gw")) if numero(nuc.get(k1))},
        "petrolio": {k2: numero(pet.get(k1)) for k1, k2 in (("total petroleum production", "prod"),
                                                              ("refined petroleum consumption", "cons"),
                                                              ("crude oil estimated reserves", "riserve")) if numero(pet.get(k1))},
        "gas": {k: numero(gas.get(k0)) for k0, k in (("production", "prod"), ("consumption", "cons"), ("imports", "imp"),
                                                       ("exports", "exp"), ("proven reserves", "riserve")) if numero(gas.get(k0))},
        "carbone": {k: numero(carb.get(k0)) for k0, k in (("production", "prod"), ("consumption", "cons"), ("imports", "imp"),
                                                            ("exports", "exp"), ("proven reserves", "riserve")) if numero(carb.get(k0))},
        "procapite": ultimo(E.get("Energy consumption per capita"), "Total energy consumption per capita"),
    }
    # sotto 5.000 barili al giorno, 100 milioni di m³ o mezzo milione di tonnellate il combustibile quasi non si usa
    dip = {"petrolio": quota(en["petrolio"].get("prod"), en["petrolio"].get("cons"), None, 5e3),
           "gas": quota(en["gas"].get("prod"), en["gas"].get("cons"), en["gas"].get("imp"), 1e8),
           "carbone": quota(en["carbone"].get("prod"), en["carbone"].get("cons"), en["carbone"].get("imp"), 5e5)}
    if en["consumo"] and en["consumo"][0] and (en["import"] or en["export"]):
        netto = (en["import"] or [0])[0] - (en["export"] or [0])[0]
        dip["elettricita"] = max(0, min(100, round(100 * netto / en["consumo"][0])))
    en["dipendenza"] = {k: v for k, v in dip.items() if v is not None}
    s["energia"] = {k: v for k, v in en.items() if v not in (None, [], {})}
    # --- trasporti e logistica
    fer, porti, flotta = T.get("Railways") or {}, T.get("Ports") or {}, T.get("Merchant marine") or {}
    tr = {"aeroporti": numero(T.get("Airports")), "eliporti": numero(T.get("Heliports")), "ferrovie": numero(fer.get("total")),
          "porti": numero(porti.get("total ports")), "porti_grandi": numero(porti.get("large")), "porti_medi": numero(porti.get("medium")),
          "porti_petrolio": numero(porti.get("ports with oil terminals")), "porti_principali": testo(porti.get("key ports")),
          "flotta": numero(flotta.get("total"))}
    m = re.search(r"([\d,]+)\s*km electrified", testo(fer.get("total")))
    if m:
        tr["ferrovie_elettr"] = int(m.group(1).replace(",", ""))
    tipi = []
    for w in testo(flotta.get("by type")).split(", "):
        m = re.match(r"^(.*?)\s+([\d,]+)$", w.strip())
        if m:
            tipi.append([NAVI.get(m.group(1).strip(), m.group(1).strip()), int(m.group(2).replace(",", ""))])
    if tipi:
        tr["flotta_tipi"] = tipi
    s["trasporti"] = {k: v for k, v in tr.items() if v not in (None, "", [])}
    # --- cibo, terra, acqua
    uso = G.get("Land use") or {}
    prodotti, anno_p = elenco(EC.get("Agricultural products"), AGRICOLI)
    acqua = (PS.get("Drinking water source") or {}).get("improved: total")
    ci = {"prodotti": [p for p in prodotti if p != "nessuno"], "prodotti_anno": anno_p, "terra_agricola": numero(uso.get("agricultural land")),
          "arabile": numero(re.sub(r"^[^:]*:", "", testo(uso.get("agricultural land: arable land")))),
          "irrigata": numero(G.get("Irrigated land")),
          "spesa_cibo": numero((EC.get("Average household expenditures") or {}).get("on food")),
          "acqua": numero(re.sub(r"^[^:]*:", "", testo(acqua)))}
    s["cibo"] = {k: v for k, v in ci.items() if v not in (None, [], "")}
    # --- commercio e dipendenze
    imp_da, a1 = partner(EC.get("Imports - partners"), stati)
    exp_a, a2 = partner(EC.get("Exports - partners"), stati)
    imp_m, a3 = elenco(EC.get("Imports - commodities"), MERCI)
    exp_m, a4 = elenco(EC.get("Exports - commodities"), MERCI)
    co = {"import": ultimo(EC.get("Imports"), "Imports "), "export": ultimo(EC.get("Exports"), "Exports "),
          "import_da": imp_da, "export_a": exp_a, "import_merci": imp_m, "export_merci": exp_m, "anno": a1 or a2 or a3 or a4}
    s["commercio"] = {k: v for k, v in co.items() if v not in (None, [], "")}
    # --- spesa per settori (in % del PIL, per confrontarle) e bilancio dello Stato
    mil = sorted(([int(re.search(r"\d{4}", k).group(0)), numero(v)[0]] for k, v in (M.get("Military expenditures") or {}).items()
                  if re.search(r"\d{4}", k) and numero(v)), reverse=True)
    san, istr, bil = PS.get("Health expenditure") or {}, PS.get("Education expenditure") or {}, EC.get("Budget") or {}
    sp = {"militare": mil[:5], "sanita": numero(san.get("Health expenditure (as % of GDP)")),
          "sanita_bilancio": numero(san.get("Health expenditure (as % of national budget)")),
          "istruzione": numero(istr.get("Education expenditure (% GDP)")),
          "istruzione_bilancio": numero(istr.get("Education expenditure (% national budget)")),
          "entrate": numero(bil.get("revenues")), "uscite": numero(bil.get("expenditures")),
          "debito": ultimo(EC.get("Public debt"), "Public debt"), "tasse": numero(EC.get("Taxes and other revenues")),
          "pil": numero(EC.get("GDP (official exchange rate)"))}
    s["spesa"] = {k: v for k, v in sp.items() if v not in (None, [], "")}
    return {k: v for k, v in s.items() if v}


def main():
    cfg = json.load(open(os.path.join(RADICE, "programma", "config.json"), encoding="utf-8"))
    paesi = json.load(open(os.path.join(RADICE, "programma", "paesi.json"), encoding="utf-8"))
    fb = cfg["sapere"]["factbook"]
    locale = sys.argv[1] if len(sys.argv) > 1 else ""

    def prendi(voce):
        stato, percorso = voce
        if locale:
            return stato, json.load(open(os.path.join(locale, percorso.replace("/", "_") + ".json"), encoding="utf-8"))
        for i in range(3):
            try:
                return stato, json.loads(urllib.request.urlopen(BASE + percorso + ".json", timeout=60).read())
            except Exception as e:  # noqa: BLE001
                errore = e
                time.sleep(2 * (i + 1))
        raise SystemExit(f"{stato}: {errore}")

    with cf.ThreadPoolExecutor(8) as ex:
        dati = dict(ex.map(prendi, fb.items()))
    stati = {s: scheda(d, paesi) for s, d in sorted(dati.items())}
    if mancanti:
        print("Senza traduzione (restano in inglese):", ", ".join(sorted(mancanti)))
    uscita = {"agg": date.today().isoformat(),
              "fonte": "CIA World Factbook, copia d'archivio (github.com/factbook/factbook.json)",
              "nota": "Ogni numero ha il suo anno. Le dipendenze sono calcolate da PanGeo su produzione e consumo: ordine di grandezza.",
              "percorsi": {s: fb[s] for s in stati}, "stati": stati}
    os.makedirs(os.path.join(RADICE, "tabelle"), exist_ok=True)
    dst = os.path.join(RADICE, "tabelle", "infra.json")
    json.dump(uscita, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(stati)} Stati, {os.path.getsize(dst) // 1024} KB → {dst}")
    for campo in ("energia", "trasporti", "cibo", "commercio", "spesa"):
        print(f"  {campo}: {sum(1 for v in stati.values() if v.get(campo))} Stati")


if __name__ == "__main__":
    main()

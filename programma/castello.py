#!/usr/bin/env python3
"""PanGeo 2.7.3 (prima «Castello mentale») - programma per Termux (Android) e per qualsiasi computer con Python 3.

Raccoglie da fonti gratuite notizie, video, voci ufficiali, disastri e traffico aereo civile,
li collega agli Stati del Castello e li mostra nella cartella «Live dal mondo» del planisfero.
Si amplia da solo: prova le fonti candidate e scopre nuovi siti tra quelli più citati.

Comandi:
  python castello.py aggiorna              raccoglie tutto e scrive web/live.js
  python castello.py serve [porta]         apre il Castello su http://127.0.0.1:8080
  python castello.py stato                 riassunto: notizie, cielo, fonti
  python castello.py fonti                 elenco delle fonti e del loro stato
  python castello.py fonte URL [tema]      aggiunge un feed RSS o Atom
  python castello.py youtube @canale       aggiunge un canale YouTube
  python castello.py telegram canale [chi] aggiunge un canale Telegram pubblico
  python castello.py chiave nome valore    salva una chiave gratuita (es. opensky_id)
  python castello.py approva               installa il programma nuovo arrivato da GitHub (mai da solo)
  python castello.py salute                controlla che il cuore del programma sia sano
  python castello.py bot                   collega il tuo bot Telegram (dopo: chiave telegram_bot)
  python castello.py sincronizza           (facoltativo) scambia file con GitHub
  python castello.py istantanea index.html [origine] [--brief file.txt]
                                           mette i dati live (e un riassunto) dentro un file del Castello
  python castello.py ripristina index.html  riprende lo storico del cielo da un file del Castello
Usa solo la libreria standard di Python: nessun pacchetto da installare.
"""
import email.utils
import functools
import hashlib
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

VERSIONE = "2.7.3"
QUI = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(QUI, "web")
DATI = os.path.join(QUI, "dati")
UA = "Mozilla/5.0 (Linux; Android 14) PanGeo/" + VERSIONE
ATOM = "{http://www.w3.org/2005/Atom}"
RSS1 = "{http://purl.org/rss/1.0/}"
DC = "{http://purl.org/dc/elements/1.1/}"
MAPPE = ["https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/json/world.json",
         "https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/js/world.js"]
OPENSKY = "https://opensky-network.org/api/states/all"
APP_FILE = ["manifest.webmanifest", "sw.js", "icona-192.png", "icona-512.png", "icona-maskable-512.png"]
OPENSKY_AUTH = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

# Parole di difesa e geopolitica: per le testate generaliste e le fonti scoperte da sole
# entrano solo i titoli che ne contengono almeno una.
FILTRO = re.compile(
    r"guerr|\bwars?\b|warfare|militar|esercit|\barmy|difes[ae]|defen[cs]|missil|\bdron|\bnato\b|attacc|attack|"
    r"strike|\braid|bomb|trupp|troop|soldat|soldier|\bnavy|naval|marina milit|air ?force|aeronautic|sanzion|"
    r"sanction|conflitt|conflict|ceasefire|cessate il fuoco|tregua|protest|golpe|\bcoup\b|elezion|election|"
    r"minist|presiden|summit|vertic|nuclear|nucleare|terror|weapon|\barmi\b|\barms\b|border|confin|refugee|"
    r"profugh|rifugiat|embargo|treaty|trattat|intelligence|\bspy|\bspi[ae]\b|cyber|hacker|propagand|disinform|"
    r"ostagg|hostage|offensiv|invasion|occupat|frontline|shelling|artiglier|artiller|militia|milizi|rebel|"
    r"ribell|insurg|jihad|\bisis\b|hamas|hezbollah|houthi|kremlin|cremlino|pentagon|diplomat|ambasciat|embassy|"
    r"tariff|\bdazi|pipeline|gasdott|undersea|sottomarin|strait|stretto di|blockade|airspace|spazio aereo|"
    r"earthquake|terremoto|cyclone|ciclone|flood|alluvion|famine|carestia|humanitarian|umanitari|"
    r"sicurezza|security|satellit|space force|spazio",
    re.I)

# Nomi in cirillico (testi russi e ucraini, come quelli dei canali Telegram ufficiali).
ALIAS_RX = {
    "Ucraina": r"Україн\w*|Украин\w*", "Russia": r"Росі[яїю]\w*|Росси\w*|\bРФ\b",
    "USA": r"\bСША\b", "Israele": r"Ізраїл\w*|Израил\w*", "Iran": r"Іран\w*|Иран\w*",
    "Cina": r"Китай\w*|Кита[яюе]\b|\bКНР\b", "Bielorussia": r"Білорус\w*|Беларус\w*|Белорусс\w*",
    "Polonia": r"Польщ\w*|Польш\w*", "Germania": r"Німеччин\w*|Германи\w*", "Francia": r"Франці\w*|Франци\w*",
    "Regno Unito": r"Великобритані\w*|Великобритани\w*", "Turchia": r"Туреччин\w*|Турци\w*",
    "Corea del Nord": r"\bКНДР\b",
}
ESCLUSI = {"news.google.com", "google.com", "youtube.com", "youtu.be", "msn.com", "yahoo.com", "facebook.com",
           "x.com", "twitter.com", "t.me", "instagram.com", "tiktok.com", "linkedin.com", "reddit.com",
           "apple.com", "bing.com", "flipboard.com", "newsbreak.com", "ground.news", "archive.org"}


# ----------------------------------------------------------------------------- utilità

def leggi_json(percorso, predefinito):
    try:
        with open(percorso, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return predefinito


def scrivi_json(percorso, dati):
    tmp = percorso + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False)
    os.replace(tmp, percorso)


def scarica(url, timeout=25, intestazioni=None, corpo=None):
    h = {"User-Agent": UA, "Accept-Language": "it,en;q=0.8"}
    h.update(intestazioni or {})
    req = urllib.request.Request(url, headers=h, data=corpo)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def data_iso(testo):
    """Converte le date dei feed (RFC 822, ISO, GDELT) in ISO UTC."""
    if not testo:
        return None
    testo = testo.strip()
    try:
        d = email.utils.parsedate_to_datetime(testo)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    m = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$", testo)
    if m:
        return datetime(*map(int, m.groups()), tzinfo=timezone.utc).isoformat()
    try:
        d = datetime.fromisoformat(testo.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def mostra_data(iso):
    if not iso:
        return ""
    return datetime.fromisoformat(iso).astimezone().strftime("%d/%m %H:%M")


def solo_http(u):
    return u if isinstance(u, str) and u.startswith(("http://", "https://")) else ""


def dominio(u):
    try:
        d = urllib.parse.urlparse(u).netloc.lower().split(":")[0]
    except ValueError:
        return ""
    return d[4:] if d.startswith("www.") else d


def pulisci(testo, massimo=240):
    testo = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", testo or ""))).strip()
    return testo if len(testo) <= massimo else testo[: massimo - 1].rstrip() + "…"


class Riconoscitore:
    """Trova i nomi degli Stati nei titoli (italiano, inglese e cirillico)."""

    def __init__(self, paesi):
        self.regole = []
        for stato, nomi in paesi.items():
            alt = "|".join(re.escape(n) for n in sorted(nomi, key=len, reverse=True))
            if stato in ALIAS_RX:
                alt += "|" + ALIAS_RX[stato]
            self.regole.append((stato, re.compile(r"(?<![\w])(?:" + alt + r")(?![\w])")))

    def trova(self, testo):
        trovati = []
        for stato, rx in self.regole:
            if rx.search(testo):
                trovati.append(stato)
                if len(trovati) == 5:
                    break
        return trovati


def leggi_rss(contenuto):
    """Restituisce (titolo, link, data, fonte, sito) da un feed RSS 2.0, RSS 1.0 o Atom."""
    testa = contenuto[:300].lstrip().lower()
    if testa.startswith((b"<!doctype html", b"<html")):
        raise ValueError("il sito ha risposto con una pagina web invece del feed (blocco anti-robot?)")
    try:
        radice = ET.fromstring(contenuto)
    except ET.ParseError:
        # feed scritti male: «&» non codificati e caratteri di controllo
        pulito = re.sub(rb"&(?!(?:[a-zA-Z]{2,8}|#\d{1,6}|#x[0-9a-fA-F]{1,6});)", b"&amp;", contenuto)
        pulito = re.sub(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", b"", pulito)
        radice = ET.fromstring(pulito)
    voci = []
    for tag in ("item", RSS1 + "item"):
        ns = RSS1 if tag.startswith("{") else ""
        for it in radice.iter(tag):
            fonte_el = it.find("source")
            voci.append((
                pulisci(it.findtext(ns + "title") or "", 300),
                (it.findtext(ns + "link") or "").strip(),
                data_iso(it.findtext("pubDate") or it.findtext(DC + "date")),
                fonte_el.text.strip() if fonte_el is not None and fonte_el.text else "",
                fonte_el.get("url", "") if fonte_el is not None else "",
            ))
    for en in radice.iter(ATOM + "entry"):
        link = ""
        for l in en.findall(ATOM + "link"):
            if l.get("rel", "alternate") == "alternate":
                link = l.get("href", "")
        autore = en.find(ATOM + "author")
        voci.append((
            pulisci(en.findtext(ATOM + "title") or "", 300),
            link,
            data_iso(en.findtext(ATOM + "published") or en.findtext(ATOM + "updated")),
            (autore.findtext(ATOM + "name") or "").strip() if autore is not None else "",
            "",
        ))
    return voci


# ----------------------------------------------------------------------------- fonti

def google_news(q, lingua):
    hl, gl = ("it", "IT") if lingua == "it" else ("en", "US")
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + " when:1d", "hl": hl, "gl": gl, "ceid": f"{gl}:{hl}"})
    voci = []
    for titolo, link, data, fonte, sito in leggi_rss(scarica(url)):
        if fonte and titolo.endswith(" - " + fonte):
            titolo = titolo[: -len(fonte) - 3]
        voci.append((titolo, link, data, fonte or "Google News", sito))
    return voci


def gdelt(q):
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(
        {"query": q, "mode": "ArtList", "format": "json", "maxrecords": "75", "timespan": "1d", "sort": "DateDesc"})
    try:
        testo = scarica(url).decode("utf-8", "replace").strip()
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        time.sleep(15)  # GDELT chiede una richiesta ogni 5 secondi: si aspetta e si riprova una volta
        testo = scarica(url).decode("utf-8", "replace").strip()
    if not testo.startswith("{"):
        raise ValueError("risposta GDELT non valida: " + testo[:80])
    voci = []
    for a in json.loads(testo).get("articles", []):
        d = a.get("domain", "")
        voci.append((a.get("title", ""), a.get("url", ""), data_iso(a.get("seendate")), d or "GDELT",
                     "https://" + d if d else ""))
    return voci


def id_canale(handle, cache):
    if handle in cache:
        return cache[handle]
    pagina = scarica("https://www.youtube.com/" + handle.lstrip("/")).decode("utf-8", "replace")
    m = (re.search(r'<meta itemprop="identifier" content="(UC[0-9A-Za-z_-]{22})"', pagina)
         or re.search(r'"externalId":"(UC[0-9A-Za-z_-]{22})"', pagina)
         or re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', pagina))
    if not m:
        raise ValueError("canale non trovato")
    cache[handle] = m.group(1)
    return cache[handle]


def telegram(canale, citati=None):
    """Legge l'anteprima pubblica di un canale Telegram (t.me/s/...), senza account."""
    pagina = scarica("https://t.me/s/" + canale.lstrip("@")).decode("utf-8", "replace")
    voci = []
    for blocco in pagina.split('class="tgme_widget_message_wrap')[1:]:
        post = re.search(r'data-post="([^"]+)"', blocco)
        testo = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', blocco, re.S)
        quando = re.search(r'<time[^>]*datetime="([^"]+)"', blocco)
        if not post or not testo:
            continue
        t = pulisci(testo.group(1).replace("<br/>", " ").replace("<br>", " "))
        if t:
            voci.append((t, "https://t.me/" + post.group(1), data_iso(quando.group(1)) if quando else None))
        if citati is not None:  # canali citati o inoltrati: servono a scoprirne di nuovi
            for nome in set(re.findall(r'href="https://t\.me/(?:s/)?([A-Za-z][A-Za-z0-9_]{4,31})(?:/\d+)?["?]', blocco)):
                if nome.lower() not in (canale.lstrip("@").lower(), "share", "joinchat", "addstickers", "proxy", "iv"):
                    citati.setdefault(nome, set()).add(canale)
    return voci


def trova_feed(dom):
    """Cerca il feed di un sito: prima i link nella home, poi gli indirizzi più comuni."""
    base = "https://" + dom
    prove = []
    try:
        pagina = scarica(base + "/", timeout=15).decode("utf-8", "replace")[:400000]
        for tag in re.findall(r"<link[^>]+>", pagina, re.I):
            if re.search(r"application/(rss|atom)\+xml", tag, re.I) and not re.search(r"comment", tag, re.I):
                h = re.search(r"href=[\"']([^\"']+)", tag)
                if h:
                    prove.append(urllib.parse.urljoin(base + "/", html.unescape(h.group(1))))
    except Exception:
        pass
    prove += [base + p for p in ("/feed/", "/rss", "/rss.xml", "/feed.xml")]
    visti = []
    for u in prove:
        if u in visti:
            continue
        visti.append(u)
        if len(visti) > 6:
            break
        try:
            voci = leggi_rss(scarica(u, timeout=15))
            if len(voci) >= 3:
                return u
        except Exception:
            continue
    return None


# ----------------------------------------------------------------------------- cielo

def decodifica(stringa, scostamento, scala):
    """Decodifica le coordinate compresse delle mappe ECharts."""
    x0, y0 = scostamento
    punti = []
    for i in range(0, len(stringa) - 1, 2):
        x = ord(stringa[i]) - 64
        y = ord(stringa[i + 1]) - 64
        x = (x >> 1) ^ (-(x & 1))
        y = (y >> 1) ^ (-(y & 1))
        x += x0
        y += y0
        x0, y0 = x, y
        punti.append((x / scala, y / scala))
    return punti


def geo_da_mappa(mappa):
    """Da una mappa ECharts (GeoJSON, anche compresso) ai contorni esterni di ogni Paese."""
    compressa = mappa.get("UTF8Encoding")
    scala = mappa.get("UTF8Scale") or 1024
    geo = {}
    for f in mappa.get("features", []):
        nome = (f.get("properties") or {}).get("name")
        g = f.get("geometry") or {}
        if not nome or g.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        poligoni = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        scost = [g.get("encodeOffsets")] if g["type"] == "Polygon" else (g.get("encodeOffsets") or [])
        anelli = []
        for k, pol in enumerate(poligoni):
            if not pol:
                continue
            anello = pol[0]
            if compressa and isinstance(anello, str):
                anello = decodifica(anello, scost[k][0], scala)
            punti = [(round(p[0], 2), round(p[1], 2)) for p in anello]
            if len(punti) < 3:
                continue
            xs, ys = [p[0] for p in punti], [p[1] for p in punti]
            anelli.append([min(xs), min(ys), max(xs), max(ys), punti])
        if anelli:
            geo[nome] = anelli
    return geo


def carica_geo():
    percorso = os.path.join(DATI, "geo.json")
    geo = leggi_json(percorso, None)
    if geo:
        return geo
    ultimo = None
    for url in MAPPE:
        try:
            testo = scarica(url, timeout=90).decode("utf-8", "replace")
            inizio = testo.find("{", testo.find("registerMap(")) if url.endswith(".js") else testo.find("{")
            mappa, _ = json.JSONDecoder().raw_decode(testo, inizio)
            geo = geo_da_mappa(mappa)
            if geo:
                scrivi_json(percorso, geo)
                return geo
        except Exception as e:
            ultimo = e
    raise ValueError(f"mappa dei confini non scaricata ({ultimo})")


def dentro(x, y, punti):
    ok = False
    j = len(punti) - 1
    for i in range(len(punti)):
        xi, yi = punti[i]
        xj, yj = punti[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            ok = not ok
        j = i
    return ok


class IndiceGeo:
    """Dice in quale Paese cade un punto (lon, lat). Griglia di 5 gradi per andare veloce."""

    def __init__(self, geo):
        self.anelli, self.celle = [], {}
        for nome, anelli in geo.items():
            for x0, y0, x1, y1, punti in anelli:
                k = len(self.anelli)
                self.anelli.append((nome, x0, y0, x1, y1, punti, (x1 - x0) * (y1 - y0)))
                for cx in range(int(x0 // 5), int(x1 // 5) + 1):
                    for cy in range(int(y0 // 5), int(y1 // 5) + 1):
                        self.celle.setdefault((cx, cy), []).append(k)

    def paese(self, x, y):
        migliore, area = None, None
        for k in self.celle.get((int(x // 5), int(y // 5)), ()):
            nome, x0, y0, x1, y1, punti, a = self.anelli[k]
            if x0 <= x <= x1 and y0 <= y <= y1 and (area is None or a < area) and dentro(x, y, punti):
                migliore, area = nome, a  # vince il contorno più piccolo: enclavi come Lesotho o San Marino
        return migliore


def opensky_token(chiavi):
    corpo = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": chiavi["opensky_id"],
                                    "client_secret": chiavi["opensky_segreto"]}).encode()
    r = json.loads(scarica(OPENSKY_AUTH, timeout=30, corpo=corpo,
                           intestazioni={"Content-Type": "application/x-www-form-urlencoded"}))
    return r["access_token"]


def cielo(chiavi, it2en, errori):
    """Conta gli aerei in volo sopra ogni Stato (OpenSky, gratis) e segnala i cieli che si svuotano.
    Salva solo i conteggi: nessuna posizione, nessun aereo singolo."""
    try:
        indice = IndiceGeo(carica_geo())
    except Exception as e:
        errori.append(f"Cielo: {e}")
        return None
    intest = {}
    if chiavi.get("opensky_id") and chiavi.get("opensky_segreto"):
        try:
            intest["Authorization"] = "Bearer " + opensky_token(chiavi)
        except Exception as e:
            errori.append(f"OpenSky accesso con account: {e} (uso l'accesso anonimo)")
    try:
        risposta = json.loads(scarica(OPENSKY, timeout=90, intestazioni=intest))
    except Exception as e:
        errori.append(f"OpenSky: {e}")
        return None
    conta, in_volo = {}, 0
    for s in risposta.get("states") or []:
        if len(s) < 9 or s[8] or s[5] is None or s[6] is None:
            continue  # a terra o senza posizione
        in_volo += 1
        p = indice.paese(float(s[5]), float(s[6]))
        if p:
            conta[p] = conta.get(p, 0) + 1
    adesso = datetime.now(timezone.utc)
    limite = (adesso - timedelta(days=7)).isoformat()
    percorso = os.path.join(DATI, "cielo_storico.json")
    storico = leggi_json(percorso, {})
    paesi = {}
    for it, en in it2en.items():
        n = conta.get(en, 0)
        serie = [x for x in storico.get(it, []) if x[0] >= limite]
        # confronto con le stesse ore dei giorni prima: di notte si vola meno
        simili = [c for t, c in serie
                  if min(abs(datetime.fromisoformat(t).hour - adesso.hour),
                         24 - abs(datetime.fromisoformat(t).hour - adesso.hour)) <= 1]
        media = round(sum(simili) / len(simili), 1) if len(simili) >= 2 else None
        segnale = ""
        if media is not None and media >= 8:
            if n == 0:
                segnale = "vuoto"
            elif n < 0.4 * media:
                segnale = "calo"
        serie.append([adesso.isoformat(), n])
        storico[it] = serie
        paesi[it] = [n, media, segnale]
    scrivi_json(percorso, storico)
    return {"agg": datetime.now().strftime("%d/%m %H:%M"), "in_volo": in_volo, "paesi": paesi,
            "fonte": "OpenSky Network" + (" (account)" if "Authorization" in intest else " (anonimo)")}


def segnali_per_stato(nome_file, conta, it2en, adesso, regola):
    """Aggiorna lo storico di 7 giorni e restituisce {Stato: [oggi, media, segnale]}."""
    percorso = os.path.join(DATI, nome_file)
    storico = leggi_json(percorso, {})
    limite = (adesso - timedelta(days=7)).isoformat()
    paesi = {}
    for it, en in it2en.items():
        n = conta.get(en, 0)
        serie = [x for x in storico.get(it, []) if x[0] >= limite]
        media = round(sum(c for _, c in serie) / len(serie), 1) if len(serie) >= 2 else None
        serie.append([adesso.isoformat(), n])
        storico[it] = serie
        paesi[it] = [n, media, regola(n, media)]
    scrivi_json(percorso, storico)
    return paesi


def calore(chiavi, it2en, errori, ore):
    """Fonti di calore viste dai satelliti NASA (FIRMS, chiave gratuita) contate per Stato,
    una volta al giorno. Un aumento forte può indicare incendi, ma anche bombardamenti: va confermato."""
    chiave = chiavi.get("firms_key")
    if not chiave:
        return None
    percorso = os.path.join(DATI, "calore.json")
    vecchio = leggi_json(percorso, None)
    adesso = datetime.now(timezone.utc)
    if vecchio and vecchio.get("iso", "") >= (adesso - timedelta(hours=ore)).isoformat():
        return vecchio
    try:
        indice = IndiceGeo(carica_geo())
        testo = scarica(f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{chiave}/VIIRS_SNPP_NRT/world/1",
                        timeout=180).decode("utf-8", "replace")
    except Exception as e:
        errori.append(f"NASA FIRMS: {e}")
        return vecchio
    righe = testo.splitlines()
    if not righe or "latitude" not in righe[0]:
        errori.append("NASA FIRMS: risposta non valida (" + (righe[0][:60] if righe else "vuota") + ")")
        return vecchio
    testa = righe[0].split(",")
    ila, ilo = testa.index("latitude"), testa.index("longitude")
    conta, totale = {}, 0
    for r in righe[1:]:
        c = r.split(",")
        try:
            la, lo = float(c[ila]), float(c[ilo])
        except (ValueError, IndexError):
            continue
        totale += 1
        p = indice.paese(lo, la)
        if p:
            conta[p] = conta.get(p, 0) + 1
    paesi = segnali_per_stato("calore_storico.json", conta, it2en, adesso,
                              lambda n, m: "aumento" if m is not None and n >= 20 and n > 3 * m else "")
    uscita = {"iso": adesso.isoformat(), "agg": datetime.now().strftime("%d/%m %H:%M"), "totale": totale,
              "paesi": paesi, "fonte": "NASA FIRMS (VIIRS, ultime 24 ore)"}
    scrivi_json(percorso, uscita)
    return uscita



# ----------------------------------------------------------------------------- analisi delle fonti

# Livelli di affidabilità: A agenzie e fonti istituzionali neutrali; B testate e centri studi
# seri; C voci di parte (governi, media statali); D non classificate o trovate da sole.
LIVELLI_NOMI = {
    "A": ["reuters", "associated press", "ap news", "afp", "agence france-presse", "ansa", "agenzia nova",
          "adnkronos", "bloomberg", "dpa", "efe", "kyodo", "yonhap", "un news", "onu", "united nations",
          "gdacs", "usgs", "reliefweb", "agi", "askanews", "lapresse"],
    "B": ["bbc", "guardian", "new york times", "washington post", "financial times", "the economist",
          "wall street journal", "le monde", "corriere", "repubblica", "sole 24 ore", "la stampa", "il post",
          "politico", "al jazeera", "dw", "deutsche welle", "france 24", "euronews", "cnn", "npr", "abc news",
          "nbc news", "cbs news", "sky news", "the times", "telegraph", "independent", "der spiegel", "faz",
          "el país", "el pais", "nikkei", "south china morning post", "the hindu", "times of india",
          "defense news", "breaking defense", "naval news", "the aviationist", "defense one", "janes",
          "war on the rocks", "the diplomat", "analisi difesa", "difesa online", "formiche", "ispi", "ecfr",
          "isw", "crisis group", "bellingcat", "kyiv independent", "meduza", "times of israel", "haaretz",
          "euvsdisinfo", "rivista italiana difesa", "military times", "stars and stripes", "axios",
          "foreign policy", "foreign affairs", "rand", "csis", "iiss", "sipri", "chatham house", "rusi",
          "limes", "rainews", "tg24", "sky tg24", "il fatto quotidiano", "il messaggero", "avvenire",
          "ilsole24ore", "wsj", "jerusalem post", "arab news", "ahram", "ekathimerini", "the hill", "c-span",
          "ctv news", "middle east eye", "quotidiano nazionale", "resto del carlino", "huffpost", "milano finanza",
          "interfax", "nation thailand", "khmer times", "modern ghana", "free malaysia today", "ynetnews",
          "il manifesto", "kyodo", "the sentry", "thesentry", "italpress", "agenparl", "unione sarda"],
    "C": ["tass", "ria novosti", "sputnik", "rt ", "xinhua", "global times", "cgtn", "china daily",
          "presstv", "press tv", "tehran times", "irna", "kcna", "anadolu", "telegram ·", "cremlino",
          "dipartimento della difesa usa", "ministero", "kremlin", "vietnam.vn", "ukrinform", "apa.az",
          "herald.co.zw", "al arabiya", "department of war", "сaba", "وكالة سبأ", "wam", "spa "],
}
STOP = set("""
alla alle anche ancora come con contro dalla dalle degli della delle dello dopo dove fino gli hanno nella
nelle negli nuovo nuova oggi ogni oltre perché però più poi prima quando quella quelle questo questa
sono sulla sulle tutti tutto tra uno una dell nell sull dall aveva essere stato stati fatto fare dice
after again against also among amid been before being between both could does during from have here into
more most news over says said than that their them then there these they this those through under until
very what when where which while will with would year years week today about live update updates video
""".split())


# Fonti che non portano notizie utili: sport, borsa, social, aggregatori automatici
RUMORE = re.compile(r"yahoo sports|espn|sports illustrated|tradingview|marketbeat|marketscreener|indexbox|zazoom|"
                    r"facebook|instagram|tiktok|\bfox sports|gazzetta dello sport|corriere dello sport|tuttosport|"
                    r"motley fool|seeking alpha|benzinga|investing\.com", re.I)

def livello_di(nome, predefinito=""):
    if predefinito:
        return predefinito
    n = " " + (nome or "").lower() + " "
    for liv in ("C", "A", "B"):
        if any(k in n for k in LIVELLI_NOMI[liv]):
            return liv
    return "D"


def parole(testo):
    return {w for w in re.findall(r"[a-zà-öø-ÿ0-9]{4,}", testo.lower()) if w not in STOP}


def raggruppa(voci):
    """Unisce le notizie che parlano dello stesso fatto (titoli molto simili, entro 48 ore).
    Restituisce per ogni voce l'indice del suo gruppo."""
    gruppi, indice, esito = [], {}, {}
    for k, v in sorted(voci.items(), key=lambda x: x[1].get("data_iso") or ""):
        p = parole(v["t"])
        quando = v.get("data_iso") or ""
        scelto = None
        if len(p) >= 3:
            conta = {}
            for w in p:
                for g in indice.get(w, ()):
                    conta[g] = conta.get(g, 0) + 1
            for g, comuni in sorted(conta.items(), key=lambda x: -x[1])[:8]:
                if comuni < 3:
                    break
                G = gruppi[g]
                if comuni / len(p | G["p"]) >= 0.3 and abs(_ore(quando) - _ore(G["d"])) <= 48:
                    scelto = g
                    break
        if scelto is None:
            scelto = len(gruppi)
            gruppi.append({"p": p, "d": quando, "fonti": {}})
            for w in p:
                indice.setdefault(w, []).append(scelto)
        gruppi[scelto]["fonti"][v.get("fonte", "")] = v.get("lv", "D")
        esito[k] = scelto
    return gruppi, esito


def _ore(iso):
    try:
        return datetime.fromisoformat(iso).timestamp() / 3600
    except (TypeError, ValueError):
        return 0


def analizza(archivio, recente, auto, cfg, chiavi, dati_cielo, paesi, errori_fonti):
    """Confronta le fonti tra loro: quante confermano ogni notizia, quanto spesso ogni fonte viene
    confermata da altre, quali Stati restano scoperti. Promuove o scarta le fonti trovate da sole."""
    voci = {k: v for k, v in archivio["notizie"].items() if (v.get("data_iso") or "") >= recente}
    for v in voci.values():
        v["lv"] = livello_di(v.get("fonte"), v.get("lv", ""))
    gruppi, esito = raggruppa(voci)
    punti = {}
    for k, v in voci.items():
        fonti = gruppi[esito[k]]["fonti"]
        altre = {f: l for f, l in fonti.items() if f != v.get("fonte")}
        v["nf"] = len(fonti)
        v["conf"] = any(l in ("A", "B") for l in altre.values())
        s = punti.setdefault(v.get("fonte", ""), [0, 0, v["lv"]])
        s[0] += 1
        s[1] += 1 if v["conf"] else 0
    # fonti trovate da sole: promosse o scartate secondo quanto vengono confermate
    promosse, scartate = [], []
    for f in auto.get("scoperte", []):
        s = punti.get(f["nome"])
        if not s:
            continue
        quota = s[1] / s[0]
        if s[0] >= 20 and quota >= 0.3 and not f.get("promossa"):
            f["promossa"] = True
            f["tema"] = "Notizie dal mondo"
            promosse.append(f["nome"])
        elif s[0] >= 40 and quota < 0.05 and not f.get("scartata"):
            f["scartata"] = True
            scartate.append(f["nome"])
    auto["scoperte"] = [f for f in auto.get("scoperte", []) if not f.get("scartata")]
    copertura = {}
    for v in voci.values():
        for p in v.get("paesi", []):
            copertura[p] = copertura.get(p, 0) + 1
    # «dove sta succedendo qualcosa»: Stati con molte più notizie nelle ultime 12 ore del solito,
    # e Stati con più notizie confermate nelle ultime 24 ore
    adesso_ = datetime.now(timezone.utc)
    ore12 = (adesso_ - timedelta(hours=12)).isoformat()
    ore24 = (adesso_ - timedelta(hours=24)).isoformat()
    ultime12, conf24 = {}, {}
    for v in voci.values():
        d = v.get("data_iso") or ""
        for p in v.get("paesi", []):
            if d >= ore12:
                ultime12[p] = ultime12.get(p, 0) + 1
            if d >= ore24 and v.get("conf"):
                conf24[p] = conf24.get(p, 0) + 1
    picchi = []
    primo_visto = min((v.get("visto") or adesso_.isoformat() for v in archivio["notizie"].values()), default=adesso_.isoformat())
    abbastanza = primo_visto <= (adesso_ - timedelta(hours=36)).isoformat()  # serve un giorno e mezzo di raccolta
    for p, n12 in (ultime12.items() if abbastanza else []):
        prima = (copertura.get(p, 0) - n12) / 5  # media per 12 ore nelle 60 ore precedenti
        if n12 >= 6 and n12 >= 2.5 * max(prima, 1):
            picchi.append([p, n12, round(prima, 1)])
    picchi.sort(key=lambda x: -x[1] / max(x[2], 1))
    primo_piano = sorted(conf24.items(), key=lambda x: -x[1])[:10]
    scoperti = sorted(s for s in paesi if not copertura.get(s))
    n = len(voci) or 1
    confermate = sum(1 for v in voci.values() if v["conf"])
    consigli = []
    if not chiavi.get("firms_key"):
        consigli.append("Calore da satellite spento: serve la chiave gratuita NASA FIRMS (LEGGIMI, «Chiavi gratuite»).")
    if dati_cielo and "anonimo" in dati_cielo.get("fonte", ""):
        consigli.append("Cielo con accesso anonimo: con un account OpenSky gratuito le richieste sono 10 volte di più.")
    if not (chiavi.get("repo_git") or cfg.get("repo_git")):
        consigli.append("Sito pubblico e scambio con Claude spenti: bash github.sh (serve un token GitHub).")
    for nome, fila in errori_fonti:
        if fila >= 3:
            consigli.append(f"La fonte «{nome}» non risponde da {fila} giri: da sostituire.")
    if len(scoperti) > 20:
        consigli.append(f"{len(scoperti)} Stati senza notizie negli ultimi giorni: la rotazione per Stato li sta coprendo.")
    classifica = sorted(((f, s[0], round(s[1] / s[0], 2), s[2]) for f, s in punti.items() if s[0] >= 5),
                        key=lambda x: (-x[2], -x[1]))
    return {
        "notizie": len(voci), "confermate": confermate, "quota_confermate": round(confermate / n, 2),
        "per_livello": {l: sum(1 for v in voci.values() if v["lv"] == l) for l in "ABCD"},
        "fonti_migliori": classifica[:12], "fonti_meno_confermate": [x for x in classifica if x[2] < 0.1][-12:],
        "promosse": promosse, "scartate": scartate,
        "stati_scoperti": len(scoperti), "esempi_scoperti": scoperti[:30],
        "picchi": picchi[:12], "primo_piano": [[p, n] for p, n in primo_piano],
        "per_stato": copertura,
        "consigli": consigli,
    }


# ----------------------------------------------------------------------------- segnali, andamento, miglioratore

def segnali_stati(archivio, recente, analisi, dati_cielo, dati_calore):
    """«Segnali da guardare» per Stato: solo fatti osservati, ognuno con le sue fonti. Nessuna previsione."""
    adesso = datetime.now(timezone.utc)
    ore24 = (adesso - timedelta(hours=24)).isoformat()
    per = {}
    voci = [v for v in archivio["notizie"].values() if (v.get("data_iso") or "") >= ore24]
    for v in sorted(voci, key=lambda v: (-(v.get("nf") or 1), v.get("data_iso") or "")):
        for p in v.get("paesi", []):
            d = per.setdefault(p, {"conf": [], "parte": 0, "visti": set()})
            if v.get("conf") and len(d["conf"]) < 3:
                chiave = " ".join(sorted(parole(v["t"]))[:6])
                if chiave not in d["visti"]:
                    d["visti"].add(chiave)
                    d["conf"].append([v.get("it") or v["t"], v.get("fonte", ""), v.get("u", ""), v.get("nf") or 1])
            if v.get("lv") == "C":
                d["parte"] += 1
    picchi = {x[0]: x for x in analisi.get("picchi", [])}
    uscita = {}
    for p in set(per) | set(picchi):
        d = per.get(p, {"conf": [], "parte": 0})
        righe = []
        if p in picchi:
            righe.append(["picco", f"Se ne parla molto più del solito: {picchi[p][1]} notizie in 12 ore, di solito {picchi[p][2]}.", []])
        c = ((dati_cielo or {}).get("paesi") or {}).get(p)
        if c and c[2]:
            righe.append(["cielo", f"Cielo {'vuoto' if c[2] == 'vuoto' else 'in forte calo'}: {c[0]} aerei in volo, di solito {c[1]} a quest'ora. Può essere uno spazio aereo chiuso, ma anche meteo o ricevitori spenti.", []])
        k = ((dati_calore or {}).get("paesi") or {}).get(p)
        if k and k[2]:
            righe.append(["calore", f"Fonti di calore da satellite in forte aumento: {k[0]} in 24 ore, media {k[1]}. Possono essere incendi, industria o attacchi.", []])
        for t, f, u, nf in d["conf"]:
            righe.append(["fatto", t, [[f + (f" e altre {nf - 1}" if nf > 1 else ""), u]]])
        if d["parte"] >= 5:
            righe.append(["voci", f"{d['parte']} dichiarazioni di governi o media statali in 24 ore: sono voci di parte, non conferme.", []])
        if any(r[0] != "voci" for r in righe):
            uscita[p] = righe[:6]
    # solo gli Stati con più segnali, per non appesantire
    return dict(sorted(uscita.items(), key=lambda x: (-sum(1 for r in x[1] if r[0] != "fatto"), -len(x[1])))[:60])


def andamento_stati(archivio):
    """«Dove peggiora»: notizie confermate per Stato e per giorno (storico di 21 giorni);
    confronta gli ultimi 7 giorni con i 7 precedenti (o, con meno storia, gli ultimi 2 con i precedenti)."""
    percorso = os.path.join(DATI, "storico_stati.json")
    storico = leggi_json(percorso, {})
    adesso = datetime.now(timezone.utc)
    conta = {}
    for v in archivio["notizie"].values():
        if v.get("conf"):
            g = (v.get("data_iso") or "")[:10]
            for p in v.get("paesi", []):
                conta.setdefault(p, {})
                conta[p][g] = conta[p].get(g, 0) + 1
    limite = (adesso - timedelta(days=21)).date().isoformat()
    for p, giorni in conta.items():
        s = storico.setdefault(p, {})
        for g, n in giorni.items():
            s[g] = max(s.get(g, 0), n)
    storico = {p: {g: n for g, n in s.items() if g >= limite} for p, s in storico.items()}
    storico = {p: s for p, s in storico.items() if s}
    scrivi_json(percorso, storico)
    giorni_noti = sorted({g for s in storico.values() for g in s})
    if len(giorni_noti) < 6:  # serve quasi una settimana di storia per un confronto onesto
        return {"giorni": len(giorni_noti), "lista": []}
    finestra = 7 if len(giorni_noti) >= 14 else max(2, len(giorni_noti) // 2)
    ora_g, prima_g = giorni_noti[-finestra:], giorni_noti[-2 * finestra:-finestra]
    lista = []
    for p, s in storico.items():
        a = sum(s.get(g, 0) for g in ora_g) / len(ora_g)
        b = sum(s.get(g, 0) for g in prima_g) / max(len(prima_g), 1)
        if a >= 2 and a >= 1.6 * max(b, 0.5):
            lista.append([p, round(a, 1), round(b, 1)])
    lista.sort(key=lambda x: -(x[1] - x[2]))
    return {"giorni": len(giorni_noti), "finestra": finestra, "lista": lista[:15]}


def miglioratore(cfg, chiavi, analisi, auto, errori):
    """Agente miglioratore: a ogni giro misura il sistema, lo confronta con i giri prima, applica da solo
    le correzioni sicure e scrive le richieste per Savino e per Claude (dati/miglioratore.json)."""
    percorso = os.path.join(DATI, "miglioratore.json")
    m = leggi_json(percorso, {"giri": [], "fatte": [], "richieste": []})
    adesso = datetime.now()
    giro = {"quando": adesso.strftime("%d/%m %H:%M"), "notizie": analisi["notizie"], "quota": analisi["quota_confermate"],
            "scoperti": analisi["stati_scoperti"], "errori": len(errori),
            "ab": analisi["per_livello"].get("A", 0) + analisi["per_livello"].get("B", 0)}
    prima = m["giri"][-1] if m["giri"] else None
    m["giri"] = (m["giri"] + [giro])[-60:]
    fatte, richieste = [], []
    imp = leggi_json(os.path.join(DATI, "impostazioni_auto.json"), {})
    # 1. troppi Stati scoperti: allarga la rotazione (fino a 12 per giro); pochi: la restringe
    rot = imp.get("rotazione_stati", cfg.get("rotazione_stati", 6))
    if analisi["stati_scoperti"] > 60 and rot < 12:
        imp["rotazione_stati"] = rot + 2
        fatte.append(f"Stati senza notizie: {analisi['stati_scoperti']}. Rotazione portata da {rot} a {rot + 2} Stati per giro.")
    elif analisi["stati_scoperti"] < 25 and rot > 6:
        imp["rotazione_stati"] = rot - 2
        fatte.append(f"Copertura buona: rotazione riportata da {rot} a {rot - 2} Stati per giro.")
    # 2. Google News rifiuta richieste: rallenta
    if sum(1 for e in errori if "Google News" in e and "429" in e) >= 2:
        imp["pausa_google"] = min(imp.get("pausa_google", 1) + 1, 5)
        fatte.append(f"Google News rifiuta richieste: pausa tra le ricerche portata a {imp['pausa_google']} secondi.")
    # 3. fonti fisse rotte da molti giri: le salta per una settimana
    for f in cfg.get("rss", []):
        st = auto.get("stato", {}).get(f["url"], {})
        if st.get("fila", 0) >= 6 and f["url"] not in imp.get("in_pausa", {}):
            imp.setdefault("in_pausa", {})[f["url"]] = (adesso + timedelta(days=7)).date().isoformat()
            fatte.append(f"«{f['nome']}» non risponde da {st['fila']} giri: messa in pausa per 7 giorni.")
    imp["in_pausa"] = {u: g for u, g in imp.get("in_pausa", {}).items() if g >= adesso.date().isoformat()}
    scrivi_json(os.path.join(DATI, "impostazioni_auto.json"), imp)
    # richieste: cose che il programma non può fare da solo
    if prima and giro["quota"] < prima["quota"] - 0.03:
        richieste.append(f"La quota di notizie confermate è scesa dal {round(100 * prima['quota'])}% al {round(100 * giro['quota'])}%: servono più fonti di livello A o B.")
    if giro["quota"] < 0.15:
        richieste.append(f"Solo il {round(100 * giro['quota'])}% delle notizie è confermato da una seconda fonte seria: aggiungere agenzie e testate (per Claude: curatore).")
    for f in [x for x in analisi.get("fonti_meno_confermate", []) if x[1] >= 15][:3]:
        richieste.append(f"La fonte «{f[0]}» ha {f[1]} notizie e quasi nessuna conferma: valutare se toglierla.")
    for nome, falta in (("firms_key", "chiave gratuita NASA FIRMS (calore da satellite)"), ("opensky_id", "account gratuito OpenSky (cielo più preciso)"),
                        ("anthropic_key", "chiave API di Claude (traduzioni e riassunto)"), ("repo_git", "collegamento GitHub (sito pubblico e aggiornamenti automatici)")):
        if not chiavi.get(nome) and not (nome == "repo_git" and cfg.get("repo_git")):
            richieste.append("Per Savino: manca " + falta + ".")
    if any("Claude" in e for e in errori):
        richieste.append("Per Savino: il cervello non risponde (" + next(e for e in errori if "Claude" in e)[:140] + ").")
    m["fatte"] = (m.get("fatte", []) + [[giro["quando"], x] for x in fatte])[-40:]
    m["richieste"] = richieste[:10]
    scrivi_json(percorso, m)
    tendenza = None
    if len(m["giri"]) >= 4:
        v = m["giri"][-8:]
        tendenza = {"quota": [v[0]["quota"], v[-1]["quota"]], "scoperti": [v[0]["scoperti"], v[-1]["scoperti"]], "giri": len(m["giri"])}
    return {"fatte": m["fatte"][-8:], "richieste": richieste[:10], "tendenza": tendenza}


# ----------------------------------------------------------------------------- cervello (facoltativo, a pagamento)

ANTHROPIC = os.environ.get("CASTELLO_API_URL", "https://api.anthropic.com/v1/messages")
NON_LATINO = re.compile(r"[Ѐ-ӿ֐-ۿ฀-๿぀-ヿ一-鿿가-힯]")


PREZZI = {"haiku": (0.10, 0.50), "sonnet": (2.0, 10.0), "opus": (5.0, 25.0)}  # dollari per milione di token (ingresso, uscita)


def costo_usd(modello, entrata, uscita):
    pi, pu = next((v for k, v in PREZZI.items() if k in modello), PREZZI["sonnet"])
    return (entrata * pi + uscita * pu) / 1e6


def chiedi_claude(chiavi, cfg, testo, massimo=900, conto=None):
    modello = cfg.get("cervello", {}).get("modello", "claude-haiku-5-5")
    corpo = json.dumps({"model": modello, "max_tokens": massimo,
                        "messages": [{"role": "user", "content": testo}]}).encode()
    intest = {"x-api-key": chiavi["anthropic_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"}
    if chiavi.get("anthropic_workspace"):
        # chiavi personali (sk-ant-usr) non legate a un'area di lavoro: serve l'ID dell'area (wrkspc_...)
        intest["anthropic-workspace-id"] = chiavi["anthropic_workspace"]
    try:
        r = json.loads(scarica(ANTHROPIC, timeout=120, corpo=corpo, intestazioni=intest))
    except urllib.error.HTTPError as e:
        # il motivo vero sta nel corpo della risposta (credito finito, limite di spesa, chiave sbagliata...)
        grezzo = ""
        try:
            grezzo = e.read().decode("utf-8", "replace")
            motivo = json.loads(grezzo).get("error", {}).get("message", "")
        except Exception:
            motivo = grezzo[:200]
        aiuto = {400: "richiesta rifiutata: se la chiave è personale (sk-ant-usr) e non è legata a un'area di lavoro, "
                      "crea una chiave scegliendo «Default Workspace», oppure salva l'ID dell'area con: python castello.py chiave anthropic_workspace",
                 401: "chiave non valida: hai incollato l'ID (apikey_...) invece della chiave sk-ant-..., oppure la chiave è stata cancellata",
                 403: "chiave senza permesso", 429: "troppe richieste o credito finito",
                 529: "servizio sovraccarico, riprova"}.get(e.code, "")
        raise RuntimeError(f"HTTP {e.code} – {motivo[:200] or aiuto}" + (f" ({aiuto})" if motivo and aiuto else ""))
    if conto is not None:
        u = r.get("usage", {})
        en, us = int(u.get("input_tokens", 0)), int(u.get("output_tokens", 0))
        d = costo_usd(modello, en, us)
        mese = datetime.now().strftime("%Y-%m")
        if conto.get("mese") != mese:
            conto["mese"], conto["usd_mese"] = mese, 0.0
        conto["usd_oggi"] = round(conto.get("usd_oggi", 0.0) + d, 5)
        conto["usd_mese"] = round(conto.get("usd_mese", 0.0) + d, 5)
        conto["token_oggi"] = conto.get("token_oggi", 0) + en + us
    return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text").strip()


def cervello(chiavi, cfg, archivio, recente, ric, errori):
    """Solo se c'è la chiave API di Claude (si paga a consumo, a parte rispetto all'abbonamento):
    traduce in italiano i titoli in alfabeti non latini e scrive «Da sapere adesso» con le sole
    notizie confermate. Al massimo cervello.max_al_giorno richieste al giorno (predefinito 6)."""
    impost = cfg.get("cervello", {})
    if not chiavi.get("anthropic_key") or not impost.get("attivo", True):
        return None
    percorso = os.path.join(DATI, "cervello.json")
    conto = leggi_json(percorso, {})
    oggi = datetime.now().date().isoformat()
    if conto.get("giorno") != oggi:
        conto = {"giorno": oggi, "chiamate": 0, "brief": conto.get("brief"), "usd_oggi": 0.0, "token_oggi": 0,
                 "mese": conto.get("mese"), "usd_mese": conto.get("usd_mese", 0.0)}
    tetto = impost.get("max_al_giorno", 6)
    # tetti di spesa stimata: oltre, il cervello si ferma da solo fino a domani o al mese dopo
    if conto.get("usd_oggi", 0) >= impost.get("max_usd_giorno", 0.15) or \
            (conto.get("mese") == datetime.now().strftime("%Y-%m") and conto.get("usd_mese", 0) >= impost.get("max_usd_mese", 3.0)):
        tetto = 0
    voci = [(k, v) for k, v in archivio["notizie"].items() if (v.get("data_iso") or "") >= recente]
    # 1. traduzioni
    da_tradurre = [v for _, v in voci if not v.get("it") and NON_LATINO.search(v["t"])][:40]
    if da_tradurre and conto["chiamate"] < tetto:
        domanda = ("Traduci in italiano questi titoli di notizie, uno per riga, nello stesso ordine e con lo "
                   "stesso numero davanti, senza commenti:\n" +
                   "\n".join(f"{i + 1}. {v['t']}" for i, v in enumerate(da_tradurre)))
        try:
            risposta = chiedi_claude(chiavi, cfg, domanda, 1500, conto)
            conto["chiamate"] += 1
            for riga in risposta.splitlines():
                m = re.match(r"\s*(\d+)[.)]\s*(.+)", riga)
                if m and 0 < int(m.group(1)) <= len(da_tradurre):
                    v = da_tradurre[int(m.group(1)) - 1]
                    v["it"] = pulisci(m.group(2), 300)
                    for p in ric.trova(v["it"]):
                        if p not in v["paesi"]:
                            v["paesi"].append(p)
        except Exception as e:
            errori.append(f"Claude (traduzioni): {re.sub(r'sk-ant-[A-Za-z0-9_-]+', '***', str(e))}")
    # 2. «Da sapere adesso», al massimo ogni 6 ore
    vecchio = (conto.get("brief") or {}).get("iso", "")
    if conto["chiamate"] < tetto and vecchio < (datetime.now(timezone.utc) - timedelta(hours=impost.get("brief_ore", 6))).isoformat():
        conf = sorted((v for _, v in voci if v.get("conf")), key=lambda v: v.get("data_iso") or "", reverse=True)[:60]
        if len(conf) >= 5:
            domanda = ("Sei un analista neutrale di difesa e geopolitica. Usa SOLO le notizie qui sotto (titolo – fonte), "
                       "già confermate da più fonti. Scrivi in italiano da 5 a 7 punti «Da sapere adesso», uno per riga, "
                       "che iniziano con «- ». Ogni punto: una o due frasi di fatti, senza giudizi né previsioni, con tra "
                       "parentesi le fonti. Non aggiungere nulla che non sia nei titoli. Niente dettagli operativi militari.\n\n" +
                       "\n".join(f"- {v.get('it') or v['t']} – {v.get('fonte', '')}" for v in conf))
            try:
                testo = chiedi_claude(chiavi, cfg, domanda, 900, conto)
                conto["chiamate"] += 1
                conto["brief"] = {"iso": datetime.now(timezone.utc).isoformat(),
                                  "agg": datetime.now().strftime("%d/%m %H:%M"), "testo": testo[:4000]}
            except Exception as e:
                errori.append(f"Claude (riassunto): {re.sub(r'sk-ant-[A-Za-z0-9_-]+', '***', str(e))}")
    scrivi_json(percorso, conto)
    b = conto.get("brief")
    return {"agg": b["agg"], "testo": b["testo"]} if b else None

# ----------------------------------------------------------------------------- raccolta

def elenco_fonti(cfg, mie, auto):
    fonti = []
    for f in cfg.get("rss", []):
        fonti.append(dict(f, tipo="fissa"))
    for f in cfg.get("candidati", []):
        fonti.append(dict(f, tipo="candidata"))
    for f in auto.get("scoperte", []):
        fonti.append(dict(f, tipo="scoperta", filtra=True))
    for f in mie.get("rss", []):
        fonti.append(dict(f, tipo="mia"))
    return fonti


def da_saltare(f, st, adesso):
    """Le candidate mai riuscite (3 tentativi) e le fonti che falliscono 8 volte di fila
    si riprovano solo dopo una settimana."""
    if f["tipo"] in ("fissa", "mia") or not st:
        return False
    rotta = (st.get("ok", 0) == 0 and st.get("fila", 0) >= 3) or st.get("fila", 0) >= 8
    if not rotta:
        return False
    return st.get("ultimo", "") >= (adesso - timedelta(days=7)).isoformat()


def aggiorna():
    """Il cuore: un solo giro alla volta. Se cron e avvia.sh partono insieme, il secondo aspetta il prossimo turno:
    così due giri non scrivono mai gli stessi file nello stesso momento."""
    os.makedirs(DATI, exist_ok=True)
    blocco = os.path.join(DATI, "aggiorna.lock")
    try:
        if time.time() - os.path.getmtime(blocco) < 45 * 60:
            print("Un aggiornamento è già in corso: questo giro si ferma qui (riprova tra qualche minuto).")
            return
    except OSError:
        pass
    with open(blocco, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    try:
        _aggiorna()
    finally:
        try:
            os.remove(blocco)
        except OSError:
            pass


def _aggiorna():
    os.makedirs(DATI, exist_ok=True)
    os.makedirs(WEB, exist_ok=True)
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    mie = leggi_json(os.path.join(DATI, "fonti_mie.json"), {})
    chiavi = leggi_json(os.path.join(DATI, "chiavi.json"), {})
    auto = leggi_json(os.path.join(DATI, "fonti_auto.json"), {})
    auto.setdefault("scoperte", [])
    auto.setdefault("stato", {})
    auto.setdefault("domini_provati", {})
    paesi = leggi_json(os.path.join(QUI, "paesi.json"), {})
    it2en = leggi_json(os.path.join(QUI, "mappa.json"), {})
    ric = Riconoscitore(paesi)
    archivio = leggi_json(os.path.join(DATI, "archivio.json"), None)
    if not isinstance(archivio, dict) or "notizie" not in archivio:
        archivio = leggi_json(os.path.join(DATI, "archivio.copia.json"), {"notizie": {}, "video": {}})  # file rovinato: riparte dalla copia
    elif len(archivio["notizie"]) > 50:
        try:
            shutil.copyfile(os.path.join(DATI, "archivio.json"), os.path.join(DATI, "archivio.copia.json"))
        except OSError:
            pass
    archivio.setdefault("video", {})
    canali = leggi_json(os.path.join(DATI, "canali.json"), {})
    errori, contati, citati = [], 0, {}
    adesso = datetime.now(timezone.utc)

    def aggiungi(tipo, voce):
        nonlocal contati
        if not voce["u"] or not voce["t"]:
            return
        chiave = hashlib.sha1((voce["u"] + voce["t"]).encode("utf-8")).hexdigest()[:16]
        if chiave not in archivio[tipo]:
            voce["visto"] = adesso.isoformat()
            archivio[tipo][chiave] = voce
            contati += 1

    def notizia(tema, titolo, link, data, fonte, sito="", filtra=False, livello="", lv="", forza=None):
        if RUMORE.search(" " + (fonte or "") + " "):
            return
        if filtra and not FILTRO.search(titolo):
            return
        if sito:
            d = dominio(sito)
            if d:
                citati[d] = citati.get(d, 0) + 1
        trovati = ric.trova(titolo)
        if forza and forza not in trovati:
            trovati = [forza] + trovati[:4]
        v = {"t": titolo, "u": solo_http(link), "data_iso": data or adesso.isoformat(), "fonte": fonte,
             "tema": tema, "paesi": trovati, "lv": livello_di(fonte, lv)}
        if livello:
            v["liv"] = livello
        aggiungi("notizie", v)

    # 1. Google News e GDELT: ricerche per tema
    for tema in cfg.get("temi", []):
        for lingua in ("it", "en"):
            q = tema.get(lingua)
            if not q:
                continue
            try:
                for v in google_news(q, lingua):
                    notizia(tema["nome"], *v)
            except Exception as e:  # una fonte che non risponde non ferma le altre
                errori.append(f"Google News ({tema['nome']}, {lingua}): {e}")
            time.sleep(1)
    # GDELT accetta poche richieste: al massimo una volta ogni 6 ore, con 12 secondi tra una e l'altra
    stato_gdelt = leggi_json(os.path.join(DATI, "gdelt.json"), {})
    if stato_gdelt.get("ultimo", "") < (adesso - timedelta(hours=cfg.get("gdelt_ore", 6))).isoformat():
        for g in cfg.get("gdelt", []):
            try:
                for v in gdelt(g["query"]):
                    notizia(g["tema"], *v)
            except Exception as e:
                errori.append(f"GDELT ({g['tema']}): {e}")
                if "429" in str(e):  # ci sta rifiutando: basta per questo giro, si riprova tra 24 ore
                    stato_gdelt["pausa"] = (adesso + timedelta(hours=24)).isoformat()
                    break
            time.sleep(12)
        scrivi_json(os.path.join(DATI, "gdelt.json"), {"ultimo": stato_gdelt.get("pausa") and
                    (adesso + timedelta(hours=18)).isoformat() or adesso.isoformat()})

    # 1b. Rotazione per Stato: a ogni giro cerca notizie sugli Stati meno coperti
    imp_auto = leggi_json(os.path.join(DATI, "impostazioni_auto.json"), {})
    rot = imp_auto.get("rotazione_stati", cfg.get("rotazione_stati", 6))
    if rot:
        cop = leggi_json(os.path.join(DATI, "copertura.json"), {})
        ultimi = (adesso - timedelta(hours=72)).isoformat()
        quanti = {}
        for v in archivio["notizie"].values():
            if (v.get("data_iso") or "") >= ultimi:
                for p in v.get("paesi", []):
                    quanti[p] = quanti.get(p, 0) + 1
        attesa = (adesso - timedelta(hours=20)).isoformat()
        ordine = sorted(paesi, key=lambda s_: (quanti.get(s_, 0), cop.get(s_, "")))
        for stato_ in [x for x in ordine if cop.get(x, "") < attesa][:rot]:
            nomi = paesi[stato_]
            en = next((n for n in nomi[1:] if "." not in n and len(n) > 3), nomi[0])
            for lingua, q in (("it", f'"{nomi[0]}" (difesa OR esercito OR governo OR sicurezza)'),
                              ("en", f'"{en}" (military OR defense OR government OR security)')):
                try:
                    for t_, l_, d_, f_, s_ in google_news(q, lingua):
                        notizia("Copertura degli Stati", t_, l_, d_, f_, s_, forza=stato_)
                except Exception as e:
                    errori.append(f"Google News ({stato_}, {lingua}): {e}")
                time.sleep(imp_auto.get("pausa_google", 1))
            cop[stato_] = adesso.isoformat()
        scrivi_json(os.path.join(DATI, "copertura.json"), cop)

    # 2. Feed RSS: fissi, candidati, scoperti da soli, aggiunti a mano
    for f in elenco_fonti(cfg, mie, auto):
        st = auto["stato"].get(f["url"], {})
        if da_saltare(f, st, adesso) or leggi_json(os.path.join(DATI, "impostazioni_auto.json"), {}).get("in_pausa", {}).get(f["url"]):
            continue
        st["ultimo"] = adesso.isoformat()
        try:
            voci = leggi_rss(scarica(f["url"]))
            if not voci:
                raise ValueError("feed vuoto")
            for titolo, link, data, fonte, _ in voci:
                notizia(f.get("tema", "Notizie dal mondo"), titolo, link, data, f.get("nome") or fonte,
                        filtra=f.get("filtra", False),
                        livello="da valutare" if f["tipo"] == "scoperta" and not f.get("promossa") else f.get("liv", ""),
                        lv=("B" if f.get("promossa") else "D") if f["tipo"] == "scoperta" else f.get("lv", ""))
            st["ok"], st["fila"] = st.get("ok", 0) + 1, 0
        except Exception as e:
            st["fila"] = st.get("fila", 0) + 1
            if f["tipo"] in ("fissa", "mia") or st.get("ok", 0):
                errori.append(f"{f.get('nome', f['url'])}: {e}")
        auto["stato"][f["url"]] = st

    # 3. Telegram: canali pubblici ufficiali (dichiarazioni di parte, non conferme)
    tg_citati = {}
    auto.setdefault("telegram", [])
    for c in cfg.get("telegram", []) + mie.get("telegram", []):
        try:
            for t, link, data in telegram(c["canale"], tg_citati):
                notizia(c.get("tema", "Voci ufficiali (Telegram)"), t, link, data, "Telegram · " + c.get("chi", c["canale"]),
                        livello="di parte", lv="C")
        except Exception as e:
            errori.append(f"Telegram {c['canale']}: {e}")
        time.sleep(1)
    # 3b. Canali Telegram trovati da soli: quelli citati o inoltrati da almeno 2 canali già seguiti.
    # Entrano come «da valutare» (livello D) e solo con i messaggi che parlano di difesa e geopolitica.
    tg = cfg.get("scoperta_telegram", {})
    if tg.get("attiva", True):
        noti = {c["canale"].lower() for c in cfg.get("telegram", []) + mie.get("telegram", []) + auto["telegram"]}
        provati = auto.setdefault("telegram_provati", {})
        nuovi_tg = 0
        for nome, da in sorted(tg_citati.items(), key=lambda x: -len(x[1])):
            if nuovi_tg >= tg.get("per_giro", 2) or len(auto["telegram"]) >= tg.get("max_canali", 30) or len(da) < tg.get("min_canali", 2):
                break
            if nome.lower() in noti or nome in provati:
                continue
            provati[nome] = adesso.isoformat()
            try:
                if len(telegram(nome)) >= 5:
                    auto["telegram"].append({"canale": nome, "chi": nome + " (trovato da solo, citato da " + ", ".join(sorted(da)[:3]) + ")",
                                             "aggiunta": adesso.date().isoformat()})
                    nuovi_tg += 1
            except Exception:
                pass
            time.sleep(1)
        for c in auto["telegram"]:
            try:
                for t, link, data in telegram(c["canale"])[-12:]:
                    if FILTRO.search(t) or NON_LATINO.search(t):
                        notizia("Telegram: canali trovati da soli (da valutare)", t, link, data, "Telegram · " + c["chi"],
                                livello="da valutare", lv="D")
            except Exception as e:
                errori.append(f"Telegram {c['canale']}: {e}")
            time.sleep(1)

    # 4. YouTube: feed dei canali, senza chiave
    for h in cfg.get("youtube", []) + mie.get("youtube", []):
        try:
            cid = h if h.startswith("UC") else id_canale(h, canali)
            for titolo, link, data, autore, _ in leggi_rss(scarica("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid)):
                aggiungi("video", {"t": titolo, "u": solo_http(link), "data_iso": data or adesso.isoformat(),
                                   "canale": autore or h, "paesi": ric.trova(titolo)})
        except Exception as e:
            errori.append(f"YouTube {h}: {e}")

    # 5. Cielo: traffico aereo civile per Stato
    dati_cielo = cielo(chiavi, it2en, errori) if cfg.get("cielo", True) else None
    dati_calore = calore(chiavi, it2en, errori, cfg.get("calore_ore", 24))

    # 6. Si amplia da solo: prova i siti più citati che non sono ancora tra le fonti
    sc = cfg.get("scoperta", {})
    nuove = []
    if sc.get("attiva", True) and len(auto["scoperte"]) < sc.get("max_fonti", 80):
        noti = {dominio(f["url"]) for f in elenco_fonti(cfg, mie, auto)}
        rinnovo = (adesso - timedelta(days=30)).isoformat()
        prove = 0
        for d, n in sorted(citati.items(), key=lambda x: -x[1]):
            if prove >= sc.get("per_giro", 3) or n < sc.get("min_citazioni", 3):
                break
            if not d or d in noti or d in ESCLUSI or auto["domini_provati"].get(d, "") >= rinnovo:
                continue
            prove += 1
            auto["domini_provati"][d] = adesso.isoformat()
            u = trova_feed(d)
            if u:
                f = {"nome": d, "url": u, "tema": "Scoperte automatiche (da valutare)", "aggiunta": adesso.date().isoformat()}
                auto["scoperte"].append(f)
                nuove.append(f)
    scrivi_json(os.path.join(DATI, "fonti_auto.json"), auto)

    # 7. Archivio e uscita per il Castello
    limite = (adesso - timedelta(days=cfg.get("giorni_archivio", 7))).isoformat()
    for tipo in ("notizie", "video"):
        archivio[tipo] = {k: v for k, v in archivio[tipo].items() if (v.get("data_iso") or "") >= limite}
    scrivi_json(os.path.join(DATI, "archivio.json"), archivio)
    scrivi_json(os.path.join(DATI, "canali.json"), canali)
    recente = (adesso - timedelta(hours=cfg.get("ore_live", 72))).isoformat()
    rotte_ = [(f.get("nome", f["url"]), auto["stato"].get(f["url"], {}).get("fila", 0))
              for f in elenco_fonti(cfg, mie, auto) if f["tipo"] in ("fissa", "mia")]
    analisi = analizza(archivio, recente, auto, cfg, chiavi, dati_cielo, paesi, rotte_)
    scrivi_json(os.path.join(DATI, "fonti_auto.json"), auto)
    brief = cervello(chiavi, cfg, archivio, recente, ric, errori)
    if brief is not None or chiavi.get("anthropic_key"):
        scrivi_json(os.path.join(DATI, "archivio.json"), archivio)  # con le traduzioni
    analisi["segnali"] = segnali_stati(archivio, recente, analisi, dati_cielo, dati_calore)
    analisi["peggiora"] = andamento_stati(archivio)
    analisi["miglioratore"] = miglioratore(cfg, chiavi, analisi, auto, errori)
    scrivi_json(os.path.join(DATI, "analisi.json"), analisi)

    def elenco(tipo, massimo):
        voci = [v for v in archivio[tipo].values() if (v.get("data_iso") or "") >= recente]
        voci.sort(key=lambda v: v.get("data_iso") or "", reverse=True)
        uscita = []
        for v in voci[:massimo]:
            w = dict(v)
            w["data"] = mostra_data(w.pop("data_iso", None))
            w.pop("visto", None)
            uscita.append(w)
        return uscita

    tutte = elenco_fonti(cfg, mie, auto)
    attive = [f for f in tutte if auto["stato"].get(f["url"], {}).get("ok")]
    live = {
        "versione": VERSIONE,
        "agg": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "notizie": elenco("notizie", cfg.get("max_notizie", 1500)),
        "video": elenco("video", cfg.get("max_video", 200)),
        "cielo": dati_cielo,
        "calore": {k: v for k, v in dati_calore.items() if k != "iso"} if dati_calore else None,
        "fonti": {"rss_attive": len(attive), "rss_totali": len(tutte),
                  "telegram": len(cfg.get("telegram", []) + mie.get("telegram", [])),
                  "youtube": len(cfg.get("youtube", []) + mie.get("youtube", [])),
                  "scoperte": [{"nome": f["nome"], "url": f["url"], "aggiunta": f.get("aggiunta", "")}
                               for f in auto["scoperte"]][-40:]},
        "analisi": analisi,
        "brief": brief,
        "errori": errori,
    }
    with open(os.path.join(WEB, "live.js.tmp"), "w", encoding="utf-8") as f:
        f.write("window.LIVE = " + json.dumps(live, ensure_ascii=False) + ";\n")
    os.replace(os.path.join(WEB, "live.js.tmp"), os.path.join(WEB, "live.js"))
    scrivi_json(os.path.join(DATI, "live.json"), live)
    segnali = [p for p, v in (dati_cielo or {}).get("paesi", {}).items() if v[2]]
    print(f"[{live['agg']}] nuove voci: {contati} · notizie live: {len(live['notizie'])} · video: {len(live['video'])} · "
          f"fonti RSS attive: {len(attive)}/{len(tutte)} · nuove fonti scoperte: {len(nuove)} · "
          f"cielo: {'non disponibile' if not dati_cielo else str(dati_cielo['in_volo']) + ' aerei in volo'}"
          + (f" · cieli che si svuotano: {', '.join(segnali)}" if segnali else "") + f" · avvisi: {len(errori)}")
    print(f"Analisi: {analisi['confermate']} notizie su {analisi['notizie']} confermate da un'altra fonte affidabile · "
          f"Stati senza notizie: {analisi['stati_scoperti']}" + (f" · fonti promosse: {', '.join(analisi['promosse'])}" if analisi['promosse'] else "")
          + (f" · fonti scartate: {', '.join(analisi['scartate'])}" if analisi['scartate'] else ""))
    for c_ in analisi["consigli"]:
        print("  consiglio:", c_)
    for q_, x_ in analisi["miglioratore"]["fatte"][-3:]:
        print("  miglioratore ha fatto:", x_)
    for x_ in analisi["miglioratore"]["richieste"]:
        print("  miglioratore chiede:", x_)
    for e in errori:
        print("  -", e)
    avvisa(cfg, segnali, dati_calore)
    avvisa_bot(chiavi, live, segnali)
    if cfg.get("repo_git") or chiavi.get("repo_git"):
        sincronizza(cfg, chiavi)


def avvisa(cfg, segnali, dati_calore):
    """Notifica sul telefono (app Termux:API) quando un cielo si svuota o il calore sale."""
    if not cfg.get("notifiche", True) or not shutil.which("termux-notification"):
        return
    caldi = [p for p, v in (dati_calore or {}).get("paesi", {}).items() if v[2]]
    righe = []
    if segnali:
        righe.append("Cieli che si svuotano: " + ", ".join(segnali[:8]))
    if caldi:
        righe.append("Calore in forte aumento: " + ", ".join(caldi[:8]))
    if not righe:
        return
    gia = os.path.join(DATI, "ultimo_avviso.txt")
    testo = " · ".join(righe)
    try:
        if open(gia, encoding="utf-8").read() == testo:
            return  # stesso avviso di prima: non ripeterlo
    except OSError:
        pass
    subprocess.run(["termux-notification", "--id", "castello", "--title", "PanGeo",
                    "--content", testo, "--action", "termux-open-url http://127.0.0.1:8080/#live"], check=False)
    with open(gia, "w", encoding="utf-8") as f:
        f.write(testo)


def bot_telegram(chiavi, testo):
    """Manda un messaggio a Savino dal suo bot Telegram (chiavi telegram_bot e telegram_chat).
    Il bot lo crea lui con @BotFather; il programma scrive solo a quella chat."""
    if not chiavi.get("telegram_bot") or not chiavi.get("telegram_chat"):
        return False
    corpo = urllib.parse.urlencode({"chat_id": chiavi["telegram_chat"], "text": testo[:3900],
                                    "disable_web_page_preview": "true"}).encode()
    try:
        scarica(f"https://api.telegram.org/bot{chiavi['telegram_bot']}/sendMessage", timeout=30, corpo=corpo)
        return True
    except Exception as e:
        print("  - bot Telegram:", re.sub(r"bot[0-9]+:[A-Za-z0-9_-]+", "bot***", str(e)))
        return False


def bot_chat(chiavi):
    """Trova il numero della chat: Savino scrive «ciao» al suo bot, poi lancia `python castello.py bot`."""
    if not chiavi.get("telegram_bot"):
        print("Prima salva il token del bot: python castello.py chiave telegram_bot")
        return
    try:
        r = json.loads(scarica(f"https://api.telegram.org/bot{chiavi['telegram_bot']}/getUpdates", timeout=30))
    except Exception as e:
        print("Il bot non risponde:", re.sub(r"bot[0-9]+:[A-Za-z0-9_-]+", "bot***", str(e)))
        return
    chat = [u["message"]["chat"]["id"] for u in r.get("result", []) if u.get("message")]
    if not chat:
        print("Nessun messaggio trovato: apri il tuo bot in Telegram, scrivigli «ciao» e rilancia questo comando.")
        return
    cmd_chiave("telegram_chat", str(chat[-1]))
    chiavi["telegram_chat"] = str(chat[-1])
    print("Chat collegata." if bot_telegram(chiavi, "PanGeo è collegato: qui arriveranno «Da sapere adesso» e gli avvisi.") else "Chat salvata, ma il messaggio di prova non è partito.")


def avvisa_bot(chiavi, live, segnali):
    """Sul bot Telegram: il riassunto quando è nuovo, i picchi e i cieli che si svuotano."""
    if not chiavi.get("telegram_bot") or not chiavi.get("telegram_chat"):
        return
    gia = leggi_json(os.path.join(DATI, "bot.json"), {})
    parti = []
    b = live.get("brief") or {}
    if b.get("testo") and b.get("agg") != gia.get("brief"):
        parti.append("PanGeo – da sapere adesso (" + b.get("agg", "") + ")\n" + b["testo"])
        gia["brief"] = b.get("agg")
    an = live.get("analisi") or {}
    picchi = ", ".join(f"{x[0]} ({x[1]})" for x in (an.get("picchi") or [])[:6])
    riga = " · ".join(x for x in [("Picchi di notizie: " + picchi) if picchi else "",
                                  ("Cieli che si svuotano: " + ", ".join(segnali[:6])) if segnali else ""] if x)
    if riga and riga != gia.get("riga"):
        parti.append(riga)
        gia["riga"] = riga
    if parti and bot_telegram(chiavi, "\n\n".join(parti)):
        scrivi_json(os.path.join(DATI, "bot.json"), gia)


# ----------------------------------------------------------------------------- istantanea nel Castello

ANCORA = "const $ = s => document.querySelector(s);"
SNAP_INIZIO = "// Istantanea live (programma Castello) - inizio"
SNAP_FINE = "// Istantanea live (programma Castello) - fine"


def istantanea(percorso, origine="programma Castello", file_brief=None):
    """Mette nel file del Castello una copia ridotta dei dati live, con lo storico del cielo e del
    calore: così anche la versione su claude.ai mostra «Live dal mondo» e i confronti continuano."""
    live = leggi_json(os.path.join(DATI, "live.json"), None)
    if not live:
        print("Nessun dato: lancia prima  python castello.py aggiorna")
        return
    snap = dict(live)
    snap["notizie"] = live.get("notizie", [])[:250]
    snap["video"] = live.get("video", [])[:20]
    snap["origine"] = origine
    if snap.get("analisi"):
        snap["analisi"] = {k: v for k, v in snap["analisi"].items() if k != "per_stato"}  # più leggero
    if file_brief and os.path.exists(file_brief):
        with open(file_brief, encoding="utf-8") as f:
            snap["brief"] = {"agg": datetime.now().strftime("%d/%m %H:%M"), "testo": f.read().strip()[:4000]}

    def compatta(nome):
        st = leggi_json(os.path.join(DATI, nome), {})
        return {k: [[t[:16], c] for t, c in v] for k, v in st.items() if any(c for _, c in v)}

    snap["storico"] = {"cielo": compatta("cielo_storico.json"), "calore": compatta("calore_storico.json")}
    snap["storico"]["stati"] = leggi_json(os.path.join(DATI, "storico_stati.json"), {})
    snap["storico"]["miglioratore"] = leggi_json(os.path.join(DATI, "miglioratore.json"), {})
    dati = json.dumps(snap, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    blocco = (SNAP_INIZIO + "\nconst LIVE_SNAP = " + dati + ";\n"
              "if (typeof window !== 'undefined' && !window.LIVE) window.LIVE = LIVE_SNAP;\n" + SNAP_FINE + "\n")
    with open(percorso, encoding="utf-8") as f:
        pagina = f.read()
    if SNAP_INIZIO in pagina:
        a = pagina.index(SNAP_INIZIO)
        b = pagina.index(SNAP_FINE, a) + len(SNAP_FINE) + 1
        pagina = pagina[:a] + blocco + pagina[b:]
    elif pagina.count(ANCORA) == 1:
        pagina = pagina.replace(ANCORA, blocco + ANCORA)
    else:
        print("Punto di inserimento non trovato nel file.")
        return
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(pagina)
    print(f"Istantanea messa nel Castello: {len(snap['notizie'])} notizie, {len(snap['video'])} video, "
          f"cielo {'sì' if snap.get('cielo') else 'no'} ({len(dati) // 1024} KB).")


def ripristina(percorso):
    """Riprende dal file del Castello lo storico del cielo e del calore (per chi lavora senza
    cartella dati permanente, come le sessioni notturne di Claude)."""
    os.makedirs(DATI, exist_ok=True)
    with open(percorso, encoding="utf-8") as f:
        pagina = f.read()
    i = pagina.find("const LIVE_SNAP = ")
    if i < 0:
        print("Nessuna istantanea nel file: si parte da zero.")
        return
    snap, _ = json.JSONDecoder().raw_decode(pagina, i + len("const LIVE_SNAP = "))
    st = snap.get("storico", {})
    for chiave, nome in (("cielo", "cielo_storico.json"), ("calore", "calore_storico.json")):
        attuale = leggi_json(os.path.join(DATI, nome), {})
        for paese, serie in st.get(chiave, {}).items():
            visti = {t[:16] for t, _ in attuale.get(paese, [])}
            attuale[paese] = sorted(attuale.get(paese, []) + [[t + ":00+00:00", c] for t, c in serie
                                                               if t[:16] not in visti])
        scrivi_json(os.path.join(DATI, nome), attuale)
    vecchi = leggi_json(os.path.join(DATI, "storico_stati.json"), {})
    for paese, giorni in (st.get("stati") or {}).items():
        d = vecchi.setdefault(paese, {})
        for g, n in giorni.items():
            d[g] = max(d.get(g, 0), n)
    scrivi_json(os.path.join(DATI, "storico_stati.json"), vecchi)
    if st.get("miglioratore") and not os.path.exists(os.path.join(DATI, "miglioratore.json")):
        scrivi_json(os.path.join(DATI, "miglioratore.json"), st["miglioratore"])
    print("Storico del cielo e del calore ripreso dal Castello.")


# ----------------------------------------------------------------------------- comandi

def sincronizza(cfg=None, chiavi=None):
    """Facoltativo: scambia file con un repository Git (es. GitHub).
    Scarica l'ultima versione del Castello pubblicata lì e carica i dati live."""
    cfg = cfg or leggi_json(os.path.join(QUI, "config.json"), {})
    chiavi = chiavi or leggi_json(os.path.join(DATI, "chiavi.json"), {})
    repo = chiavi.get("repo_git") or cfg.get("repo_git")
    if not repo:
        print("Nessun repository: python castello.py chiave repo_git https://github.com/NOME/castello.git")
        return
    cartella = os.path.join(DATI, "repo")
    try:
        if not os.path.isdir(os.path.join(cartella, ".git")):
            subprocess.run(["git", "clone", "--depth", "1", repo, cartella], check=True)
        else:
            subprocess.run(["git", "-C", cartella, "pull", "--ff-only"], check=True)
        # nuove versioni del programma, se Claude le ha messe nel repository (cartella programma/)
        cambiati = []
        for nome in ("castello.py", "config.json", "paesi.json", "mappa.json", "LEGGIMI.txt"):
            src = os.path.join(cartella, "programma", nome)
            dst = os.path.join(QUI, nome)
            if os.path.exists(src) and (not os.path.exists(dst) or open(src, "rb").read() != open(dst, "rb").read()):
                try:  # controllo di salute: un file rotto non sostituisce mai quello che funziona
                    if nome.endswith(".py"):
                        compile(open(src, encoding="utf-8").read(), nome, "exec")
                    elif nome.endswith(".json"):
                        json.load(open(src, encoding="utf-8"))
                except (SyntaxError, ValueError) as e:
                    print(f"Scartato {nome} arrivato da GitHub: non è valido ({str(e)[:80]}). Resta la versione di prima.")
                    continue
                if nome.endswith(".py") and cfg.get("codice_nuovo", "chiedi") == "chiedi":
                    # l'umano resta l'interruttore: il codice nuovo aspetta il tuo sì
                    os.makedirs(os.path.join(DATI, "in_attesa"), exist_ok=True)
                    shutil.copyfile(src, os.path.join(DATI, "in_attesa", nome))
                    print("C'è una versione nuova del programma: NON è stata installata. Per accettarla:  python castello.py approva")
                    continue
                if os.path.exists(dst):
                    os.makedirs(os.path.join(DATI, "copie"), exist_ok=True)
                    shutil.copyfile(dst, os.path.join(DATI, "copie", nome + ".prima"))
                shutil.copyfile(src, dst)
                cambiati.append(nome)
        if cambiati:
            print("Programma aggiornato da GitHub:", ", ".join(cambiati))
        nuova = os.path.join(cartella, "index.html")
        if os.path.exists(nuova):
            # le nuove versioni del Castello arrivano dal repository (le pubblica Claude)
            shutil.copyfile(nuova, os.path.join(WEB, "index.html"))
        else:
            # repository nuovo: ci mette il Castello del telefono, così il sito pubblico parte subito
            shutil.copyfile(os.path.join(WEB, "index.html"), nuova)
            subprocess.run(["git", "-C", cartella, "add", "index.html"], check=True)
        # file dell'app (icona, installazione, funzionamento senza rete): li aggiunge se mancano
        for nome in APP_FILE:
            dest = os.path.join(cartella, nome)
            if not os.path.exists(dest) and os.path.exists(os.path.join(WEB, nome)):
                shutil.copyfile(os.path.join(WEB, nome), dest)
                subprocess.run(["git", "-C", cartella, "add", nome], check=True)
        # tabelle aperte (CSV e JSON con date e fonti): sul sito pubblico si leggono senza account
        if os.path.exists(os.path.join(WEB, "tabelle.html")):
            shutil.copyfile(os.path.join(WEB, "tabelle.html"), os.path.join(cartella, "tabelle.html"))
            shutil.copytree(os.path.join(WEB, "tabelle"), os.path.join(cartella, "tabelle"), dirs_exist_ok=True)
            subprocess.run(["git", "-C", cartella, "add", "tabelle.html", "tabelle"], check=True)
        for nome in ("live.json", "live.js"):
            sorgente = os.path.join(DATI if nome.endswith(".json") else WEB, nome)
            if os.path.exists(sorgente):
                shutil.copyfile(sorgente, os.path.join(cartella, nome))
                subprocess.run(["git", "-C", cartella, "add", nome], check=True)
        if subprocess.run(["git", "-C", cartella, "diff", "--cached", "--quiet"]).returncode != 0:
            subprocess.run(["git", "-C", cartella, "-c", "user.name=Castello", "-c", "user.email=castello@localhost",
                            "commit", "-m", "Dati live dal telefono"], check=True)
            subprocess.run(["git", "-C", cartella, "push"], check=True)
        print("Sincronizzazione fatta.")
    except (OSError, subprocess.CalledProcessError) as e:
        # mai mostrare il token contenuto nell'indirizzo del repository
        print("Sincronizzazione non riuscita:", re.sub(r"//[^@/\s]+@", "//***@", str(e)))


def aggiungi_mia(tipo, voce, chiave):
    os.makedirs(DATI, exist_ok=True)
    percorso = os.path.join(DATI, "fonti_mie.json")
    mie = leggi_json(percorso, {})
    lista = mie.setdefault(tipo, [])
    if any((x.get(chiave) if isinstance(x, dict) else x) == (voce.get(chiave) if isinstance(voce, dict) else voce)
           for x in lista):
        print("Già presente.")
        return
    lista.append(voce)
    scrivi_json(percorso, mie)
    print("Aggiunta. Entra nel prossimo aggiornamento.")


def cmd_fonte(url, tema):
    try:
        n = len(leggi_rss(scarica(url)))
        print(f"Feed valido: {n} voci.")
    except Exception as e:
        print(f"Attenzione, il feed ora non risponde ({e}): lo aggiungo lo stesso.")
    aggiungi_mia("rss", {"nome": dominio(url), "url": url, "tema": tema or "Notizie dal mondo", "filtra": True}, "url")


def cmd_chiave(nome, valore):
    os.makedirs(DATI, exist_ok=True)
    percorso = os.path.join(DATI, "chiavi.json")
    chiavi = leggi_json(percorso, {})
    chiavi[nome] = valore
    scrivi_json(percorso, chiavi)
    try:
        os.chmod(percorso, 0o600)
    except OSError:
        pass
    print(f"Chiave «{nome}» salvata solo su questo telefono, in dati/chiavi.json.")


def cmd_fonti():
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    mie = leggi_json(os.path.join(DATI, "fonti_mie.json"), {})
    auto = leggi_json(os.path.join(DATI, "fonti_auto.json"), {})
    stato = auto.get("stato", {})
    for f in elenco_fonti(cfg, mie, auto):
        st = stato.get(f["url"], {})
        esito = "mai provata" if not st else ("ok" if st.get("fila", 0) == 0 and st.get("ok") else
                                              f"non risponde da {st.get('fila', 0)} giri")
        print(f"[{f['tipo']}] {f.get('nome', '')}: {esito}")
    print("Telegram:", ", ".join(c["canale"] for c in cfg.get("telegram", []) + mie.get("telegram", [])))
    print("Telegram trovati da soli:", ", ".join(c["canale"] for c in auto.get("telegram", [])) or "nessuno per ora")
    print("YouTube:", ", ".join(cfg.get("youtube", []) + mie.get("youtube", [])))


class Gestore(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map,
                          **{".webmanifest": "application/manifest+json", ".js": "text/javascript",
                             ".json": "application/json"})

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def serve(porta=8080):
    gestore = functools.partial(Gestore, directory=WEB)
    with http.server.ThreadingHTTPServer(("127.0.0.1", porta), gestore) as srv:
        print(f"PanGeo aperto su http://127.0.0.1:{porta}/  · tabelle aperte: http://127.0.0.1:{porta}/tabelle.html  (Ctrl+C per chiudere)")
        srv.serve_forever()


def stato():
    live = leggi_json(os.path.join(DATI, "live.json"), None)
    if not live:
        print("Nessun dato: lancia prima  python castello.py aggiorna")
        return
    print(f"Ultimo aggiornamento: {live['agg']} · notizie: {len(live['notizie'])} · video: {len(live['video'])}")
    conta = {}
    for n in live["notizie"]:
        for p in n.get("paesi", []):
            conta[p] = conta.get(p, 0) + 1
    for p, c in sorted(conta.items(), key=lambda x: -x[1])[:15]:
        print(f"  {p}: {c}")
    c = live.get("cielo")
    if c:
        print(f"Cielo ({c['agg']}): {c['in_volo']} aerei in volo nel mondo")
        for p, v in c["paesi"].items():
            if v[2]:
                print(f"  {p}: {v[0]} ora, di solito {v[1]} ({v[2]})")
    f = live.get("fonti") or {}
    if f:
        print(f"Fonti RSS attive: {f.get('rss_attive')}/{f.get('rss_totali')} · scoperte da sole: {len(f.get('scoperte', []))}")
    an = live.get("analisi") or {}
    if an:
        print(f"Notizie confermate da più fonti: {an.get('confermate')} su {an.get('notizie')} "
              f"({round(100 * an.get('quota_confermate', 0))}%) · per livello: {an.get('per_livello')} · "
              f"Stati senza notizie: {an.get('stati_scoperti')}")
        for c in an.get("consigli", []):
            print("  da migliorare:", c)
        mg = an.get("miglioratore") or {}
        for q_, x_ in mg.get("fatte", [])[-5:]:
            print(f"  miglioratore ha fatto ({q_}):", x_)
        for x_ in mg.get("richieste", []):
            print("  miglioratore chiede:", x_)
        pg = (an.get("peggiora") or {}).get("lista") or []
        if pg:
            print("Dove peggiora:", ", ".join(f"{x[0]} ({x[1]} al giorno, prima {x[2]})" for x in pg[:8]))
    chiavi = leggi_json(os.path.join(DATI, "chiavi.json"), {})
    conto = leggi_json(os.path.join(DATI, "cervello.json"), {})
    if chiavi.get("anthropic_key"):
        print(f"Cervello (API di Claude): attivo · richieste oggi {conto.get('chiamate', 0)}"
              f" su {leggi_json(os.path.join(QUI, 'config.json'), {}).get('cervello', {}).get('max_al_giorno', 6)}"
              f" · spesa stimata oggi {conto.get('usd_oggi', 0):.4f} $ · questo mese {conto.get('usd_mese', 0):.4f} $")
    else:
        print("Cervello (API di Claude): spento (nessuna chiave)")
    if live.get("brief"):
        print("Da sapere adesso (" + live["brief"].get("agg", "") + "):")
        print(live["brief"].get("testo", ""))


def salute():
    """Controllo del cuore: file presenti e leggibili, ultimo giro, blocchi rimasti, spazio."""
    ok = True
    for nome in ("castello.py", "config.json", "paesi.json", "mappa.json", os.path.join("web", "index.html")):
        p = os.path.join(QUI, nome)
        stato_ = "ok"
        try:
            if nome.endswith(".json"):
                json.load(open(p, encoding="utf-8"))
            elif not os.path.getsize(p):
                stato_ = "VUOTO"
        except (OSError, ValueError) as e:
            stato_ = "ROTTO (" + str(e)[:60] + ")"
        ok = ok and stato_ == "ok"
        print(f"  {nome}: {stato_}")
    for nome in ("archivio.json", "live.json", "analisi.json", "fonti_auto.json", "storico_stati.json", "miglioratore.json"):
        p = os.path.join(DATI, nome)
        if not os.path.exists(p):
            print(f"  dati/{nome}: non ancora creato")
            continue
        try:
            json.load(open(p, encoding="utf-8"))
            print(f"  dati/{nome}: ok ({os.path.getsize(p) // 1024} KB)")
        except ValueError:
            ok = False
            print(f"  dati/{nome}: ROTTO: cancellalo, al prossimo giro si ricrea (l'archivio riparte dalla copia)")
    live = leggi_json(os.path.join(DATI, "live.json"), {})
    print("  ultimo giro:", live.get("agg", "mai"), "· versione", VERSIONE)
    if os.path.exists(os.path.join(DATI, "aggiorna.lock")):
        print("  un giro è in corso adesso (o si è interrotto: il blocco scade da solo dopo 45 minuti)")
    print("Cuore sano." if ok else "Qualcosa non va: guarda le righe con ROTTO o VUOTO.")


if __name__ == "__main__":
    a = sys.argv[1:]
    comando = a[0] if a else "aiuto"
    if comando == "aggiorna":
        aggiorna()
    elif comando == "serve":
        serve(int(a[1]) if len(a) > 1 else 8080)
    elif comando == "stato":
        stato()
    elif comando == "fonti":
        cmd_fonti()
    elif comando == "fonte" and len(a) > 1:
        cmd_fonte(a[1], " ".join(a[2:]))
    elif comando == "youtube" and len(a) > 1:
        aggiungi_mia("youtube", a[1] if a[1].startswith(("@", "UC")) else "@" + a[1], None)
    elif comando == "telegram" and len(a) > 1:
        aggiungi_mia("telegram", {"canale": a[1].lstrip("@"), "chi": " ".join(a[2:]) or a[1].lstrip("@")}, "canale")
    elif comando == "chiave" and len(a) > 2:
        cmd_chiave(a[1], a[2])
    elif comando == "chiave" and len(a) == 2:
        import getpass  # chiede la chiave senza mostrarla sullo schermo
        valore = getpass.getpass(f"Incolla la chiave «{a[1]}» e premi Invio (non si vede, è normale): ").strip()
        if valore:
            cmd_chiave(a[1], valore)
        else:
            print("Nessuna chiave: niente è cambiato.")
    elif comando == "approva":
        src_ = os.path.join(DATI, "in_attesa", "castello.py")
        if not os.path.exists(src_):
            print("Nessuna versione in attesa.")
        else:
            compile(open(src_, encoding="utf-8").read(), "castello.py", "exec")
            os.makedirs(os.path.join(DATI, "copie"), exist_ok=True)
            shutil.copyfile(os.path.join(QUI, "castello.py"), os.path.join(DATI, "copie", "castello.py.prima"))
            shutil.move(src_, os.path.join(QUI, "castello.py"))
            print("Versione nuova installata. Quella di prima è in dati/copie/castello.py.prima")
    elif comando == "provacervello":
        ch_ = leggi_json(os.path.join(DATI, "chiavi.json"), {})
        if not ch_.get("anthropic_key"):
            print("Nessuna chiave: python castello.py chiave anthropic_key")
        else:
            k_ = ch_["anthropic_key"]
            print("Chiave salvata: inizia con", k_[:10] + "…", "(vanno bene sk-ant-api e sk-ant-usr; non l'ID che inizia con apikey_)")
            try:
                print("Risposta:", chiedi_claude(ch_, leggi_json(os.path.join(QUI, "config.json"), {}), "Rispondi solo: ok", 10))
                print("Il cervello funziona.")
            except Exception as e:
                print("Non funziona:", re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e)))
    elif comando == "salute":
        salute()
    elif comando == "bot":
        bot_chat(leggi_json(os.path.join(DATI, "chiavi.json"), {}))
    elif comando == "sincronizza":
        sincronizza()
    elif comando == "istantanea" and len(a) > 1:
        resto = a[2:]
        fb = None
        if "--brief" in resto:
            i = resto.index("--brief")
            fb = resto[i + 1] if i + 1 < len(resto) else None
            resto = resto[:i] + resto[i + 2:]
        istantanea(a[1], " ".join(resto) or "programma Castello", fb)
    elif comando == "ripristina" and len(a) > 1:
        ripristina(a[1])
    else:
        print(__doc__)

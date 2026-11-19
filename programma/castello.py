#!/usr/bin/env python3
"""PanGeo 2.20 (prima «Castello mentale») - programma per Termux (Android) e per qualsiasi computer con Python 3.

Raccoglie da fonti gratuite notizie, video, voci ufficiali, disastri e traffico aereo civile,
li collega agli Stati del Castello e li mostra nella cartella «Live dal mondo» del planisfero.
Si amplia da solo: prova le fonti candidate e scopre nuovi siti tra quelli più citati.

Comandi:
  python castello.py aggiorna completo      forza un giro completo adesso (leggero = solo feed, Telegram, YouTube)
  python castello.py aggiorna              raccoglie tutto e scrive web/live.js
  python castello.py serve [porta]         apre il Castello su http://127.0.0.1:8080
  python castello.py stato                 riassunto: notizie, cielo, fonti
  python castello.py fonti                 elenco delle fonti e del loro stato
  python castello.py fonte URL [tema]      aggiunge un feed RSS o Atom
  python castello.py youtube @canale       aggiunge un canale YouTube
  python castello.py telegram canale [chi] aggiunge un canale Telegram pubblico
  (da solo: cerca notizie sugli Stati meno coperti, studia gli Stati su Wikipedia, trova feed e canali nuovi)
  python castello.py chiave nome valore    salva una chiave gratuita (es. opensky_id)
  python castello.py approva               installa il programma nuovo arrivato da GitHub (mai da solo)
  python castello.py domande                le domande che il programma si fa, e le risposte che trova
  python castello.py piano                  a che punto è il lavoro a piano (alleanze, patti, appalti)
  python castello.py veglia                 controlla che PanGeo sia acceso e, se no, lo riaccende
  python castello.py giri                   quanti giri fa, ogni quanto, quanto durano, a che punto è quello in corso
  python castello.py rapporto [ore]         che cosa ha raccolto e dove è migliorato (dal diario, 24 ore)
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
import glob
import gzip
import hashlib
import html
import http.server
import json
import math
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
import threading
import xml.etree.ElementTree as ET
import zlib
from datetime import date, datetime, timedelta, timezone

VERSIONE = "2.20"
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
    r"ribell|insurg|jihad|\bisis\b|\bhamas\b|hezbollah|houthi|kremlin|cremlino|pentagon|diplomat|ambasciat|embassy|"
    r"trade (?:deal|agreement|pact|war|talks)|free trade|accord[oi] commercial|libero scambio|guerra commerciale|"
    r"export (?:control|ban)|\bwto\b|mercosur|\bbrics\b|"
    r"\binterpol\b|europol|\boms\b|world health|outbreak|epidemi|pandemi|consolat|consulate|"
    r"etnic|ethnic|sectarian|settari|minoranz|minorit|religious (?:freedom|violence|tension)|libertà religiosa|\bcast[ae]s?\b|"
    r"disuguaglianz|inequalit|peace (?:deal|agreement|treaty|talks)|accord[oi] di pace|normaliz|abraham accords|accordi di abramo|"
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


_ULTIMA = {}
RICHIESTE, RIFIUTI = {}, {}  # richieste fatte e rifiuti (429) per sito, nel giro in corso


RETE = {"su": True, "falliti": 0, "controllo": 0.0}
_GAI = socket.getaddrinfo
_DNS = {}


class SenzaRete(OSError):
    """La rete non c'è: non è colpa della fonte, e la fonte non va penalizzata."""


def rete_ok(forza=False):
    """C'è la rete? Prova a collegarsi a tre indirizzi numerici (così non serve il DNS). Il risultato vale un minuto."""
    if not forza and time.time() - RETE["controllo"] < 60:
        return RETE["su"]
    su = False
    for ip in ("1.1.1.1", "8.8.8.8", "9.9.9.9", "github.com", "www.wikipedia.org"):
        try:
            socket.create_connection((ip, 443), timeout=5).close()
            su = True
            break
        except OSError:
            continue
    RETE.update(su=su, controllo=time.time(), falliti=0)
    return su


def _errore_di_rete(e):
    """Vero se l'errore viene dalla rete (nome non trovato, rete irraggiungibile), non dal sito."""
    t = str(e).lower()
    return any(k in t for k in ("no address associated", "name or service not known", "temporary failure in name resolution",
                                "network is unreachable", "no route to host", "nodename nor servname", "rete assente"))


def _risolvi_fuori(host):
    """Il DNS del telefono non trova il sito: l'indirizzo si chiede a un DNS pubblico via HTTPS (Cloudflare, poi Google)."""
    for url in ("https://1.1.1.1/dns-query?name=%s&type=A", "https://8.8.8.8/resolve?name=%s&type=A"):
        try:
            req = urllib.request.Request(url % urllib.parse.quote(host), headers={"accept": "application/dns-json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8) as r:
                for a in json.loads(r.read().decode("utf-8", "replace")).get("Answer", []):
                    if a.get("type") == 1:
                        return a.get("data")
        except Exception:
            continue
    return None


def _getaddrinfo(host, *a, **k):
    try:
        return _GAI(host, *a, **k)
    except socket.gaierror:
        if not isinstance(host, str) or re.fullmatch(r"[0-9a-fA-F.:]+", host) or not RETE["su"] or _DNS.get(host) == "":
            raise
        ip = _DNS.get(host) or _risolvi_fuori(host)
        _DNS[host] = ip or ""  # se nemmeno il DNS pubblico lo trova, in questo giro non si riprova
        if not ip:
            raise
        return _GAI(ip, *a, **k)


socket.getaddrinfo = _getaddrinfo

ERRORI_IT = [
    (r"<urlopen error \[Errno 7\] No address associated with hostname>|<urlopen error \[Errno -2\] Name or service not known>|"
     r"<urlopen error \[Errno -3\] Temporary failure in name resolution>|<urlopen error \[Errno 8\] nodename nor servname[^>]*>",
     "il sito non si trova (né il DNS del telefono né quello pubblico lo conoscono: forse ha cambiato indirizzo)"),
    (r"<urlopen error \[Errno 101\] Network is unreachable>|<urlopen error \[Errno 113\] No route to host>", "rete assente"),
    (r"<urlopen error timed out>|<urlopen error _ssl\.c:\d+: The handshake operation timed out>|The read operation timed out|timed out",
     "tempo scaduto: il sito non ha risposto"),
    (r"HTTP Error 401: \w+(?: \w+)*", "accesso negato: servono credenziali valide (401)"),
    (r"HTTP Error 403: \w+(?: \w+)*", "il sito rifiuta l'accesso ai programmi (403)"),
    (r"HTTP Error 404: \w+(?: \w+)*", "l'indirizzo non esiste più (404)"),
    (r"HTTP Error 410: \w+(?: \w+)*", "l'indirizzo è stato tolto (410)"),
    (r"HTTP Error 429: \w+(?: \w+)*", "troppe richieste: il sito chiede di rallentare (429)"),
    (r"HTTP Error 5\d\d: \w+(?: \w+)*", "il sito ha un guasto suo (errore 500 e simili)"),
    (r"<urlopen error \[Errno 111\] Connection refused>|Connection refused", "collegamento rifiutato dal sito"),
    (r"<urlopen error \[Errno 104\] Connection reset by peer>|Connection reset by peer|Remote end closed connection without response",
     "collegamento interrotto dal sito"),
    (r"<urlopen error \[SSL[^>]*>", "certificato di sicurezza del sito non valido"),
    (r"not well-formed \(invalid token\): line \d+, column \d+|syntax error: line \d+, column \d+|mismatched tag: line \d+, column \d+|"
     r"no element found: line \d+, column \d+|junk after document element: line \d+, column \d+",
     "il feed non è leggibile (pagina di blocco o formato cambiato)"),
    (r"undefined entity: line \d+, column \d+|XML or text declaration not at start of entity: line \d+, column \d+",
     "il feed non è leggibile (formato non valido)"),
    (r"feed vuoto", "il feed è vuoto"),
    (r"<urlopen error ([^>]*)>", r"errore di collegamento (\1)"),
]


def in_italiano(testo):
    for modello, it in ERRORI_IT:
        testo = re.sub(modello, it, testo)
    return testo


def riassumi_errori(errori):
    """Gli avvisi in italiano; quelli di rete, tanti e tutti uguali, diventano una riga sola."""
    di_rete = [e for e in errori if _errore_di_rete(e)]
    if len(di_rete) < 5:
        return [in_italiano(e) for e in errori]
    return [f"Rete assente o instabile durante il giro: {len(di_rete)} fonti non raggiunte. Non vengono penalizzate: "
            "il programma le rilegge da solo appena la rete torna."] + [in_italiano(e) for e in errori if e not in di_rete]


BYTE = {"n": 0}


def scarica(url, timeout=25, intestazioni=None, corpo=None, risposta=None):
    if not RETE["su"]:
        raise SenzaRete("rete assente")
    # rispetto dei siti: tra due richieste allo stesso sito passano almeno 2 secondi
    d_ = urllib.parse.urlparse(url).netloc
    attesa_ = 2.0 - (time.time() - _ULTIMA.get(d_, 0))
    if attesa_ > 0:
        time.sleep(attesa_)
    _ULTIMA[d_] = time.time()
    # «Accept-Encoding: gzip»: i feed viaggiano compressi (da 4 a 8 volte meno dati)
    h = {"User-Agent": UA, "Accept-Language": "it,en;q=0.8", "Accept-Encoding": "gzip"}
    h.update(intestazioni or {})
    req = urllib.request.Request(url, headers=h, data=corpo)
    RICHIESTE[d_] = RICHIESTE.get(d_, 0) + 1
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            dati_ = r.read()
            BYTE["n"] += len(dati_)  # quanti dati consuma un giro (va nel diario, in MB)
            if risposta is not None:  # per chiedere, la volta dopo, «solo se è cambiato»
                risposta["etag"], risposta["lm"] = r.headers.get("ETag") or "", r.headers.get("Last-Modified") or ""
            compr_ = (r.headers.get("Content-Encoding") or "").lower()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            RIFIUTI[d_] = RIFIUTI.get(d_, 0) + 1
        RETE["falliti"] = 0
        raise
    except OSError as e:
        # errore di rete e non del sito: dopo 5 di fila si guarda se la rete c'è ancora
        if _errore_di_rete(e):
            RETE["falliti"] += 1
            if RETE["falliti"] >= 5 and not rete_ok(forza=True):
                raise SenzaRete("rete assente") from e
        raise
    RETE["falliti"] = 0
    # alcuni siti (es. UN News dal novembre 2026) mandano il feed compresso anche se non lo si chiede
    try:
        if dati_[:2] == b"\x1f\x8b":
            dati_ = gzip.decompress(dati_)
        elif "deflate" in compr_:
            dati_ = zlib.decompress(dati_, -zlib.MAX_WBITS if dati_[:1] != b"\x78" else zlib.MAX_WBITS)
    except (OSError, EOFError, zlib.error):
        pass
    return dati_


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
        try:
            radice = ET.fromstring(pulito)
        except ET.ParseError:
            # entità del linguaggio delle pagine web (&nbsp; &eacute; …) che in un feed non sono ammesse: si scrivono per esteso
            testo_ = pulito.decode("utf-8", "replace")
            testo_ = re.sub(r"&(?!(?:amp|lt|gt|quot|apos);)([a-zA-Z]{2,8});",
                            lambda m: html.unescape(m.group(0)) if html.unescape(m.group(0)) != m.group(0) else " ", testo_)
            radice = ET.fromstring(testo_.encode("utf-8"))
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

def google_news(q, lingua, giorni=1):
    hl, gl, ceid = EDIZIONI.get(lingua, EDIZIONI["en"])
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + f" when:{giorni}d", "hl": hl, "gl": gl, "ceid": ceid})
    voci = []
    for titolo, link, data, fonte, sito in leggi_rss(scarica(url)):
        if fonte and titolo.endswith(" - " + fonte):
            titolo = titolo[: -len(fonte) - 3]
        voci.append((titolo, link, data, fonte or "Google News", sito))
    return voci


def gdelt(q, con_paese=False):
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
                     "https://" + d if d else "") + ((a.get("sourcecountry", ""),) if con_paese else ()))
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


CAL_PASSO = 4  # celle di un quarto di grado (circa 28 km): abbastanza larghe da non indicare nessun punto preciso
FIRMS_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
FIRMS_SATELLITI = ("VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT", "VIIRS_SNPP_NRT", "MODIS_NRT")
# file pubblici delle ultime 24 ore: si leggono anche senza chiave
FIRMS_APERTI = (("VIIRS_NOAA20_NRT", "noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv"),
                ("VIIRS_NOAA21_NRT", "noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_24h.csv"),
                ("VIIRS_SNPP_NRT", "suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv"),
                ("MODIS_NRT", "modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"))


def firms_righe(testo):
    """Il CSV di FIRMS in righe (lat, lon, quando, notte). I rilevamenti a bassa affidabilità si scartano:
    sono spesso riflessi del sole. Restituisce (righe, scartati); None se la risposta non è un CSV di FIRMS."""
    linee = testo.splitlines()
    if not linee or "latitude" not in linee[0]:
        return None
    testa = linee[0].split(",")
    try:
        ila, ilo, idt, iora = testa.index("latitude"), testa.index("longitude"), testa.index("acq_date"), testa.index("acq_time")
    except ValueError:
        return None
    iconf = testa.index("confidence") if "confidence" in testa else -1
    idn = testa.index("daynight") if "daynight" in testa else -1
    righe, scartati = [], 0
    for r in linee[1:]:
        c = r.split(",")
        try:
            la, lo = float(c[ila]), float(c[ilo])
            ora = c[iora].strip().zfill(4)
            quando = datetime(int(c[idt][0:4]), int(c[idt][5:7]), int(c[idt][8:10]), int(ora[:2]), int(ora[2:]), tzinfo=timezone.utc)
        except (ValueError, IndexError):
            continue
        if iconf >= 0 and iconf < len(c):
            aff = c[iconf].strip().lower()
            if aff in ("l", "low") or (aff.isdigit() and int(aff) < 30):
                scartati += 1
                continue
        righe.append((la, lo, quando, idn >= 0 and idn < len(c) and c[idn].strip().upper() == "N"))
    return righe, scartati


def calore_conta(righe, indice, vicini_cache):  # vicini_cache tiene anche i punti già localizzati (chiave: coppia di numeri)
    """Rilevamenti → {Stato (nome della mappa): {n, notte, celle {cella: rilevamenti}, conf {Stato vicino: rilevamenti}}}.
    Un rilevamento è «nella fascia di confine» se entro circa 30 km dalla sua cella c'è un altro Stato."""
    stati = {}
    for la, lo, _, notte in righe:
        p = vicini_cache.get((la, lo), 0)
        if p == 0:
            p = vicini_cache[(la, lo)] = indice.paese(lo, la)
        if not p:
            continue
        cy, cx = math.floor(la * CAL_PASSO), math.floor(lo * CAL_PASSO)
        s = stati.setdefault(p, {"n": 0, "notte": 0, "celle": {}, "conf": {}})
        s["n"] += 1
        s["notte"] += 1 if notte else 0
        chiave = f"{cy}_{cx}"
        c = s["celle"].setdefault(chiave, [0, 0])
        c[0] += 1
        c[1] += 1 if notte else 0
        vic = vicini_cache.get(chiave)
        if vic is None:
            vic, passo = set(), 1.0 / CAL_PASSO
            x0, y0 = (cx + 0.5) * passo, (cy + 0.5) * passo
            for dx in (-passo, 0, passo):
                for dy in (-passo, 0, passo):
                    q = indice.paese(x0 + dx, y0 + dy)
                    if q:
                        vic.add(q)
            vicini_cache[chiave] = vic
        for q in vic:
            if q != p:
                s["conf"][q] = s["conf"].get(q, 0) + 1
    return stati


def calore_giorno(storia, data, fam, stati, en2it, vuoto=False):
    """Mette un giorno intero nello storico (30 giorni): conteggi per Stato e per confine, e le celle accese."""
    giorni = storia.setdefault("giorni", {})
    giorni[data] = {"f": fam, "s": {en2it.get(p, p): [s["n"], s["notte"], {en2it.get(q, q): n for q, n in s["conf"].items()}]
                                    for p, s in stati.items()}}
    if vuoto:
        giorni[data]["vuoto"] = True
    for vecchia in sorted(giorni)[:-30]:
        del giorni[vecchia]
    # celle: un bit per giorno (bit 0 = il giorno «celle_al», bit 1 = il giorno prima…)
    celle = storia.setdefault("celle", {}).setdefault(fam, {})
    al = storia.setdefault("celle_al", {}).get(fam)
    giorno = date.fromisoformat(data)
    if al is None:
        storia["celle_al"][fam] = al = data
    passi = (giorno - date.fromisoformat(al)).days
    if passi > 0:  # giorno più recente: tutto scorre indietro
        tetto = (1 << 30) - 1
        for k in list(celle):
            m = (celle[k] << passi) & tetto
            if m:
                celle[k] = m
            else:
                del celle[k]
        storia["celle_al"][fam] = data
        passi = 0
    if -passi < 30:
        bit = 1 << (-passi)
        for s in stati.values():
            for k in s["celle"]:
                celle[k] = celle.get(k, 0) | bit


def calore_scarica(chiave, satellite, coda, errori, cosa):
    """Una richiesta a FIRMS con la chiave. Restituisce (righe, scartati) oppure None."""
    try:
        testo = scarica(FIRMS_API + f"{chiave}/{satellite}/world/{coda}", timeout=180).decode("utf-8", "replace")
    except Exception as e:
        errori.append(f"NASA FIRMS ({cosa}): {e}")
        return None
    r = firms_righe(testo)
    if r is None:
        errori.append(f"NASA FIRMS ({cosa}): risposta non valida ({testo[:60].strip() or 'vuota'})")
    return r


def calore_recupero(chiave, storia, indice, vicini_cache, en2it, errori, adesso, quanti=2):
    """Lo storico si riempie anche all'indietro: fino a 2 giorni passati per volta, al massimo 10, una volta ogni 2 ore.
    Serve la chiave (i file pubblici hanno solo le ultime 24 ore)."""
    if not chiave or not storia.get("sat"):
        return 0
    if storia.get("recupero", "") > (adesso - timedelta(minutes=110)).isoformat():
        return 0
    fam = "M" if storia["sat"].startswith("MODIS") else "V"
    ieri = (adesso - timedelta(days=1)).date()
    mancano = [d for d in ((ieri - timedelta(days=k)).isoformat() for k in range(0, 11))
               if d not in storia.get("giorni", {}) or storia["giorni"][d].get("f") != fam]
    if not mancano:
        return 0
    storia["recupero"] = adesso.isoformat()
    fatti = 0
    for d in mancano[:quanti]:
        r = calore_scarica(chiave, storia["sat"], "1/" + d, errori, "giorni passati")
        if r is None:
            break
        righe = [x for x in r[0] if x[2].date().isoformat() == d]
        calore_giorno(storia, d, fam, calore_conta(righe, indice, vicini_cache), en2it, vuoto=not righe)
        fatti += 1
    return fatti


def calore(chiavi, it2en, errori, ore):
    """Fonti di calore viste dai satelliti NASA (FIRMS), una volta al giorno, con storico di 30 giorni.
    Per ogni Stato: quante nelle ultime 24 ore e quante di solito; quante nella fascia di confine con ogni vicino;
    quante in zone che nelle due settimane prima erano spente e quante in zone sempre accese (industria, pozzi,
    vulcani, incendi stagionali); quante di notte. Il satellite vede il calore, non che cosa lo produce: ogni
    segnale va confermato con le notizie. Si salvano solo conteggi per Stato e celle di 28 km, nessun punto preciso."""
    chiave = chiavi.get("firms_key")
    percorso, percorso_zone = os.path.join(DATI, "calore.json"), os.path.join(DATI, "calore_zone.json")
    vecchio = leggi_json(percorso, None)
    adesso = datetime.now(timezone.utc)
    en2it = {en: it for it, en in it2en.items()}
    fresco = vecchio and vecchio.get("totale") and vecchio.get("iso", "") >= (adesso - timedelta(hours=ore)).isoformat()
    storia = leggi_json(percorso_zone, {})
    try:
        indice = IndiceGeo(carica_geo())
    except Exception as e:
        errori.append(f"NASA FIRMS: {e}")
        return vecchio
    vicini_cache = {}
    if fresco:  # i dati di oggi ci sono già: si usa il giro per riempire lo storico all'indietro
        if calore_recupero(chiave, storia, indice, vicini_cache, en2it, errori, adesso):
            scrivi_json(percorso_zone, storia)
            vecchio["storia"] = calore_storia(storia)
            scrivi_json(percorso, vecchio)
        return vecchio
    # 1. i dati: con la chiave oggi e ieri (ieri è un giorno intero, buono per lo storico); senza, il file pubblico
    righe, scartati, satellite, intero = None, 0, "", False
    if chiave:
        for satellite in FIRMS_SATELLITI:  # se un satellite non ha dati (manutenzione), si prova il successivo
            r = calore_scarica(chiave, satellite, "2", errori, "oggi e ieri")
            if r and r[0]:
                righe, scartati, intero = r[0], r[1], True
                break
            if r is None:
                break  # rete o chiave: inutile insistere, si passa ai file pubblici
    if not righe:
        for satellite, coda in FIRMS_APERTI:
            try:
                r = firms_righe(scarica("https://firms.modaps.eosdis.nasa.gov/data/active_fire/" + coda, timeout=180).decode("utf-8", "replace"))
            except Exception:
                r = None
            if r and r[0]:
                righe, scartati, intero = r[0], r[1], False
                break
    if not righe:
        errori.append("NASA FIRMS: nessun dato da nessun satellite nelle ultime 24 ore (riprovo al prossimo giro)")
        return vecchio
    fam = "M" if satellite.startswith("MODIS") else "V"
    storia["sat"] = satellite
    ieri = (adesso - timedelta(days=1)).date().isoformat()
    # 2. lo storico: il giorno intero di ieri (con la chiave) oppure, senza chiave, le ultime 24 ore come campione
    if ieri not in storia.get("giorni", {}) or storia["giorni"][ieri].get("f") != fam:
        campione = [x for x in righe if x[2].date().isoformat() == ieri] if intero else righe
        calore_giorno(storia, ieri, fam, calore_conta(campione, indice, vicini_cache), en2it, vuoto=not campione)
    calore_recupero(chiave, storia, indice, vicini_cache, en2it, errori, adesso)
    # 3. le ultime 24 ore, confrontate con i giorni interi prima di ieri (stesso tipo di satellite)
    finestra = [x for x in righe if x[2] >= adesso - timedelta(hours=24)]
    oggi = calore_conta(finestra, indice, vicini_cache)
    base = [g["s"] for d, g in sorted(storia["giorni"].items()) if d < ieri and g.get("f") == fam and not g.get("vuoto")][-14:]
    limite14 = (adesso - timedelta(days=15)).date().isoformat()
    giorni14 = sum(1 for d, g in storia["giorni"].items() if limite14 <= d < ieri and g.get("f") == fam and not g.get("vuoto"))
    giorni30 = sum(1 for d, g in storia["giorni"].items() if d < ieri and g.get("f") == fam and not g.get("vuoto"))
    celle = storia.get("celle", {}).get(fam, {})
    fuori = (date.fromisoformat(storia["celle_al"][fam]) - date.fromisoformat(ieri)).days  # di norma 0
    conta, zone = {}, {}
    for p, s in oggi.items():
        it = en2it.get(p)
        if not it:
            continue
        conta[p] = s["n"]
        media = round(sum(g.get(it, [0])[0] for g in base) / len(base), 1) if len(base) >= 2 else None
        z = {"notte": s["notte"], "conf": {}, "note": []}
        for q, n in sorted(s["conf"].items(), key=lambda kv: -kv[1])[:4]:
            qit = en2it.get(q, q)
            mq = round(sum(g.get(it, [0, 0, {}])[2].get(qit, 0) for g in base) / len(base), 1) if len(base) >= 2 else None
            z["conf"][qit] = [n, mq]
            if mq is not None and n >= 8 and n > 3 * mq + 3:
                z["note"].append(f"Calore insolito nella fascia di confine con {qit}: {n} rilevamenti in 24 ore, di solito {str(mq).replace('.', ',')}.")
        if giorni14 >= 5:  # zone nuove e zone sempre accese: servono almeno 5 giorni di storico
            nuove, ril_nuove, fisse, notte_fuori = 0, 0, 0, 0
            for k, (n, n_notte) in s["celle"].items():
                m = celle.get(k, 0) >> max(0, fuori)
                prima = (m >> 1) & ((1 << 14) - 1)
                accesa = bin((m >> 1) & ((1 << 29) - 1)).count("1")
                if giorni30 >= 7 and accesa >= max(4, (giorni30 + 1) // 2):
                    fisse += n
                else:
                    notte_fuori += n_notte
                    if not prima:
                        nuove += 1 if n >= 3 else 0
                        ril_nuove += n
            z["nuove"], z["fisse"] = [nuove, ril_nuove], fisse
            if nuove >= 2 and ril_nuove >= 15:
                z["note"].append(f"{nuove} zone accese che nelle due settimane prima erano spente ({ril_nuove} rilevamenti).")
            z["solito"] = s["n"] >= 20 and fisse >= 0.6 * s["n"]  # quasi tutto da zone sempre accese: non è una novità
            if notte_fuori >= 15 and notte_fuori >= 0.5 * max(1, s["n"] - fisse) and media is not None and s["n"] > 2 * media:
                z["note"].append(f"{notte_fuori} rilevamenti di notte fuori dalle zone sempre accese: gli incendi agricoli si vedono soprattutto di giorno.")
        if s["n"] >= 10 or z["note"]:
            zone[it] = z
    paesi = segnali_per_stato("calore_storico.json", conta, it2en, adesso, lambda n, m: "")
    for it, v in paesi.items():  # la media giusta è quella dei giorni interi dello stesso satellite
        s = oggi.get(it2en.get(it), None)
        if len(base) >= 2:
            v[1] = round(sum(g.get(it, [0])[0] for g in base) / len(base), 1)
        v[2] = "aumento" if v[1] is not None and v[0] >= 20 and v[0] > 3 * v[1] and not (zone.get(it) or {}).get("solito") else ""
    scrivi_json(percorso_zone, storia)
    uscita = {"iso": adesso.isoformat(), "agg": datetime.now().strftime("%d/%m %H:%M"), "totale": len(finestra),
              "paesi": paesi, "zone": zone, "scartati": scartati, "storia": calore_storia(storia),
              "fonte": f"NASA FIRMS ({satellite}, ultime 24 ore" + ("" if intero else ", file pubblico") + ")"}
    scrivi_json(percorso, uscita)
    return uscita


def calore_storia(storia):
    fam = "M" if storia.get("sat", "").startswith("MODIS") else "V"
    buoni = sorted(d for d, g in storia.get("giorni", {}).items() if g.get("f") == fam and not g.get("vuoto"))
    return {"giorni": len(buoni), "dal": buoni[0] if buoni else "", "satellite": "MODIS" if fam == "M" else "VIIRS"}



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
          "ilsole24ore", "wsj", "jerusalem post", "ahram", "ekathimerini", "the hill", "c-span",
          "ctv news", "middle east eye", "quotidiano nazionale", "resto del carlino", "huffpost", "milano finanza",
          "interfax", "nation thailand", "khmer times", "modern ghana", "free malaysia today", "ynetnews",
          "il manifesto", "kyodo", "the sentry", "thesentry", "italpress", "agenparl", "unione sarda",
          "quotidiano.net", "euronews", "tgcom24", "il foglio", "la nazione", "il mattino", "gazzetta del mezzogiorno",
          "internazionale", "libero", "tgla7", "ticinonline", "radio radicale", "agenzia dire", "cnbc", "straits times",
          "the national", "daily star", "ndtv", "inquirer", "rudaw", "the new arab", "iranwire", "censor", "цензор",
          "ukrainian news agency", "унн", "new voice of ukraine", "chosun", "조선일보", "매일경제", "아시아경제",
          "파이낸셜뉴스", "sbs", "联合早报", "zaobao", "national review", "the star", "asia news network", "upi",
          "ani news", "small wars journal", "zona militar", "ares difesa", "asian military review", "global initiative",
          "eurasia review", "mmegi", "modern ghana", "the sun malaysia", "rúv", "ruv.is", "vijesti", "notizie geopolitiche"],
    "C": ["tass", "ria novosti", "sputnik", "rt ", "xinhua", "global times", "cgtn", "china daily",
          "presstv", "press tv", "tehran times", "irna", "kcna", "anadolu", "telegram ·", "cremlino",
          "dipartimento della difesa usa", "ministero", "kremlin", "vietnam.vn", "ukrinform", "apa.az",
          "herald.co.zw", "al arabiya", "department of war", "сaba", "وكالة سبأ", "wam", "spa ", "united24",
          "agenzia fides", "trend news agency", "a news", "world socialist", "unione sindacale"],
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
                    r"motley fool|seeking alpha|benzinga|investing\.com|3bmeteo|orizzonte scuola|proactive financial|biggo|"
                    r"ad-hoc-news|newsbreak|msn\b", re.I)

APPRESI = {}  # livelli imparati dal programma: {nome fonte: "B" o "scarto"} (dati/fonti_auto.json)


LIVELLI_NOMI["C"] += ["trt", "armenpress", "xinhuanet", "sputniknews", "arab news", "asharq al-awsat", "iran international",
                      "middle east monitor", "astana times", "vnexpress", "agência brasil", "agencia brasil", "focus taiwan",
                      "radio free asia", "radio free europe", "rfe/rl", "voa", "voice of america"]
_RX_LIVELLI = {}


def _regole_livelli():
    """Nomi interi, non pezzi di parola: «efe» non deve trovare «defence», «ansa» non «Arkansas»,
    «rt» non «Report», «a news» non «Nigeria News». I nomi in altri alfabeti restano a confronto semplice."""
    if not _RX_LIVELLI:
        for liv, nomi in LIVELLI_NOMI.items():
            nomi = [k.strip() for k in nomi if k.strip()]
            latini = sorted({re.escape(k) for k in nomi if k.isascii()}, key=len, reverse=True)
            _RX_LIVELLI[liv] = (re.compile(r"(?<![a-z0-9])(?:" + "|".join(latini) + r")(?![a-z])"),
                                [k for k in nomi if not k.isascii()])
    return _RX_LIVELLI


def livello_di(nome, predefinito=""):
    if predefinito:
        return predefinito
    if APPRESI.get(nome) == "B":
        return "B"
    n = (nome or "").lower()
    for liv in ("C", "A", "B"):
        rx, altri = _regole_livelli()[liv]
        if rx.search(n) or any(k in n for k in altri):
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
    # il livello scelto a mano (config.json, fonti trovate da sole, Telegram) resta; quello indovinato
    # dal nome della testata (Google News, GDELT) si ricalcola, così le correzioni valgono anche per l'archivio
    fissi = {f.get("nome") for f in cfg.get("rss", []) + cfg.get("candidati", []) + auto.get("scoperte", [])}
    for v in voci.values():
        f_ = v.get("fonte") or ""
        if f_ in fissi or f_.startswith("Telegram") or v.get("liv") == "da valutare":
            v["lv"] = livello_di(f_, v.get("lv", ""))
        else:
            v["lv"] = livello_di(f_)
    gruppi, esito = raggruppa(voci)
    punti = {}
    for k, v in voci.items():
        fonti = gruppi[esito[k]]["fonti"]
        altre = {f: l for f, l in fonti.items() if f != v.get("fonte")}
        v["nf"] = len(fonti)
        v["gr"] = esito[k]  # gruppo dello stesso fatto in questo giro (serve alla memoria)
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
    # le fonti non classificate (per esempio quelle che arrivano da Google News) imparano il loro livello
    appresi = auto.setdefault("livelli_appresi", {})
    for f, st_ in punti.items():
        if not f or st_[2] != "D" or f in appresi or f in promosse or f in scartate:
            continue
        quota_ = st_[1] / st_[0]
        if st_[0] >= 15 and quota_ >= 0.3:
            appresi[f] = "B"
            promosse.append(f)
        elif st_[0] >= 30 and quota_ < 0.03:
            appresi[f] = "scarto"
            scartate.append(f)
    APPRESI.update(appresi)
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
        consigli.append("Calore da satellite senza chiave: funziona con i file pubblici, ma lo storico cresce solo di un giorno al giorno. Con la chiave gratuita NASA FIRMS recupera subito 10 giorni (LEGGIMI, «Chiavi gratuite»).")
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
    con_calore = {p_ for p_, z_ in ((dati_calore or {}).get("zone") or {}).items() if z_.get("note")}
    for p in set(per) | set(picchi) | con_calore:
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
        for nota_ in (((dati_calore or {}).get("zone") or {}).get(p) or {}).get("note", []):
            righe.append(["calore", nota_ + " Il satellite vede il calore, non chi lo produce: da confermare con le notizie.", []])
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
    if analisi["stati_scoperti"] > 60 and rot < 8:
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
        if st.get("fila", 0) == 10:
            fatte.append(f"«{f['nome']}» non risponde da 10 giri: la riprovo una volta al giorno e cerco un sostituto.")
    imp["in_pausa"] = {}  # dalla 2.15 nessuna fonte resta bloccata
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
    # una volta al giorno, se c'è il cervello: 3 miglioramenti concreti scritti da Claude sui numeri del sistema
    oggi_ = adesso.date().isoformat()
    if chiavi.get("anthropic_key") and m.get("rapporto_giorno") != oggi_:
        try:
            dati_ = {"giri": m["giri"][-8:], "per_livello": analisi["per_livello"], "fonti_meno_confermate":
                     analisi.get("fonti_meno_confermate", [])[:8], "stati_scoperti": analisi.get("esempi_scoperti", [])[:20],
                     "errori": errori[:10], "fatte": m["fatte"][-5:],
                     "fonti_rotte": [f.get("nome", "") for f in cfg.get("rss", []) + cfg.get("candidati", [])
                                     if auto.get("stato", {}).get(f["url"], {}).get("fila", 0) >= 3][:10]}
            conto_ = leggi_json(os.path.join(DATI, "cervello.json"), {})
            m["rapporto"] = chiedi_claude(chiavi, cfg, "Sei il revisore di un programma che raccoglie notizie di difesa e geopolitica "
                                          "da fonti gratuite e le confronta tra loro. Con questi numeri scrivi in italiano 3 miglioramenti "
                                          "concreti e piccoli (una riga ciascuno, che iniziano con «- »): fonti da aggiungere o togliere, "
                                          "Stati da coprire, errori da sistemare. Niente premesse. Poi scrivi una riga con la sola parola RICERCHE e sotto "
                                          "fino a 8 ricerche per Google News sugli Stati e sui temi meno coperti, una per riga, nel formato "
                                          "lingua (it o en)|nome dello Stato in italiano|parole da cercare (con il nome dello Stato tra virgolette). "
                                          "Infine una riga con la sola parola FONTI e sotto fino a 10 siti di notizie o di istituzioni che hanno un "
                                          "feed RSS: prima un sostituto equivalente (stesso Paese o stesso tema) per ciascuna delle fonti_rotte, "
                                          "poi siti che coprono gli Stati meno coperti, anche in lingue diverse dall'inglese. "
                                          "Uno per riga, nel formato dominio|nome dello Stato in italiano.\n"
                                          + json.dumps(dati_, ensure_ascii=False)[:6000], 1000, conto_)[:3500]
            scrivi_json(os.path.join(DATI, "cervello.json"), conto_)
            pezzi_ = re.split(r"(?m)^\W*RICERCHE\W*$", m["rapporto"], maxsplit=1)
            if len(pezzi_) == 2:
                m["rapporto"], righe_ = pezzi_[0].strip(), pezzi_[1]
                pezzi_ = re.split(r"(?m)^\W*FONTI\W*$", righe_, maxsplit=1)
                righe_ = pezzi_[0]
                for riga in (pezzi_[1].splitlines() if len(pezzi_) == 2 else []):
                    parti = [x.strip(" -•*`") for x in riga.split("|")]
                    d_ = re.sub(r"^(https?://)?(www\.)?", "", parti[0].lower()).split("/")[0]
                    if re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,60}\.[a-z]{2,}", d_) and d_ not in ESCLUSI:
                        auto.setdefault("da_provare", []).append({"d": d_, "stato": parti[1] if len(parti) > 1 else ""})
                auto["da_provare"] = auto.get("da_provare", [])[-30:]
                perc_r = os.path.join(DATI, "ricerche.json")
                R = leggi_json(perc_r, {"code": []})
                paesi_ = leggi_json(os.path.join(QUI, "paesi.json"), {})
                note_ = {x["q"] for x in R.setdefault("code", [])}
                for riga in righe_.splitlines():
                    parti = [x.strip(" -•*") for x in riga.split("|")]
                    if len(parti) == 3 and parti[0] in ("it", "en") and 8 <= len(parti[2]) <= 140 and parti[2] not in note_ \
                            and not re.search(r"[<>{}\\]|https?:", parti[2]):
                        R["code"].append({"q": parti[2], "l": parti[0], "stato": parti[1] if parti[1] in paesi_ else "",
                                          "tema": "Ricerca autonoma", "da": "cervello", "prove": 0, "nuove": 0, "ultimo": ""})
                        note_.add(parti[2])
                scrivi_json(perc_r, R)
            m["rapporto_giorno"] = oggi_
            scrivi_json(percorso, m)
        except Exception as e:
            errori.append("Claude (rapporto del miglioratore): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:150])
    return {"fatte": m["fatte"][-8:], "richieste": richieste[:10], "tendenza": tendenza,
            "rapporto": m.get("rapporto", ""), "rapporto_giorno": m.get("rapporto_giorno", "")}


# ----------------------------------------------------------------------------- cervello (facoltativo, a pagamento)

ANTHROPIC = os.environ.get("CASTELLO_API_URL", "https://api.anthropic.com/v1/messages")
NON_LATINO = re.compile(r"[Ѐ-ӿ֐-ۿ฀-๿぀-ヿ一-鿿가-힯]")


PREZZI = {"haiku": (0.10, 0.50), "sonnet": (2.0, 10.0), "opus": (5.0, 25.0)}  # dollari per milione di token (ingresso, uscita)


def costo_usd(modello, entrata, uscita):
    pi, pu = next((v for k, v in PREZZI.items() if k in modello), PREZZI["sonnet"])
    return (entrata * pi + uscita * pu) / 1e6


def pulisci_brief(testo):
    """Il riassunto nella pagina: senza segni di Markdown, senza la riga del titolo (la pagina ha già il suo)
    e senza un ultimo punto rimasto a metà."""
    righe = [r.strip() for r in (testo or "").replace("**", "").replace("__", "").splitlines()]
    righe = [r for r in righe if r and not re.match(r"^#*\s*«?da sapere adesso»?\s*:?$", r, re.I)]
    if len(righe) > 1 and righe[-1].startswith("-") and not righe[-1].endswith((")", ".", "»", '"', "!", "?")):
        righe.pop()
    return "\n".join(righe)


def chiedi_claude(chiavi, cfg, testo, massimo=900, conto=None):
    modello = cfg.get("cervello", {}).get("modello", "claude-haiku-5-5")
    imp_c = cfg.get("cervello", {})
    dati_r = {"model": modello, "max_tokens": massimo + imp_c.get("riserva_token", 1500),
              "messages": [{"role": "user", "content": testo}]}
    # Haiku 5.5 ragiona prima di rispondere e il ragionamento consuma lo stesso tetto di token: per tradurre e
    # riassumere non serve, quindi si spegne (per riaccenderlo: "pensiero": "acceso" in config.json)
    if imp_c.get("pensiero", "spento") == "spento":
        dati_r["thinking"] = {"type": "disabled"}
    intest = {"x-api-key": chiavi["anthropic_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"}
    if chiavi.get("anthropic_workspace"):
        # chiavi personali (sk-ant-usr) non legate a un'area di lavoro: serve l'ID dell'area (wrkspc_...)
        intest["anthropic-workspace-id"] = chiavi["anthropic_workspace"]
    try:
        try:
            r = json.loads(scarica(ANTHROPIC, timeout=120, corpo=json.dumps(dati_r).encode(), intestazioni=intest))
        except urllib.error.HTTPError as e0:
            if e0.code != 400 or "thinking" not in dati_r:
                raise
            # alcuni modelli non permettono di spegnere il ragionamento: si riprova una volta lasciandolo acceso
            del dati_r["thinking"]
            r = json.loads(scarica(ANTHROPIC, timeout=120, corpo=json.dumps(dati_r).encode(), intestazioni=intest))
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
    uscita_ = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text").strip()
    if r.get("stop_reason") == "max_tokens" and "\n" in uscita_:
        uscita_ = uscita_.rsplit("\n", 1)[0].rstrip()  # l'ultima riga è rimasta a metà: meglio toglierla
    return uscita_


def _conto_cervello():
    """Il conto del cervello di oggi (richieste e spesa stimata): riparte da zero a mezzanotte, il mese resta."""
    conto = leggi_json(os.path.join(DATI, "cervello.json"), {})
    oggi = datetime.now().date().isoformat()
    if conto.get("giorno") != oggi:
        conto = {"giorno": oggi, "chiamate": 0, "brief": conto.get("brief"), "usd_oggi": 0.0, "token_oggi": 0,
                 "mese": conto.get("mese"), "usd_mese": conto.get("usd_mese", 0.0)}
    return conto


def _cervello_libero(conto, impost):
    """Vero se il cervello può ancora lavorare: sotto il tetto di richieste e sotto i tetti di spesa del giorno e del mese."""
    if conto.get("chiamate", 0) >= impost.get("max_al_giorno", 6) or conto.get("usd_oggi", 0) >= impost.get("max_usd_giorno", 0.15):
        return False
    return not (conto.get("mese") == datetime.now().strftime("%Y-%m") and conto.get("usd_mese", 0) >= impost.get("max_usd_mese", 3.0))


def cervello(chiavi, cfg, archivio, recente, ric, errori):
    """Solo se c'è la chiave API di Claude (si paga a consumo, a parte rispetto all'abbonamento):
    traduce in italiano i titoli in alfabeti non latini e scrive «Da sapere adesso» con le sole
    notizie confermate. Al massimo cervello.max_al_giorno richieste al giorno (predefinito 6)."""
    impost = cfg.get("cervello", {})
    if not chiavi.get("anthropic_key") or not impost.get("attivo", True):
        return None
    percorso = os.path.join(DATI, "cervello.json")
    conto = _conto_cervello()
    tetto = impost.get("max_al_giorno", 6)
    # tetti di spesa stimata: oltre, il cervello si ferma da solo fino a domani o al mese dopo
    conto["tetto"] = ""
    if conto.get("usd_oggi", 0) >= impost.get("max_usd_giorno", 0.15):
        tetto, conto["tetto"] = 0, "giorno"
    elif conto.get("mese") == datetime.now().strftime("%Y-%m") and conto.get("usd_mese", 0) >= impost.get("max_usd_mese", 3.0):
        tetto, conto["tetto"] = 0, "mese"
    pausa_l = impost.get("pausa_lotti_minuti", 0)  # con i giri fitti: traduzioni e sala d'attesa non più spesso di così
    lotti_ok = not pausa_l or conto.get("ultimo_lotto", "") <= (datetime.now(timezone.utc) - timedelta(minutes=pausa_l - 2)).isoformat()
    # passo di spesa: il tetto del giorno si spende un po' per volta, così il cervello lavora fino a mezzanotte invece di
    # finire i soldi nel pomeriggio. Se a quest'ora si è già speso più della quota, traduzioni e sala d'attesa saltano
    # un giro (il riassunto e il lavoro a piano no).
    ora_ = datetime.now()
    quota_ = impost.get("max_usd_giorno", 0.15) * min(1.0, (ora_.hour * 60 + ora_.minute) / 1440 + 0.12)
    conto["passo"] = bool(impost.get("spesa_a_passo", True) and tetto and conto.get("usd_oggi", 0) > quota_)
    if conto["passo"]:
        lotti_ok = False
    voci = [(k, v) for k, v in archivio["notizie"].items() if (v.get("data_iso") or "") >= recente]
    # 1. traduzioni
    # (titoli in altri alfabeti o trovati cercando in un'altra lingua; prima i più recenti, a lotti)
    tutto_it = impost.get("traduci_tutto", True)  # anche l'inglese: nella pagina tutto si legge in italiano
    da_tradurre = sorted((v for _, v in voci if not v.get("it") and not v.get("gia_it")
                          and (NON_LATINO.search(v["t"]) or v.get("lg") or (tutto_it and lingua_titolo(v["t"]) != "it"))),
                         key=lambda v: v.get("data_iso") or "", reverse=True)
    lotto_, lotti_ = impost.get("traduzioni_lotto", 30), 0
    numerata = re.compile(r"\s*\**(\d+)\**\s*[.):\-]\s*\**\s*(.+)")
    if lotti_ok and tetto and (da_tradurre or any(not v_.get("no") for v_ in archivio.get("attesa", {}).values())):
        conto["ultimo_lotto"] = datetime.now(timezone.utc).isoformat()
    while da_tradurre and lotti_ok and conto["chiamate"] < tetto and lotti_ < impost.get("traduzioni_per_giro", 6):
        gruppo, da_tradurre = da_tradurre[:lotto_], da_tradurre[lotto_:]
        lotti_ += 1
        domanda = ("Traduci in italiano questi titoli di notizie (sono in lingue diverse), uno per riga, nello stesso ordine e "
                   "con lo stesso numero davanti, senza commenti. Traduzione fedele e completa, in italiano corretto e "
                   "scorrevole; nomi di persone, luoghi, sigle e numeri restano come sono; non aggiungere e non togliere nulla:\n" +
                   "\n".join(f"{i + 1}. {v['t']}" for i, v in enumerate(gruppo)))
        try:
            risposta = chiedi_claude(chiavi, cfg, domanda, 4500, conto)
            conto["chiamate"] += 1
            presi_ = 0
            for riga in risposta.splitlines():
                m = numerata.match(riga)
                if m and 0 < int(m.group(1)) <= len(gruppo):
                    v = gruppo[int(m.group(1)) - 1]
                    v["it"] = pulisci(m.group(2), 300)
                    if v["it"].strip().lower() == v["t"].strip().lower():
                        v["gia_it"] = True  # era già in italiano
                        del v["it"]
                    presi_ += 1
                    if "it" not in v:
                        continue
                    for p in ric.trova(v["it"]):
                        if p not in v["paesi"]:
                            v["paesi"].append(p)
                    if not v["paesi"] and v.get("rip"):
                        v["paesi"] = [v["rip"]]  # notizia locale che non nomina nessuno Stato: è del Paese della testata
            if not presi_:
                errori.append(f"Claude (traduzioni): risposta senza righe numerate ({len(risposta)} caratteri)")
                break
        except Exception as e:
            errori.append(f"Claude (traduzioni): {re.sub(r'sk-ant-[A-Za-z0-9_-]+', '***', str(e))}")
            break
    # 1a. sala d'attesa: titoli delle testate nella lingua del posto. Il cervello traduce quelli che riguardano i temi di
    # PanGeo e scarta gli altri (sport, spettacolo, cronaca minuta) con un trattino: così costa poco.
    attesa = archivio.setdefault("attesa", {})
    in_coda = sorted(((k, v) for k, v in attesa.items() if not v.get("no")), key=lambda kv: kv[1].get("data_iso") or "", reverse=True)
    lotto_a, lotti_a, entrate_, scartate_ = impost.get("attesa_lotto", 40), 0, 0, 0
    while in_coda and lotti_ok and conto["chiamate"] < tetto and lotti_a < impost.get("attesa_per_giro", 10):
        gruppo, in_coda = in_coda[:lotto_a], in_coda[lotto_a:]
        lotti_a += 1
        domanda = ("Sono titoli di giornali e televisioni di molti Paesi, in lingue diverse. Servono a un archivio di difesa e "
                   "geopolitica: tieni SOLO i titoli che parlano di uno di questi argomenti, e davanti metti la sua lettera tra "
                   "parentesi quadre:\n"
                   "[G] guerre, attacchi, operazioni militari, tregue e negoziati di pace\n"
                   "[D] forze armate, armi, esercitazioni, spesa militare, leva, basi e truppe all'estero\n"
                   "[I] industria della difesa, appalti e vendite di armi\n"
                   "[A] rapporti tra Stati: vertici, trattati, alleanze, ambasciate, crisi diplomatiche, confini\n"
                   "[C] sanzioni, dazi, accordi commerciali tra Stati, energia e materie prime come arma politica\n"
                   "[S] terrorismo, spionaggio, servizi segreti, attacchi informatici, colpi di Stato\n"
                   "[P] crisi di governo, elezioni nazionali, proteste di massa, stati d'emergenza, nomine e dimissioni di capi di "
                   "Stato, di governo, ministri della Difesa o degli Esteri, capi militari\n"
                   "[T] tensioni e violenze etniche, religiose o sociali; profughi e migrazioni di massa\n"
                   "[O] ONU, NATO, Unione europea, OMS, Interpol e altri organismi internazionali; epidemie ed emergenze "
                   "che toccano più Stati\n"
                   "Scarta tutto il resto scrivendo solo un trattino: cronaca nera e giudiziaria, processi, politica interna di "
                   "tutti i giorni, economia e aziende senza legame con gli argomenti sopra, sport, spettacolo, meteo, salute, "
                   "costume, incidenti. Nel dubbio scarta. Per i titoli tenuti scrivi, dopo la lettera, la traduzione in "
                   "italiano: fedele, completa, in italiano corretto; nomi, sigle e numeri restano come sono (se il titolo è "
                   "già in italiano riscrivilo uguale). Una riga per titolo, nello stesso ordine e con lo stesso numero "
                   "davanti, senza commenti. Esempio: «3. [D] La Polonia compra 96 elicotteri Apache» oppure «4. -».\n" +
                   "\n".join(f"{i + 1}. {v['t']}" for i, (k, v) in enumerate(gruppo)))
        try:
            risposta = chiedi_claude(chiavi, cfg, domanda, 4500, conto)
            conto["chiamate"] += 1
            viste_ = set()
            for riga in risposta.splitlines():
                m = numerata.match(riga)
                if not m or not 0 < int(m.group(1)) <= len(gruppo):
                    continue
                k, v = gruppo[int(m.group(1)) - 1]
                viste_.add(k)
                testo_ = pulisci(m.group(2), 300)
                mt_ = re.match(r"^\[([A-Za-z])\]\s*(.*)$", testo_)
                tema_ = TEMI_TRIAGE.get(mt_.group(1).upper()) if mt_ else None
                if mt_:
                    testo_ = mt_.group(2).strip()
                if len(testo_) < 8 or testo_.strip(" -–—.") == "":
                    v["no"] = True  # non riguarda PanGeo: resta in attesa solo per non rileggerlo
                    scartate_ += 1
                    continue
                if testo_.strip().lower() == v["t"].strip().lower():
                    v["gia_it"] = True  # titolo già in italiano
                else:
                    v["it"] = testo_
                if tema_ and v.get("tema") in ("Notizie dal mondo", "Scoperte automatiche (da valutare)", "", None):
                    v["tema"] = tema_  # la testata è generalista: l'argomento lo dice il cervello
                v["paesi"] = list(dict.fromkeys(v.get("paesi", []) + ric.trova(testo_))) or ([v["rip"]] if v.get("rip") else [])
                archivio["notizie"][k] = v
                attesa[k] = {"no": True, "data_iso": v.get("data_iso"), "t": "", "u": ""}
                entrate_ += 1
            if not viste_:
                errori.append(f"Claude (titoli in attesa): risposta senza righe numerate ({len(risposta)} caratteri)")
                break
        except Exception as e:
            errori.append(f"Claude (titoli in attesa): {re.sub(r'sk-ant-[A-Za-z0-9_-]+', '***', str(e))}")
            break
    conto["attesa"] = [entrate_, scartate_, sum(1 for v in attesa.values() if not v.get("no"))]
    # 1b. il «sapere» letto in inglese (Wikipedia in inglese, World Factbook) diventa italiano
    S_ = leggi_json(os.path.join(DATI, "sapere.json"), {})
    da_s = [(st_, k) for st_, v in S_.items() for k in ("forze", "storia", "factbook")
            if isinstance(v.get(k), dict) and v[k].get("lingua") == "en" and not v[k].get("testo_it")][:impost.get("sapere_per_giro", 8)]
    if da_s and conto["chiamate"] < tetto:
        domanda = ("Traduci in italiano questi testi, uno per riga, nello stesso ordine e con lo stesso numero davanti. "
                   "Ogni traduzione su una riga sola, senza commenti e senza aggiungere nulla:\n" +
                   "\n".join(f"{i + 1}. {S_[a][b]['testo']}" for i, (a, b) in enumerate(da_s)))
        try:
            risposta = chiedi_claude(chiavi, cfg, domanda, 4500, conto)
            conto["chiamate"] += 1
            for riga in risposta.splitlines():
                m = numerata.match(riga)
                if m and 0 < int(m.group(1)) <= len(da_s):
                    a, b = da_s[int(m.group(1)) - 1]
                    S_[a][b]["testo_it"] = pulisci(m.group(2), 1800)
            scrivi_sapere(S_)
        except Exception as e:
            errori.append(f"Claude (traduzione del sapere): {re.sub(r'sk-ant-[A-Za-z0-9_-]+', '***', str(e))}")
    # 2. «Da sapere adesso», al massimo ogni 6 ore
    vecchio = (conto.get("brief") or {}).get("iso", "")
    if conto["chiamate"] < tetto and vecchio < (datetime.now(timezone.utc) - timedelta(hours=impost.get("brief_ore", 6))).isoformat():
        conf = sorted((v for _, v in voci if v.get("conf")), key=lambda v: v.get("data_iso") or "", reverse=True)[:60]
        if len(conf) >= 5:
            domanda = ("Sei il redattore di un bollettino di difesa e geopolitica. Usa SOLO le notizie qui sotto (ora – titolo – "
                       "fonte), già confermate da più fonti. Scrivi in italiano da 6 a 8 punti «Da sapere adesso», uno per riga, che "
                       "iniziano con «- ». Regole: un solo fatto per punto, mai due fatti diversi nella stessa frase; comincia dal "
                       "luogo o da chi agisce; frasi brevi e complete, al passato; niente giudizi, previsioni o aggettivi di "
                       "colore; se due titoli dicono cose diverse sullo stesso fatto scrivi «secondo … , secondo …»; metti prima "
                       "i fatti più recenti; alla fine di ogni punto, tra parentesi, le fonti. Scrivi solo la versione finale: non "
                       "correggerti dentro il testo e non lasciare frasi a metà. Non aggiungere nulla che non sia nei titoli. "
                       "Niente dettagli operativi militari.\n\n" +
                       "\n".join(f"- {mostra_data(v.get('data_iso'))} – {v.get('it') or v['t']} – {v.get('fonte', '')}" for v in conf))
            try:
                testo = chiedi_claude(chiavi, cfg, domanda, 1200, conto)
                conto["chiamate"] += 1
                conto["brief"] = {"iso": datetime.now(timezone.utc).isoformat(),
                                  "agg": datetime.now().strftime("%d/%m %H:%M"), "testo": pulisci_brief(testo)[:4000]}
            except Exception as e:
                errori.append(f"Claude (riassunto): {re.sub(r'sk-ant-[A-Za-z0-9_-]+', '***', str(e))}")
    scrivi_json(percorso, conto)
    b = conto.get("brief")
    return {"agg": b["agg"], "testo": b["testo"]} if b else None

# ----------------------------------------------------------------------------- ricerca autonoma e sapere

# Edizioni di Google News per lingua: (hl, gl, ceid)
EDIZIONI = {"it": ("it", "IT", "IT:it"), "en": ("en", "US", "US:en"), "fr": ("fr", "FR", "FR:fr"),
            "es": ("es-419", "US", "US:es-419"), "pt": ("pt-BR", "BR", "BR:pt-419"), "ar": ("ar", "EG", "EG:ar"),
            "ru": ("ru", "RU", "RU:ru"), "de": ("de", "DE", "DE:de"),
            "zh": ("zh-CN", "CN", "CN:zh-Hans"), "zh-TW": ("zh-TW", "TW", "TW:zh-Hant"), "ja": ("ja", "JP", "JP:ja"),
            "ko": ("ko", "KR", "KR:ko"), "tr": ("tr", "TR", "TR:tr"), "hi": ("hi", "IN", "IN:hi"), "id": ("id", "ID", "ID:id"),
            "uk": ("uk", "UA", "UA:uk"), "pl": ("pl", "PL", "PL:pl"), "nl": ("nl", "NL", "NL:nl"), "sv": ("sv", "SE", "SE:sv"),
            "el": ("el", "GR", "GR:el"), "he": ("he", "IL", "IL:he"), "vi": ("vi", "VN", "VN:vi"), "th": ("th", "TH", "TH:th"),
            "bn": ("bn", "BD", "BD:bn"), "ro": ("ro", "RO", "RO:ro"), "hu": ("hu", "HU", "HU:hu"), "cs": ("cs", "CZ", "CZ:cs"),
            "sk": ("sk", "SK", "SK:sk"), "bg": ("bg", "BG", "BG:bg"), "sr": ("sr", "RS", "RS:sr"), "sl": ("sl", "SI", "SI:sl"),
            "lt": ("lt", "LT", "LT:lt"), "lv": ("lv", "LV", "LV:lv"), "no": ("no", "NO", "NO:no"),
            "ta": ("ta", "IN", "IN:ta"), "te": ("te", "IN", "IN:te"), "mr": ("mr", "IN", "IN:mr"), "ml": ("ml", "IN", "IN:ml")}
# Lingua in cui scrive la stampa del posto e nome dello Stato in quella lingua
LOCALE = {
    "Algeria": ("fr", "Algérie"), "Marocco": ("fr", "Maroc"), "Tunisia": ("fr", "Tunisie"), "Mauritania": ("fr", "Mauritanie"),
    "Senegal": ("fr", "Sénégal"), "Mali": ("fr", "Mali"), "Burkina Faso": ("fr", "Burkina Faso"), "Niger": ("fr", "Niger"),
    "Ciad": ("fr", "Tchad"), "Camerun": ("fr", "Cameroun"), "Gabon": ("fr", "Gabon"), "Congo": ("fr", "Congo-Brazzaville"),
    "RD Congo": ("fr", "RDC"), "Repubblica Centrafricana": ("fr", "Centrafrique"), "Costa d’Avorio": ("fr", "Côte d'Ivoire"),
    "Guinea": ("fr", "Guinée"), "Benin": ("fr", "Bénin"), "Togo": ("fr", "Togo"), "Burundi": ("fr", "Burundi"),
    "Ruanda": ("fr", "Rwanda"), "Gibuti": ("fr", "Djibouti"), "Madagascar": ("fr", "Madagascar"), "Comore": ("fr", "Comores"),
    "Haiti": ("fr", "Haïti"), "Lussemburgo": ("fr", "Luxembourg"), "Monaco": ("fr", "Monaco"),
    "Messico": ("es", "México"), "Guatemala": ("es", "Guatemala"), "Honduras": ("es", "Honduras"), "El Salvador": ("es", "El Salvador"),
    "Nicaragua": ("es", "Nicaragua"), "Costa Rica": ("es", "Costa Rica"), "Panama": ("es", "Panamá"), "Cuba": ("es", "Cuba"),
    "Repubblica Dominicana": ("es", "República Dominicana"), "Colombia": ("es", "Colombia"), "Venezuela": ("es", "Venezuela"),
    "Ecuador": ("es", "Ecuador"), "Perù": ("es", "Perú"), "Bolivia": ("es", "Bolivia"), "Cile": ("es", "Chile"),
    "Argentina": ("es", "Argentina"), "Paraguay": ("es", "Paraguay"), "Uruguay": ("es", "Uruguay"),
    "Guinea Equatoriale": ("es", "Guinea Ecuatorial"),
    "Brasile": ("pt", "Brasil"), "Angola": ("pt", "Angola"), "Mozambico": ("pt", "Moçambique"), "Capo Verde": ("pt", "Cabo Verde"),
    "Guinea-Bissau": ("pt", "Guiné-Bissau"), "São Tomé e Príncipe": ("pt", "São Tomé e Príncipe"), "Timor Est": ("pt", "Timor-Leste"),
    "Egitto": ("ar", "مصر"), "Arabia Saudita": ("ar", "السعودية"), "Iraq": ("ar", "العراق"), "Siria": ("ar", "سوريا"),
    "Libano": ("ar", "لبنان"), "Giordania": ("ar", "الأردن"), "Libia": ("ar", "ليبيا"), "Sudan": ("ar", "السودان"),
    "Yemen": ("ar", "اليمن"), "Oman": ("ar", "سلطنة عمان"), "Kuwait": ("ar", "الكويت"), "Qatar": ("ar", "قطر"),
    "Bahrein": ("ar", "البحرين"), "Emirati Arabi": ("ar", "الإمارات"), "Palestina": ("ar", "فلسطين"),
    "Kazakistan": ("ru", "Казахстан"), "Uzbekistan": ("ru", "Узбекистан"), "Turkmenistan": ("ru", "Туркменистан"),
    "Tagikistan": ("ru", "Таджикистан"), "Kirghizistan": ("ru", "Киргизия"), "Bielorussia": ("ru", "Беларусь"),
    "Armenia": ("ru", "Армения"), "Azerbaigian": ("ru", "Азербайджан"),
    "Austria": ("de", "Österreich"), "Svizzera": ("de", "Schweiz"), "Liechtenstein": ("de", "Liechtenstein"),
    "Germania": ("de", "Deutschland"), "Francia": ("fr", "France"), "Belgio": ("fr", "Belgique"), "Spagna": ("es", "España"),
    "Portogallo": ("pt", "Portugal"), "Russia": ("ru", "Россия"), "Georgia": ("ru", "Грузия"), "Somalia": ("ar", "الصومال"),
    "Cina": ("zh", "中国"), "Taiwan": ("zh-TW", "台灣"), "Giappone": ("ja", "日本"), "Corea del Sud": ("ko", "한국"),
    "Corea del Nord": ("ko", "북한"), "Turchia": ("tr", "Türkiye"), "India": ("hi", "भारत"), "Indonesia": ("id", "Indonesia"),
    "Ucraina": ("uk", "Україна"), "Polonia": ("pl", "Polska"), "Paesi Bassi": ("nl", "Nederland"), "Suriname": ("nl", "Suriname"),
    "Svezia": ("sv", "Sverige"), "Grecia": ("el", "Ελλάδα"), "Cipro": ("el", "Κύπρος"), "Israele": ("he", "ישראל"),
    "Vietnam": ("vi", "Việt Nam"), "Thailandia": ("th", "ประเทศไทย"), "Bangladesh": ("bn", "বাংলাদেশ"),
    "Romania": ("ro", "România"), "Moldavia": ("ro", "Moldova"), "Ungheria": ("hu", "Magyarország"),
    "Repubblica Ceca": ("cs", "Česko"), "Slovacchia": ("sk", "Slovensko"), "Bulgaria": ("bg", "България"),
    "Serbia": ("sr", "Србија"), "Montenegro": ("sr", "Црна Гора"), "Slovenia": ("sl", "Slovenija"),
    "Lituania": ("lt", "Lietuva"), "Lettonia": ("lv", "Latvija"), "Norvegia": ("no", "Norge"),
}
PAROLE_LOCALI = {"fr": "(armée OR militaire OR défense OR gouvernement OR sécurité)",
                 "es": "(ejército OR militar OR defensa OR gobierno OR seguridad)",
                 "pt": "(exército OR militar OR defesa OR governo OR segurança)",
                 "ar": "(الجيش OR الدفاع OR الحكومة OR الأمن)",
                 "ru": "(армия OR оборона OR правительство OR безопасность)",
                 "de": "(Armee OR Militär OR Verteidigung OR Regierung OR Sicherheit)",
                 "zh": "(军队 OR 国防 OR 政府 OR 安全)", "zh-TW": "(軍隊 OR 國防 OR 政府 OR 安全)",
                 "ja": "(自衛隊 OR 防衛 OR 政府 OR 安全保障)", "ko": "(군 OR 국방 OR 정부 OR 안보)",
                 "tr": "(ordu OR askeri OR savunma OR hükümet OR güvenlik)", "hi": "(सेना OR रक्षा OR सरकार OR सुरक्षा)",
                 "id": "(militer OR tentara OR pertahanan OR pemerintah OR keamanan)",
                 "uk": "(армія OR військові OR оборона OR уряд OR безпека)",
                 "pl": "(wojsko OR armia OR obrona OR rząd OR bezpieczeństwo)",
                 "nl": "(leger OR militair OR defensie OR regering OR veiligheid)",
                 "sv": "(armén OR militär OR försvar OR regeringen OR säkerhet)",
                 "el": "(στρατός OR άμυνα OR κυβέρνηση OR ασφάλεια)", "he": "(צבא OR ביטחון OR ממשלה OR הגנה)",
                 "vi": '("quân đội" OR "quốc phòng" OR "chính phủ" OR "an ninh")',
                 "th": "(กองทัพ OR กลาโหม OR รัฐบาล OR ความมั่นคง)", "bn": "(সেনাবাহিনী OR প্রতিরক্ষা OR সরকার OR নিরাপত্তা)",
                 "ro": "(armata OR militar OR apărare OR guvern OR securitate)",
                 "hu": "(hadsereg OR katonai OR védelem OR kormány OR biztonság)",
                 "cs": "(armáda OR vojenský OR obrana OR vláda OR bezpečnost)",
                 "sk": "(armáda OR vojenský OR obrana OR vláda OR bezpečnosť)",
                 "bg": "(армия OR отбрана OR правителство OR сигурност)", "sr": "(војска OR одбрана OR влада OR безбедност)",
                 "sl": "(vojska OR obramba OR vlada OR varnost)", "lt": "(kariuomenė OR gynyba OR vyriausybė OR saugumas)",
                 "lv": "(armija OR aizsardzība OR valdība OR drošība)", "no": "(forsvaret OR militær OR regjeringen OR sikkerhet)",
                 "ta": "(இராணுவம் OR பாதுகாப்பு OR அரசு)", "te": "(సైన్యం OR రక్షణ OR ప్రభుత్వం OR భద్రత)",
                 "mr": "(लष्कर OR संरक्षण OR सरकार OR सुरक्षा)", "ml": "(സൈന്യം OR പ്രതിരോധം OR സർക്കാർ OR സുരക്ഷ)"}
# Altre lingue e lingue regionali dello stesso Stato: si alternano con la principale
LOCALE_ALTRE = {
    "India": [("ta", "இந்தியா"), ("te", "భారతదేశం"), ("bn", "ভারত"), ("mr", "भारत"), ("ml", "ഇന്ത്യ")],
    "Belgio": [("nl", "België")], "Svizzera": [("fr", "Suisse")], "Canada": [("fr", "Canada")], "Lussemburgo": [("de", "Luxemburg")],
    "Israele": [("ar", "إسرائيل")], "Ucraina": [("ru", "Украина")], "Moldavia": [("ru", "Молдавия")], "Lettonia": [("ru", "Латвия")],
    "Estonia": [("ru", "Эстония")], "Cipro": [("tr", "Kıbrıs")], "Libano": [("fr", "Liban")],
    "Marocco": [("ar", "المغرب")], "Algeria": [("ar", "الجزائر")], "Tunisia": [("ar", "تونس")], "Mauritania": [("ar", "موريتانيا")],
    "Ciad": [("ar", "تشاد")], "Gibuti": [("ar", "جيبوتي")], "Comore": [("ar", "جزر القمر")],
    "Sri Lanka": [("ta", "இலங்கை")], "Singapore": [("zh", "新加坡"), ("ta", "சிங்கப்பூர்")], "Malesia": [("zh", "马来西亚"), ("ta", "மலேசியா")],
    "Bosnia ed Erzegovina": [("sr", "Босна и Херцеговина")], "Kosovo": [("sr", "Косово")],
}
# Lingue senza edizione di Google News: si leggono da GDELT, che le indicizza (nome della lingua per GDELT)
GDELT_LINGUE = {"fa": "persian", "ur": "urdu", "sw": "swahili", "fi": "finnish", "da": "danish", "hr": "croatian", "sq": "albanian",
                "et": "estonian", "ka": "georgian", "hy": "armenian", "az": "azerbaijani", "kk": "kazakh", "mn": "mongolian",
                "ne": "nepali", "si": "sinhalese", "ms": "malay", "so": "somali", "mk": "macedonian", "bs": "bosnian",
                "is": "icelandic", "ca": "catalan", "gl": "galician", "af": "afrikaans", "pa": "punjabi", "gu": "gujarati",
                "kn": "kannada", "bo": "tibetan"}


def lingue_di(stato):
    """Le lingue in cui scrive la stampa di uno Stato (oltre all'inglese): [(lingua, nome dello Stato in quella lingua)]."""
    return ([LOCALE[stato]] if stato in LOCALE else []) + LOCALE_ALTRE.get(stato, [])


def lingua_ok(resa, lg, giro):
    """Una lingua che per tre volte non ha portato nulla (edizione che non risponde) si riprova solo ogni 8 giri."""
    p_, v_ = resa.get(lg, [0, 0])[:2]
    return not (p_ >= 3 and v_ == 0) or giro % 8 == 0
MODELLI_LOCALI = {
    "fr": [("Industria e appalti", '"{n}" (armement OR armes OR défense) (contrat OR livraison OR accord)'),
           ("Proteste e crisi politiche", '"{n}" manifestation OR putsch OR élection OR troubles'),
           ("Basi e truppe all’estero", '"{n}" "base militaire" OR "troupes étrangères" OR "casques bleus"'),
           ("Accordi commerciali e dazi", '"{n}" "accord commercial" OR "droits de douane" OR sanctions OR "libre-échange"')],
    "es": [("Industria e appalti", '"{n}" (armas OR armamento OR defensa) (contrato OR compra OR acuerdo)'),
           ("Proteste e crisi politiche", '"{n}" protestas OR golpe OR elecciones OR disturbios'),
           ("Difesa e forze armate", '"{n}" "fuerzas armadas" OR militares OR ejército'),
           ("Accordi commerciali e dazi", '"{n}" "acuerdo comercial" OR aranceles OR sanciones OR "libre comercio"')],
    "pt": [("Industria e appalti", '"{n}" (armas OR armamento OR defesa) (contrato OR compra OR acordo)'),
           ("Proteste e crisi politiche", '"{n}" protestos OR golpe OR eleições'),
           ("Accordi commerciali e dazi", '"{n}" "acordo comercial" OR tarifas OR sanções OR "livre comércio"')],
    "ar": [("Industria e appalti", '"{n}" (أسلحة OR تسليح OR صفقة) (الدفاع OR الجيش)'),
           ("Proteste e crisi politiche", '"{n}" احتجاجات OR انقلاب OR انتخابات'),
           ("Accordi commerciali e dazi", '"{n}" "اتفاق تجاري" OR "رسوم جمركية" OR عقوبات')],
    "ru": [("Industria e appalti", '"{n}" (вооружение OR оружие OR оборона) (контракт OR поставка OR соглашение)'),
           ("Proteste e crisi politiche", '"{n}" протесты OR переворот OR выборы'),
           ("Accordi commerciali e dazi", '"{n}" "торговое соглашение" OR пошлины OR санкции')],
}

# Domande che il programma si fa da solo sugli Stati meno coperti: (tema, lingua, modello)
MODELLI_RICERCA = [
    ("Difesa e forze armate", "en", '"{en}" "armed forces" OR army OR troops OR military'),
    ("Industria e appalti", "en", '"{en}" (arms OR weapons OR defense) (contract OR deal OR delivery OR procurement)'),
    ("Basi e truppe all’estero", "en", '"{en}" "military base" OR "foreign troops" OR peacekeepers'),
    ("Proteste e crisi politiche", "en", '"{en}" protest OR coup OR election OR unrest'),
    ("Difesa e forze armate", "it", '"{it}" "forze armate" OR esercito OR militari OR "ministro della Difesa"'),
    ("Sicurezza privata e mercenari", "en", '"{en}" mercenaries OR "private military" OR "security contractors"'),
    ("Alleanze e diplomazia", "en", '"{en}" "defense agreement" OR "security pact" OR "military cooperation"'),
    ("Accordi commerciali e dazi", "en", '"{en}" tariffs OR "trade agreement" OR "trade deal" OR sanctions OR "export controls"'),
    ("Ambasciate e relazioni diplomatiche", "en", '"{en}" embassy (opens OR reopens OR closes OR expels OR recalls) OR "diplomatic relations"'),
    ("Tensioni etniche, religiose e sociali", "en", '"{en}" "ethnic minority" OR "religious minority" OR sectarian OR "ethnic tensions" OR inequality'),
]


# Stati che in inglese si chiamano come in italiano, o dove il secondo nome dell'elenco è la capitale
INGLESE = {"Russia": "Russia", "Iran": "Iran", "Taiwan": "Taiwan", "Laos": "Laos", "Eswatini": "Eswatini",
           "Macedonia del Nord": "North Macedonia", "Bosnia ed Erzegovina": "Bosnia and Herzegovina"}


def nome_inglese(nomi):
    if nomi[0] in INGLESE:
        return INGLESE[nomi[0]]
    return next((n for n in nomi[1:] if "." not in n and len(n) > 3), nomi[0])


def wikipedia(lingua, cerca):
    """Prima voce di Wikipedia per una ricerca: titolo, inizio del testo (al massimo 700 caratteri), indirizzo."""
    url = f"https://{lingua}.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "generator": "search", "gsrsearch": cerca, "gsrlimit": "1", "prop": "extracts|info",
        "exintro": "1", "explaintext": "1", "inprop": "url", "redirects": "1", "format": "json"})
    ua = {"User-Agent": "PanGeo/" + VERSIONE + " (https://github.com/54v0B3110CCH1/pangeo; archivio personale, poche richieste)"}
    try:
        r = json.loads(scarica(url, timeout=30, intestazioni=ua))
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        try:
            attesa = min(int(e.headers.get("retry-after") or 5), 20)
        except ValueError:
            attesa = 5
        time.sleep(attesa + 2)  # il sito chiede di aspettare: si aspetta e si riprova una volta sola
        r = json.loads(scarica(url, timeout=30, intestazioni=ua))
    for pag in (r.get("query", {}).get("pages") or {}).values():
        testo = re.sub(r"\s+", " ", pag.get("extract") or "").strip()
        if len(testo) < 150:
            continue
        if len(testo) > 700:
            taglio = testo.rfind(". ", 0, 700)
            testo = testo[: taglio + 1] if taglio > 300 else testo[:700] + "…"
        return {"titolo": pag.get("title", ""), "testo": testo, "url": solo_http(pag.get("fullurl", "")), "lingua": lingua}
    return None


def scrivi_sapere(S_):
    scrivi_json(os.path.join(DATI, "sapere.json"), S_)
    with open(os.path.join(WEB, "sapere.js.tmp"), "w", encoding="utf-8") as f:
        f.write("window.SAPERE = " + json.dumps({k: v for k, v in S_.items() if len(v) > 1}, ensure_ascii=False) + ";\n")
    os.replace(os.path.join(WEB, "sapere.js.tmp"), os.path.join(WEB, "sapere.js"))


def testo_factbook(x):
    """Un campo del World Factbook: testo semplice, oppure più voci (es. la spesa anno per anno)."""
    if not isinstance(x, dict):
        return ""
    if "text" in x:
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(x["text"])))).strip()
    return "; ".join(t for t in (testo_factbook(v) for v in list(x.values())[:3]) if t)


def factbook(percorso):
    """Forze armate e sicurezza di uno Stato dalla copia d'archivio del CIA World Factbook (chiuso il 4 febbraio 2026)."""
    d = json.loads(scarica("https://raw.githubusercontent.com/factbook/factbook.json/master/" + percorso + ".json", timeout=30))
    ms = d.get("Military and Security") or {}
    pezzi = []
    for campo, nome in (("Military and security forces", "Forces"), ("Military and security service personnel strengths", "Personnel"),
                        ("Military expenditures", "Spending"), ("Military equipment inventories and acquisitions", "Equipment"),
                        ("Military service age and obligation", "Service"), ("Military deployments", "Deployments")):
        t = testo_factbook(ms.get(campo))
        if t:
            pezzi.append(nome + ": " + (t if len(t) <= 300 else t[:300].rsplit(" ", 1)[0] + "…"))
    if not pezzi:
        return None
    return {"titolo": "World Factbook, forze armate e sicurezza (copia d'archivio, febbraio 2026)", "testo": " ".join(pezzi)[:1700],
            "url": "https://github.com/factbook/factbook.json/blob/master/" + percorso + ".json", "lingua": "en"}


def sapere(cfg, paesi, errori, adesso):
    """Il programma studia da solo: per pochi Stati a giro legge su Wikipedia (italiano, poi inglese) le voci
    sulle forze armate e sulla storia e, dalla copia d'archivio del World Factbook, la parte su forze armate e
    sicurezza. Tiene titolo, indirizzo e data. Sono fonti per orientarsi, non conferme."""
    imp = cfg.get("sapere", {})
    perc = os.path.join(DATI, "sapere.json")
    if not imp.get("attivo", True):
        return sum(1 for v in leggi_json(perc, {}).values() if len(v) > 1)
    S_ = leggi_json(perc, {})
    if not S_:  # prima volta: parte da ciò che è già nel repository (lo ha preparato Claude), senza rifare le richieste
        try:
            testo = open(os.path.join(DATI, "repo", "sapere.js"), encoding="utf-8").read()
            S_ = json.loads(testo[testo.index("{"):testo.rindex("}") + 1])
            scrivi_json(perc, S_)
        except (OSError, ValueError):
            S_ = {}
    vecchio = (adesso - timedelta(days=imp.get("giorni", 90))).date().isoformat()
    fbm = imp.get("factbook", {})
    da_fare = [x for x in paesi if S_.get(x, {}).get("data", "") < vecchio
               or (x in fbm and "factbook" not in S_.get(x, {}) and "factbook_no" not in S_.get(x, {}))][:imp.get("per_giro", 4)]
    for st_ in da_fare:
        nomi = paesi[st_]
        en = nome_inglese(nomi)
        fresco = S_.get(st_, {}).get("data", "") >= vecchio  # Wikipedia è già stata letta di recente: manca solo il Factbook
        voce = dict(S_[st_]) if fresco else {"data": adesso.date().isoformat()}
        riuscito = True
        radice = re.sub(r"[^a-z]", "", nomi[0].lower())[:5]
        for chiave, q_it, q_en in (() if fresco else (("forze", "forze armate " + nomi[0], en + " armed forces military"),
                                                      ("storia", "storia " + nomi[0], "history of " + en))):
            try:
                for lingua, q_ in (("it", q_it), ("en", q_en)):
                    v = wikipedia(lingua, q_)
                    inizio = (v or {}).get("testo", "")[:400].lower()
                    if v and (radice in re.sub(r"[^a-z]", "", v["titolo"].lower()) or nomi[0].lower() in inizio
                              or en.lower() in inizio or en.lower() in v["titolo"].lower()):
                        voce[chiave] = v
                        break
            except Exception as e:
                errori.append(f"Wikipedia ({st_}): {e}")
                riuscito = False
                break
        if not riuscito:
            break  # il sito non risponde: si riprova al prossimo giro, senza insistere
        if st_ in fbm and "factbook" not in voce:
            try:
                fb_ = factbook(fbm[st_])
                if fb_:
                    voce["factbook"] = fb_
                else:
                    voce["factbook_no"] = adesso.date().isoformat()
            except Exception as e:
                errori.append(f"World Factbook ({st_}): {e}")
        S_[st_] = voce
    if da_fare or (S_ and not os.path.exists(os.path.join(WEB, "sapere.js"))):
        scrivi_sapere(S_)
    return sum(1 for v in S_.values() if len(v) > 1)


# ----------------------------------------------------------------------------- memoria e diario

def memoria_stati(archivio, adesso, cfg, ore=30):
    """La memoria che cresce da sola: per ogni Stato i fatti confermati da più fonti, tenuti 120 giorni
    (al massimo 40 per Stato). È ciò che resta quando le notizie escono dall'archivio di 7 giorni."""
    perc = os.path.join(DATI, "memoria.json")
    M = leggi_json(perc, {})
    da_ = (adesso - timedelta(hours=ore)).isoformat()
    limite = (adesso - timedelta(days=cfg.get("memoria_giorni", 120))).date().isoformat()
    nuovi, visti = 0, set()
    ordine = {"A": 0, "B": 1, "C": 2, "D": 3}
    # prima i fatti con più fonti e, a parità, la fonte di livello migliore: di ogni fatto resta una riga sola
    for v in sorted(archivio["notizie"].values(), key=lambda v: (-(v.get("nf") or 1), ordine.get(v.get("lv"), 3))):
        if not v.get("conf") or (v.get("nf") or 1) < 2 or (v.get("data_iso") or "") < da_:
            continue
        p_ = parole(v.get("it") or v["t"])
        for st_ in v.get("paesi", [])[:3]:
            if (st_, v.get("gr")) in visti:
                continue
            visti.add((st_, v.get("gr")))
            l = M.setdefault(st_, [])
            if any(len(p_ & set(x[5].split())) >= 0.4 * max(len(p_ | set(x[5].split())), 1) for x in l):
                continue  # lo stesso fatto c'è già
            l.append([v["data_iso"][:10], v.get("it") or v["t"], v.get("fonte", ""), v.get("nf") or 1, v.get("u", ""),
                      " ".join(sorted(p_)), v.get("lv", "")])
            nuovi += 1
    for st_ in list(M):
        M[st_] = sorted((x for x in M[st_] if x[0] >= limite), key=lambda x: x[0], reverse=True)[:cfg.get("memoria_per_stato", 40)]
        if not M[st_]:
            del M[st_]
    scrivi_json(perc, M)
    return nuovi, sum(len(l) for l in M.values())


NOMI_TAPPE = {"temi": "ricerche per tema", "stati": "rotazione degli Stati", "ricerca": "ricerca autonoma", "lingue": "giro delle lingue",
              "piano": "lavoro a piano",
              "feed": "feed delle testate", "telegram": "Telegram", "video": "YouTube", "altro": "altro"}


def rapporto(ore=24):
    """Che cosa ha preso il programma nelle ultime ore, quanto, da dove, e dove è migliorato (dal diario)."""
    diario = leggi_json(os.path.join(DATI, "diario.json"), [])
    da_ = (datetime.now(timezone.utc) - timedelta(hours=ore)).isoformat()
    g = [x for x in diario if x.get("iso", "") >= da_]
    if not g:
        print(f"Nessun giro nel diario nelle ultime {ore} ore. Controlla con:  python castello.py salute")
        return
    i0 = diario.index(g[0])
    a, z = (diario[i0 - 1] if i0 else g[0]), g[-1]
    pd = lambda x: round(100 * x["livelli"].get("D", 0) / max(sum(x["livelli"].values()), 1))
    leggeri_ = sum(1 for x in g if x.get("tipo") == "leggero")
    print(f"Diario delle ultime {ore} ore: {len(g)} giri ({len(g) - leggeri_} completi, {leggeri_} leggeri), dal {g[0]['quando']} al {z['quando']} (versione {z['v']})")
    print(f"Voci nuove raccolte: {sum(x['nuove'] for x in g)}")
    da_dove = {}
    for x in g:
        for k, v in x.get("da", {}).items():
            da_dove[k] = da_dove.get(k, 0) + v
    for k, v in sorted(da_dove.items(), key=lambda x: -x[1]):
        print(f"  da {NOMI_TAPPE.get(k, k)}: {v}")
    print(f"Notizie degli ultimi 3 giorni: da {a['live']} a {z['live']} · confermate da più fonti: dal {round(100 * a['quota'])}% al {round(100 * z['quota'])}%")
    print(f"Fonti non classificate (livello D): dal {pd(a)}% al {pd(z)}% delle notizie")
    print(f"Stati senza notizie: da {a['scoperti']} a {z['scoperti']}")
    ora_ = sorted(set(a.get("senza", [])) - set(z.get("senza", [])))
    persi_ = sorted(set(z.get("senza", [])) - set(a.get("senza", [])))
    if ora_:
        print("  ora coperti:", ", ".join(ora_))
    if persi_:
        print("  tornati senza notizie:", ", ".join(persi_))
    print(f"Feed attivi: da {a['fonti'][0]} a {z['fonti'][0]} (su {z['fonti'][1]})")
    fn = [n for x in g for n in x.get("fonti_nuove", [])]
    if fn:
        print("  feed trovati da solo:", ", ".join(fn))
    tg = sorted(set(z.get("tg_trovati", [])) - set(a.get("tg_trovati", [])))
    if tg:
        print("  canali Telegram trovati da solo:", ", ".join(tg))
    print(f"Stati studiati su Wikipedia: da {a.get('sapere', 0)} a {z.get('sapere', 0)} · fatti confermati in memoria: da {a['memoria'][1]} a {z['memoria'][1]}")
    rese = {}
    for x in g:
        for q_, nuove_, prove_, da_chi in (r_[:4] for r_ in x.get("ricerche", [])):
            rese[q_] = max(rese.get(q_, 0), nuove_)
    buone = sorted(rese.items(), key=lambda x: -x[1])[:5]
    if buone:
        print(f"Ricerca autonoma: {len(rese)} domande provate, {sum(1 for v in rese.values() if v)} hanno portato notizie. Le migliori:")
        for q_, n_ in buone:
            if n_:
                print(f"  {n_} notizie: {q_[:80]}")
    sg = [sum(x.get("seguiti", [0, 0])[i] for x in g) for i in (0, 1)]
    vr = [sum(x.get("verifiche", [0, 0])[i] for x in g) for i in (0, 1)]
    print(f"Domande di seguito sui fatti più confermati: {sg[0]}, notizie portate: {sg[1]}")
    print(f"Verifiche attive (notizie di fonti di parte o non classificate): {vr[0]} cercate, {vr[1]} confermate da una fonte affidabile"
          + (" (non trovare conferma non vuol dire che la notizia è falsa)" if vr[0] else ""))
    resa_ = leggi_json(os.path.join(DATI, "ricerche.json"), {}).get("resa", {})
    tipi_ = []
    for m_, (p_, n_) in resa_.items():
        if p_ >= 2:
            if m_[0] == "R" and m_[1:].isdigit() and int(m_[1:]) < len(MODELLI_RICERCA):
                nome_ = MODELLI_RICERCA[int(m_[1:])][0] + " (" + MODELLI_RICERCA[int(m_[1:])][1] + ")"
            else:
                lg_ = m_.rstrip("0123456789")
                j_ = int(m_[len(lg_):] or 0)
                nome_ = (MODELLI_LOCALI.get(lg_, [("?", "")])[j_][0] if j_ < len(MODELLI_LOCALI.get(lg_, [])) else "?") + " (" + lg_ + ")"
            tipi_.append((n_ / p_, nome_, p_))
    if tipi_:
        print("Tipi di domanda che rendono di più (notizie nuove per prova): "
              + " · ".join(f"{nome_} {resa2_:.1f}".replace(".", ",") for resa2_, nome_, p_ in sorted(tipi_, reverse=True)[:5]))
    rif = {}
    for x in g:
        for k, v in x.get("rifiuti", {}).items():
            rif[k] = rif.get(k, 0) + v
    print(f"Richieste ai siti: {sum(x['richieste'] for x in g)} in tutto, {round(sum(x['richieste'] for x in g) / len(g))} per giro · "
          f"rifiuti per troppe richieste: {sum(rif.values())}" + (" (" + ", ".join(f"{k} {v}" for k, v in rif.items()) + ")" if rif else ""))
    print(f"Durata media di un giro: {round(sum(x['durata'] for x in g) / len(g) / 60)} minuti · avvisi per giro: {round(sum(x['errori'] for x in g) / len(g), 1)}")
    print(f"Titoli tradotti in archivio: {z.get('tradotti', 0)} · spesa del cervello: oggi {z.get('usd_oggi', 0):.4f} $, questo mese {z.get('usd_mese', 0):.4f} $")
    if len(g) < 2:
        print("Per vedere dove migliora servono almeno due giri: riprova più tardi.")


CHIAVI_NO = set("""yesterday today tomorrow monday tuesday wednesday thursday friday saturday sunday january february
march april june july august september october november december announcement statement joint breaking report
reports according latest watch read full minister ministry president government official officials spokesman
oggi ieri domani lunedì martedì mercoledì giovedì venerdì sabato domenica gennaio febbraio marzo aprile maggio
giugno luglio agosto settembre ottobre novembre dicembre nonostante secondo governo ministro ministero presidente
telegram video foto""".split())


def parole_chiave(titolo, escludi=(), quante=4):
    """Le parole che distinguono un titolo: prima nomi propri e numeri, poi le più lunghe."""
    escl = {w for e in escludi for w in re.findall(r"[^\W_]+", e.lower())} | CHIAVI_NO
    viste, proprie, altre = set(), [], []
    for i, w in enumerate(re.findall(r"[^\W_]{3,}", titolo or "")):
        wl = w.lower()
        if wl in viste or wl in STOP or wl in escl or (len(w) < 4 and not w.isdigit()):
            continue
        viste.add(wl)
        (proprie if (w[0].isupper() and i > 0) or w.isdigit() else altre).append(w)
    altre.sort(key=len, reverse=True)
    return (proprie + altre)[:quante]


TEMI_TRIAGE = {"G": "Conflitti e guerre", "D": "Difesa e forze armate", "I": "Industria e appalti",
               "A": "Alleanze e diplomazia", "C": "Accordi commerciali e dazi",
               "S": "Terrorismo, spionaggio e attacchi informatici", "P": "Proteste e crisi politiche",
               "T": "Tensioni etniche, religiose e sociali", "O": "OMS, Interpol e organismi internazionali"}


def lingua_titolo(t):
    n = " " + (t or "").lower() + " "
    n = re.sub(r"[^\w\s’']", " ", n).replace("’", "' ").replace("'", "' ")
    it = sum(n.count(w) for w in (" il ", " la ", " di ", " che ", " per ", " del ", " della ", " con ", " gli ", " dei ", " nel ",
                                  " i ", " e ", " le ", " un ", " una ", " non ", " si ", " da ", " al ", " alla ", " è ", " l' "))
    en = sum(n.count(w) for w in (" the ", " of ", " and ", " to ", " for ", " with ", " says ", " after ", " over ", " as ",
                                  " is ", " on ", " at ", " by ", " from ", " its ", " has "))
    if it == en:
        return "it" if re.search(r"[àèéìòù]", n) else "en"
    return "it" if it > en else "en"


# ----------------------------------------------------------------------------- lavoro a piano

# Le due domande di base del lavoro a piano, per lingua: (accordi e patti, appalti e contratti). {n} = nome dello Stato.
PIANO_Q = {
    "en": ('"{n}" ("defense agreement" OR "defence agreement" OR "security pact" OR "defense pact" OR "military cooperation" OR treaty OR alliance) (signs OR signed OR ratifies OR ratified OR joins OR withdraws OR suspends)',
           '"{n}" (contract OR order OR deal OR procurement OR purchase) (fighter OR jets OR tanks OR missiles OR frigates OR submarines OR drones OR helicopters OR "air defense" OR artillery OR ammunition)'),
    "it": ('"{n}" ("accordo di difesa" OR "accordo di sicurezza" OR "cooperazione militare" OR trattato OR alleanza OR patto) (firma OR firmato OR ratifica OR aderisce OR sospende OR esce)',
           '"{n}" (contratto OR commessa OR acquisto OR fornitura OR ordine) (caccia OR carri OR missili OR fregate OR sottomarini OR droni OR elicotteri OR munizioni OR "difesa aerea")'),
    "fr": ('"{n}" ("accord de défense" OR "accord de sécurité" OR "coopération militaire" OR traité OR alliance) (signe OR signé OR ratifie OR rejoint OR suspend OR quitte)',
           '"{n}" (contrat OR commande OR achat OR acquisition) ("avions de combat" OR chars OR missiles OR frégates OR "sous-marins" OR drones OR hélicoptères OR munitions)'),
    "es": ('"{n}" ("acuerdo de defensa" OR "acuerdo de seguridad" OR "cooperación militar" OR tratado OR alianza) (firma OR firmó OR ratifica OR adhiere OR suspende OR abandona)',
           '"{n}" (contrato OR compra OR adquisición OR pedido) (cazas OR tanques OR misiles OR fragatas OR submarinos OR drones OR helicópteros OR municiones)'),
    "pt": ('"{n}" ("acordo de defesa" OR "acordo de segurança" OR "cooperação militar" OR tratado OR aliança) (assina OR assinou OR ratifica OR adere OR suspende)',
           '"{n}" (contrato OR compra OR aquisição OR encomenda) (caças OR tanques OR mísseis OR fragatas OR submarinos OR drones OR helicópteros OR munições)'),
    "de": ('"{n}" (Verteidigungsabkommen OR Sicherheitsabkommen OR Militärkooperation OR Bündnis OR Staatsvertrag) (unterzeichnet OR ratifiziert OR beigetreten OR gekündigt OR ausgesetzt)',
           '"{n}" (Auftrag OR Vertrag OR Beschaffung OR Bestellung) (Kampfjets OR Panzer OR Raketen OR Fregatten OR "U-Boote" OR Drohnen OR Hubschrauber OR Flugabwehr OR Munition)'),
    "ru": ('"{n}" ("соглашение об обороне" OR "военное сотрудничество" OR "договор о безопасности" OR союз) (подписал OR подписали OR ратифицировал OR присоединился OR приостановил)',
           '"{n}" (контракт OR поставка OR закупка) (истребители OR танки OR ракеты OR фрегаты OR "подводные лодки" OR беспилотники OR вертолёты OR боеприпасы)'),
    "ar": ('"{n}" ("اتفاقية دفاع" OR "اتفاق أمني" OR "تعاون عسكري" OR معاهدة OR تحالف) (توقع OR وقعت OR تصادق OR تنضم OR تعلق)',
           '"{n}" (صفقة OR عقد OR شراء) (مقاتلات OR دبابات OR صواريخ OR فرقاطات OR غواصات OR "طائرات مسيرة" OR مروحيات OR ذخائر)'),
}
PIANO_STATI_ACCORDO = ("firmato", "ratificato", "in vigore", "in trattativa", "annunciato", "sospeso", "disdetto")
PIANO_STATI_APPALTO = ("firmato", "in consegna", "consegnato", "approvato", "in trattativa", "annunciato", "annullato")


def piano_ordine(cfg, paesi):
    """L'ordine del lavoro a piano: blocco per blocco (prima l'Europa), Stato per Stato. Sta in config.json › piano › blocchi."""
    visti, ordine = set(), []
    for blocco in cfg.get("piano", {}).get("blocchi", []):
        if not isinstance(blocco, list) or len(blocco) != 2:
            continue
        for s in blocco[1]:
            if s in paesi and s not in visti:
                visti.add(s)
                ordine.append((blocco[0], s))
    for s in sorted(paesi):
        if s not in visti:
            ordine.append(("Altri Stati", s))
    return ordine


def _nome_in_lingua(stato, lingua, paesi):
    loc = LOCALE.get(stato)
    if loc and loc[0] == lingua:
        return loc[1]
    return paesi[stato][0] if lingua == "it" else nome_inglese(paesi[stato])


def _piano_titoli(domande, giorni, errori, pausa=1.0):
    """Fa le domande a Google News e mette insieme i titoli, senza doppioni. Restituisce i titoli, le domande con quanti
    titoli ha portato ognuna, e quante domande sono fallite."""
    titoli, visti, fatte, fallite = [], set(), [], 0
    for tipo, lingua, q in domande:
        n0 = len(titoli)
        try:
            for t_, u_, d_, f_, _s in google_news(q, lingua if lingua in EDIZIONI else "en", giorni)[:45]:
                chiave = re.sub(r"\W+", " ", (t_ or "").lower()).strip()[:90]
                if len(chiave) < 12 or chiave in visti or RUMORE.search(" " + (f_ or "") + " ") or APPRESI.get(f_) == "scarto":
                    continue
                visti.add(chiave)
                titoli.append({"t": pulisci(t_, 240), "u": solo_http(u_), "iso": d_ or "", "d": (d_ or "")[:10], "f": f_ or "", "k": tipo, "l": lingua})
        except SenzaRete:
            raise
        except Exception as e:
            fallite += 1
            errori.append(f"Lavoro a piano ({q[:40]}): {e}")
        fatte.append([tipo, lingua, q, len(titoli) - n0])
        time.sleep(pausa)
    return titoli, fatte, fallite


def _piano_domanda(stato, titoli, giorni, noti):
    righe = "\n".join(f"{i + 1}. {x['d'] or 'senza data'} – {x['t']} – {x['f']}" for i, x in enumerate(titoli))
    gia = ("\nGIÀ IN ARCHIVIO per " + stato + " (non ripeterli, a meno che un titolo dica che qualcosa è cambiato):\n"
           + "\n".join("· " + n for n in noti[:14]) + "\n") if noti else ""
    return (f"Lavori a un archivio pubblico di difesa e geopolitica. Qui sotto ci sono titoli di giornale su {stato} degli ultimi "
            f"{giorni} giorni (numero. data – titolo – fonte), in lingue diverse. Usa SOLO quello che dicono i titoli: non "
            "aggiungere nulla che sai per conto tuo, e se un titolo non è chiaro lascialo stare.\n\n"
            f"PARTE 1, ACCORDI: alleanze, patti, trattati e accordi militari o di sicurezza che riguardano {stato}. Una riga per accordo:\n"
            "A | data | con chi | che cosa, in una frase in italiano | stato | numeri dei titoli\n"
            "dove «stato» è una di queste parole: " + ", ".join(PIANO_STATI_ACCORDO) + ".\n\n"
            f"PARTE 2, APPALTI: contratti, ordini, acquisti e vendite di armamenti in cui {stato} compra o vende. Una riga per contratto:\n"
            "C | data | chi compra | chi vende (azienda e Stato, se sono scritti) | che cosa, in italiano, con le quantità se sono "
            "scritte | valore, oppure - | stato | numeri dei titoli\n"
            "dove «stato» è una di queste parole: " + ", ".join(PIANO_STATI_APPALTO) + ".\n\n"
            "PARTE 3, DOMANDE: fino a 2 cose che i titoli lasciano aperte e che conviene cercare (per esempio se un contratto "
            "annunciato è poi stato firmato, o se un accordo è stato ratificato). Una riga per domanda:\n"
            "D | lingua in cui cercare (it, en, oppure la sigla della lingua del posto) | da 3 a 7 parole da cercare, senza "
            "virgolette | che cosa vuoi sapere, in italiano\n\n"
            "Regole. La data è quella del titolo più recente che ne parla, scritta AAAA-MM-GG. Lo stesso fatto una volta sola: se ne "
            "parlano più titoli, metti tutti i loro numeri. Niente giudizi, niente previsioni, niente dettagli operativi. Se un "
            "titolo riporta un'accusa o una voce, scrivi «secondo» e chi lo dice. Le notizie che non sono né accordi né appalti "
            "ignorale. Se una parte è vuota scrivi «A | nessuno» oppure «C | nessuno». Scrivi solo le righe, senza titoli e senza "
            "commenti.\n" + gia + "\nTITOLI\n" + righe)


def _piano_fonti(testo, titoli, massimo=4):
    """I numeri dei titoli citati dal cervello diventano fonti vere: [testata, indirizzo, data, titolo]."""
    presi = []
    for x in re.findall(r"\d+", testo or ""):
        i = int(x)
        if 0 < i <= len(titoli) and i not in presi:
            presi.append(i)
    return [[titoli[i - 1]["f"], titoli[i - 1]["u"], titoli[i - 1]["d"], titoli[i - 1]["t"][:160]] for i in presi[:massimo]]


def _piano_leggi(risposta, titoli):
    """Legge le righe del cervello: «A | …» accordi, «C | …» appalti, «D | …» domande aperte. Una riga senza il numero di
    almeno un titolo vero viene scartata: nell'archivio entra solo ciò che ha una fonte."""
    def data_di(testo, fonti):
        m = re.search(r"(19|20)\d\d-\d\d-\d\d", testo or "")
        return m.group(0) if m else max((f[2] for f in fonti if f[2]), default="")

    def stato_di(testo, ammessi):
        t = (testo or "").lower().strip(" .")
        return next((a for a in sorted(ammessi, key=len, reverse=True) if a in t), "annunciato" if t else "")

    accordi, appalti, domande_ = [], [], []
    for riga in (risposta or "").splitlines():
        p = [x.strip(" *`") for x in riga.strip().lstrip("-•* ").split("|")]
        sigla = p[0].upper().strip(" .:)") if p else ""
        if sigla == "A" and len(p) >= 6:
            fonti = _piano_fonti(p[5], titoli)
            if fonti and len(p[3]) > 8:
                accordi.append({"d": data_di(p[1], fonti), "con": pulisci(p[2], 120), "cosa": pulisci(p[3], 300),
                                "st": stato_di(p[4], PIANO_STATI_ACCORDO), "f": fonti})
        elif sigla == "C" and len(p) >= 8:
            fonti = _piano_fonti(p[7], titoli)
            if fonti and len(p[4]) > 5:
                appalti.append({"d": data_di(p[1], fonti), "acq": pulisci(p[2], 80), "forn": pulisci(p[3], 120),
                                "ogg": pulisci(p[4], 300), "val": "" if p[5].strip(" -–—") == "" else pulisci(p[5], 60),
                                "st": stato_di(p[6], PIANO_STATI_APPALTO), "f": fonti})
        elif sigla == "D" and len(p) >= 4:
            q = " ".join(re.sub(r'[<>{}\\"«»()]|https?:\S*', " ", p[2]).split())
            if 2 <= len(q.split()) <= 9 and len(q) <= 110:
                domande_.append({"l": re.sub(r"[^a-zA-Z-]", "", p[1])[:5].lower() or "en", "q": q, "perche": pulisci(p[3], 200)})
    return accordi, appalti, domande_[:2]


def _piano_unisci(vecchi, nuovi, campo, massimo=30):
    """Aggiunge i fatti nuovi a quelli delle passate precedenti, senza doppioni; in cima i più recenti."""
    def firma(x):
        return re.sub(r"\W+", " ", (x.get(campo) or "").lower()).strip()[:60]
    visti = {firma(x) for x in nuovi}
    tutti = nuovi + [x for x in (vecchi or []) if firma(x) not in visti]
    return sorted(tutti, key=lambda x: x.get("d") or "", reverse=True)[:massimo]


def passo_piano(cfg, chiavi, paesi, leggero, errori, notizia=None):
    """Lavoro a piano (dentro il giro, non un secondo ciclo): uno Stato alla volta, blocco per blocco a partire dall'Europa.
    Per ogni Stato: tre domande sulla stampa (accordi e patti, appalti e contratti, e una nella lingua del posto), poi il
    cervello legge i titoli, tira fuori accordi e appalti ognuno con le sue fonti, e scrive che cosa resta da chiarire.
    Le domande rimaste aperte vengono fatte nei giri dopo. Finiti tutti gli Stati ricomincia: la seconda passata aggiorna.
    Restituisce [Stati lavorati in questo giro, accordi trovati, appalti trovati]."""
    imp = cfg.get("piano", {})
    perc = os.path.join(DATI, "piano.json")
    P = leggi_json(perc, {})
    adesso = datetime.now(timezone.utc)
    for campo, valore in (("stati", {}), ("i", 0), ("passata", 1), ("inizio", adesso.isoformat()), ("ultimi", [])):
        P.setdefault(campo, valore)
    ordine = piano_ordine(cfg, paesi)
    if not ordine or P.get("riposo", "") > adesso.isoformat():
        return [0, 0, 0]  # dopo un rifiuto di Google News (429) il piano riposa tre quarti d'ora
    base = leggi_json(os.path.join(QUI, "piano_base.json"), {})
    giorni, imp_c = imp.get("giorni", 120), cfg.get("cervello", {})
    con_cervello = bool(chiavi.get("anthropic_key")) and imp_c.get("attivo", True)
    conto = _conto_cervello()
    fatti = n_acc = n_app = 0
    try:
        for _ in range(imp.get("per_giro_leggero", 1) if leggero else imp.get("per_giro_completo", 3)):
            if con_cervello and not _cervello_libero(conto, imp_c):
                break  # il cervello ha toccato un tetto: il piano lo aspetta, senza saltare Stati
            blocco, stato = ordine[P["i"] % len(ordine)]
            loc = LOCALE.get(stato)
            lg = loc[0] if loc and loc[0] in PIANO_Q else None
            en = nome_inglese(paesi[stato])
            dom = [("accordi", "en", PIANO_Q["en"][0].format(n=en)), ("appalti", "en", PIANO_Q["en"][1].format(n=en))]
            # terza domanda nella lingua del posto (in italiano dove non c'è): una passata gli appalti, quella dopo gli accordi
            tipo_l = "appalti" if P["passata"] % 2 else "accordi"
            dom.append((tipo_l, lg or "it", PIANO_Q[lg or "it"][1 if tipo_l == "appalti" else 0].format(n=loc[1] if lg else paesi[stato][0])))
            vecchio = P["stati"].get(stato, {})
            dom += [("aperta", d["l"], d["q"] if _nome_in_lingua(stato, d["l"], paesi).lower() in d["q"].lower()
                     else '"%s" %s' % (_nome_in_lingua(stato, d["l"], paesi), d["q"]))
                    for d in vecchio.get("aperte", []) if not d.get("fatta")][:1]
            titoli, fatte, fallite = _piano_titoli(dom, giorni, errori, imp.get("pausa", 1.0))
            if fallite and any("429" in e for e in errori[-fallite:]):
                P["riposo"] = (adesso + timedelta(minutes=45)).isoformat()  # Google News sta rifiutando: basta per ora
            if fallite >= len(dom):
                break  # Google News non risponde: si riprova più tardi, dallo stesso Stato
            titoli.sort(key=lambda x: x["iso"], reverse=True)
            titoli = titoli[:imp.get("titoli_max", 70)]
            if notizia:  # i titoli della settimana entrano anche tra le notizie dal vivo
                for x in (y for y in titoli if y["iso"]):
                    notizia("Industria e appalti" if x["k"] == "appalti" else "Alleanze e diplomazia", x["t"], x["u"], x["iso"],
                            x["f"], forza=stato, lingua=x["l"])
            scheda = {"blocco": blocco, "quando": adesso.isoformat(), "passata": P["passata"], "titoli": len(titoli), "domande": fatte,
                      "accordi": vecchio.get("accordi", []), "appalti": vecchio.get("appalti", []), "aperte": [],
                      "risposte": vecchio.get("risposte", [])[-6:], "cervello": False}
            if titoli and con_cervello:
                b_ = base.get(stato, {})
                noti = [str(x) for x in b_.get("tr", []) + b_.get("ap", [])] + \
                       [x["cosa"] for x in vecchio.get("accordi", [])[:6]] + [x["ogg"] for x in vecchio.get("appalti", [])[:6]]
                try:
                    risposta = chiedi_claude(chiavi, cfg, _piano_domanda(stato, titoli, giorni, noti), 2500, conto)
                    conto["chiamate"] = conto.get("chiamate", 0) + 1
                except Exception as e:
                    errori.append("Claude (lavoro a piano): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:160])
                    break  # il cervello non ha risposto: stesso Stato al prossimo giro
                acc, app, aperte = _piano_leggi(risposta, titoli)
                scheda.update({"accordi": _piano_unisci(vecchio.get("accordi"), acc, "cosa"),
                               "appalti": _piano_unisci(vecchio.get("appalti"), app, "ogg"), "aperte": aperte, "cervello": True})
                scheda["nuovi"] = [len(acc), len(app)]
                n_acc, n_app = n_acc + len(acc), n_app + len(app)
            elif titoli:  # senza cervello: restano i titoli da leggere a mano, divisi per domanda
                scheda["da_leggere"] = [[x["t"], x["u"], x["f"], x["d"], x["k"]] for x in titoli[:16]]
            P["stati"][stato] = scheda
            P["ultimi"] = ([s for s in P["ultimi"] if s != stato] + [stato])[-40:]
            P["i"] += 1
            if P["i"] >= len(ordine):
                P["i"], P["passata"] = 0, P["passata"] + 1
            fatti += 1
        # domande rimaste aperte: il cervello le aveva scritte leggendo i titoli; qui si cercano e si risponde
        for _ in range(imp.get("seguiti_per_giro", 1) if con_cervello else 0):
            if not _cervello_libero(conto, imp_c) or P.get("riposo", "") > adesso.isoformat():
                break
            scelta = next(((s, d) for s in P["ultimi"] for d in P["stati"].get(s, {}).get("aperte", [])
                           if not d.get("fatta") and s in paesi and P["stati"][s].get("quando") != adesso.isoformat()), None)
            if not scelta:
                break
            stato, d = scelta
            nome = _nome_in_lingua(stato, d["l"], paesi)
            q = d["q"] if nome.lower() in d["q"].lower() else '"%s" %s' % (nome, d["q"])
            titoli, _fatte, fallite = _piano_titoli([("aperta", d["l"], q)], giorni, errori, imp.get("pausa", 1.0))
            if fallite:
                if "429" in errori[-1]:
                    P["riposo"] = (adesso + timedelta(minutes=45)).isoformat()
                break
            d["fatta"] = adesso.isoformat()
            titoli = sorted(titoli, key=lambda x: x["iso"], reverse=True)[:30]
            esito = {"q": q, "l": d["l"], "perche": d.get("perche", ""), "n": len(titoli), "quando": adesso.isoformat(),
                     "r": "nessun titolo trovato", "f": []}
            if titoli:
                try:
                    risposta = chiedi_claude(chiavi, cfg, (
                        f"Domanda su {stato}: {d.get('perche') or d['q']}\nTitoli trovati cercando «{q}» (numero. data – titolo – "
                        "fonte):\n" + "\n".join(f"{i + 1}. {x['d'] or 'senza data'} – {x['t']} – {x['f']}" for i, x in enumerate(titoli))
                        + "\n\nRispondi in italiano con una riga sola, usando SOLO quello che dicono i titoli, senza giudizi:\n"
                          "R | risposta in una o due frasi | numeri dei titoli usati\n"
                          "Se i titoli non bastano per rispondere scrivi: R | i titoli non bastano | -"), 500, conto)
                    conto["chiamate"] = conto.get("chiamate", 0) + 1
                    for riga in risposta.splitlines():
                        p = [x.strip(" *`") for x in riga.strip().lstrip("-•* ").split("|")]
                        if len(p) >= 2 and p[0].upper().strip(" .:") == "R" and len(p[1]) > 5:
                            esito["r"], esito["f"] = pulisci(p[1], 400), _piano_fonti(p[2] if len(p) > 2 else "", titoli, 3)
                            break
                    else:
                        esito["r"] = "i titoli non bastano"
                except Exception as e:
                    errori.append("Claude (domanda aperta del piano): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:160])
                    d.pop("fatta", None)
                    break
            P["stati"][stato].setdefault("risposte", []).append(esito)
            P["stati"][stato]["risposte"] = P["stati"][stato]["risposte"][-6:]
    except SenzaRete:
        errori.append("rete assente: lavoro a piano interrotto, riprende dallo stesso Stato")
    P["agg"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    scrivi_json(perc, P)
    scrivi_json(os.path.join(DATI, "cervello.json"), conto)
    try:
        with open(os.path.join(WEB, "piano.js.tmp"), "w", encoding="utf-8") as f:
            f.write("window.PIANO=" + json.dumps({"agg": P["agg"], "passata": P["passata"], "i": P["i"], "totale": len(ordine),
                                                  "blocchi": cfg.get("piano", {}).get("blocchi", []), "ultimi": P["ultimi"],
                                                  "stati": P["stati"]}, ensure_ascii=False, separators=(",", ":")) + ";")
        os.replace(os.path.join(WEB, "piano.js.tmp"), os.path.join(WEB, "piano.js"))
    except OSError:
        pass
    return [fatti, n_acc, n_app]


def piano_riassunto(cfg, paesi):
    """Il lavoro a piano in breve, per la pagina (live.json) e per i comandi «piano» e «domande»."""
    P = leggi_json(os.path.join(DATI, "piano.json"), {})
    ordine = piano_ordine(cfg, paesi)
    if not P.get("stati") or not ordine:
        return None
    i = P.get("i", 0) % len(ordine)
    S = P["stati"]
    ult = [s for s in reversed(P.get("ultimi", [])) if s in S]
    return {"agg": P.get("agg", ""), "passata": P.get("passata", 1), "i": i, "totale": len(ordine), "blocco": ordine[i][0],
            "prossimi": [s for _, s in ordine[i:i + 6]], "con_scheda": len(S),
            "accordi": sum(len(v.get("accordi", [])) for v in S.values()), "appalti": sum(len(v.get("appalti", [])) for v in S.values()),
            "ultimi": [[s, S[s].get("quando", ""), len(S[s].get("accordi", [])), len(S[s].get("appalti", [])), S[s].get("titoli", 0),
                        S[s].get("blocco", "")] for s in ult[:10]],
            "domande": [[s] + list(d) for s in ult[:5] for d in S[s].get("domande", [])][:16],
            "aperte": [[s, d.get("l", ""), d.get("q", ""), d.get("perche", ""), bool(d.get("fatta"))] for s in ult[:12]
                       for d in S[s].get("aperte", [])][:12],
            "risposte": sorted(([s, r.get("perche") or r.get("q", ""), r.get("r", ""), r.get("f", []), r.get("quando", "")]
                                for s in ult for r in S[s].get("risposte", [])), key=lambda x: x[4], reverse=True)[:8]}


TIPI_DOMANDA = {"programma": "domanda di base su uno Stato poco coperto", "seguito": "nata da un fatto confermato da più fonti, per saperne di più",
                "verifica": "cerca se una fonte affidabile conferma una notizia di una fonte debole",
                "cervello": "proposta dal cervello nel rapporto del giorno"}


def domande():
    """Le domande che il programma si fa: quelle dell'ultimo giro completo, quelle del lavoro a piano, quelle rimaste aperte."""
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    paesi = leggi_json(os.path.join(QUI, "paesi.json"), {})
    R = leggi_json(os.path.join(DATI, "ricerche.json"), {})
    print("LE DOMANDE CHE PANGEO SI FA")
    print("\n1. Nell'ultimo giro completo (le cerca su Google News; il numero è quante notizie nuove ha portato):")
    for x in R.get("ultime", []):
        print(f"   [{x[3] or 'programma'}] {x[0]}  →  {x[1]}" + (f"   ({x[4]})" if len(x) > 4 and x[4] else ""))
    if not R.get("ultime"):
        print("   ancora nessuna: le scrive il primo giro completo.")
    print("   Tipi: " + "; ".join(f"{k} = {v}" for k, v in TIPI_DOMANDA.items()) + ".")
    coda = [x for x in R.get("code", []) if x.get("da") == "cervello"]
    if coda:
        print("\n2. Proposte dal cervello (provate / notizie nuove):")
        for x in coda[-8:]:
            print(f"   [{x.get('l', '')}] {x['q']}  →  {x.get('prove', 0)} / {x.get('nuove', 0)}")
    rs = piano_riassunto(cfg, paesi)
    print("\n3. Lavoro a piano (alleanze, patti, appalti):")
    if not rs:
        print("   non ancora partito: comincia al prossimo giro.")
    else:
        nomi_ = {"accordi": "accordi e patti", "appalti": "appalti e contratti", "aperta": "domanda rimasta aperta"}
        for d in rs["domande"]:
            print(f"   {d[0]} · {nomi_.get(d[1], d[1])}, lingua {d[2]}  →  {d[4]} titoli\n      {d[3]}")
        if rs["aperte"]:
            print("\n4. Domande che il cervello ha lasciato aperte leggendo i titoli:")
            for s, l, q, perche, fatta in rs["aperte"]:
                print(f"   {s} [{l}] {q} — {perche}" + ("  (già cercata)" if fatta else "  (da cercare)"))
        if rs["risposte"]:
            print("\n5. Risposte trovate:")
            for s, perche, r, fonti, _q in rs["risposte"]:
                print(f"   {s}: {perche}\n      → {r}" + (" (" + ", ".join(f[0] for f in fonti) + ")" if fonti else ""))
    resa = R.get("resa", {})
    if resa:
        migliori = sorted(((v[1] / v[0], k, v) for k, v in resa.items() if v[0]), reverse=True)[:5]
        print("\nI tipi di domanda che rendono di più (notizie nuove per prova): "
              + ", ".join(f"{k} {m:.1f}" for m, k, _ in migliori))


def cmd_piano():
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    paesi = leggi_json(os.path.join(QUI, "paesi.json"), {})
    rs = piano_riassunto(cfg, paesi)
    ordine = piano_ordine(cfg, paesi)
    if not rs:
        print(f"Lavoro a piano non ancora partito: {len(ordine)} Stati in {len(cfg.get('piano', {}).get('blocchi', []))} blocchi, "
              "comincia al prossimo giro" + (f" da {ordine[0][1]}." if ordine else "."))
        return
    print(f"LAVORO A PIANO – passata {rs['passata']}: {rs['i']} Stati su {rs['totale']} · ora nel blocco «{rs['blocco']}»")
    print(f"Trovati finora: {rs['accordi']} accordi e patti, {rs['appalti']} appalti e contratti, in {rs['con_scheda']} Stati.")
    print("Prossimi:", ", ".join(rs["prossimi"]))
    print("Ultimi lavorati (accordi / appalti / titoli letti):")
    for s, _q, a, c, t, _b in rs["ultimi"]:
        print(f"   {s:<24} {a:>3} / {c:>3} / {t:>3}")
    print("Per vedere le domande:  python castello.py domande")


def _tieni_sveglio():
    """Sul telefono: tiene sveglio Termux e riaccende il giro automatico (cron) se si era fermato."""
    try:
        if shutil.which("termux-wake-lock"):
            _esegui(["termux-wake-lock"], 15)
        if shutil.which("crond") and _cron_vivo() is False:
            subprocess.run(["crond"], check=False, timeout=15)
    except (OSError, subprocess.SubprocessError):
        pass


def _avvio_al_riavvio():
    """Con l'app Termux:Boot installata, PanGeo riparte da solo quando il telefono si riaccende.
    Senza quell'app il file resta lì e non fa nulla."""
    casa = os.path.expanduser("~/.termux")
    if not os.path.isdir(casa):
        return
    try:
        os.makedirs(os.path.join(casa, "boot"), exist_ok=True)
        perc = os.path.join(casa, "boot", "pangeo.sh")
        with open(perc, "w", encoding="utf-8") as f:
            f.write("#!/data/data/com.termux/files/usr/bin/sh\n# PanGeo: riparte dopo il riavvio del telefono (lo scrive castello.py serve)\n"
                    "termux-wake-lock\ncrond\ncd %s && %s castello.py veglia zitto >> dati/log.txt 2>&1\n" % (shlex.quote(QUI), shlex.quote(sys.executable)))
        os.chmod(perc, 0o700)
    except OSError:
        pass


ORDINE_TAPPE = ["ricerche sui 16 temi (Google News, GDELT)", "Stati meno coperti, prima nella loro lingua e poi in inglese",
                "domande che si pone da solo, domande di seguito, verifiche", "ogni Stato nella sua lingua e giro delle lingue",
                "lavoro a piano: alleanze, patti e appalti, uno Stato alla volta (prima l'Europa)",
                "feed delle testate", "canali Telegram", "canali YouTube", "studio degli Stati (Wikipedia, World Factbook)",
                "cielo e calore da satellite", "ricerca di fonti nuove e di sostituti", "analisi: livelli, conferme, segnali",
                "cervello: traduzioni in italiano e riassunto", "memoria, diario, pagina", "invio a GitHub"]


def giri(quanti=12):
    """Quanti giri fa, ogni quanto, quanto durano e a che punto è quello in corso."""
    diario = leggi_json(os.path.join(DATI, "diario.json"), [])
    try:
        tab = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    except OSError:
        tab = ""
    riga = next((r for r in tab.splitlines() if "castello.py aggiorna" in r and not r.strip().startswith("#")), "")
    ora = datetime.now()
    campi = riga.split()[:5]
    if riga and campi[0].replace(",", "").isdigit() and campi[1] in ("*", "*/3"):
        minuti_, ogni3 = sorted(int(x) for x in campi[0].split(",")), campi[1] == "*/3"
        pross = min(t for t in (ora.replace(minute=m, second=0, microsecond=0) + timedelta(hours=k) for k in range(0, 5) for m in minuti_)
                    if t > ora and (not ogni3 or t.hour % 3 == 0))
        ai = ("al minuto " if len(minuti_) == 1 else "ai minuti ") + ", ".join(str(m) for m in minuti_)
        print((f"Giro automatico: uno ogni {60 // len(minuti_)} minuti ({ai}): {24 * len(minuti_)} al giorno. Ogni 3 ore è un giro completo "
               "(ricerche comprese), gli altri sono giri leggeri (feed, Telegram, YouTube, cielo)." if not ogni3 else
               "Giro automatico: uno ogni 3 ore, al minuto 17 (0:17, 3:17, 6:17 … 21:17), 8 al giorno.")
              + f" Prossimo: {pross.strftime('%H:%M')}"
              + ("" if _cron_vivo() else "  ATTENZIONE: il giro automatico è FERMO, lancia  bash avvia.sh"))
    elif riga:
        print("Giro automatico programmato così:", " ".join(riga.split()[:5]))
    else:
        print("Giro automatico NON programmato su questo dispositivo (bash installa.sh).")
    try:
        interno = subprocess.run(["pgrep", "-f", "castello.py serve"], capture_output=True).returncode == 0
    except OSError:
        interno = None
    if interno is not None:
        print("Orologio interno (fa partire i giri anche se cron si ferma):", "acceso" if interno else "SPENTO: lancia  bash avvia.sh")
    def _ora(iso_):
        try:
            return datetime.fromisoformat(iso_).astimezone().strftime("%d/%m %H:%M")
        except (ValueError, TypeError):
            return "?"
    fermi_ = leggi_json(os.path.join(DATI, "fermi.json"), [])
    if fermi_:
        print("Le ultime volte che si è fermato:")
        for f_ in fermi_[-4:]:
            print(f"   dal {_ora(f_.get('dal'))} al {_ora(f_.get('al'))} ({f_.get('minuti', '?')} minuti): {f_.get('motivo', '')}")
    ieri_s = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    sosp_ = [x for x in (leggi_json(os.path.join(DATI, "battito.json"), {}).get("sosp") or []) if x[0] > ieri_s]
    if sosp_:
        print(f"Nelle ultime 24 ore Android ha messo in pausa Termux {len(sosp_)} volte, per {round(sum(x[1] for x in sosp_) / 60)} minuti in tutto"
              " (batteria di Termux su «Senza restrizioni» e Termux aperto tra le app recenti lo evitano).")
    blocco = os.path.join(DATI, "aggiorna.lock")
    pr = leggi_json(os.path.join(DATI, "progresso.json"), {})
    try:
        in_corso = time.time() - os.path.getmtime(blocco) < 45 * 60
        with open(blocco, encoding="utf-8") as f_b:
            chi_b = f_b.read().strip()
        in_corso = in_corso and (not chi_b.isdigit() or _vivo_pid(chi_b))
    except OSError:
        in_corso = False
    if in_corso:
        print(f"Un giro è in corso da {round((time.time() - os.path.getmtime(blocco)) / 60)} minuti: ultima tappa finita «"
              f"{NOMI_TAPPE.get(pr.get('fatta', ''), pr.get('fatta', '?'))}», {pr.get('voci', 0)} voci nuove finora.")
    if not diario:
        print("Il diario è ancora vuoto: il primo giro lo riempie.")
        return
    oggi_ = [x for x in diario if x.get("iso", "") >= (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()]
    if oggi_:
        print(f"Ultime 24 ore: {len(oggi_)} giri, durata media {round(sum(x['durata'] for x in oggi_) / len(oggi_) / 60)} minuti, "
              f"{sum(x['nuove'] for x in oggi_)} voci nuove in tutto.")
    giu_ = leggi_json(os.path.join(DATI, "rete.json"), {}).get("giu_dal")
    if giu_:
        print("RETE ASSENTE dal", datetime.fromisoformat(giu_).astimezone().strftime("%d/%m %H:%M") + ": il programma lavora su quello che ha "
              "e riparte da solo quando torna.")
    print("quando        tipo        min  nuove  tradotti  senza  richieste  rifiuti  avvisi  versione  gradi  batt   MB")
    prima = None
    for x in diario[-quanti:]:
        if prima and x.get("iso") and prima.get("iso"):
            try:
                buco = (datetime.fromisoformat(x["iso"]) - datetime.fromisoformat(prima["iso"])).total_seconds() / 3600
                if buco > (1.6 if x.get("tipo") else 3.6):
                    print(f"   — buco di {buco:.1f} ore: in questo intervallo il programma era fermo —")
            except ValueError:
                pass
        print(f"{x['quando']:<12}  {x.get('tipo', 'completo'):<10} {max(1, round(x['durata'] / 60)):>3} {x['nuove']:>6} {x.get('tradotti', 0):>9} {x['scoperti']:>6} "
              f"{x['richieste']:>10} {sum(x.get('rifiuti', {}).values()):>8} {x['errori']:>7}  {x['v']:<8}"
              + (lambda t_: f" {'' if t_[0] is None else t_[0]:>5}  {'' if t_[1] is None else str(t_[1]) + '%':>4} {x.get('mb', ''):>5}")(x.get("tel") or [None, None])
              + (f"  ({x['motivo']})" if x.get("motivo") else ""))
        prima = x
    z = diario[-1]
    if z.get("lingue"):
        print("Lingue delle voci nuove dell'ultimo giro:", ", ".join(f"{k} {v}" for k, v in z["lingue"].items()))
    print("Come procede un giro, nell'ordine:")
    for i, t in enumerate(ORDINE_TAPPE, 1):
        print(f"  {i:>2}. {t}")


def _cron_vivo():
    try:
        return subprocess.run(["pgrep", "-x", "crond"], capture_output=True).returncode == 0
    except OSError:
        return None


def _riserva_cron():
    """Orologio interno (non un secondo ciclo): finché la pagina sul telefono è accesa, ogni minuto guarda quando è
    partito l'ultimo giro e, se è passato il tempo di un giro (mezz'ora, o quello scritto in config.json), lancia lo stesso `aggiorna`.
    Così i giri partono anche se cron non funziona. Il blocco in dati/aggiorna.lock garantisce che ne giri uno solo."""
    while True:
        time.sleep(60)
        try:
            passo_ = passo_minuti(leggi_json(os.path.join(QUI, "config.json"), {}))
            ultimo = (leggi_json(os.path.join(DATI, "diario.json"), []) or [{}])[-1].get("iso", "")  # conta anche il lavoro senza rete
            try:
                eta = (datetime.now(timezone.utc) - datetime.fromisoformat(ultimo)).total_seconds() / 60 if ultimo else 1e9
            except ValueError:
                eta = 1e9
            giu_ = leggi_json(os.path.join(DATI, "rete.json"), {}).get("giu_dal")
            if eta >= passo_ + 2 or (giu_ and rete_ok(forza=True)):
                with open(os.path.join(DATI, "log.txt"), "a", encoding="utf-8") as log:
                    subprocess.run([sys.executable, os.path.join(QUI, "castello.py"), "aggiorna", "auto"], stdout=log,
                                   stderr=subprocess.STDOUT, check=False)
        except OSError:
            pass


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


def da_saltare(f, st, adesso, leggero=False):
    """Una fonte che non risponde non viene mai bloccata: viene riprovata sempre più di rado.
    Fino a 3 errori di fila, a ogni giro; da 3 a 9, solo nei giri completi (ogni 3 ore); da 10 in su, una volta al giorno.
    Gli errori dovuti alla rete assente non contano."""
    fila = (st or {}).get("fila", 0)
    if fila < 3:
        return False
    if fila < 10:
        return leggero
    return st.get("ultimo", "") >= (adesso - timedelta(hours=24)).isoformat()


def telefono():
    """Batteria del telefono: temperatura in gradi, carica in % e se è sotto carica. Ogni valore è None se non si
    può leggere (su un computer, oppure senza l'app Termux:API e con i file di sistema chiusi da Android)."""
    t = pct = carica = None
    st_v = leggi_json(os.path.join(DATI, "veglia.json"), {})
    muta = st_v.get("api_muta", "") > (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    if shutil.which("termux-battery-status") and not muta:
        uscita = _esegui(["termux-battery-status"], 8)
        if uscita is None:  # l'app Termux:API non risponde: non si riprova a ogni giro (ogni tentativo perde 8 secondi)
            st_v["api_muta"] = datetime.now(timezone.utc).isoformat()
            scrivi_json(os.path.join(DATI, "veglia.json"), st_v)
        try:
            d = json.loads(uscita or "{}")
            t, pct = d.get("temperature"), d.get("percentage")
            if "plugged" in d:
                carica = str(d["plugged"]).upper() not in ("", "UNPLUGGED")
        except (ValueError, AttributeError):
            pass
    base = "/sys/class/power_supply/battery/"
    try:
        if t is None:
            with open(base + "temp", encoding="utf-8") as f:
                t = int(f.read().strip()) / 10.0
    except (OSError, ValueError):
        pass
    try:
        if pct is None:
            with open(base + "capacity", encoding="utf-8") as f:
                pct = int(f.read().strip())
        if carica is None:
            with open(base + "status", encoding="utf-8") as f:
                carica = f.read().strip().lower() in ("charging", "full")
    except (OSError, ValueError):
        pass
    if t is None:  # ultima strada: i sensori di temperatura del sistema, se Android li lascia leggere
        for zona in sorted(glob.glob("/sys/class/thermal/thermal_zone*"))[:60]:
            try:
                with open(zona + "/type", encoding="utf-8") as f:
                    if "batt" not in f.read().lower():
                        continue
                with open(zona + "/temp", encoding="utf-8") as f:
                    v_ = float(f.read().strip())
                t = v_ / 1000.0 if v_ > 1000 else v_ / 10.0 if v_ > 100 else v_
                break
            except (OSError, ValueError):
                continue
    try:
        t = round(float(t), 1) if t is not None and 0 < float(t) < 90 else None
    except (TypeError, ValueError):
        t = None
    return {"temp": t, "batteria": pct, "in_carica": carica}


def guardia_telefono(cfg, tel):
    """Il programma si ferma da solo solo per tre motivi: telefono troppo caldo, batteria quasi scarica (e non in
    carica), tetto di spesa del cervello. Qui i primi due. Restituisce il motivo della pausa, oppure "".
    Dopo una pausa per il caldo riparte solo quando la temperatura è scesa sotto «temp_ok» (non a ogni mezzo grado)."""
    g = cfg.get("guardia", {})
    if not g.get("attiva", True):
        return ""
    perc = os.path.join(DATI, "guardia.json")
    st = leggi_json(perc, {})
    t, pct = tel.get("temp"), tel.get("batteria")
    motivo = ""
    if t is not None and (t >= g.get("temp_max", 42) or (st.get("caldo") and t > g.get("temp_ok", 38))):
        motivo = f"telefono caldo: {str(t).replace('.', ',')} gradi"
    elif pct is not None and tel.get("in_carica") is False and pct <= g.get("batteria_min", 15):
        motivo = f"batteria al {pct}% e non in carica"
    caldo = motivo.startswith("telefono caldo")
    if caldo != bool(st.get("caldo")) or (t is not None) != bool(st.get("termometro")):
        scrivi_json(perc, {"caldo": caldo, "termometro": t is not None})  # «termometro»: la temperatura si legge
    return motivo


def _pausa(motivo, tel):
    """Giro saltato per proteggere il telefono: lo scrive nel diario (al massimo una riga ogni 25 minuti), così un
    buco nei giri si distingue da una pausa voluta."""
    adesso = datetime.now(timezone.utc)
    print("Giro in pausa:", motivo)
    diario = leggi_json(os.path.join(DATI, "diario.json"), [])
    if diario and diario[-1].get("tipo") == "pausa" and diario[-1].get("iso", "") > (adesso - timedelta(minutes=25)).isoformat():
        return
    _riga_diario("pausa", motivo, tel)


def _riga_diario(tipo, motivo, tel, **altro):
    """Una riga del diario che non è un giro: una pausa voluta, oppure il programma rimasto fermo (con l'ora di inizio e
    di fine). Parte dai numeri dell'ultimo giro vero, così i grafici non crollano a zero."""
    adesso = datetime.now(timezone.utc)
    diario = leggi_json(os.path.join(DATI, "diario.json"), [])
    base = dict(next((x for x in reversed(diario) if x.get("tipo") not in ("senza rete", "pausa", "fermo")), {}))
    base.update({"quando": datetime.now().strftime("%d/%m %H:%M"), "iso": adesso.isoformat(), "v": VERSIONE, "tipo": tipo,
                 "motivo": motivo, "tel": [tel.get("temp"), tel.get("batteria"), tel.get("in_carica")], "durata": 0, "nuove": 0,
                 "da": {}, "fonti_nuove": [], "richieste": 0, "siti": [], "rifiuti": {}, "errori": 0, "seguiti": [0, 0],
                 "verifiche": [0, 0], "lingue": {}, "ricerche": [], "mb": 0, "attesa": [0, 0, (base.get("attesa") or [0, 0, 0])[2]]})
    for campo in ("offline", "senza_rete_dal", "fermo", "piano", "sosp", "passo"):
        base.pop(campo, None)
    base.update(altro)
    for campo, valore in (("live", 0), ("quota", 0), ("livelli", {}), ("scoperti", 0), ("senza", []), ("fonti", [0, 0]),
                          ("sapere", 0), ("tradotti", 0), ("usd_oggi", 0), ("usd_mese", 0), ("confermate", 0), ("memoria", [0, 0])):
        base.setdefault(campo, valore)
    base["memoria"] = [0, (base.get("memoria") or [0, 0])[1]]
    diario.append(base)
    scrivi_json(os.path.join(DATI, "diario.json"), diario[-120:])
    live = leggi_json(os.path.join(DATI, "live.json"), {})
    if live:
        live["diario"] = [{k: v for k, v in x.items() if k not in ("ricerche", "siti")} for x in diario[-60:]]
        scrivi_json(os.path.join(DATI, "live.json"), live)
        try:
            with open(os.path.join(WEB, "live.js.tmp"), "w", encoding="utf-8") as f:
                f.write("window.LIVE = " + json.dumps(live, ensure_ascii=False) + ";\n")
            os.replace(os.path.join(WEB, "live.js.tmp"), os.path.join(WEB, "live.js"))
        except OSError:
            pass


def ripara_fonti(stato, errori):
    """Se molte fonti risultano «ferme» tutte insieme non sono i siti: era la rete (o il DNS) del telefono.
    Succede dopo una notte senza rete con una versione vecchia, che contava ogni tentativo come un errore del sito:
    le fonti restavano poi lette una volta al giorno. Qui si rimettono tutte in lettura."""
    ferme = [u for u, st in stato.items() if st.get("fila", 0) >= 3]
    if len(ferme) >= 20 and len(ferme) >= 0.3 * max(1, len(stato)):
        for u in ferme:
            stato[u]["fila"] = 0
            stato[u].pop("prossimo", None)
        errori.append(f"{len(ferme)} fonti erano segnate come ferme tutte insieme: era la rete, non i siti. Rimesse in lettura da questo giro.")
        return len(ferme)
    return 0


# ----------------------------------------------------------------------------- guardiano e scatola nera

def _esegui(comando, attesa=8):
    """Lancia un comando del telefono e ne legge l'uscita. Se non risponde in tempo chiude lui e i suoi figli: un comando
    di Termux:API senza l'app installata resta appeso per sempre, e Android chiude Termux quando i processi lasciati in
    giro sono troppi."""
    try:
        p = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, text=True,
                             start_new_session=True)
    except OSError:
        return None
    try:
        return p.communicate(timeout=attesa)[0] or ""
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            p.communicate(timeout=3)
        except Exception:
            pass
        return None


def _su_termux():
    return "com.termux" in QUI or "com.termux" in sys.executable or os.path.isdir("/data/data/com.termux/files")


def _vivo(porta=8080):
    """Chiede alla pagina sul telefono se è accesa: restituisce la versione che risponde, "" se è spenta, "?" se sulla
    porta risponde qualcos'altro (o un PanGeo vecchio, che non conosce la domanda)."""
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=4) as s:
            s.settimeout(4)
            s.sendall(b"GET /vivo HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n")
            dati = b""
            while len(dati) < 2000:
                pezzo = s.recv(1000)
                if not pezzo:
                    break
                dati += pezzo
    except OSError:
        return ""
    m = re.search(rb"pangeo ([0-9.]+)", dati)
    return m.group(1).decode() if m else "?"


def _vivo_pid(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def _accendi():
    with open(os.path.join(DATI, "log.txt"), "a", encoding="utf-8") as log:
        subprocess.Popen([sys.executable, os.path.join(QUI, "castello.py"), "serve"], cwd=QUI, stdin=subprocess.DEVNULL,
                         stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def veglia(parla=True):
    """Il guardiano. Controlla che la pagina sul telefono (e con lei l'orologio che fa partire i giri) sia accesa e sia
    della versione giusta; se no, la riaccende. Lo chiamano cron ogni 5 minuti, Termux ogni volta che lo apri, il telefono
    quando si riaccende e, con Termux:API, Android ogni 15 minuti. Non è un secondo ciclo: rilancia lo stesso «serve»."""
    os.makedirs(DATI, exist_ok=True)
    try:  # il registro non deve crescere senza fine
        registro = os.path.join(DATI, "log.txt")
        if os.path.getsize(registro) > 2_000_000:
            with open(registro, "rb") as f:
                f.seek(-300_000, 2)
                coda = f.read()
            with open(registro, "wb") as f:
                f.write(coda[coda.find(b"\n") + 1:])
    except OSError:
        pass
    chi = _vivo()
    if chi == VERSIONE:
        if parla:
            print(f"PanGeo è acceso (versione {VERSIONE}).")
        return True
    if chi:  # risponde una versione vecchia (dopo «approva»), oppure un altro programma
        try:
            pid_ = [int(x) for x in (subprocess.run(["pgrep", "-f", "castello.py serve"], capture_output=True, text=True, timeout=10).stdout or "").split()
                    if x.isdigit() and int(x) != os.getpid()]
        except (OSError, subprocess.SubprocessError):
            pid_ = []
        if not pid_:
            if parla:
                print("La porta 8080 è occupata da un altro programma: PanGeo non può aprire la sua pagina.")
            return False
        for p_ in pid_:
            try:
                os.kill(p_, signal.SIGTERM)
            except OSError:
                pass
        for _ in range(20):
            if not _vivo():
                break
            time.sleep(0.5)
    _tieni_sveglio()
    _accendi()
    for _ in range(20):
        time.sleep(0.5)
        if _vivo() == VERSIONE:
            break
    acceso = _vivo() == VERSIONE
    with open(os.path.join(DATI, "log.txt"), "a", encoding="utf-8") as log:
        log.write(f"[{datetime.now().strftime('%d/%m %H:%M')}] guardiano: PanGeo era "
                  + ("spento" if not chi else "acceso con una versione vecchia") + (", riacceso\n" if acceso else ", NON si riaccende\n"))
    if parla:
        print("PanGeo era " + ("spento" if not chi else "acceso con una versione vecchia") + (": riacceso." if acceso else ": non si riaccende, guarda dati/log.txt"))
    return acceso


def _riga_bashrc():
    return '(cd %s && %s castello.py veglia zitto >> dati/log.txt 2>&1 &)  # PanGeo: riparte da solo quando apri Termux' % (
        shlex.quote(QUI), shlex.quote(sys.executable))


def _avvio_con_termux():
    """Una riga in ~/.bashrc (solo su Termux, segnata col nome PanGeo): ogni volta che apri Termux il guardiano controlla
    che PanGeo sia acceso e lo riaccende. Così, se Android chiude Termux, basta riaprirlo: non serve scrivere nulla."""
    if not _su_termux():
        return
    perc = os.path.expanduser("~/.bashrc")
    try:
        testo = ""
        if os.path.exists(perc):
            with open(perc, encoding="utf-8", errors="replace") as f:
                testo = f.read()
        if "castello.py veglia" in testo:
            return
        with open(perc, "a", encoding="utf-8") as f:
            f.write(("" if not testo or testo.endswith("\n") else "\n") + _riga_bashrc() + "\n")
    except OSError:
        pass


def _lavoro_android():
    """Con l'app Termux:API: chiede ad Android di richiamare il guardiano ogni 15 minuti, anche quando Termux è stato
    chiuso del tutto (è l'unico modo per ripartire senza che nessuno riapra Termux). Una volta al giorno rinnova la richiesta."""
    if not _su_termux() or not shutil.which("termux-job-scheduler"):
        return ""
    perc = os.path.join(DATI, "veglia.json")
    st = leggi_json(perc, {})
    oggi = datetime.now().date().isoformat()
    if st.get("giorno") == oggi:
        return st.get("esito", "")
    script = os.path.join(QUI, "veglia.sh")
    try:
        with open(script, "w", encoding="utf-8") as f:
            f.write("#!/data/data/com.termux/files/usr/bin/sh\n# PanGeo: lo richiama Android ogni 15 minuti (lo scrive castello.py)\n"
                    "cd %s && %s castello.py veglia zitto >> dati/log.txt 2>&1\n" % (shlex.quote(QUI), shlex.quote(sys.executable)))
        os.chmod(script, 0o700)
    except OSError:
        return ""
    uscita = _esegui(["termux-job-scheduler", "--job-id", "2611", "--script", script, "--period-ms", "900000",
                      "--persisted", "true", "--battery-not-low", "false", "--network", "none"], 12)
    esito = "senza risposta: manca l'app Termux:API" if uscita is None else (uscita.strip()[:160] or "richiesta fatta")
    scrivi_json(perc, {"giorno": oggi, "esito": esito})
    return esito


def _acceso_da():
    """Da quanti secondi è acceso il telefono (per distinguere un riavvio da una chiusura di Termux)."""
    try:
        return time.clock_gettime(time.CLOCK_BOOTTIME)
    except (AttributeError, OSError):
        pass
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            return float(f.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def scatola_nera():
    """All'avvio della pagina sul telefono: se l'ultimo battito è vecchio, il programma era rimasto fermo. Lo scrive nel
    diario con l'ora in cui si è fermato, l'ora in cui è ripartito e il motivo più probabile, così un buco si spiega."""
    perc = os.path.join(DATI, "battito.json")
    st = leggi_json(perc, {})
    adesso = datetime.now(timezone.utc)
    try:
        ultimo = datetime.fromisoformat(st.get("t", ""))
    except (ValueError, TypeError):
        ultimo = None
    if ultimo and (adesso - ultimo).total_seconds() > 360:
        secondi = (adesso - ultimo).total_seconds()
        acceso = _acceso_da()
        if st.get("fine"):
            motivo = "chiusura chiesta: " + st["fine"]
        elif acceso is not None and acceso < secondi - 30:
            motivo = "il telefono è stato spento o riavviato"
        else:
            motivo = ("chiuso di colpo, senza preavviso: di solito è Android che ferma Termux per risparmiare batteria o memoria "
                      "(oppure Termux è stato chiuso o aggiornato a mano)")
        try:
            if datetime.fromisoformat(st.get("finestra", "")) > ultimo - timedelta(minutes=15):
                motivo += "; poco prima era stata chiusa la finestra di Termux"
        except (ValueError, TypeError):
            pass
        diario = leggi_json(os.path.join(DATI, "diario.json"), [])
        try:
            fine_giro = max(datetime.fromisoformat(x["iso"]) + timedelta(seconds=x.get("durata", 0)) for x in diario[-8:] if x.get("iso") and x.get("tipo") in (None, "completo", "leggero"))
            passo_ = passo_minuti(leggi_json(os.path.join(QUI, "config.json"), {}))
            if (adesso - fine_giro).total_seconds() < (passo_ + 10) * 60:
                motivo += "; i giri sono andati avanti lo stesso (li ha lanciati cron)"
        except (ValueError, KeyError, TypeError):
            pass
        fermo = [ultimo.isoformat(), adesso.isoformat(), int(secondi / 60)]
        fermi = leggi_json(os.path.join(DATI, "fermi.json"), [])
        fermi.append({"dal": fermo[0], "al": fermo[1], "minuti": fermo[2], "motivo": motivo})
        scrivi_json(os.path.join(DATI, "fermi.json"), fermi[-40:])
        print(f"PanGeo era fermo da {fermo[2]} minuti: {motivo}.")
    else:
        fermo = motivo = None
    scrivi_json(perc, {"pid": os.getpid(), "t": adesso.isoformat(), "avvio": adesso.isoformat(), "sosp": (st.get("sosp") or [])[-40:]})
    if fermo:
        threading.Thread(target=_scrivi_fermo, args=(motivo, fermo), daemon=True).start()


def _scrivi_fermo(motivo, fermo):
    """La riga «fermo» entra nel diario quando nessun giro lo sta usando (un giro lanciato da cron può essere in corso)."""
    blocco = os.path.join(DATI, "aggiorna.lock")
    for _ in range(500):
        try:
            with open(blocco, encoding="utf-8") as f:
                chi = f.read().strip()
            if not chi.isdigit() or not _vivo_pid(chi) or time.time() - os.path.getmtime(blocco) > 45 * 60:
                break
        except OSError:
            break
        time.sleep(3)
    try:
        _riga_diario("fermo", motivo, telefono(), fermo=fermo)
    except Exception as e:
        print("Scatola nera (diario):", e)


def _battito():
    """Ogni minuto la pagina sul telefono scrive «sono viva». Se tra due battiti passano più di tre minuti vuol dire che
    Android aveva messo Termux in pausa: lo annota (ora e durata), così si vede se il telefono lo lascia lavorare."""
    perc = os.path.join(DATI, "battito.json")
    prima, giri_ = time.time(), 0
    while True:
        time.sleep(60)
        try:
            ora, giri_ = time.time(), giri_ + 1
            st = leggi_json(perc, {})
            if ora - prima > 200:
                st["sosp"] = (st.get("sosp") or [])[-39:] + [[datetime.now(timezone.utc).isoformat(), int(ora - prima - 60)]]
            prima = ora
            st.update({"pid": os.getpid(), "t": datetime.now(timezone.utc).isoformat()})
            scrivi_json(perc, st)
            if giri_ % 5 == 0 and shutil.which("crond") and _cron_vivo() is False:
                subprocess.run(["crond"], check=False, timeout=15)  # cron si era fermato: lo riaccende
        except (OSError, subprocess.SubprocessError, ValueError):
            pass


def _segnale(num, _quadro=None):
    """Segnali che si possono vedere arrivare. Quando Android chiude di colpo (segnale 9) non arriva nulla: per questo
    all'avvio la scatola nera guarda l'ultimo battito."""
    perc = os.path.join(DATI, "battito.json")
    try:
        st = leggi_json(perc, {})
        if num == getattr(signal, "SIGHUP", -1):
            st["finestra"] = datetime.now(timezone.utc).isoformat()  # la finestra di Termux è stata chiusa: si va avanti
            scrivi_json(perc, st)
            return
        st["fine"] = {signal.SIGTERM: "segnale 15 (riavvio con avvia.sh o col guardiano, oppure chiusura di Termux)",
                      signal.SIGINT: "Ctrl+C"}.get(num, f"segnale {num}")
        st["t"] = datetime.now(timezone.utc).isoformat()
        scrivi_json(perc, st)
    except OSError:
        pass
    raise SystemExit(0)



def passo_minuti(cfg):
    """Ogni quanti minuti parte un giro: 180 senza giro leggero, altrimenti giro_leggero.ogni_minuti (10, 15, 20, 30 o 60).
    Sta in config.json, che il telefono prende da solo a ogni giro: per cambiare ritmo non serve «approva»."""
    gl = cfg.get("giro_leggero", {})
    if not gl.get("attivo", True):
        return 180
    try:
        m = int(gl.get("ogni_minuti", 60))
        ss = gl.get("senza_sosta", {})
        # «senza sosta»: passo più corto, ma solo se il telefono dice la sua temperatura. Senza termometro il programma
        # non potrebbe fermarsi per il caldo, quindi resta al passo normale.
        if ss.get("attivo") and leggi_json(os.path.join(DATI, "guardia.json"), {}).get("termometro"):
            m = int(ss.get("ogni_minuti", 10))
    except (TypeError, ValueError):
        m = 60
    return min((10, 15, 20, 30, 60), key=lambda x: abs(x - m))


def passo_cron(cfg):
    m = passo_minuti(cfg)
    if m >= 180:
        return "17 */3 * * *"
    return ",".join(str(x) for x in sorted((17 + k * m) % 60 for k in range(60 // m))) + " * * * *"


def programma_cron(cfg):
    """Tiene in cron la riga di PanGeo: al ritmo di config.json se il giro leggero è acceso, ogni 3 ore se è spento, con i percorsi
    completi di python e della cartella (dentro cron «python» da solo può non essere trovato). Tocca solo la propria riga."""
    if not shutil.which("crontab"):
        return ""
    passo = passo_cron(cfg)
    qui_ = f"cd {shlex.quote(QUI)} && {shlex.quote(sys.executable)} castello.py"
    volute = [f"{passo} {qui_} aggiorna >> dati/log.txt 2>&1",
              f"*/5 * * * * {qui_} veglia zitto >> dati/log.txt 2>&1"]  # il guardiano: riaccende la pagina se si è spenta
    try:
        tab = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=15).stdout
        attuali = tab.splitlines()
        righe = [r for r in attuali if r.strip().startswith("#") or not ("castello.py aggiorna" in r or "castello.py veglia" in r)]
        if all(v in attuali for v in volute) and len(righe) == len(attuali) - len(volute):
            return ""
        subprocess.run(["crontab", "-"], input="\n".join(righe + volute) + "\n", text=True, timeout=15, check=False)
        return passo if volute[0] not in attuali else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _senza_rete():
    """La rete non c'è: niente raccolta e nessuna fonte penalizzata. Il programma lavora su quello che ha già:
    rifà gruppi e conferme su tutti i 7 giorni dell'archivio (non solo sugli ultimi 3), consolida la memoria dei fatti
    confermati, fa una copia di sicurezza e scrive nel diario da quando la rete manca. Al ritorno parte subito un giro completo."""
    adesso = datetime.now(timezone.utc)
    inizio = time.time()
    perc_r = os.path.join(DATI, "rete.json")
    st_r = leggi_json(perc_r, {})
    if not st_r.get("giu_dal"):
        st_r = {"giu_dal": adesso.isoformat(), "tentativi": 0}
    st_r["tentativi"] = st_r.get("tentativi", 0) + 1
    da_ = datetime.fromisoformat(st_r["giu_dal"]).astimezone().strftime("%d/%m %H:%M")
    if st_r.get("lavoro", "") >= (adesso - timedelta(minutes=55)).isoformat():
        scrivi_json(perc_r, st_r)
        print(f"Rete assente dal {da_}. Il lavoro senza rete è già stato fatto in quest'ora: riprovo al prossimo giro.")
        return
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    auto = leggi_json(os.path.join(DATI, "fonti_auto.json"), {})
    archivio = leggi_json(os.path.join(DATI, "archivio.json"), {"notizie": {}, "video": {}})
    voci = {k: v for k, v in archivio.get("notizie", {}).items()
            if (v.get("data_iso") or "") >= (adesso - timedelta(days=7)).isoformat()}
    confermate_prima = sum(1 for v in voci.values() if v.get("conf"))
    if voci:
        gruppi, esito = raggruppa(voci)
        for k, v in voci.items():
            fonti = gruppi[esito[k]]["fonti"]
            v["nf"], v["gr"] = len(fonti), esito[k]
            v["conf"] = any(l in ("A", "B") for f, l in fonti.items() if f != v.get("fonte"))
    confermate_dopo = sum(1 for v in voci.values() if v.get("conf"))
    nuovi_m, tot_m = memoria_stati(archivio, adesso, cfg, ore=7 * 24)
    try:
        shutil.copyfile(os.path.join(DATI, "archivio.json"), os.path.join(DATI, "archivio.copia.json"))
    except OSError:
        pass
    scrivi_json(os.path.join(DATI, "archivio.json"), archivio)
    # diario e pagina: si vede che la rete manca e che cosa è stato fatto intanto
    diario = leggi_json(os.path.join(DATI, "diario.json"), [])
    base = dict(next((x for x in reversed(diario) if x.get("tipo") != "senza rete"), {}))
    base.update({"quando": datetime.now().strftime("%d/%m %H:%M"), "iso": adesso.isoformat(), "v": VERSIONE, "tipo": "senza rete",
                 "durata": int(time.time() - inizio), "nuove": 0, "da": {}, "fonti_nuove": [], "richieste": 0, "siti": [],
                 "rifiuti": {}, "errori": 0, "seguiti": [0, 0], "verifiche": [0, 0], "lingue": {}, "ricerche": [],
                 "memoria": [nuovi_m, tot_m], "senza_rete_dal": st_r["giu_dal"],
                 "offline": [confermate_dopo - confermate_prima, nuovi_m]})
    for campo, valore in (("live", len(voci)), ("quota", 0), ("livelli", {}), ("scoperti", 0), ("senza", []), ("fonti", [0, 0]),
                          ("sapere", 0), ("tradotti", 0), ("usd_oggi", 0), ("usd_mese", 0), ("confermate", confermate_dopo)):
        base.setdefault(campo, valore)
    diario.append(base)
    scrivi_json(os.path.join(DATI, "diario.json"), diario[-120:])
    live = leggi_json(os.path.join(DATI, "live.json"), {})
    if live:
        live["rete"] = {"giu_dal": st_r["giu_dal"]}
        live["diario"] = [{k: v for k, v in x.items() if k not in ("ricerche", "siti")} for x in diario[-60:]]
        scrivi_json(os.path.join(DATI, "live.json"), live)
        try:
            with open(os.path.join(WEB, "live.js.tmp"), "w", encoding="utf-8") as f:
                f.write("window.LIVE = " + json.dumps(live, ensure_ascii=False) + ";\n")
            os.replace(os.path.join(WEB, "live.js.tmp"), os.path.join(WEB, "live.js"))
            shutil.copyfile(os.path.join(DATI, "diario.json"), os.path.join(WEB, "diario.json"))
        except OSError:
            pass
    st_r["lavoro"] = adesso.isoformat()
    scrivi_json(perc_r, st_r)
    print(f"Rete assente dal {da_}: nessuna raccolta e nessuna fonte penalizzata. Intanto ho lavorato su quello che ho: "
          f"{len(voci)} notizie di 7 giorni rilette, {confermate_dopo - confermate_prima:+d} conferme, {nuovi_m} fatti nuovi in memoria "
          f"({tot_m} in tutto). Appena la rete torna parte un giro completo.")


def aggiorna(tipo=""):
    """Il cuore: un solo giro alla volta. Se cron e avvia.sh partono insieme, il secondo aspetta il prossimo turno:
    così due giri non scrivono mai gli stessi file nello stesso momento."""
    os.makedirs(DATI, exist_ok=True)
    os.makedirs(WEB, exist_ok=True)
    blocco = os.path.join(DATI, "aggiorna.lock")
    try:
        if time.time() - os.path.getmtime(blocco) < 45 * 60:
            with open(blocco, encoding="utf-8") as f:
                chi_ = f.read().strip()
            if not chi_.isdigit() or _vivo_pid(chi_):
                print("Un aggiornamento è già in corso: questo giro si ferma qui (riprova tra qualche minuto).")
                return
            print("Il giro di prima è stato interrotto a metà (il programma era stato chiuso): si riparte.")
    except OSError:
        pass
    with open(blocco, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    try:
        _tieni_sveglio()  # ogni giro si assicura che il prossimo parta
        cfg_ = leggi_json(os.path.join(QUI, "config.json"), {})
        nuovo_passo = programma_cron(cfg_)
        if nuovo_passo:
            print(f"Giro automatico portato a: uno ogni {passo_minuti(cfg_)} minuti ({nuovo_passo})")
        tel_ = telefono()
        motivo_ = guardia_telefono(cfg_, tel_)
        if motivo_ and tipo not in ("completo", "leggero"):  # un giro chiesto a mano parte comunque
            _pausa(motivo_, tel_)
            return
        if not rete_ok(forza=True):
            _senza_rete()  # niente rete: lavora su quello che ha e aspetta
            return
        st_r = leggi_json(os.path.join(DATI, "rete.json"), {})
        tornata = bool(st_r.get("giu_dal"))
        if tornata:
            scrivi_json(os.path.join(DATI, "rete.json"), {"tornata": datetime.now(timezone.utc).isoformat(), "era_giu_dal": st_r["giu_dal"]})
            print("La rete è tornata: giro completo per recuperare.")
            if tipo in ("", "auto"):
                tipo = "completo"
        diario_ = leggi_json(os.path.join(DATI, "diario.json"), [])
        veri_ = [x for x in diario_ if x.get("tipo") != "senza rete"]
        if tipo == "auto":
            ultimo_ = (veri_ or [{}])[-1].get("iso", "")
            passo_ = max(6, passo_minuti(cfg_) - 10)
            if ultimo_ >= (datetime.now(timezone.utc) - timedelta(minutes=passo_)).isoformat():
                return  # un giro c'è appena stato (l'ha fatto cron o l'hai lanciato tu): l'orologio interno non raddoppia
        # giro completo ogni 3 ore; nelle ore in mezzo un giro leggero (solo feed, Telegram, YouTube, cielo): lo decide il
        # tempo passato dall'ultimo giro completo. Si può forzare:  python castello.py aggiorna completo | leggero
        if tipo not in ("completo", "leggero"):
            gl_ = cfg_.get("giro_leggero", {})
            ultimo_c = next((x.get("iso", "") for x in reversed(veri_) if x.get("tipo", "completo") == "completo"), "")
            soglia = (datetime.now(timezone.utc) - timedelta(minutes=gl_.get("minuti_completo", 170))).isoformat()
            tipo = "leggero" if gl_.get("attivo", True) and ultimo_c >= soglia else "completo"
        _aggiorna(tipo == "leggero")
    finally:
        try:
            os.remove(blocco)
        except OSError:
            pass


def _aggiorna(leggero=False):
    os.makedirs(DATI, exist_ok=True)
    os.makedirs(WEB, exist_ok=True)
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    if leggero:
        # giro leggero: niente ricerche (Google News, GDELT), niente studio, niente scoperta di fonti.
        # Ogni fonte riceve una sola richiesta, come è normale per un feed letto una volta l'ora.
        cfg = dict(cfg, temi=[], gdelt=[], rotazione_stati=0, giro_lingue={"attivo": False},
                   ricerca=dict(cfg.get("ricerca", {}), attiva=False), sapere=dict(cfg.get("sapere", {}), attivo=False),
                   scoperta=dict(cfg.get("scoperta", {}), attiva=False),
                   scoperta_telegram=dict(cfg.get("scoperta_telegram", {}), per_giro=0))
    mie = leggi_json(os.path.join(DATI, "fonti_mie.json"), {})
    chiavi = leggi_json(os.path.join(DATI, "chiavi.json"), {})
    auto = leggi_json(os.path.join(DATI, "fonti_auto.json"), {})
    auto.setdefault("scoperte", [])
    auto.setdefault("stato", {})
    auto.setdefault("domini_provati", {})
    APPRESI.update(auto.get("livelli_appresi", {}))
    paesi = leggi_json(os.path.join(QUI, "paesi.json"), {})
    it2en = leggi_json(os.path.join(QUI, "mappa.json"), {})
    ric = Riconoscitore(paesi)
    archivio = leggi_json(os.path.join(DATI, "archivio.json"), None)
    if isinstance(archivio, dict):
        archivio.setdefault("attesa", {})
    if not isinstance(archivio, dict) or "notizie" not in archivio:
        archivio = leggi_json(os.path.join(DATI, "archivio.copia.json"), {"notizie": {}, "video": {}})  # file rovinato: riparte dalla copia
    elif len(archivio["notizie"]) > 50:
        try:
            shutil.copyfile(os.path.join(DATI, "archivio.json"), os.path.join(DATI, "archivio.copia.json"))
        except OSError:
            pass
    archivio.setdefault("video", {})
    archivio.setdefault("attesa", {})
    canali = leggi_json(os.path.join(DATI, "canali.json"), {})
    errori, contati, citati = [], 0, {}
    citati_stato, tappe, _prima, inizio_ = {}, {}, [0], time.time()
    in_verifica, conferme_ver, n_seguiti, nuove_seguiti = [], {}, 0, 0
    RICHIESTE.clear()
    RIFIUTI.clear()

    def tappa(nome):  # quante voci nuove ha portato ogni pezzo del giro (per il diario)
        tappe[nome] = tappe.get(nome, 0) + contati - _prima[0]
        _prima[0] = contati
        try:  # a che punto è il giro: lo legge  python castello.py giri
            scrivi_json(os.path.join(DATI, "progresso.json"), {"inizio": adesso.isoformat(), "fatta": nome, "voci": contati,
                                                               "minuti": round((time.time() - inizio_) / 60, 1)})
        except OSError:
            pass
    adesso = datetime.now(timezone.utc)

    limite_arch = (adesso - timedelta(days=cfg.get("giorni_archivio", 7))).isoformat()
    futuro_ = (adesso + timedelta(minutes=10)).isoformat()
    scade_att = (adesso - timedelta(hours=cfg.get("cervello", {}).get("attesa_ore", 36))).isoformat()
    for tipo_ in ("notizie", "video", "attesa"):  # e si correggono quelle già in archivio
        for v_ in archivio.get(tipo_, {}).values():
            if (v_.get("data_iso") or "") > futuro_:
                v_["data_iso"] = v_.get("visto") or adesso.isoformat()
    # tutte le testate generaliste passano dal cervello, che sceglie e traduce (anche quelle in inglese e in italiano):
    # il filtro a parole lasciava passare «defense witness» di un processo e scartava notizie vere. Senza cervello
    # (manca la chiave, è spento o ha toccato il tetto di spesa) resta il filtro a parole.
    imp_c = cfg.get("cervello", {})
    triage_tutte = bool(imp_c.get("attivo") and imp_c.get("triage_tutte", True) and chiavi.get("anthropic_key")
                        and not leggi_json(os.path.join(DATI, "cervello.json"), {}).get("tetto"))

    def aggiungi(tipo, voce):
        nonlocal contati
        if not voce["u"] or not voce["t"]:
            return
        if (voce.get("data_iso") or "") < limite_arch:
            return  # più vecchia dell'archivio: a fine giro verrebbe tolta, e al giro dopo ricontata come «nuova»
        if voce["data_iso"] > futuro_:
            voce["data_iso"] = adesso.isoformat()  # data nel futuro (fuso orario sbagliato nel feed): vale l'ora in cui la vediamo
        if tipo == "attesa" and voce["data_iso"] < scade_att:
            return  # troppo vecchia per la sala d'attesa: verrebbe lasciata cadere a fine giro e ricontata al giro dopo
        chiave = hashlib.sha1((voce["u"] + voce["t"]).encode("utf-8")).hexdigest()[:16]
        if chiave not in archivio[tipo]:
            voce["visto"] = adesso.isoformat()
            archivio[tipo][chiave] = voce
            contati += 1

    def notizia(tema, titolo, link, data, fonte, sito="", filtra=False, livello="", lv="", forza=None, ripiego=None, lingua="",
                attesa=False):
        if RUMORE.search(" " + (fonte or "") + " "):
            return
        if APPRESI.get(fonte) == "scarto":
            return
        if filtra and not attesa and not FILTRO.search(titolo):
            return
        if sito:
            d = dominio(sito)
            if d:
                citati[d] = citati.get(d, 0) + 1
                if forza:
                    cs_ = citati_stato.setdefault(d, {})
                    cs_[forza] = cs_.get(forza, 0) + 1
        trovati, rip_ = ric.trova(titolo), None
        if forza and forza not in trovati:
            trovati = [forza] + trovati[:4]
        if ripiego and not trovati:
            if lingua and lingua not in ("it", "en"):
                rip_ = ripiego  # titolo in un'altra lingua: prima si traduce, poi si vede di quale Stato parla
            else:
                trovati = [ripiego]  # testata nazionale («stato» in config.json): le notizie locali non nominano il Paese
        v = {"t": titolo, "u": solo_http(link), "data_iso": data or adesso.isoformat(), "fonte": fonte,
             "tema": tema, "paesi": trovati, "lv": livello_di(fonte, lv)}
        if livello:
            v["liv"] = livello
        if lingua and lingua not in ("it", "en"):
            v["lg"] = lingua  # titolo in un'altra lingua: il cervello lo traduce
            if rip_:
                v["rip"] = rip_
        # testata generalista in un'altra lingua: il titolo aspetta in «attesa» finché il cervello non lo traduce
        # e dice se riguarda i temi di PanGeo (il filtro a parole funziona solo in italiano e in inglese)
        aggiungi("attesa" if attesa else "notizie", v)

    # 1. Google News e GDELT: ricerche per tema
    meta_ = (adesso.hour // 3) % 2
    for n_tema, tema in enumerate(cfg.get("temi", [])):
        if cfg.get("temi_alterni", True) and n_tema % 2 != meta_:
            continue  # questo tema lo cerca il giro dopo
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
    if not leggero and stato_gdelt.get("ultimo", "") < (adesso - timedelta(hours=cfg.get("gdelt_ore", 6))).isoformat():
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
        # lingue senza edizione di Google News (persiano, urdu, swahili, finlandese, danese…): 4 a giro di GDELT, a rotazione
        if not stato_gdelt.get("pausa") and cfg.get("giro_lingue", {}).get("attivo", True):
            codici_ = sorted(GDELT_LINGUE)
            i0_ = stato_gdelt.get("i_lingua", 0)
            per_nome = {n_.lower(): k_ for k_, l_ in paesi.items() for n_ in l_}
            for n_ in range(cfg.get("giro_lingue", {}).get("gdelt_per_giro", 4)):
                lg_ = codici_[(i0_ + n_) % len(codici_)]
                try:
                    for t_, u_, d_, f_, s_, paese_ in gdelt("(military OR army OR defense OR government OR security) sourcelang:"
                                                            + GDELT_LINGUE[lg_], True)[:30]:
                        notizia("Difesa e forze armate", t_, u_, d_, f_, s_, ripiego=per_nome.get((paese_ or "").lower()), lingua=lg_)
                except Exception as e:
                    errori.append(f"GDELT (lingua {lg_}): {e}")
                    if "429" in str(e):
                        stato_gdelt["pausa"] = (adesso + timedelta(hours=24)).isoformat()
                        break
                time.sleep(12)
            stato_gdelt["i_lingua"] = (i0_ + cfg.get("giro_lingue", {}).get("gdelt_per_giro", 4)) % len(codici_)
        scrivi_json(os.path.join(DATI, "gdelt.json"), {"i_lingua": stato_gdelt.get("i_lingua", 0), "ultimo": stato_gdelt.get("pausa") and
                    (adesso + timedelta(hours=18)).isoformat() or adesso.isoformat()})

    tappa("temi")
    # 1b. Rotazione per Stato: a ogni giro cerca notizie sugli Stati meno coperti
    imp_auto = leggi_json(os.path.join(DATI, "impostazioni_auto.json"), {})
    rot = 0 if leggero else imp_auto.get("rotazione_stati", cfg.get("rotazione_stati", 6))
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
            en = nome_inglese(nomi)
            # prima la lingua del posto (se lo Stato ne ha più d'una, si alternano), poi l'inglese; dove la stampa
            # scrive in inglese: inglese e italiano. I titoli vengono poi tradotti in italiano dal cervello.
            sue_ = lingue_di(stato_) if cfg.get("lingue_locali", True) else []
            loc = sue_[(adesso.toordinal() * 8 + adesso.hour // 3) % len(sue_)] if sue_ else None
            coppie = ([(loc[0], f'"{loc[1]}" ' + PAROLE_LOCALI[loc[0]])] if loc else []) + \
                     [("en", f'"{en}" (military OR defense OR government OR security)')] + \
                     ([] if loc else [("it", f'"{nomi[0]}" (difesa OR esercito OR governo OR sicurezza)')])
            for lingua, q in coppie:
                try:
                    for t_, l_, d_, f_, s_ in google_news(q, lingua):
                        notizia("Copertura degli Stati", t_, l_, d_, f_, s_, forza=stato_, lingua=lingua)
                except Exception as e:
                    errori.append(f"Google News ({stato_}, {lingua}): {e}")
                time.sleep(imp_auto.get("pausa_google", 1))
            cop[stato_] = adesso.isoformat()
        scrivi_json(os.path.join(DATI, "copertura.json"), cop)

        tappa("stati")
        # 1c. Ricerca autonoma: il programma si fa da solo le domande sugli Stati e sui temi meno coperti,
        # le prova, tiene quelle che portano notizie nuove e scarta le altre (anche il cervello ne propone)
        ra = cfg.get("ricerca", {})
        if ra.get("attiva", True):
            perc_r = os.path.join(DATI, "ricerche.json")
            R = leggi_json(perc_r, {"code": []})
            code = R.setdefault("code", [])
            note_ = {x["q"] for x in code}
            # impara quali tipi di domanda rendono: notizie nuove per prova, per ogni modello (R["resa"]).
            # I tre modelli migliori vengono usati il doppio; quelli mai provati partono alti, così si provano tutti.
            resa = R.setdefault("resa", {})

            def voto(m_):
                p_, n2_ = resa.get(m_, [0, 0])
                return n2_ / p_ if p_ else 99

            classifica = sorted(range(len(MODELLI_RICERCA)), key=lambda i_: -voto("R%d" % i_))
            ciclo_ = classifica[:3] * 2 + classifica[3:]
            if sum(1 for x in code if not x.get("prove")) < 12:
                # uno Stato dove le ultime tre domande non hanno portato nulla riposa tre giorni: le domande vanno
                # dove la stampa scrive, invece di tornare sempre sugli stessi microstati
                vuoti_ = R.setdefault("vuoti", {})
                tre_gg_ = (adesso - timedelta(days=3)).isoformat()
                for n_, stato_ in enumerate([s_ for s_ in ordine if vuoti_.get(s_, [0, ""])[0] < 3 or vuoti_[s_][1] < tre_gg_][:14]):
                    nomi = paesi[stato_]
                    i_ = ciclo_[(R.get("giro", 0) + n_) % len(ciclo_)]
                    tema_, l_, modello = MODELLI_RICERCA[i_]
                    m_ = "R%d" % i_
                    q_ = modello.format(it=nomi[0], en=nome_inglese(nomi))
                    sue_ = lingue_di(stato_) if cfg.get("lingue_locali", True) else []
                    loc = sue_[(R.get("giro", 0) + n_) % len(sue_)] if sue_ else None
                    if loc and (R.get("giro", 0) + n_) % 3 and loc[0] in MODELLI_LOCALI:
                        scelta_ = sorted(range(len(MODELLI_LOCALI[loc[0]])), key=lambda j_: -voto(loc[0] + str(j_)))
                        j_ = scelta_[(R.get("giro", 0) // 2) % len(scelta_)]
                        tema_, modello = MODELLI_LOCALI[loc[0]][j_]
                        l_, q_, m_ = loc[0], modello.format(n=loc[1]), loc[0] + str(j_)
                    elif loc and (R.get("giro", 0) + n_) % 3:  # lingua senza modelli: la domanda generale su difesa e governo
                        tema_, l_, q_, m_ = "Difesa e forze armate", loc[0], '"%s" %s' % (loc[1], PAROLE_LOCALI[loc[0]]), loc[0] + "g"
                    if q_ not in note_:
                        code.append({"q": q_, "l": l_, "stato": stato_, "tema": tema_, "da": "programma", "m": m_,
                                     "prove": 0, "nuove": 0, "ultimo": ""})
                        note_.add(q_)
            ieri_ = (adesso - timedelta(hours=24)).isoformat()
            vv0_ = R.setdefault("vuoti", {})
            fermo_ = {s_ for s_, v_ in vv0_.items() if v_[0] >= 3 and v_[1] >= (adesso - timedelta(days=3)).isoformat()}
            scelte = sorted((x for x in code if x.get("ultimo", "") < ieri_ and not (x.get("da") == "programma" and x.get("stato") in fermo_)),
                            key=lambda x: (x.get("prove", 0) > 0, -(x.get("nuove", 0) / max(x.get("prove", 1), 1))))[:ra.get("per_giro", 6)]

            def nome_per(stato2_, lingua2_):  # il nome dello Stato nella lingua della domanda
                loc2_ = LOCALE.get(stato2_)
                if loc2_ and loc2_[0] == lingua2_:
                    return loc2_[1]
                return paesi[stato2_][0] if lingua2_ == "it" else nome_inglese(paesi[stato2_])

            extra = []  # domande nate dai fatti: si provano subito, una volta sola
            # domande di seguito: sui fatti più confermati delle ultime 24 ore il programma scava più a fondo
            seguiti = R.setdefault("seguiti", [])
            fatti_ = sorted((v for v in archivio["notizie"].values()
                             if v.get("conf") and (v.get("nf") or 1) >= 4 and (v.get("data_iso") or "") >= ieri_ and v.get("paesi")),
                            key=lambda v: -(v.get("nf") or 1))
            for v in fatti_:
                if len([x for x in extra if x["da"] == "seguito"]) >= ra.get("seguiti_per_giro", 2):
                    break
                st2_ = v["paesi"][0]
                if st2_ not in paesi:
                    continue
                chiavi_ = parole_chiave(v["t"], paesi[st2_], 3)
                firma_ = " ".join(sorted(w.lower() for w in chiavi_))
                if len(chiavi_) < 2 or firma_ in seguiti or any(x["stato"] == st2_ for x in extra):
                    continue
                l2_ = v.get("lg") or lingua_titolo(v["t"])
                seguiti.append(firma_)
                extra.append({"q": '"%s" %s' % (nome_per(st2_, l2_), " ".join(chiavi_)), "l": l2_, "stato": st2_,
                              "tema": v.get("tema") or "Ricerca autonoma", "da": "seguito", "prove": 0, "nuove": 0})
            R["seguiti"] = seguiti[-300:]
            # verifica attiva: per le notizie di fonti di parte o non classificate che nessun altro ha ancora
            # riportato, cerca se una fonte affidabile dà lo stesso fatto. Non trovarla NON vuol dire che è falsa.
            da12_ = (adesso - timedelta(hours=12)).isoformat()
            dubbie_ = sorted(((k, v) for k, v in archivio["notizie"].items()
                              if "nf" in v and not v.get("conf") and not v.get("ver") and v.get("lv") in ("C", "D")
                              and (v.get("nf") or 1) == 1 and v.get("paesi") and (v.get("data_iso") or "") >= da12_),
                             key=lambda kv: (kv[1].get("lv") != "C", kv[1].get("data_iso") or ""))
            visti_st = set()
            for k, v in dubbie_:
                if len(in_verifica) >= ra.get("verifiche_per_giro", 3):
                    break
                st2_ = v["paesi"][0]
                t2_ = v["t"]
                l2_ = v.get("lg") or lingua_titolo(t2_)
                if NON_LATINO.search(t2_) and not v.get("lg"):
                    if not v.get("it"):
                        continue  # alfabeto non latino, senza traduzione: non si sa in che lingua cercare
                    t2_, l2_ = v["it"], "it"
                chiavi_ = parole_chiave(t2_, paesi.get(st2_, []), 4)
                if st2_ not in paesi or st2_ in visti_st or len(chiavi_) < 3:
                    continue
                visti_st.add(st2_)
                v["ver"] = "in corso"
                in_verifica.append(k)
                extra.append({"q": '"%s" %s' % (nome_per(st2_, l2_), " ".join(chiavi_)), "l": l2_, "stato": st2_,
                              "tema": v.get("tema") or "Ricerca autonoma", "da": "verifica", "prove": 0, "nuove": 0,
                              "k": k, "chiavi": [w.lower() for w in chiavi_], "fonte": v.get("fonte", "")})
            for x in scelte + extra:
                prima_ = contati
                try:
                    trovate_ = google_news(x["q"], x["l"], 3)
                    if x.get("da") in ("seguito", "verifica"):
                        trovate_ = list(trovate_)[:25]  # una domanda nata da un fatto non deve riempire l'archivio di una sola storia
                    for t_, l2_, d_, f_, s_ in trovate_:
                        notizia(x.get("tema") or "Ricerca autonoma", t_, l2_, d_, f_, s_, forza=x.get("stato") or None, lingua=x["l"])
                        # verifica: una fonte affidabile (A o B), diversa da quella di partenza, con le stesse parole chiave nel titolo
                        if x.get("da") == "verifica" and x["k"] not in conferme_ver and f_ != x["fonte"] and livello_di(f_) in ("A", "B"):
                            tl_ = t_.lower()
                            if sum(1 for w in x["chiavi"] if w in tl_) >= max(3, len(x["chiavi"]) - 1):
                                conferme_ver[x["k"]] = f_
                except Exception as e:
                    errori.append(f"Ricerca autonoma ({x['q'][:40]}): {e}")
                x["prove"] = x.get("prove", 0) + 1
                x["nuove"] = x.get("nuove", 0) + contati - prima_
                x["ultimo"] = adesso.isoformat()
                if x.get("m"):
                    r_ = resa.setdefault(x["m"], [0, 0])
                    r_[0], r_[1] = r_[0] + 1, r_[1] + contati - prima_
                if x.get("da") == "programma" and x.get("stato"):
                    vv_ = R.setdefault("vuoti", {})
                    if contati > prima_:
                        vv_.pop(x["stato"], None)
                    else:
                        vv_[x["stato"]] = [(vv_.get(x["stato"], [0, ""])[0] if vv_.get(x["stato"], [0, ""])[1] >= (adesso - timedelta(days=3)).isoformat() else 0) + 1, adesso.isoformat()]
                if x.get("da") == "seguito":
                    n_seguiti, nuove_seguiti = n_seguiti + 1, nuove_seguiti + contati - prima_
                time.sleep(imp_auto.get("pausa_google", 1))
            R["code"] = [x for x in code if not (x.get("prove", 0) >= 3 and x.get("nuove", 0) == 0)][-150:]
            R["giro"] = R.get("giro", 0) + 1
            R["ultime"] = [[x["q"], x["nuove"], x["prove"], x.get("da", ""), x.get("stato", ""), x.get("tema", "")] for x in scelte + extra]
            scrivi_json(perc_r, R)

    tappa("ricerca")
    # 1d. Ogni Stato nella sua lingua: a turno su tutti gli Stati che ne hanno una (4 a giro), così anche quelli già
    # ben coperti in inglese vengono letti dalla loro stampa. Poi il giro delle lingue: 2 lingue a rotazione, le notizie
    # di difesa, governo e sicurezza di chi scrive in quella lingua. Il cervello traduce i titoli in italiano.
    gl_ = cfg.get("giro_lingue", {})
    if gl_.get("attivo", True):
        perc_l = os.path.join(DATI, "lingue.json")
        st_l = leggi_json(perc_l, {})
        resa_l, giro_l = st_l.setdefault("resa", {}), st_l.get("giri", 0)

        def cerca_lingua(q_, lg_, stato2_=None):
            prima_ = contati
            r_ = resa_l.setdefault(lg_, [0, 0])
            r_[0] += 1
            try:
                for t_, l_, d_, f_, s_ in list(google_news(q_, lg_))[:gl_.get("voci", 30)]:
                    notizia("Copertura degli Stati" if stato2_ else "Difesa e forze armate", t_, l_, d_, f_, s_, forza=stato2_, lingua=lg_)
            except Exception as e:
                errori.append(f"Google News (lingua {lg_}): {e}")
            r_[1] += contati - prima_
            time.sleep(imp_auto.get("pausa_google", 1))

        con_lingua = sorted(x for x in paesi if lingue_di(x))
        for n_ in range(min(gl_.get("stati_per_giro", 4), len(con_lingua))):
            stato2_ = con_lingua[(st_l.get("s", 0) + n_) % len(con_lingua)]
            sue_ = lingue_di(stato2_)
            lg_, nome2_ = sue_[(giro_l // max(len(con_lingua) // max(gl_.get("stati_per_giro", 4), 1), 1)) % len(sue_)]
            if lingua_ok(resa_l, lg_, giro_l):
                cerca_lingua('"%s" %s' % (nome2_, PAROLE_LOCALI[lg_]), lg_, stato2_)
        st_l["s"] = (st_l.get("s", 0) + gl_.get("stati_per_giro", 4)) % max(len(con_lingua), 1)
        lingue_ = [l for l in PAROLE_LOCALI if l in EDIZIONI]
        for n_ in range(min(gl_.get("per_giro", 2), len(lingue_))):
            lg_ = lingue_[(st_l.get("i", 0) + n_) % len(lingue_)]
            if lingua_ok(resa_l, lg_, giro_l):
                # solo le prime due parole (esercito, militari o difesa): «governo» e «sicurezza» senza il nome di uno
                # Stato portano troppa cronaca locale
                cerca_lingua(" OR ".join(PAROLE_LOCALI[lg_].strip("()").split(" OR ")[:2]), lg_)
        st_l["i"] = (st_l.get("i", 0) + gl_.get("per_giro", 2)) % max(len(lingue_), 1)
        st_l["giri"] = giro_l + 1
        scrivi_json(perc_l, st_l)
    tappa("lingue")
    # 1e. Lavoro a piano: alleanze, patti e appalti militari, uno Stato alla volta, blocco per blocco (prima l'Europa).
    # Gira anche nei giri leggeri (uno Stato, tre domande), così avanza sempre.
    piano_giro = [0, 0, 0]
    if cfg.get("piano", {}).get("attivo", True):
        try:
            piano_giro = passo_piano(cfg, chiavi, paesi, leggero, errori, notizia)
        except Exception as e:
            errori.append(f"Lavoro a piano: {e}")
    tappa("piano")
    # 2. Feed RSS: fissi, candidati, scoperti da soli, aggiunti a mano
    cadute_rete = []
    # Giri fitti (giro_leggero.fonti_a_ritmo): ogni fonte ha il suo ritmo. Chi ha appena portato novità si rilegge dopo
    # «fonte_min_minuti», chi tace sempre più di rado, fino a «fonte_max_minuti». Nei giri completi si leggono tutte.
    gl_r = cfg.get("giro_leggero", {})
    a_ritmo = bool(gl_r.get("fonti_a_ritmo"))
    fmin, fmax = gl_r.get("fonte_min_minuti", 10), gl_r.get("fonte_max_minuti", 120)

    def dovuto(nome):  # Telegram, YouTube e cielo: nei giri fitti al massimo ogni «altri_min_minuti»
        if not (a_ritmo and leggero):
            return True
        r_ = auto.setdefault("ritmo", {})
        if r_.get(nome, "") > (adesso - timedelta(minutes=gl_r.get("altri_min_minuti", 30) - 2)).isoformat():
            return False
        r_[nome] = adesso.isoformat()
        return True

    saltate_ritmo = invariate = 0
    ripara_fonti(auto["stato"], errori)
    for f in elenco_fonti(cfg, mie, auto):
        st = auto["stato"].get(f["url"], {})
        if da_saltare(f, st, adesso, leggero):
            continue
        if a_ritmo and leggero and st.get("prossimo", "") > adesso.isoformat():
            saltate_ritmo += 1
            continue
        prima_ult = st.get("ultimo", "")
        st["ultimo"] = adesso.isoformat()
        contati_f = contati
        # nei giri leggeri si chiede al sito «solo se è cambiato» (risposta 304: nessun dato scaricato);
        # nei giri completi si rilegge sempre tutto, così un sito che risponde male non resta fermo
        risp_, cond_ = {}, {}
        if leggero and st.get("etag"):
            cond_["If-None-Match"] = st["etag"]
        if leggero and st.get("lm"):
            cond_["If-Modified-Since"] = st["lm"]
        try:
            try:
                grezzo_ = scarica(f["url"], intestazioni=cond_ or None, risposta=risp_)
            except urllib.error.HTTPError as e304:
                if e304.code != 304:
                    raise
                grezzo_ = None
                invariate += 1
            voci = leggi_rss(grezzo_) if grezzo_ is not None else []
            if grezzo_ is not None:
                if not voci:
                    raise ValueError("feed vuoto")
                st["etag"], st["lm"] = risp_.get("etag", ""), risp_.get("lm", "")
            for titolo, link, data, fonte, _ in voci:
                notizia(f.get("tema", "Notizie dal mondo"), titolo, link, data, f.get("nome") or fonte,
                        filtra=f.get("filtra", False),
                        livello="da valutare" if f["tipo"] == "scoperta" and not f.get("promossa") and not f.get("ufficiale") else f.get("liv", ""),
                        lv=("B" if f.get("promossa") else "D") if f["tipo"] == "scoperta" and not f.get("ufficiale") else f.get("lv", ""),
                        ripiego=f.get("stato"), lingua=f.get("lingua", ""),
                        attesa=bool(f.get("filtra")) and (triage_tutte or f.get("lingua", "it") not in ("it", "en")))
            st["ok"], st["fila"] = st.get("ok", 0) + 1, 0
            if a_ritmo:
                st["passo"] = fmin if contati > contati_f else min(fmax, max(fmin, round(st.get("passo", fmin) * 1.5)))
                st["prossimo"] = (adesso + timedelta(minutes=st["passo"] - 2)).isoformat()
        except SenzaRete:
            # la rete è caduta: questa fonte e quelle fallite per lo stesso motivo non vengono penalizzate
            st["ultimo"] = prima_ult
            auto["stato"][f["url"]] = st
            for u_ in cadute_rete:
                auto["stato"][u_]["fila"] = max(auto["stato"][u_].get("fila", 1) - 1, 0)
            errori.append("rete assente: lettura dei feed interrotta")
            break
        except Exception as e:
            st["fila"] = st.get("fila", 0) + 1
            if _errore_di_rete(e):
                cadute_rete.append(f["url"])
            if f["tipo"] in ("fissa", "mia") or st.get("ok", 0):
                errori.append(f"{f.get('nome', f['url'])}: {e}")
        auto["stato"][f["url"]] = st

    tappa("feed")
    # 3. Telegram: canali pubblici ufficiali (dichiarazioni di parte, non conferme)
    tg_citati = {}
    auto.setdefault("telegram", [])
    leggi_tg = dovuto("telegram")
    for c in (cfg.get("telegram", []) + mie.get("telegram", [])) if leggi_tg else []:
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
    if tg.get("attiva", True) and leggi_tg:
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

    tappa("telegram")
    # 4. YouTube: feed dei canali, senza chiave
    for h in (cfg.get("youtube", []) + mie.get("youtube", [])) if dovuto("video") else []:
        try:
            cid = h if h.startswith("UC") else id_canale(h, canali)
            for titolo, link, data, autore, _ in leggi_rss(scarica("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid)):
                aggiungi("video", {"t": titolo, "u": solo_http(link), "data_iso": data or adesso.isoformat(),
                                   "canale": autore or h, "paesi": ric.trova(titolo)})
        except Exception as e:
            errori.append(f"YouTube {h}: {e}")

    tappa("video")
    # 4b. Sapere: pochi Stati a giro studiati su Wikipedia (forze armate e storia)
    stati_studiati = sapere(cfg, paesi, errori, adesso)

    # 5. Cielo: traffico aereo civile per Stato
    if not cfg.get("cielo", True):
        dati_cielo = None
    elif dovuto("cielo"):
        dati_cielo = cielo(chiavi, it2en, errori)
    else:  # giro fitto: il cielo è quello di pochi minuti fa
        dati_cielo = (leggi_json(os.path.join(DATI, "live.json"), {}) or {}).get("cielo")
    try:
        dati_calore = calore(chiavi, it2en, errori, cfg.get("calore_ore", 24))
    except Exception as e:  # il calore non deve mai fermare il giro
        errori.append(f"NASA FIRMS (analisi): {e}")
        dati_calore = leggi_json(os.path.join(DATI, "calore.json"), None)

    # 6. Si amplia da solo: prova i siti più citati che non sono ancora tra le fonti
    sc = cfg.get("scoperta", {})
    nuove = []
    if sc.get("attiva", True) and len(auto["scoperte"]) < sc.get("max_fonti", 80):
        noti = {dominio(f["url"]) for f in elenco_fonti(cfg, mie, auto)}
        rinnovo = (adesso - timedelta(days=30)).isoformat()
        prove = 0
        # fonti fisse che non rispondono da 3 giri: cerca da solo il loro indirizzo nuovo sullo stesso sito
        for f in elenco_fonti(cfg, mie, auto):
            if prove >= sc.get("per_giro", 3):
                break
            d = dominio(f["url"])
            if f["tipo"] not in ("fissa", "mia") or auto["stato"].get(f["url"], {}).get("fila", 0) < 3 \
                    or auto["domini_provati"].get("rotta:" + d, "") >= rinnovo:
                continue
            prove += 1
            auto["domini_provati"]["rotta:" + d] = adesso.isoformat()
            try:
                u = trova_feed(d)
            except Exception:
                u = None
            if u and u != f["url"] and u not in {x["url"] for x in auto["scoperte"]}:
                nf_ = {"nome": f.get("nome", d) + " (indirizzo nuovo)", "url": u, "tema": f.get("tema", "Notizie dal mondo"),
                       "aggiunta": adesso.date().isoformat(), "sostituisce": f["url"]}
                if f.get("stato"):
                    nf_["stato"] = f["stato"]
                if f.get("lv") in ("A", "B"):
                    nf_["promossa"] = True  # è la stessa testata: tiene il livello di prima
                auto["scoperte"].append(nf_)
                nuove.append(nf_)
        # poi i siti proposti dal cervello («da_provare») e i più citati nelle notizie di questo giro
        coda_ = [(x["d"], 99, x.get("stato", "")) for x in auto.get("da_provare", [])] + \
                [(d, n, "") for d, n in sorted(citati.items(), key=lambda x: -x[1])]
        for d, n, st_ in coda_:
            if prove >= sc.get("per_giro", 3) or n < sc.get("min_citazioni", 3):
                break
            if not d or d in noti or d in ESCLUSI or auto["domini_provati"].get(d, "") >= rinnovo:
                continue
            prove += 1
            auto["domini_provati"][d] = adesso.isoformat()
            u = trova_feed(d)
            if u:
                f = {"nome": d, "url": u, "tema": "Scoperte automatiche (da valutare)", "aggiunta": adesso.date().isoformat()}
                # testata di un solo Stato: quasi tutte le sue notizie sono arrivate dalle ricerche su quello Stato
                per_st = citati_stato.get(d, {})
                if not st_ and per_st and max(per_st.values()) >= 3 and max(per_st.values()) >= 0.8 * citati.get(d, 1):
                    # prudenza: lo Stato si assegna solo se il suo nome (o la capitale) è nel nome del sito,
                    # così una testata straniera che parla spesso di un Paese non viene scambiata per una testata locale
                    cand_, dn_ = max(per_st, key=per_st.get), re.sub(r"[^a-z]", "", d.lower())
                    if any(len(k_) >= 5 and k_ in dn_ for k_ in (re.sub(r"[^a-z]", "", n_.lower()) for n_ in paesi.get(cand_, []))):
                        st_ = cand_
                if st_ in paesi:
                    f["stato"] = st_
                auto["scoperte"].append(f)
                nuove.append(f)
        auto["da_provare"] = [x for x in auto.get("da_provare", []) if x["d"] not in auto["domini_provati"]][-30:]
        fatti_s = 0
        for st_s, ente_s, url_s in sc.get("semi", []):
            if fatti_s >= sc.get("semi_per_giro", 8):
                break
            d_s = dominio(url_s)
            if not d_s or auto["domini_provati"].get("seme:" + d_s):
                continue
            auto["domini_provati"]["seme:" + d_s] = adesso.isoformat()
            fatti_s += 1
            if d_s in noti or st_s not in paesi:
                continue
            try:
                u_s = trova_feed(d_s)
            except Exception:
                u_s = None
            if u_s and u_s not in {x["url"] for x in auto["scoperte"]}:
                f_s = {"nome": f"{ente_s} ({st_s})", "url": u_s, "tema": "Voci ufficiali e organismi internazionali",
                       "aggiunta": adesso.date().isoformat(), "stato": st_s, "lv": "C", "liv": "di parte", "ufficiale": True}
                lg_s = lingue_di(st_s)
                if lg_s and lg_s[0][0] not in ("it", "en"):
                    f_s["lingua"] = lg_s[0][0]
                auto["scoperte"].append(f_s)
                nuove.append(f_s)
                noti.add(d_s)
    scrivi_json(os.path.join(DATI, "fonti_auto.json"), auto)

    # 7. Archivio e uscita per il Castello
    limite = (adesso - timedelta(days=cfg.get("giorni_archivio", 7))).isoformat()
    scade_ = (adesso - timedelta(hours=cfg.get("cervello", {}).get("attesa_ore", 36))).isoformat()
    archivio["attesa"] = {k: v for k, v in archivio.get("attesa", {}).items() if v.get("no") or (v.get("data_iso") or "") >= scade_}
    for tipo in ("notizie", "video", "attesa"):
        archivio[tipo] = {k: v for k, v in archivio.get(tipo, {}).items() if (v.get("data_iso") or "") >= limite}
    scrivi_json(os.path.join(DATI, "archivio.json"), archivio)
    scrivi_json(os.path.join(DATI, "canali.json"), canali)
    recente = (adesso - timedelta(hours=cfg.get("ore_live", 72))).isoformat()
    rotte_ = [(f.get("nome", f["url"]), auto["stato"].get(f["url"], {}).get("fila", 0))
              for f in elenco_fonti(cfg, mie, auto) if f["tipo"] in ("fissa", "mia")]
    # titoli in altre lingue rimasti senza traduzione da più di 6 ore: vanno al Paese della loro testata
    sei_ore_ = (adesso - timedelta(hours=6)).isoformat()
    for v_ in archivio["notizie"].values():
        if v_.get("rip") and not v_.get("paesi") and (v_.get("visto") or "") < sei_ore_:
            v_["paesi"] = [v_["rip"]]
    analisi = analizza(archivio, recente, auto, cfg, chiavi, dati_cielo, paesi, rotte_)
    scrivi_json(os.path.join(DATI, "fonti_auto.json"), auto)
    brief = cervello(chiavi, cfg, archivio, recente, ric, errori)
    # esito delle verifiche attive: «confermata» se adesso un'altra fonte affidabile riporta lo stesso fatto
    ver_giro = [len(in_verifica), 0]
    if in_verifica:
        R_ = leggi_json(os.path.join(DATI, "ricerche.json"), {})
        for k_ in in_verifica:
            v_ = archivio["notizie"].get(k_)
            if not v_:
                continue
            ok_ = bool(v_.get("conf")) or k_ in conferme_ver
            v_["ver"] = "confermata" if ok_ else "nessuna conferma"
            ver_giro[1] += 1 if ok_ else 0
            R_.setdefault("verifiche", []).append([adesso.strftime("%Y-%m-%d"), v_.get("it") or v_["t"], v_.get("fonte", ""),
                                                   v_.get("lv", ""), v_["ver"], v_.get("u", ""), conferme_ver.get(k_, "")])
        R_["verifiche"] = R_.get("verifiche", [])[-80:]
        scrivi_json(os.path.join(DATI, "ricerche.json"), R_)
    scrivi_json(os.path.join(DATI, "archivio.json"), archivio)  # con conferme, gruppi, verifiche e traduzioni
    analisi["segnali"] = segnali_stati(archivio, recente, analisi, dati_cielo, dati_calore)
    analisi["peggiora"] = andamento_stati(archivio)
    analisi["miglioratore"] = miglioratore(cfg, chiavi, analisi, auto, errori)
    scrivi_json(os.path.join(DATI, "fonti_auto.json"), auto)  # con i siti proposti dal cervello
    mem_nuovi, mem_totale = memoria_stati(archivio, adesso, cfg)
    scrivi_json(os.path.join(DATI, "analisi.json"), analisi)

    def elenco(tipo, massimo):
        voci = [v for v in archivio[tipo].values() if (v.get("data_iso") or "") >= recente]
        voci.sort(key=lambda v: v.get("data_iso") or "", reverse=True)
        uscita, per_fonte, tetto_f = [], {}, max(25, massimo // 25)
        for v in voci:
            if len(uscita) >= massimo:
                break
            f_ = v.get("fonte") or ""
            per_fonte[f_] = per_fonte.get(f_, 0) + 1
            if per_fonte[f_] > tetto_f and not v.get("conf"):
                continue
            w = dict(v)
            w["data"] = mostra_data(w.pop("data_iso", None))
            w.pop("visto", None)
            uscita.append(w)
        return uscita

    tutte = elenco_fonti(cfg, mie, auto)
    attive = [f for f in tutte if auto["stato"].get(f["url"], {}).get("ok")]
    errori[:] = riassumi_errori(errori)
    if not RETE["su"]:
        st_r = leggi_json(os.path.join(DATI, "rete.json"), {})
        if not st_r.get("giu_dal"):
            scrivi_json(os.path.join(DATI, "rete.json"), {"giu_dal": adesso.isoformat(), "tentativi": 1})
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
        "ricerca": {"in_coda": len(leggi_json(os.path.join(DATI, "ricerche.json"), {}).get("code", [])),
                    "ultime": leggi_json(os.path.join(DATI, "ricerche.json"), {}).get("ultime", []),
                    "verifiche": leggi_json(os.path.join(DATI, "ricerche.json"), {}).get("verifiche", [])[-12:]},
        "sapere_stati": stati_studiati,
        "piano": piano_riassunto(cfg, paesi),
        "errori": errori,
    }
    # diario del giro: che cosa è entrato, da dove, quanto è costato ai siti (lo legge `rapporto`, va anche su GitHub)
    tappa("altro")
    lingue_nuove = {}
    for v_ in archivio["notizie"].values():
        if v_.get("visto") == adesso.isoformat() and v_.get("lg"):
            lingue_nuove[v_["lg"]] = lingue_nuove.get(v_["lg"], 0) + 1
    conto_c = leggi_json(os.path.join(DATI, "cervello.json"), {})
    diario = leggi_json(os.path.join(DATI, "diario.json"), [])
    tel_g = telefono()
    batt_ = leggi_json(os.path.join(DATI, "battito.json"), {})
    dopo_ = next((x.get("iso", "") for x in reversed(diario) if x.get("tipo") in ("completo", "leggero", None)), "")
    sosp_ = [x for x in (batt_.get("sosp") or []) if x[0] > dopo_]
    rs_p = live.get("piano") or {}
    diario.append({
        "quando": datetime.now().strftime("%d/%m %H:%M"), "iso": adesso.isoformat(), "v": VERSIONE,
        "tipo": "leggero" if leggero else "completo",
        "mb": round(BYTE["n"] / 1e6, 1), "tel": [tel_g.get("temp"), tel_g.get("batteria"), tel_g.get("in_carica")],
        "tetto": conto_c.get("tetto", ""), "a_ritmo": saltate_ritmo, "invariate": invariate,
        "passo": bool(conto_c.get("passo")), "sosp": [len(sosp_), sum(x[1] for x in sosp_)],
        "piano": piano_giro + [rs_p.get("i", 0), rs_p.get("totale", 0), rs_p.get("passata", 0)],
        "durata": int(time.time() - inizio_), "nuove": contati, "da": {k: v for k, v in tappe.items() if v},
        "live": analisi["notizie"], "confermate": analisi["confermate"], "quota": analisi["quota_confermate"],
        "livelli": analisi["per_livello"], "scoperti": analisi["stati_scoperti"],
        "senza": sorted(s_ for s_ in paesi if not analisi["per_stato"].get(s_)),
        "fonti": [len(attive), len(tutte)],
        "fonti_nuove": [f["nome"] + (" (" + f["stato"] + ")" if f.get("stato") and f["stato"] not in f["nome"] else "") for f in nuove],
        "tg_trovati": [c["canale"] for c in auto.get("telegram", [])], "sapere": stati_studiati,
        "memoria": [mem_nuovi, mem_totale], "ricerche": live["ricerca"]["ultime"],
        "seguiti": [n_seguiti, nuove_seguiti], "verifiche": ver_giro,
        "lingue": {k_: v_ for k_, v_ in sorted(lingue_nuove.items(), key=lambda x: -x[1])[:25]},
        "attesa": conto_c.get("attesa", [0, 0, len([1 for v_ in archivio.get("attesa", {}).values() if not v_.get("no")])]),
        "richieste": sum(RICHIESTE.values()), "siti": sorted(RICHIESTE.items(), key=lambda x: -x[1])[:6],
        "rifiuti": dict(RIFIUTI), "errori": len(errori), "usd_oggi": conto_c.get("usd_oggi", 0),
        "usd_mese": conto_c.get("usd_mese", 0), "tradotti": sum(1 for v in archivio["notizie"].values() if v.get("it")),
    })
    scrivi_json(os.path.join(DATI, "diario.json"), diario[-120:])
    live["diario"] = [{k: v for k, v in x.items() if k not in ("ricerche", "siti")} for x in diario[-60:]]  # per la pagina
    try:
        shutil.copyfile(os.path.join(DATI, "diario.json"), os.path.join(WEB, "diario.json"))
        mem_ = leggi_json(os.path.join(DATI, "memoria.json"), {})
        with open(os.path.join(WEB, "memoria.js.tmp"), "w", encoding="utf-8") as f:
            f.write("window.MEMORIA=" + json.dumps({k: [[x[0], x[1], x[2], x[3], x[4], x[6] if len(x) > 6 else ""] for x in l]
                                                    for k, l in mem_.items()}, ensure_ascii=False, separators=(",", ":")) + ";")
        os.replace(os.path.join(WEB, "memoria.js.tmp"), os.path.join(WEB, "memoria.js"))
    except OSError:
        pass
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
        sincronizza(cfg, chiavi, solo_diario=leggero)


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
    snap["diario"] = (live.get("diario") or [])[-30:]  # la pagina su claude.ai resta leggera
    if snap.get("analisi"):
        snap["analisi"] = {k: v for k, v in snap["analisi"].items() if k != "per_stato"}  # più leggero
        seg_ = snap["analisi"].get("segnali") or {}
        if len(seg_) > 25:  # nella pagina bastano i 25 Stati con più segnali (sono già in ordine): resta leggera
            snap["analisi"]["segnali"] = dict(list(seg_.items())[:25])
    if (snap.get("brief") or {}).get("testo"):
        snap["brief"] = dict(snap["brief"], testo=pulisci_brief(snap["brief"]["testo"]))
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

def sincronizza(cfg=None, chiavi=None, solo_diario=False):
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
        elif subprocess.run(["git", "-C", cartella, "pull", "--ff-only"]).returncode != 0:
            # la cartella di scambio si è disallineata (es. un invio non riuscito): si riallinea al repository.
            # Non si perde nulla: i dati del telefono vengono ricopiati qui sotto a ogni giro.
            subprocess.run(["git", "-C", cartella, "fetch", "--depth", "1", "origin"], check=True)
            subprocess.run(["git", "-C", cartella, "reset", "--hard", "FETCH_HEAD"], check=True)
        # nuove versioni del programma, se Claude le ha messe nel repository (cartella programma/)
        cambiati = []
        for nome in ("castello.py", "config.json", "paesi.json", "mappa.json", "LEGGIMI.txt", "piano_base.json"):
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
        if os.path.exists(os.path.join(cartella, "tabelle.html")):  # le prepara Claude nel repository: il telefono le riceve
            shutil.copyfile(os.path.join(cartella, "tabelle.html"), os.path.join(WEB, "tabelle.html"))
            if os.path.isdir(os.path.join(cartella, "tabelle")):
                shutil.copytree(os.path.join(cartella, "tabelle"), os.path.join(WEB, "tabelle"), dirs_exist_ok=True)
        # dopo un giro leggero su GitHub va solo il diario (pochi KB): i dati grossi ci vanno ogni 3 ore, così il
        # repository non cresce tre volte più in fretta
        for nome in (("diario.json",) if solo_diario else ("live.json", "live.js", "sapere.js", "memoria.js", "piano.js", "diario.json")):
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

    def do_GET(self):
        if self.path.split("?")[0] == "/vivo":  # lo chiede il guardiano: chi sei, e che versione
            corpo = ("pangeo " + VERSIONE).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        super().do_GET()


def serve(porta=8080):
    os.makedirs(DATI, exist_ok=True)
    os.makedirs(WEB, exist_ok=True)
    gestore = functools.partial(Gestore, directory=WEB)
    srv = None
    for tentativo_ in range(5):
        try:
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", porta), gestore)
            break
        except OSError as e:
            if _vivo(porta) == VERSIONE or tentativo_ == 4:
                print(f"La porta {porta} è già occupata: PanGeo è già acceso, oppure la usa un altro programma ({e}).")
                return
            time.sleep(1.5)  # la pagina di prima si sta ancora chiudendo (riavvio con avvia.sh)
    for nome_ in ("SIGTERM", "SIGINT", "SIGHUP"):
        try:
            signal.signal(getattr(signal, nome_), _segnale)
        except (AttributeError, ValueError, OSError):
            pass

    def _avvio():  # dietro le quinte, così la pagina risponde subito anche se un comando del telefono è lento
        try:
            scatola_nera()  # se era rimasto fermo, lo scrive nel diario con il motivo più probabile
        except Exception as e:
            print("Scatola nera:", e)
        threading.Thread(target=_battito, daemon=True).start()
        try:
            _tieni_sveglio()
            _avvio_al_riavvio()
            _avvio_con_termux()
            programma_cron(leggi_json(os.path.join(QUI, "config.json"), {}))
            _lavoro_android()
        except Exception as e:
            print("Avvio:", e)

    threading.Thread(target=_avvio, daemon=True).start()
    threading.Thread(target=_riserva_cron, daemon=True).start()
    with srv:
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
        if mg.get("rapporto"):
            print(f"Rapporto del cervello ({mg.get('rapporto_giorno', '')}):")
            print(mg["rapporto"])
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
    rc = live.get("ricerca") or {}
    if rc:
        print(f"Ricerca autonoma: {rc.get('in_coda', 0)} ricerche in coda · Stati studiati su Wikipedia: {live.get('sapere_stati', 0)}")
        for q_, nuove_, prove_, da_ in (r_[:4] for r_ in rc.get("ultime", [])):
            print(f"  {nuove_} notizie nuove in {prove_} prove ({da_}): {q_[:70]}")
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
    for nome in ("archivio.json", "live.json", "analisi.json", "fonti_auto.json", "storico_stati.json", "miglioratore.json", "diario.json", "memoria.json"):
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
    try:
        tab_ = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        vivo_ = _cron_vivo()
        print("  giro automatico ogni 3 ore:", "programmato" if "castello.py aggiorna" in tab_ else "NON programmato (bash installa.sh)",
              "·", "attivo" if vivo_ else "FERMO: lancia  bash avvia.sh")
    except OSError:
        print("  giro automatico: qui non si può controllare")
    try:
        ore_ = (time.time() - os.path.getmtime(os.path.join(DATI, "live.json"))) / 3600
        if ore_ > 4:
            print(f"  ATTENZIONE: l'ultimo giro è di {ore_:.0f} ore fa. Lancia  bash avvia.sh  e lascia Termux aperto.")
    except OSError:
        pass
    print("  giri nel diario:", len(leggi_json(os.path.join(DATI, "diario.json"), [])), "· per il riepilogo:  python castello.py rapporto")
    print("Cuore sano." if ok else "Qualcosa non va: guarda le righe con ROTTO o VUOTO.")


if __name__ == "__main__":
    a = sys.argv[1:]
    comando = a[0] if a else "aiuto"
    if comando == "aggiorna":
        aggiorna(a[1] if len(a) > 1 else "")
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
            # il guardiano della versione nuova spegne la pagina vecchia e accende la nuova: non serve altro
            subprocess.run([sys.executable, os.path.join(QUI, "castello.py"), "veglia"], check=False)
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
    elif comando == "veglia":
        veglia(parla=not (len(a) > 1 and a[1] == "zitto"))
    elif comando == "domande":
        domande()
    elif comando == "piano":
        cmd_piano()
    elif comando == "giri":
        giri(int(a[1]) if len(a) > 1 and a[1].isdigit() else 12)
    elif comando == "rapporto":
        rapporto(int(a[1]) if len(a) > 1 and a[1].isdigit() else 24)
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

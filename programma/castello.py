#!/usr/bin/env python3
"""PanGeo 2.22 (prima «Castello mentale») - programma per Termux (Android) e per qualsiasi computer con Python 3.

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
  python castello.py ricostruisci          dopo una reinstallazione: rimette pagina e dati presi da GitHub (le chiavi no)
  python castello.py istantanea index.html [origine] [--brief file.txt]
                                           mette i dati live (e un riassunto) dentro un file del Castello
  python castello.py ripristina index.html  riprende lo storico del cielo da un file del Castello
Usa solo la libreria standard di Python: nessun pacchetto da installare.
"""
import concurrent.futures
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

VERSIONE = "2.33.6"
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
# copia di riserva su GitHub dei file di lavoro (una volta al giorno, dentro riserva.json). MAI chiavi.json: le chiavi
# non escono dal telefono. Diario, memoria, sapere, piano e ultime notizie sono già nel repository per conto loro.
RISERVA = ["fonti_auto.json", "fonti_mie.json", "ricerche.json", "cervello.json", "storico_stati.json",
           "miglioratore.json", "impostazioni_auto.json", "canali.json", "lingue.json", "copertura.json", "quadro.json"]
RISERVA_STORICI = ["cielo_storico.json", "calore_storico.json"]  # serie di 7 giorni: nella riserva va un campione all'ora
# Gli script di questa versione, con la loro impronta (SHA-256). Quando approvi il programma approvi anche questi: il telefono
# li prende da GitHub solo se l'impronta è la stessa scritta qui. Uno script cambiato dopo aspetta un nuovo «approva».
SCRIPT = {"avvia.sh": "b3395152b30e3f8614296feea714ea28dc4984747b79e8bd9cabece87b5cad9c", "github.sh": "82e68b06381b6a44634b518c0d4c054b4a4e8da6ae15c199f701aeff7f528ed1", "installa.sh": "43e36d11baca2f524e3d7434bfc962aa297d5744147e64ab0ff46eaddb9301d9", "ripara.sh": "3360b86c5b5f5feefe9c113f7dbc9eda758f8c4466fc8c34e03c7f281d5c73ea"}
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
_LUCCHETTO = threading.Lock()  # dalla 2.32: contatori e attese per sito condivisi dai download in parallelo
_SITI_LOCK = {}


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
    with _LUCCHETTO:
        l_sito = _SITI_LOCK.setdefault(d_, threading.Lock())
    with l_sito:  # anche con i download in parallelo, allo stesso sito una richiesta ogni 2 secondi
        attesa_ = 2.0 - (time.time() - _ULTIMA.get(d_, 0))
        if attesa_ > 0:
            time.sleep(attesa_)
        _ULTIMA[d_] = time.time()
    # «Accept-Encoding: gzip»: i feed viaggiano compressi (da 4 a 8 volte meno dati)
    h = {"User-Agent": UA, "Accept-Language": "it,en;q=0.8", "Accept-Encoding": "gzip"}
    h.update(intestazioni or {})
    req = urllib.request.Request(url, headers=h, data=corpo)
    with _LUCCHETTO:
        RICHIESTE[d_] = RICHIESTE.get(d_, 0) + 1
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            dati_ = r.read()
            with _LUCCHETTO:
                BYTE["n"] += len(dati_)  # quanti dati consuma un giro (va nel diario, in MB)
            if risposta is not None:  # per chiedere, la volta dopo, «solo se è cambiato»
                risposta["etag"], risposta["lm"] = r.headers.get("ETag") or "", r.headers.get("Last-Modified") or ""
            compr_ = (r.headers.get("Content-Encoding") or "").lower()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            with _LUCCHETTO:
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


def telegram(canale, citati=None, yt=None):
    """Legge l'anteprima pubblica di un canale Telegram (t.me/s/...), senza account.
    Dalla 2.30 raccoglie anche i video e i canali YouTube citati (yt), per trovare canali nuovi da soli."""
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
        if yt is not None:
            youtube_da_link(blocco, yt, canale)
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


MARCHI_FONTI = ("bbc", "dw", "rfi", "france 24", "al jazeera", "tass", "yle", "err", "lsm", "lrt", "nhk", "antara", "yonhap",
                "vnexpress", "el país", "n1", "meduza", "ukrainska pravda", "the local", "euronews", "reuters",
                "associated press", "ansa", "agi", "efe", "xinhua", "trt", "iran international", "rtp", "rtve", "rts", "srf",
                "orf", "nos", "nrk", "svt", "dr", "vrt", "rtbf")


def famiglia_fonte(nome):
    """La stessa testata in più lingue o sezioni (BBC in arabo e BBC World, Ukrainska Pravda in inglese e in ucraino,
    il canale Telegram di Meduza e il suo sito) è UNA fonte: non può confermare sé stessa (dalla 2.28)."""
    n = (nome or "").lower().strip()
    n = re.sub(r"^telegram\s*·\s*", "", n)
    n = re.sub(r"\s*\(.*?\)", "", n).split(",")[0].strip()
    n = re.sub(r"\s+in\s+[a-zà-ù]+$", "", n).strip()
    for m_ in MARCHI_FONTI:
        if n == m_ or (m_ != "dr" and n.startswith(m_ + " ")):
            return m_
    return n


_LV_ORDINE = {"A": 0, "B": 1, "C": 2, "D": 3}


def confermata(fonti, fonte):
    """Vero se nel gruppo c'è almeno una fonte affidabile (A o B) di un'altra testata."""
    proprio = famiglia_fonte(fonte)
    return any(l in ("A", "B") for f, l in fonti.items() if f != proprio)


def raggruppa(voci):
    """Unisce le notizie che parlano dello stesso fatto (titoli molto simili, entro 48 ore).
    Dalla 2.28 confronta il testo italiano quando c'è: così un titolo in russo, uno in arabo e uno in inglese sullo
    stesso fatto si confermano a vicenda (prima i titoli in altri alfabeti non si confrontavano con nessuno).
    Le fonti di un gruppo sono contate per testata (famiglia_fonte), con il livello migliore.
    Restituisce per ogni voce l'indice del suo gruppo."""
    gruppi, indice, esito = [], {}, {}
    for k, v in sorted(voci.items(), key=lambda x: x[1].get("data_iso") or ""):
        p = parole(v.get("it") or v["t"])
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
        fam_, lv_ = famiglia_fonte(v.get("fonte", "")), v.get("lv", "D")
        prima_ = gruppi[scelto]["fonti"].get(fam_)
        if prima_ is None or _LV_ORDINE.get(lv_, 3) < _LV_ORDINE.get(prima_, 3):
            gruppi[scelto]["fonti"][fam_] = lv_
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
        v["nf"] = len(fonti)
        v["gr"] = esito[k]  # gruppo dello stesso fatto in questo giro (serve alla memoria)
        v["conf"] = confermata(fonti, v.get("fonte"))
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
        # dalla 2.33.5 anche il totale di sempre (parte dalla spesa del mese in cui nasce il campo)
        conto["usd_totale"] = round((conto["usd_totale"] if "usd_totale" in conto else conto["usd_mese"] - d) + d, 5)
        # dalla 2.33.6 la memoria dello scorrere del tempo: la spesa di ogni mese e degli ultimi 400 giorni
        conto.setdefault("mesi", {})[mese] = conto["usd_mese"]
        g_ = conto.setdefault("giorni", {})
        g_[datetime.now().date().isoformat()] = conto["usd_oggi"]
        if len(g_) > 400:
            conto["giorni"] = dict(sorted(g_.items())[-400:])
        conto["token_oggi"] = conto.get("token_oggi", 0) + en + us
        l_ = lavoro_di(testo)  # dalla 2.27: quanto costa ogni lavoro (per sapere che cosa conviene far fare al telefono)
        for campo_ in ("lavori_oggi", "lavori_mese"):
            conto.setdefault(campo_, {})
            conto[campo_][l_] = round(conto[campo_].get(l_, 0.0) + d, 5)
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
                 "mese": conto.get("mese"), "usd_mese": conto.get("usd_mese", 0.0),
                 **{k_: conto[k_] for k_ in ("usd_totale", "mesi", "giorni") if k_ in conto},
                 "lavori_mese": conto.get("lavori_mese", {}) if conto.get("mese") == datetime.now().strftime("%Y-%m") else {}}
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
    try:  # dalla 2.27: le lingue che il traduttore del telefono sa fare le traduce lui, gratis
        da_tradurre = officina_traduci(da_tradurre, cfg, ric, errori)
    except Exception as e:
        errori.append(f"Officina (traduzioni): {str(e)[:100]}")
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
    filtrati_ = 0
    try:  # dalla 2.28: il filtro che impara dalle scelte del cervello ordina la coda e toglie i titoli sicuramente inutili
        filtro_primi_esempi(archivio)
        in_coda, filtrati_ = filtro_attesa(in_coda, cfg, errori)
    except Exception as e:
        errori.append(f"Filtro della sala d'attesa: {str(e)[:100]}")
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
                    filtro_esempio(v.get("t"), False, v.get("fonte"), v.pop("ctrl", False))
                    continue
                filtro_esempio(v.get("t"), True, v.get("fonte"), v.pop("ctrl", False))
                v.pop("fp", None)
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
    conto["attesa"] = [entrate_, scartate_, sum(1 for v in attesa.values() if not v.get("no")), filtrati_]
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
    # 1c. i servizi di intelligence (dalla 2.23): dalla voce di Wikipedia un riassunto in italiano di una o due frasi
    Sv = leggi_json(os.path.join(DATI, "servizi.json"), {})
    da_v = [q for q, v in Sv.items() if v.get("testo") and not v.get("sintesi")][:impost.get("servizi_per_giro", 10)]
    if da_v and conto["chiamate"] < tetto:
        domanda = ("Per ogni servizio di informazione e di sicurezza qui sotto scrivi un riassunto in italiano di una o due frasi, "
                   "al massimo 300 caratteri: che cosa fa (informazioni all'estero, sicurezza interna, militare, intercettazioni o "
                   "altro), da chi dipende, quando è nato e da quale servizio deriva, se il testo lo dice. Usa SOLO il testo dato e "
                   "non aggiungere nulla. Niente nomi di persone, niente indirizzi, niente giudizi. Una riga per servizio, nello "
                   "stesso ordine e con lo stesso numero davanti, senza commenti:\n" +
                   "\n".join(f"{i + 1}. {Sv[q].get('nome', '')} ({Sv[q].get('stato', '')}): {Sv[q]['testo']}" for i, q in enumerate(da_v)))
        try:
            risposta = chiedi_claude(chiavi, cfg, domanda, 1800, conto)
            conto["chiamate"] += 1
            for riga in risposta.splitlines():
                m = numerata.match(riga)
                if m and 0 < int(m.group(1)) <= len(da_v) and len(m.group(2).strip()) > 20:
                    Sv[da_v[int(m.group(1)) - 1]]["sintesi"] = pulisci(m.group(2), 400)
            scrivi_servizi(Sv)
        except Exception as e:
            errori.append(f"Claude (riassunto dei servizi): {re.sub(r'sk-ant-[A-Za-z0-9_-]+', '***', str(e))}")
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


# ----------------------------------------------------------------------------- servizi di intelligence (dalla 2.23)

def _wiki_json(lingua, parametri):
    """Una richiesta all'API di Wikipedia, con una sola attesa se il sito chiede di rallentare (429)."""
    url = f"https://{lingua}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(dict(parametri, format="json"))
    ua = {"User-Agent": "PanGeo/" + VERSIONE + " (https://github.com/54v0B3110CCH1/pangeo; archivio personale, poche richieste)"}
    try:
        return json.loads(scarica(url, timeout=30, intestazioni=ua))
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        try:
            attesa = min(int(e.headers.get("retry-after") or 5), 20)
        except ValueError:
            attesa = 5
        time.sleep(attesa + 2)
        return json.loads(scarica(url, timeout=30, intestazioni=ua))


def wikipedia_voce(url, massimo=900):
    """L'inizio di una voce di Wikipedia dato il suo indirizzo. Se la voce è in un'altra lingua e esiste quella in
    italiano, prende quella in italiano. Restituisce titolo, testo, indirizzo e lingua, oppure None."""
    m = re.match(r"https?://([a-z-]+)\.wikipedia\.org/wiki/(.+)$", url or "")
    if not m:
        return None
    lingua, titolo = m.group(1), urllib.parse.unquote(m.group(2)).replace("_", " ")
    for _ in range(2):
        r = _wiki_json(lingua, {"action": "query", "titles": titolo, "prop": "extracts|info|langlinks", "exintro": "1",
                                "explaintext": "1", "inprop": "url", "lllang": "it", "redirects": "1"})
        pag = next(iter((r.get("query", {}).get("pages") or {}).values()), {})
        it_ = (pag.get("langlinks") or [{}])[0].get("*")
        if lingua != "it" and it_:
            lingua, titolo = "it", it_  # c'è la voce in italiano: si legge quella
            continue
        testo = re.sub(r"\s+", " ", pag.get("extract") or "").strip()
        if len(testo) < 80:
            return None
        if len(testo) > massimo:
            taglio = testo.rfind(". ", 0, massimo)
            testo = testo[: taglio + 1] if taglio > 250 else testo[:massimo] + "…"
        return {"titolo": pag.get("title", titolo), "testo": testo, "url": solo_http(pag.get("fullurl", "")) or url, "lingua": lingua}
    return None


def elenco_servizi():
    """L'elenco dei servizi di ogni Stato preparato da Claude (tools/dati/intel.json nel repository):
    {Stato: [[nome, anno, voce di Wikipedia, sito ufficiale, codice Wikidata], ...]}."""
    for perc in (os.path.join(DATI, "repo", "tools", "dati", "intel.json"), os.path.join(QUI, "intel.json")):
        stati = leggi_json(perc, {}).get("stati") if os.path.exists(perc) else None
        if isinstance(stati, dict) and stati:
            return stati
    return {}


def scrivi_servizi(S_):
    """servizi.json per il programma, servizi.js per la pagina (solo i riassunti fatti)."""
    scrivi_json(os.path.join(DATI, "servizi.json"), S_)
    pagina = {q: {"s": v["sintesi"], "t": v.get("titolo", ""), "u": v.get("url", ""), "d": v.get("data", ""), "l": v.get("lingua", "")}
              for q, v in S_.items() if v.get("sintesi")}
    with open(os.path.join(WEB, "servizi.js.tmp"), "w", encoding="utf-8") as f:
        f.write("window.SERVIZI = " + json.dumps(pagina, ensure_ascii=False, separators=(",", ":")) + ";\n")
    os.replace(os.path.join(WEB, "servizi.js.tmp"), os.path.join(WEB, "servizi.js"))


def studia_servizi(cfg, errori, adesso):
    """Come per gli Stati: pochi servizi a giro, letti su Wikipedia (prima in italiano). Il riassunto in italiano lo scrive
    poi il cervello (vedi cervello(), punto 1c). Ogni voce si rilegge dopo servizi.giorni giorni (predefinito 120)."""
    imp = cfg.get("servizi", {})
    perc = os.path.join(DATI, "servizi.json")
    S_ = leggi_json(perc, {})
    if not S_:  # prima volta o dopo una reinstallazione: parte dai riassunti già sul sito, senza pagarli due volte
        try:
            for q, v in _js_dati(os.path.join(DATI, "repo", "servizi.js")).items():
                S_[q] = {"sintesi": v.get("s", ""), "titolo": v.get("t", ""), "url": v.get("u", ""), "data": v.get("d", ""),
                         "lingua": v.get("l", "")}
        except (OSError, ValueError):
            S_ = {}
    if not imp.get("attivo", True):
        return sum(1 for v in S_.values() if v.get("sintesi"))
    elenco = elenco_servizi()
    vecchio = (adesso - timedelta(days=imp.get("giorni", 120))).date().isoformat()
    da_fare = [(st_, x) for st_, l in sorted(elenco.items()) for x in l
               if len(x) > 4 and x[4] and x[2] and S_.get(x[4], {}).get("data", "") < vecchio][:imp.get("per_giro", 8)]
    for st_, x in da_fare:
        try:
            v = wikipedia_voce(x[2])
        except Exception as e:
            errori.append(f"Wikipedia (servizi): {e}")
            break  # il sito non risponde: si riprova al prossimo giro
        prima = S_.get(x[4], {})
        nuovo = {"stato": st_, "nome": x[0], "data": adesso.date().isoformat()}
        if v:
            nuovo.update(v)
            if prima.get("sintesi") and prima.get("testo") == v["testo"]:
                nuovo["sintesi"] = prima["sintesi"]  # stesso testo: il riassunto resta, non si paga due volte
        elif prima.get("sintesi"):
            nuovo.update({k: prima[k] for k in ("sintesi", "titolo", "url", "lingua") if k in prima})
        S_[x[4]] = nuovo
    if da_fare or (S_ and not os.path.exists(os.path.join(WEB, "servizi.js"))):
        scrivi_servizi(S_)
    return sum(1 for v in S_.values() if v.get("sintesi"))


# ----------------------------------------------------------------------------- siti militari da Wikidata (dalla 2.24)

BASI_CLASSI = {
    "Q245016": "base militare", "Q695850": "base aerea", "Q1324633": "base navale", "Q6981985": "base aeronavale",
    "Q331367": "base di sottomarini", "Q2604714": "base operativa avanzata", "Q2886620": "base militare",
    "Q21193688": "base missilistica", "Q136558797": "base dell’esercito", "Q136644356": "base militare",
    "Q141816817": "base navale", "Q85881832": "base militare", "Q7373622": "base aerea", "Q1778846": "area di addestramento",
    "Q133288241": "stazione radar", "Q6646468": "stazione di ascolto", "Q55624858": "base navale",
    "Q105622437": "base della guardia costiera", "Q1428515": "base aerea", "Q7619063": "base navale",
    "Q142188473": "base navale", "Q1198413": "campo militare", "Q29918961": "centro di addestramento", "Q1593547": "base aerea"}
# «optimizer None» e le classi per prime: così Wikidata parte dalle poche migliaia di siti militari e non da tutto ciò che
# sta in uno Stato. Senza, per gli Stati grandi la risposta non arriva (504); con, arriva in pochi secondi.
BASI_Q = """SELECT ?s ?sLabel ?d ?cls ?opLabel ?opIso ?luogoLabel ?coord ?fine ?it ?en ?link WHERE {
  hint:Query hint:optimizer "None" .
  VALUES ?cls { %s }
  ?s wdt:P31 ?cls ; wdt:P17 ?c . ?c wdt:P298 "%s" .
  OPTIONAL { ?s wdt:P137 ?op . OPTIONAL { ?op wdt:P17 ?oc . ?oc wdt:P298 ?opIso } }
  OPTIONAL { ?s wdt:P131 ?luogo }
  OPTIONAL { ?s wdt:P625 ?coord }
  OPTIONAL { ?s wdt:P576|wdt:P3999|wdt:P582|wdt:P2669 ?fine }
  OPTIONAL { ?s schema:description ?d FILTER(lang(?d)="en") }
  OPTIONAL { ?it schema:about ?s ; schema:isPartOf <https://it.wikipedia.org/> }
  OPTIONAL { ?en schema:about ?s ; schema:isPartOf <https://en.wikipedia.org/> }
  ?s wikibase:sitelinks ?link .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}"""
# forze armate che non esistono più: un sito gestito solo da loro è storico, anche se Wikidata non ha la data di chiusura
BASI_GESTORE_STORICO = re.compile(r"Army Air Forces|Army Air Corps|Regia Aeronautica|Regia Marina|Regio Esercito|Wehrmacht|Kriegsmarine|"
                                  r"Luftstreitkräfte|Imperial Japanese|Soviet|sovietic|Royal Flying Corps|Red Army|Armata Rossa|"
                                  r"Confederate|Austro-Hungarian|austro-ungaric", re.I)
BASI_CHIUSO = re.compile(r"\b(former|formerly|ex-|defunct|closed|disused|abandoned|decommissioned|demolished|historic|world war|wwii|ww2)\b", re.I)


def _basi_leggi(righe, iso_stato, massimo=300):
    """Le righe di Wikidata diventano l'elenco dei siti di uno Stato: nome, tipo, luogo, chi lo gestisce, se risulta chiuso.
    Le coordinate si tengono a un decimo di grado (livello di città), come per le altre basi di PanGeo."""
    siti = {}
    for x in righe:
        g = lambda n: (x.get(n) or {}).get("value", "")
        q = g("s").rsplit("/", 1)[-1]
        nome = pulisci(g("sLabel"), 120)
        if not q or not nome or re.fullmatch(r"Q\d+", nome):
            continue  # senza un nome leggibile non si mostra
        e = siti.setdefault(q, {"q": q, "n": nome, "t": BASI_CLASSI.get(g("cls").rsplit("/", 1)[-1], "sito militare"), "l": "",
                                "g": [], "gs": [], "ch": False, "w": solo_http(g("it") or g("en")), "k": int(g("link") or 0)})
        if g("luogoLabel") and not e["l"] and not re.fullmatch(r"Q\d+", g("luogoLabel")):
            e["l"] = pulisci(g("luogoLabel"), 80)
        if g("opLabel") and not re.fullmatch(r"Q\d+", g("opLabel")) and g("opLabel") not in e["g"]:
            e["g"].append(pulisci(g("opLabel"), 80))
        st_op = iso_stato.get(g("opIso"))
        if st_op and st_op not in e["gs"]:
            e["gs"].append(st_op)
        if g("fine") or BASI_CHIUSO.search(g("d")):
            e["ch"] = True
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", g("coord"))
        if m and "c" not in e:
            e["c"] = [round(float(m.group(1)), 1), round(float(m.group(2)), 1)]
    for e in siti.values():
        if e["g"] and all(BASI_GESTORE_STORICO.search(x) for x in e["g"]):
            e["ch"] = True
    scelti = sorted(siti.values(), key=lambda e: (e["ch"], -e["k"], e["n"]))[:massimo]
    for e in scelti:
        e["g"], e["gs"] = e["g"][:3], e["gs"][:3]
        for k in ("l", "w"):
            if not e[k]:
                del e[k]
        for k in ("g", "gs"):
            if not e[k]:
                del e[k]
        if not e["ch"]:
            del e["ch"]
        del e["k"]
    return scelti


def scrivi_basi(B):
    scrivi_json(os.path.join(DATI, "basi_wd.json"), B)
    with open(os.path.join(WEB, "basi.js.tmp"), "w", encoding="utf-8") as f:
        f.write("window.BASI_WD = " + json.dumps({"agg": B.get("agg", ""), "stati": B.get("stati", {}), "letti": B.get("letti", {})},
                                                  ensure_ascii=False, separators=(",", ":")) + ";\n")
    os.replace(os.path.join(WEB, "basi.js.tmp"), os.path.join(WEB, "basi.js"))


def siti_militari(cfg, paesi, errori, adesso):
    """Un pezzo alla volta: a ogni giro il programma chiede a Wikidata i siti militari di UNO Stato (basi, basi aeree e
    navali, aree di addestramento, stazioni radar) e chi li gestisce. In qualche giorno copre tutti gli Stati, poi
    ricomincia dopo siti_militari.giorni giorni. Wikidata non sempre registra le chiusure: ogni sito porta il suo stato."""
    imp = cfg.get("siti_militari", {})
    perc = os.path.join(DATI, "basi_wd.json")
    B = leggi_json(perc, {})
    if not B.get("stati"):  # prima volta o dopo una reinstallazione: riparte da ciò che è già sul sito
        try:
            B = _js_dati(os.path.join(DATI, "repo", "basi.js"))
        except (OSError, ValueError):
            B = {}
    B.setdefault("stati", {})
    B.setdefault("letti", {})
    iso = imp.get("iso", {})
    if not imp.get("attivo", True) or not iso:
        return len(B["letti"])
    iso_stato = {v: k for k, v in iso.items()}
    vecchio = (adesso - timedelta(days=imp.get("giorni", 90))).date().isoformat()
    da_fare = [s_ for s_ in paesi if s_ in iso and B["letti"].get(s_, "") < vecchio][:imp.get("per_giro", 1)]
    fatti = 0
    for st_ in da_fare:
        try:
            corpo = urllib.parse.urlencode({"query": BASI_Q % (" ".join("wd:" + k for k in BASI_CLASSI), iso[st_]), "format": "json"}).encode()
            r = json.loads(scarica("https://query.wikidata.org/sparql", timeout=90, corpo=corpo, intestazioni={
                "User-Agent": "PanGeo/" + VERSIONE + " (https://github.com/54v0B3110CCH1/pangeo; archivio personale, poche richieste)",
                "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/sparql-results+json"}))
            B["stati"][st_] = _basi_leggi(r.get("results", {}).get("bindings", []), iso_stato, imp.get("massimo", 300))
            B["letti"][st_] = adesso.date().isoformat()
            fatti += 1
        except Exception as e:
            errori.append(f"Wikidata (siti militari, {st_}): {e}")
            # il sito non risponde: stesso Stato al prossimo giro. Dopo 3 volte di fila si passa oltre e lo si riprova tra una
            # settimana, così uno Stato difficile non ferma tutti gli altri.
            B.setdefault("falliti", {})[st_] = B.get("falliti", {}).get(st_, 0) + 1
            if B["falliti"][st_] >= 3:
                B["falliti"][st_] = 0
                B["letti"][st_] = (adesso - timedelta(days=max(imp.get("giorni", 90) - 7, 0))).date().isoformat()
                B["stati"].setdefault(st_, [])
            scrivi_json(perc, B)
            break
    if fatti or (B["letti"] and not os.path.exists(os.path.join(WEB, "basi.js"))):
        B["agg"] = adesso.date().isoformat()
        scrivi_basi(B)
    return len(B["letti"])


# ----------------------------------------------------------------------------- memoria e diario

def memoria_stati(archivio, adesso, cfg, ore=30):
    """La memoria che cresce da sola: per ogni Stato i fatti confermati da più fonti, tenuti 120 giorni
    (al massimo 40 per Stato). È ciò che resta quando le notizie escono dall'archivio di 7 giorni."""
    perc = os.path.join(DATI, "memoria.json")
    M = leggi_json(perc, {})
    da_ = (adesso - timedelta(hours=ore)).isoformat()
    limite = (adesso - timedelta(days=cfg.get("memoria_giorni", 120))).date().isoformat()
    aggiunti, visti = [], set()
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
            aggiunti.append((st_, l[-1][1]))
    for st_ in list(M):
        M[st_] = sorted((x for x in M[st_] if x[0] >= limite), key=lambda x: x[0], reverse=True)[:cfg.get("memoria_per_stato", 40)]
        if not M[st_]:
            del M[st_]
    # nuovi sono solo quelli che restano: negli Stati con più di 40 fatti recenti quelli in più escono subito, e
    # prima della 2.25 venivano contati come nuovi a ogni giro
    nuovi = sum(1 for st_, testo_ in aggiunti if any(x[1] == testo_ for x in M.get(st_, [])))
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


# ----------------------------------------------------------------------------- rapporto ogni 12 ore (dalla 2.25)

SITO_PUBBLICO = "https://54v0b3110cch1.github.io/pangeo"
RAPPORTO_NOMI = {
    "giri": "giri", "voci_nuove": "voci nuove", "errori_medi": "avvisi per giro", "temp_max": "temperatura massima del telefono",
    "fermo_max": "fermo più lungo (minuti)", "live": "notizie degli ultimi 3 giorni", "quota": "notizie confermate da due fonti (%)",
    "d_pct": "notizie da fonti non classificate (%)", "senza_n": "Stati senza notizie", "fonti_attive": "fonti attive",
    "tradotti": "titoli tradotti", "memoria": "fatti confermati in memoria", "sapere": "Stati studiati su Wikipedia",
    "piano_stati": "Stati del lavoro a piano", "accordi": "accordi", "appalti": "appalti", "intel": "fatti sui servizi",
    "puzzle": "pezzi del puzzle", "servizi": "servizi di intelligence riassunti", "basi_stati": "Stati con i siti militari letti",
    "siti": "siti militari in elenco", "collegamenti": "collegamenti del quadro", "sintesi": "Stati con la sintesi",
    "magazzino_notizie": "notizie nel magazzino del telefono"}
# verso: +1 più è meglio, -1 meno è meglio; poi la differenza più piccola che conta («rel» in proporzione, «abs» in valore)
RAPPORTO_VERSO = {"giri": (1, "rel", 0.1), "voci_nuove": (1, "rel", 0.25), "errori_medi": (-1, "abs", 0.5),
                  "temp_max": (-1, "abs", 3), "fermo_max": (-1, "abs", 15), "live": (1, "rel", 0.03), "quota": (1, "abs", 1),
                  "d_pct": (-1, "abs", 1), "senza_n": (-1, "abs", 1), "fonti_attive": (1, "abs", 2), "tradotti": (1, "rel", 0.01),
                  "memoria": (1, "rel", 0.01), "sapere": (1, "abs", 1), "piano_stati": (1, "abs", 1), "accordi": (1, "abs", 1),
                  "appalti": (1, "abs", 1), "intel": (1, "abs", 1), "puzzle": (1, "abs", 1), "servizi": (1, "abs", 1),
                  "basi_stati": (1, "abs", 1), "siti": (1, "abs", 1), "collegamenti": (1, "abs", 1), "sintesi": (1, "abs", 1),
                  "magazzino_notizie": (1, "rel", 0.01)}


def _it(n, dec=0):
    """Numero all'italiana: 12.345 · 0,28."""
    if n is None:
        return "–"
    s = f"{n:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def _veri(giri):
    return [x for x in giri if x.get("tipo") in ("completo", "leggero", None)]


def _attivita(G, prima_di=None, fine=None):
    """Che cosa è successo in una finestra di giri del diario."""
    from statistics import median
    tipi = {}
    for x in G:
        tipi[x.get("tipo") or "completo"] = tipi.get(x.get("tipo") or "completo", 0) + 1
    Gt = [x for x in G if x.get("iso")]
    t = [datetime.fromisoformat(x["iso"]) for x in Gt]
    # un tratto senza rete non è un fermo: il telefono lavora lo stesso (fino alla 2.27 scriveva una riga all'ora,
    # dalla 2.27.2 una a giro); dopo una riga «senza rete» un buco fino a 75 minuti è ancora rete assente, non un fermo
    buchi = []
    for i in range(len(t) - 1):
        m = (t[i + 1] - t[i]).total_seconds() / 60
        if Gt[i + 1].get("tipo") == "senza rete" or (Gt[i].get("tipo") == "senza rete" and m <= 75):
            continue
        buchi.append((m, Gt[i]))
    if fine and t:
        buchi.append(((fine - t[-1]).total_seconds() / 60, Gt[-1]))
    lungo = max(buchi, key=lambda b: b[0]) if buchi else (0, {})
    da = {}
    for x in G:
        for k, v in (x.get("da") or {}).items():
            da[k] = da.get(k, 0) + v
    temp = [x["tel"][0] for x in G if x.get("tel") and x["tel"][0] is not None]
    batt = [x["tel"][1] for x in G if x.get("tel") and len(x["tel"]) > 1 and x["tel"][1] is not None]
    veri = _veri(G)
    rif = {}
    for x in G:
        for k, v in (x.get("rifiuti") or {}).items():
            rif[k] = rif.get(k, 0) + v
    spesa, prec = 0.0, (prima_di or {}).get("usd_mese")
    for x in G:
        u = x.get("usd_mese")
        if u is None:
            continue
        if prec is not None:
            spesa += (u - prec) if u >= prec else u  # mese nuovo: il conto riparte da zero
        prec = u
    return {"giri": len(veri), "tipi": tipi, "ritmo": round(median([b[0] for b in buchi[:-1] or buchi]), 1) if buchi else None,
            "fermo_max": round(lungo[0]), "fermo_dopo": lungo[1].get("quando", ""), "voci_nuove": sum(x.get("nuove", 0) for x in veri),
            "da": da, "errori_medi": round(sum(x.get("errori", 0) for x in veri) / len(veri), 1) if veri else None,
            "temp_min": min(temp) if temp else None, "temp_med": round(median(temp), 1) if temp else None,
            "temp_max": max(temp) if temp else None, "batt_min": min(batt) if batt else None,
            "pause": [[x.get("quando", ""), x.get("motivo") or ""] for x in G if x.get("tipo") in ("pausa", "senza rete", "fermo")],
            "mb": round(sum(x.get("mb") or 0 for x in G), 1), "rifiuti": rif, "spesa": round(spesa, 4),
            "richieste": {k: int(median([x.get("richieste", 0) for x in veri if x.get("tipo") == k]))
                          for k in ("completo", "leggero") if any(x.get("tipo") == k for x in veri)},
            "versioni": sorted({x.get("v", "") for x in G if x.get("v")})}


def _stato_numeri(z, live=None, basi=None, piano=None):
    """I numeri dell'archivio alla fine di una finestra: dal giro (diario) e, se ci sono, dai dati completi."""
    lv = z.get("livelli") or {}
    n = {"live": z.get("live"), "quota": round(100 * (z.get("quota") or 0), 1),
         "d_pct": round(100 * lv.get("D", 0) / max(sum(lv.values()), 1), 1) if lv else None,
         "senza_n": len(z.get("senza") or []), "fonti_attive": (z.get("fonti") or [None])[0],
         "tradotti": z.get("tradotti"), "memoria": (z.get("memoria") or [0, None])[1], "sapere": z.get("sapere"),
         "servizi": z.get("servizi"), "basi_stati": z.get("basi"), "usd_oggi": z.get("usd_oggi"), "usd_mese": z.get("usd_mese")}
    if z.get("mag"):
        n["magazzino_mb"], n["magazzino_notizie"] = z["mag"][0], z["mag"][2]
    pz = z.get("piano") or []
    if len(pz) >= 6:
        n["piano_i"], n["piano_tot"], n["passata"] = pz[3], pz[4], pz[5]
    if isinstance(z.get("intel"), list) and len(z["intel"]) > 1:
        n["intel"] = z["intel"][1]
    rp = (live or {}).get("piano") or {}
    if rp:
        n.update({"piano_stati": rp.get("con_scheda"), "accordi": rp.get("accordi"), "appalti": rp.get("appalti"),
                  "intel": rp.get("intel"), "puzzle": sum((rp.get("puzzle") or {}).values()), "puzzle_temi": rp.get("puzzle") or {},
                  "piano_i": rp.get("i", n.get("piano_i")), "piano_tot": rp.get("totale", n.get("piano_tot")),
                  "passata": rp.get("passata", n.get("passata")), "sintesi": rp.get("sintesi")})
    if piano and piano.get("stati"):
        S = piano["stati"]
        n["sintesi"] = sum(1 for v in S.values() if v.get("sintesi"))
    q = (live or {}).get("quadro") or {}
    if q:
        n["collegamenti"] = len(q.get("collegamenti") or [])
    if basi and basi.get("stati") is not None:
        n["basi_stati"] = len(basi.get("letti") or {})
        n["siti"] = sum(1 for l in basi["stati"].values() for e in l if not e.get("ch"))
    return {k: v for k, v in n.items() if v is not None}


def _confronta(ora, prima):
    meglio, peggio = [], []
    for k, (verso, modo, soglia) in RAPPORTO_VERSO.items():
        a, b = prima.get(k), ora.get(k)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or a == b:
            continue
        if abs(b - a) < (soglia * abs(a) if modo == "rel" else soglia):
            continue
        dec = 1 if k in ("quota", "d_pct", "errori_medi", "temp_max") else 0
        riga = f"{RAPPORTO_NOMI.get(k, k)}: {_it(a, dec)} → {_it(b, dec)}"
        (meglio if (b - a) * verso > 0 else peggio).append(riga)
    return meglio, peggio


def rapporto_dati(diario, live=None, basi=None, prec=None, fine=None, ore=12, cfg=None, piano=None):
    """Il rapporto delle ultime `ore`: che cosa ha fatto, quante informazioni ha, che cosa è migliorato o peggiorato
    rispetto al rapporto di prima (o, se manca, rispetto alla fine della finestra precedente)."""
    cfg = cfg or {}
    fine = fine or datetime.now(timezone.utc)
    da, da2 = fine - timedelta(hours=ore), fine - timedelta(hours=2 * ore)
    G = [x for x in diario if x.get("iso") and da.isoformat() <= x["iso"] <= fine.isoformat()]
    G0 = [x for x in diario if x.get("iso") and da2.isoformat() <= x["iso"] < da.isoformat()]
    prima_di = next((x for x in reversed(diario) if x.get("iso", "") < da.isoformat()), None)
    veri = _veri(diario)
    z = (_veri(G) or veri or [{}])[-1]
    att = _attivita(G, prima_di, fine)
    att0 = _attivita(G0, next((x for x in reversed(diario) if x.get("iso", "") < da2.isoformat()), None), da) if G0 else None
    numeri = _stato_numeri(z, live, basi, piano)
    numeri.update({k: att[k] for k in ("giri", "voci_nuove", "errori_medi", "temp_max", "fermo_max") if att.get(k) is not None})
    if prec and prec.get("numeri"):
        prima, prima_quando = prec["numeri"], prec.get("quando", "")
    else:
        a0 = (_veri(G0) or [None])[-1]
        prima = _stato_numeri(a0) if a0 else {}
        if att0:
            prima.update({k: att0[k] for k in ("giri", "voci_nuove", "errori_medi", "temp_max", "fermo_max") if att0.get(k) is not None})
        prima_quando = "le " + str(ore) + " ore prima" if prima else ""
    meglio, peggio = _confronta(numeri, prima) if prima else ([], [])
    # problemi: il verdetto in prima riga
    ultimo = datetime.fromisoformat(z["iso"]) if z.get("iso") else None
    eta = (fine - ultimo).total_seconds() / 60 if ultimo else None
    tetto_g = cfg.get("cervello", {}).get("max_usd_giorno", 1.5)
    tetto_m = cfg.get("cervello", {}).get("max_usd_mese", 45)
    proiezione = round(att["spesa"] * 24 / ore * 30, 2)
    problemi = []
    ult_ = diario[-1] if diario else {}
    eta_u = (fine - datetime.fromisoformat(ult_["iso"])).total_seconds() / 60 if ult_.get("iso") else None
    if ult_.get("tipo") == "senza rete" and eta_u is not None and eta_u <= 45:
        problemi.append("telefono senza rete dalle " + (datetime.fromisoformat(ult_["senza_rete_dal"]).astimezone().strftime("%H:%M")
                        if ult_.get("senza_rete_dal") else ult_.get("quando", "?")) + ": lavora su quello che ha e recupera al ritorno della rete")
    elif eta is None or eta > 45:
        problemi.append("il programma è fermo: ultimo giro " + (f"alle {z.get('quando', '?')}" if ultimo else "mai visto"))
    if att["giri"] < ore * 60 / 15 * 0.5:
        problemi.append(f"pochi giri: {att['giri']} in {ore} ore (attesi circa {ore * 4})")
    if (att.get("temp_max") or 0) >= 40:
        problemi.append(f"telefono caldo: fino a {_it(att['temp_max'], 1)} gradi")
    if z.get("tetto"):
        problemi.append("il cervello è fermo per il tetto di spesa (" + str(z["tetto"]) + ")")
    if (numeri.get("usd_oggi") or 0) > 0.8 * tetto_g:
        problemi.append(f"spesa di oggi vicina al tetto: {_it(numeri['usd_oggi'], 2)} $ su {_it(tetto_g, 2)}")
    if proiezione > 0.8 * tetto_m:
        problemi.append(f"proiezione su 30 giorni alta: {_it(proiezione, 2)} $ su {_it(tetto_m, 0)}")
    if (att.get("errori_medi") or 0) > 3:
        problemi.append(f"molti avvisi: {_it(att['errori_medi'], 1)} per giro")
    if numeri.get("senza_n", 0) > 10:
        problemi.append(f"{numeri['senza_n']} Stati senza notizie")
    if prima.get("quota") is not None and numeri.get("quota") is not None and numeri["quota"] <= prima["quota"] - 3:
        problemi.append(f"notizie confermate in calo: {_it(prima['quota'], 1)}% → {_it(numeri['quota'], 1)}%")
    if prima.get("fonti_attive") and numeri.get("fonti_attive") and numeri["fonti_attive"] < 0.95 * prima["fonti_attive"]:
        problemi.append(f"fonti attive in calo: {prima['fonti_attive']} → {numeri['fonti_attive']}")
    verdetto = "Tutto regolare." if not problemi else "ATTENZIONE: " + "; ".join(problemi) + "."
    try:  # l'ora italiana anche quando il rapporto lo calcola il cloud (che è in UTC)
        from zoneinfo import ZoneInfo
        locale = fine.astimezone(ZoneInfo("Europe/Rome"))
    except Exception:
        locale = fine.astimezone()
    quando = locale.strftime("%d/%m %H:%M")
    # avvisi che si ripetono: quelli dell'ultimo giro completo e i rifiuti dei siti nella finestra
    avvisi = [e for e in ((live or {}).get("errori") or []) if e][:5]
    for k, v in sorted(att["rifiuti"].items(), key=lambda x: -x[1])[:3]:
        avvisi.append(f"{k}: {v} rifiuti per troppe richieste")
    for c_ in (((live or {}).get("analisi") or {}).get("consigli") or [])[:3]:
        if c_ not in avvisi:
            avvisi.append(c_)
    nomi_tappe = {"temi": "temi", "stati": "Stati", "ricerca": "ricerca autonoma", "lingue": "lingue", "piano": "piano",
                  "feed": "feed", "telegram": "Telegram", "video": "YouTube", "altro": "altro"}
    T = []
    T.append(f"PanGeo · rapporto del {quando} ora italiana ({fine.astimezone(timezone.utc).strftime('%H:%M')} GMT), ultime {ore} ore · programma {z.get('v', '?')}")
    T.append("VERDETTO: " + verdetto)
    T.append("")
    T.append("CHE COSA HA FATTO")
    tipi = att["tipi"]
    pz_ = ", ".join(f"{p[0]} {p[1]}".strip() for p in att["pause"][:4])
    T.append(f"- Giri: {att['giri']} ({tipi.get('completo', 0)} completi, {tipi.get('leggero', 0)} leggeri"
             + (f", {len(att['pause'])} {'tra pause, fermi e ore senza rete' if len(att['pause']) > 1 else 'pausa, fermo o ora senza rete'}: {pz_}" if att["pause"] else "") + ")."
             + (f" Un giro ogni {_it(att['ritmo'], 0)} minuti." if att.get("ritmo") else "")
             + (f" Fermo più lungo: {att['fermo_max']} minuti (dopo il giro delle {att['fermo_dopo']})." if att["fermo_max"] >= 30 else ""))
    T.append(f"- Voci nuove: {_it(att['voci_nuove'])}" + (" (" + " · ".join(f"{nomi_tappe.get(k, k)} {_it(v)}" for k, v in
             sorted(att["da"].items(), key=lambda x: -x[1])[:6]) + ")" if att["da"] else "") + ".")
    if numeri.get("piano_tot"):
        d_st = (numeri.get("piano_stati") or 0) - (prima.get("piano_stati") or numeri.get("piano_stati") or 0)
        T.append(f"- Lavoro a piano: {numeri.get('piano_stati', numeri.get('piano_i', 0))} Stati su {numeri['piano_tot']}"
                 + (f" ({d_st:+d})" if d_st else "") + f", passata {numeri.get('passata', 1)}."
                 + (f" Accordi {_it(numeri['accordi'])}, appalti {_it(numeri['appalti'])}, fatti sui servizi {_it(numeri.get('intel'))}."
                    if numeri.get("accordi") is not None else ""))
    if numeri.get("puzzle_temi"):
        nomi_pz = {"energia": "energia", "ia": "IA militare", "trasporti": "trasporti", "cibo": "cibo"}
        T.append("- Puzzle: " + ", ".join(f"{nomi_pz.get(k, k)} {v}" for k, v in numeri["puzzle_temi"].items()) + " pezzi.")
    if numeri.get("basi_stati") is not None:
        T.append(f"- Siti militari letti: {numeri['basi_stati']} Stati su 198" + (f" ({_it(numeri['siti'])} siti in uso)" if numeri.get("siti") else "") + ".")
    if numeri.get("sintesi") is not None:
        T.append(f"- Sintesi per Stato scritte: {numeri['sintesi']}.")
    can_ = (live or {}).get("canali") or {}
    if can_:  # dalla 2.30: canali seguiti, trovati da soli e spenti
        T.append(f"- Canali: Telegram {can_.get('telegram', 0)}, YouTube {can_.get('youtube', 0)}"
                 + (f" · trovati da soli negli ultimi 3 giorni: {', '.join((can_.get('nuovi_tg') or []) + (can_.get('nuovi_yt') or []))[:300]}"
                    if (can_.get("nuovi_tg") or can_.get("nuovi_yt")) else "")
                 + (f" · spenti perché non rispondono: {', '.join(x.split(':', 1)[-1] for x in can_['spenti'][:8])}" if can_.get("spenti") else "") + ".")
    eco_ = ((live or {}).get("officina") or {}).get("economia") or {}
    if eco_:
        T.append(f"- Economia: dati della Banca Mondiale ({eco_.get('bm', 0)} indicatori), tassi dei titoli di Stato di {eco_.get('tassi', 0)} Stati, "
                 f"valute ({eco_.get('valute', 0)} giorni di storia), commercio e armi dalle dogane ONU per {eco_.get('comtrade', 0)} Stati.")
    n_bing = sum(x.get("bing") or 0 for x in G)
    if n_bing:
        T.append(f"- Bing News, la seconda fonte di ricerca: {_it(n_bing)} titoli in più.")
    mot_ = (live or {}).get("motori") or {}
    if mot_:
        nomi_m = {"google": "Google News", "bing": "Bing News"}
        T.append("- Motori di ricerca, da quando contano: " + " · ".join(
            f"{nomi_m.get(k, k)} {_it(v.get('titoli') or 0)} titoli in {_it(v.get('prove') or 0)} domande"
            + (f" ({v['errori']} errori)" if v.get("errori") else "")
            + (" – in pausa" if (v.get("pausa") or "") > fine.isoformat() else "") for k, v in mot_.items()) + ".")
    if numeri.get("collegamenti") is not None:
        T.append(f"- Quadro: {numeri['collegamenti']} collegamenti tra i fatti.")
    T.append("")
    T.append("QUANTE INFORMAZIONI HA")
    lv = z.get("livelli") or {}
    T.append(f"- Notizie degli ultimi 3 giorni: {_it(numeri.get('live'))}, confermate da due fonti il {_it(numeri.get('quota'), 1)}%."
             + (" Livelli: " + " · ".join(f"{k} {_it(lv[k])}" for k in sorted(lv)) + "." if lv else ""))
    T.append(f"- Fatti confermati in memoria: {_it(numeri.get('memoria'))}. Stati studiati su Wikipedia: {numeri.get('sapere', '–')}."
             f" Servizi di intelligence riassunti: {numeri.get('servizi', '–')}. Titoli tradotti: {_it(numeri.get('tradotti'))}.")
    senza = z.get("senza") or []
    T.append("- Stati senza notizie: " + (", ".join(senza[:12]) + (f" e altri {len(senza) - 12}" if len(senza) > 12 else "") if senza else "nessuno") + ".")
    T.append("")
    T.append("MEGLIO E PEGGIO" + (f" RISPETTO AL RAPPORTO DEL {prima_quando}" if prec else (" RISPETTO ALLE " + prima_quando.upper().replace("LE ", "", 1) if prima_quando else "")))
    if not prima:
        T.append("- Primo rapporto: il confronto arriva con il prossimo.")
    else:
        T += ["+ " + x for x in meglio] or ["+ niente di migliorato in modo visibile"]
        T += ["- " + x for x in peggio] or ["- niente di peggiorato"]
    T.append("")
    T.append("TELEFONO E COSTI")
    if att.get("temp_max") is not None:
        T.append(f"- Temperatura: minima {_it(att['temp_min'], 1)}, media {_it(att['temp_med'], 1)}, massima {_it(att['temp_max'], 1)} gradi"
                 + (f" · batteria minima {att['batt_min']}%" if att.get("batt_min") is not None else "") + ".")
    else:
        T.append("- Temperatura: non letta (serve l'app Termux:API).")
    off_rete = [x for x in G if x.get("tipo") == "senza rete"]
    if off_rete:
        T.insert(T.index("CHE COSA HA FATTO") + 1, f"- Senza rete per un tratto (dalle {datetime.fromisoformat(off_rete[0]['senza_rete_dal']).astimezone().strftime('%H:%M') if off_rete[0].get('senza_rete_dal') else off_rete[0].get('quando', '?')}): "
                 f"lavoro sul telefono in {len(off_rete)} {'ora' if len(off_rete) == 1 else 'ore'}, {sum((x.get('offline') or [0])[0] for x in off_rete)} conferme in più, "
                 f"{sum((x.get('offline') or [0, 0])[1] for x in off_rete)} fatti riordinati in memoria"
                 + (f", {sum((x.get('offline') or [0, 0, 0])[2] for x in off_rete if len(x.get('offline') or []) > 2)} titoli tradotti dall'officina" if any(len(x.get('offline') or []) > 2 for x in off_rete) else "") + ".")
    mag_ = z.get("mag")
    if mag_:
        peso_ = f"{_it(mag_[0] / 1000, 1)} GB" if mag_[0] >= 1000 else f"{_it(mag_[0])} MB"
        T.append(f"- Magazzino sul telefono: {peso_}, {mag_[1]} giorni, {_it(mag_[2])} notizie · spazio libero {_it(mag_[3], 1)} GB"
                 + (" · copia di sicurezza: sì" if mag_[4] else " · copia di sicurezza spenta (si accende con: termux-setup-storage)") + ".")
    T.append(f"- Dati scaricati: {_it(att['mb'])} MB in {ore} ore (circa {_it(att['mb'] * 24 / ore / 1000, 1)} GB al giorno).")
    T.append(f"- Cervello (conto del programma, listino Haiku 5.5): {_it(att['spesa'], 2)} $ in {ore} ore · oggi {_it(numeri.get('usd_oggi', 0), 2)} $"
             f" su {_it(tetto_g, 2)} · mese {_it(numeri.get('usd_mese', 0), 2)} $ su {_it(tetto_m, 0)} · a questo ritmo {_it(proiezione, 2)} $ in 30 giorni.")
    lav_ = ((live or {}).get("spesa_lavori") or {}).get("lavori_mese") or {}
    if lav_:
        T.append("- Spesa del mese per lavoro: " + " · ".join(f"{k} {_it(v, 2)} $" for k, v in sorted(lav_.items(), key=lambda x: -x[1])[:7]) + ".")
    off_ = (live or {}).get("officina") or {}
    if off_.get("fase"):
        pr_ = off_.get("prova") or {}
        T.append(f"- Officina del telefono: {off_['fase']}"
                 + (f" · prova: {pr_.get('titoli')} titoli, {_it(pr_.get('secondi_a_titolo'), 1)} secondi a titolo, lingue buone: "
                    + (", ".join(NOMI_LINGUE.get(x, x) for x in pr_.get("buone") or []) or "nessuna") if pr_ else "")
                 + (f" · tradotti gratis oggi: {off_.get('tradotti_oggi') or 0}" if off_.get("tradotti_tutti") else "") + ".")
    fi_ = off_.get("filtro") or {}
    if fi_.get("esempi"):
        T.append(f"- Filtro della sala d'attesa (impara dal cervello): {_it(fi_['esempi'])} esempi"
                 + (f" · scarta da solo il {_it((fi_.get('copre') or 0) * 100, 0)}% dei titoli inutili, errore misurato "
                    f"{_it((fi_.get('errore') or 0) * 100, 1)}% · oggi {_it(fi_.get('scartati_oggi') or 0)} titoli risparmiati al cervello"
                    if fi_.get("attivo") else f" · non scarta ancora da solo: {fi_.get('perche') or 'sta imparando'}")
                 + (f" · controlli {fi_['controlli'][0]} giusti e {fi_['controlli'][1]} sbagliati" if sum(fi_.get("controlli") or [0, 0]) else "")
                 + ".")
    T.append("  Il credito vero si vede solo nella console: https://platform.claude.com/settings/billing")
    if avvisi:
        T.append("")
        T.append("AVVISI")
        T += ["- " + pulisci(a, 200) for a in avvisi[:6]]
    T.append("")
    T.append(f"Sito: {SITO_PUBBLICO}  ·  tutti i rapporti: {SITO_PUBBLICO}/#documenti")
    oggetto = f"PanGeo · rapporto {quando} · " + ("tutto regolare" if not problemi else "ATTENZIONE: " + problemi[0])
    return {"quando": quando, "fine": fine.isoformat(), "inizio": da.isoformat(), "ore": ore, "versione": z.get("v", ""),
            "verdetto": verdetto, "problemi": problemi, "oggetto": oggetto[:180], "testo": "\n".join(T),
            "numeri": numeri, "attivita": att, "meglio": meglio, "peggio": peggio, "prima": prima_quando}


def _ultimo_turno(adesso_locale, ore_turni):
    """L'ultimo orario del rapporto già passato (es. 8 e 20): «2026-11-20 20»."""
    for giorno in (0, 1):
        d = (adesso_locale - timedelta(days=giorno)).date()
        for h in sorted(ore_turni, reverse=True):
            t = datetime(d.year, d.month, d.day, h, tzinfo=adesso_locale.tzinfo)
            if t <= adesso_locale:
                return t.strftime("%Y-%m-%d %H")
    return ""


def rapporto_12(cfg, forza=False):
    """Alle 8 e alle 20 (config.json › rapporto › ore) il programma scrive il rapporto: dati/rapporto.json (l'ultimo,
    con il testo della mail) e dati/rapporti.json (gli ultimi 60). Vanno su GitHub; la mail la manda un'attività di
    Claude che li legge da lì, così arriva anche quando il telefono è fermo (e lo dice)."""
    imp = cfg.get("rapporto", {})
    if not imp.get("attivo", True):
        return None
    adesso = datetime.now(timezone.utc)
    if imp.get("ore_utc"):  # dalla 2.27.2: ore di Greenwich, uguali tutto l'anno (l'ora legale non le sposta)
        turno = _ultimo_turno(adesso.astimezone(timezone.utc), imp["ore_utc"]) + " GMT"
    else:
        turno = _ultimo_turno(adesso.astimezone(), imp.get("ore", [8, 20]))
    perc_r, perc_l = os.path.join(DATI, "rapporto.json"), os.path.join(DATI, "rapporti.json")
    ultimo = leggi_json(perc_r, {})
    if not forza and ultimo.get("turno") == turno:
        return None
    R = rapporto_dati(leggi_json(os.path.join(DATI, "diario.json"), []), leggi_json(os.path.join(DATI, "live.json"), {}),
                      leggi_json(os.path.join(DATI, "basi_wd.json"), {}), ultimo if ultimo.get("numeri") else None,
                      adesso, imp.get("ore_finestra", 12), cfg, leggi_json(os.path.join(DATI, "piano.json"), {}))
    R["turno"] = turno
    scrivi_json(perc_r, R)
    elenco = leggi_json(perc_l, [])
    elenco.append({k: R[k] for k in ("turno", "quando", "fine", "versione", "verdetto", "problemi", "meglio", "peggio", "numeri", "testo")})
    scrivi_json(perc_l, elenco[-imp.get("tieni", 60):])
    return R


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
# terzo tema del lavoro a piano (dalla 2.22): fatti PUBBLICI sui servizi di informazione e sicurezza di ogni Stato
PIANO_Q_INTEL = {
    "en": '"{n}" ("intelligence service" OR "intelligence agency" OR "spy agency" OR "security service" OR "intelligence chief" OR espionage OR "threat assessment") (report OR appoints OR appointed OR reform OR law OR oversight OR expels OR expelled OR arrested OR warns)',
    "it": '"{n}" (intelligence OR "servizi segreti" OR "servizi di sicurezza" OR spionaggio OR controspionaggio) (relazione OR rapporto OR nomina OR direttore OR riforma OR legge OR espulsi OR arrestato OR allarme)',
    "fr": '"{n}" (renseignement OR "services secrets" OR espionnage OR "contre-espionnage") (rapport OR nomme OR nommé OR réforme OR loi OR expulse OR arrêté OR alerte)',
    "es": '"{n}" (inteligencia OR "servicios secretos" OR espionaje OR contraespionaje) (informe OR nombra OR director OR reforma OR ley OR expulsa OR detenido OR alerta)',
    "pt": '"{n}" (inteligência OR "serviços secretos" OR espionagem OR "serviço de informações") (relatório OR nomeia OR diretor OR reforma OR lei OR expulsa OR detido OR alerta)',
    "de": '"{n}" (Nachrichtendienst OR Geheimdienst OR Spionage OR Verfassungsschutz OR Spionageabwehr) (Bericht OR ernennt OR Präsident OR Reform OR Gesetz OR ausgewiesen OR festgenommen OR warnt)',
    "ru": '"{n}" (разведка OR спецслужбы OR шпионаж OR контрразведка) (доклад OR назначен OR директор OR реформа OR закон OR выслали OR задержан)',
    "ar": '"{n}" (المخابرات OR الاستخبارات OR تجسس OR "جهاز الأمن") (تقرير OR تعيين OR رئيس OR قانون OR طرد OR اعتقال)',
}
# Puzzle (dalla 2.24): a ogni Stato il lavoro a piano aggiunge UN solo tema in più, a rotazione, con una domanda in inglese
# e una nella lingua del posto. Pezzi piccoli, uno alla volta: così Google News non blocca, e ogni 3 ore il quadro li collega.
PIANO_PUZZLE = {
    "energia": {
        "nome": "ENERGIA E RETI",
        "cosa": "reti e forniture di energia: gasdotti, oleodotti, elettrodotti e interconnessioni, centrali, gas liquefatto, contratti "
                "di fornitura, guasti, sabotaggi e attacchi alle reti, dipendenza da un fornitore",
        "q": {
            "en": '"{n}" (pipeline OR "power grid" OR "gas supply" OR LNG OR "power plant" OR "nuclear plant" OR interconnector OR blackout OR "energy security") (deal OR agreement OR attack OR sabotage OR outage OR cut OR imports OR opens)',
            "it": '"{n}" (gasdotto OR oleodotto OR "rete elettrica" OR "forniture di gas" OR GNL OR centrale OR elettrodotto OR blackout OR "sicurezza energetica") (accordo OR attacco OR sabotaggio OR guasto OR taglio OR importazioni OR inaugura)',
            "fr": '"{n}" (gazoduc OR oléoduc OR "réseau électrique" OR GNL OR "centrale nucléaire" OR interconnexion OR "sécurité énergétique" OR "panne de courant") (accord OR attaque OR sabotage OR coupure OR importations)',
            "es": '"{n}" (gasoducto OR oleoducto OR "red eléctrica" OR GNL OR "central nuclear" OR interconexión OR apagón OR "seguridad energética") (acuerdo OR ataque OR sabotaje OR corte OR importaciones)',
            "pt": '"{n}" (gasoduto OR oleoduto OR "rede elétrica" OR GNL OR "central nuclear" OR "usina nuclear" OR apagão OR "segurança energética") (acordo OR ataque OR sabotagem OR corte OR importações)',
            "de": '"{n}" (Pipeline OR Stromnetz OR Gaslieferungen OR LNG OR Kraftwerk OR Atomkraftwerk OR Stromausfall OR Energiesicherheit) (Abkommen OR Angriff OR Sabotage OR Ausfall OR Importe)',
            "ru": '"{n}" (газопровод OR нефтепровод OR энергосистема OR "поставки газа" OR СПГ OR электростанция OR АЭС OR блэкаут) (соглашение OR атака OR диверсия OR авария OR отключение)',
            "ar": '"{n}" ("خط أنابيب" OR "شبكة الكهرباء" OR "إمدادات الغاز" OR "الغاز المسال" OR "محطة كهرباء" OR "أمن الطاقة") (اتفاق OR هجوم OR تخريب OR انقطاع OR استيراد)',
        }},
    "ia": {
        "nome": "INTELLIGENZA ARTIFICIALE IN CAMPO MILITARE",
        "cosa": "intelligenza artificiale in campo militare: sistemi adottati o provati dalle forze armate (riconoscimento dei bersagli, "
                "droni e mezzi autonomi, analisi di intelligence, comando e controllo), contratti con aziende di IA, regole e leggi, "
                "incidenti e critiche. Niente dettagli tecnici su come si usano",
        "q": {
            "en": '"{n}" ("artificial intelligence" OR AI OR autonomous OR "drone swarm" OR "machine learning") (military OR army OR defense OR defence OR "armed forces" OR weapons OR targeting OR battlefield)',
            "it": '"{n}" ("intelligenza artificiale" OR IA OR autonomi OR "sciami di droni" OR algoritmi) (militare OR esercito OR difesa OR "forze armate" OR armi OR bersagli)',
            "fr": '"{n}" ("intelligence artificielle" OR IA OR autonomes OR "essaim de drones" OR algorithmes) (militaire OR armée OR défense OR armes OR ciblage)',
            "es": '"{n}" ("inteligencia artificial" OR IA OR autónomos OR "enjambre de drones" OR algoritmos) (militar OR ejército OR defensa OR "fuerzas armadas" OR armas)',
            "pt": '"{n}" ("inteligência artificial" OR IA OR autônomos OR "enxame de drones" OR algoritmos) (militar OR exército OR defesa OR "forças armadas" OR armas)',
            "de": '"{n}" ("künstliche Intelligenz" OR KI OR autonome OR Drohnenschwarm OR Algorithmen) (Militär OR Bundeswehr OR Armee OR Verteidigung OR Waffen OR Streitkräfte)',
            "ru": '"{n}" ("искусственный интеллект" OR ИИ OR автономные OR "рой дронов" OR нейросеть) (военные OR армия OR оборона OR "вооружённые силы" OR оружие)',
            "ar": '"{n}" ("الذكاء الاصطناعي" OR "أسراب المسيرات" OR "أنظمة ذاتية") (عسكري OR الجيش OR الدفاع OR "القوات المسلحة" OR أسلحة)',
        }},
    "trasporti": {
        "nome": "TRASPORTI E LOGISTICA",
        "cosa": "trasporti e logistica: porti, ferrovie, corridoi, strade, aeroporti, canali e stretti, blocchi e interruzioni, grandi "
                "opere, catene di rifornimento, mobilità militare",
        "q": {
            "en": '"{n}" (port OR railway OR corridor OR "supply chain" OR shipping OR airport OR canal OR strait OR logistics OR "military mobility") (blockade OR closure OR disruption OR opens OR deal OR strike OR expansion)',
            "it": '"{n}" (porto OR ferrovia OR corridoio OR logistica OR "catena di approvvigionamento" OR aeroporto OR canale OR stretto OR "mobilità militare") (blocco OR chiusura OR interruzione OR inaugura OR accordo OR sciopero)',
            "fr": '"{n}" (port OR "chemin de fer" OR corridor OR logistique OR approvisionnement OR aéroport OR canal OR détroit) (blocus OR fermeture OR perturbation OR inauguration OR accord OR grève)',
            "es": '"{n}" (puerto OR ferrocarril OR corredor OR logística OR "cadena de suministro" OR aeropuerto OR canal OR estrecho) (bloqueo OR cierre OR interrupción OR inaugura OR acuerdo OR huelga)',
            "pt": '"{n}" (porto OR ferrovia OR corredor OR logística OR "cadeia de abastecimento" OR aeroporto OR canal OR estreito) (bloqueio OR fechamento OR interrupção OR inaugura OR acordo OR greve)',
            "de": '"{n}" (Hafen OR Eisenbahn OR Korridor OR Logistik OR Lieferkette OR Flughafen OR Kanal OR Meerenge) (Blockade OR Sperrung OR Störung OR Eröffnung OR Abkommen OR Streik)',
            "ru": '"{n}" (порт OR "железная дорога" OR коридор OR логистика OR "цепочка поставок" OR аэропорт OR канал OR пролив) (блокада OR закрытие OR перебои OR открытие OR соглашение)',
            "ar": '"{n}" (ميناء OR "سكة حديد" OR ممر OR "سلاسل الإمداد" OR مطار OR قناة OR مضيق) (حصار OR إغلاق OR تعطل OR افتتاح OR اتفاق)',
        }},
    "cibo": {
        "nome": "CIBO, ACQUA E RISORSE",
        "cosa": "cibo, acqua e risorse: raccolti, siccità, importazioni di grano e fertilizzanti, divieti di esportazione, riserve "
                "strategiche, prezzi del cibo, carestie, materie prime critiche e terre rare",
        "q": {
            "en": '"{n}" (wheat OR grain OR fertilizer OR "food security" OR drought OR harvest OR "food prices" OR famine OR "critical minerals" OR "rare earths" OR "water shortage") (imports OR "export ban" OR shortage OR reserves OR deal OR crisis)',
            "it": '"{n}" (grano OR cereali OR fertilizzanti OR "sicurezza alimentare" OR siccità OR raccolto OR "prezzi alimentari" OR carestia OR "materie prime critiche" OR "terre rare" OR "crisi idrica") (importazioni OR "blocco delle esportazioni" OR carenza OR riserve OR accordo OR crisi)',
            "fr": '"{n}" (blé OR céréales OR engrais OR "sécurité alimentaire" OR sécheresse OR récolte OR famine OR "terres rares" OR "minerais critiques" OR pénurie) (importations OR exportations OR réserves OR accord OR crise)',
            "es": '"{n}" (trigo OR cereales OR fertilizantes OR "seguridad alimentaria" OR sequía OR cosecha OR hambruna OR "tierras raras" OR "minerales críticos" OR escasez) (importaciones OR exportaciones OR reservas OR acuerdo OR crisis)',
            "pt": '"{n}" (trigo OR cereais OR fertilizantes OR "segurança alimentar" OR seca OR colheita OR fome OR "terras raras" OR "minerais críticos" OR escassez) (importações OR exportações OR reservas OR acordo OR crise)',
            "de": '"{n}" (Weizen OR Getreide OR Düngemittel OR Ernährungssicherheit OR Dürre OR Ernte OR Hungersnot OR "Seltene Erden" OR "kritische Rohstoffe" OR Wasserknappheit) (Importe OR Exportverbot OR Knappheit OR Reserven OR Abkommen OR Krise)',
            "ru": '"{n}" (пшеница OR зерно OR удобрения OR "продовольственная безопасность" OR засуха OR урожай OR голод OR "редкоземельные металлы" OR "дефицит воды") (импорт OR "запрет экспорта" OR дефицит OR резервы OR соглашение)',
            "ar": '"{n}" (القمح OR الحبوب OR الأسمدة OR "الأمن الغذائي" OR الجفاف OR المحصول OR المجاعة OR "المعادن النادرة" OR "أزمة المياه") (استيراد OR "حظر تصدير" OR نقص OR مخزون OR اتفاق)',
        }},
}
PUZZLE_ORDINE = ("energia", "ia", "trasporti", "cibo")
PIANO_TIPI_INTEL = ("nomina", "legge", "relazione", "espulsione", "processo", "accordo", "allarme", "altro")
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


def _piano_titoli(domande, giorni, errori, pausa=1.0, bing=()):
    """Fa le domande a Google News e mette insieme i titoli, senza doppioni. Restituisce i titoli, le domande con quanti
    titoli ha portato ognuna, e quante domande sono fallite."""
    titoli, visti, fatte, fallite = [], set(), [], 0
    M_, ad_ = _motori(), datetime.now(timezone.utc)
    for tipo, lingua, q in domande:
        n0 = len(titoli)
        err_ = None
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
            err_ = e
            errori.append(f"Lavoro a piano ({q[:40]}): {e}")
        motore_esito(M_, "google", tipo, len(titoli) - n0, err_, ad_)
        fatte.append([tipo, lingua, q, len(titoli) - n0])
        time.sleep(pausa)
    # dalla 2.26: domande semplici anche a Bing News (seconda fonte: più titoli, e lavora quando Google rifiuta)
    for tipo, q in bing:
        if not motore_ok(M_, "bing", tipo, ad_):
            fatte.append([tipo, "bing", q, -1])  # -1: saltata, il motore riposa o per questo tipo rende poco
            continue
        n0 = len(titoli)
        err_ = None
        try:
            for t_, u_, d_, f_, _s in bing_news(q, min(giorni, 30))[:25]:
                chiave = re.sub(r"\W+", " ", (t_ or "").lower()).strip()[:90]
                if len(chiave) < 12 or chiave in visti or RUMORE.search(" " + (f_ or "") + " ") or APPRESI.get(f_) == "scarto":
                    continue
                visti.add(chiave)
                titoli.append({"t": pulisci(t_, 240), "u": solo_http(u_), "iso": d_ or "", "d": (d_ or "")[:10], "f": f_ or "",
                               "k": tipo, "l": "en", "da": "bing"})
        except SenzaRete:
            raise
        except Exception as e:
            err_ = e
            errori.append(f"Bing News ({q[:40]}): {str(e)[:120]}")
        motore_esito(M_, "bing", tipo, len(titoli) - n0, err_, ad_)
        fatte.append([tipo, "bing", q, len(titoli) - n0])
        _piano_titoli.bing = getattr(_piano_titoli, "bing", 0) + len(titoli) - n0
        time.sleep(pausa)
    scrivi_json(os.path.join(DATI, "motori.json"), M_)
    return titoli, fatte, fallite


def _piano_domanda(stato, titoli, giorni, noti, tema=None, tema2=None):
    pz, pz2 = PIANO_PUZZLE.get(tema), PIANO_PUZZLE.get(tema2)
    parte5 = (f"PARTE 5, {pz['nome']}: fatti su {pz['cosa']}, che riguardano {stato}. Solo fatti accaduti o decisi, non "
              "commenti. Una riga per fatto:\n"
              "F | data | che cosa, in una frase in italiano | numeri dei titoli | rilevanza\n"
              "Se non ce ne sono scrivi «F | nessuno».\n\n") if pz else ""
    if pz and pz2:  # dalla 2.26 due temi per Stato: il secondo con le righe G
        parte5 += (f"PARTE 6, {pz2['nome']}: fatti su {pz2['cosa']}, che riguardano {stato}. Solo fatti accaduti o decisi, non "
                   "commenti. Una riga per fatto:\n"
                   "G | data | che cosa, in una frase in italiano | numeri dei titoli | rilevanza\n"
                   "Se non ce ne sono scrivi «G | nessuno».\n\n")
    righe = "\n".join(f"{i + 1}. {x['d'] or 'senza data'} – {x['t']} – {x['f']}" for i, x in enumerate(titoli))
    gia = ("\nGIÀ IN ARCHIVIO per " + stato + " (non ripeterli, a meno che un titolo dica che qualcosa è cambiato):\n"
           + "\n".join("· " + n for n in noti[:14]) + "\n") if noti else ""
    return (f"Lavori a un archivio pubblico di difesa e geopolitica. Qui sotto ci sono titoli di giornale su {stato} degli ultimi "
            f"{giorni} giorni (numero. data – titolo – fonte), in lingue diverse. Usa SOLO quello che dicono i titoli: non "
            "aggiungere nulla che sai per conto tuo, e se un titolo non è chiaro lascialo stare.\n\n"
            f"PARTE 1, ACCORDI: alleanze, patti, trattati e accordi militari o di sicurezza che riguardano {stato}. Una riga per accordo:\n"
            "A | data | con chi | che cosa, in una frase in italiano | stato | numeri dei titoli | rilevanza\n"
            "dove «stato» è una di queste parole: " + ", ".join(PIANO_STATI_ACCORDO) + ".\n\n"
            f"PARTE 2, APPALTI: contratti, ordini, acquisti e vendite di armamenti in cui {stato} compra o vende. Una riga per contratto:\n"
            "C | data | chi compra | chi vende (azienda e Stato, se sono scritti) | che cosa, in italiano, con le quantità se sono "
            "scritte | valore, oppure - | stato | numeri dei titoli | rilevanza\n"
            "dove «stato» è una di queste parole: " + ", ".join(PIANO_STATI_APPALTO) + ".\n\n"
            f"PARTE 3, INTELLIGENCE: fatti pubblici sui servizi di informazione e di sicurezza di {stato}, o che li riguardano: "
            "nomine e cambi al vertice, leggi e riforme, relazioni e rapporti pubblicati dai servizi o da chi li controlla, espulsioni "
            "di diplomatici, processi e arresti per spionaggio, accordi di scambio di informazioni, allarmi pubblici. Una riga per fatto:\n"
            "I | data | quale servizio o ente (il nome come sta nel titolo, oppure -) | che cosa, in una frase in italiano | tipo | "
            "numeri dei titoli | rilevanza\n"
            "dove «tipo» è una di queste parole: " + ", ".join(PIANO_TIPI_INTEL) + ".\n"
            "Nelle righe I non scrivere MAI il nome di persone private (indagati, arrestati, testimoni, agenti): scrivi il ruolo, per "
            "esempio «un funzionario» o «due cittadini stranieri». I nomi di ministri, capi dei servizi e altre cariche pubbliche "
            "vanno bene. Niente indirizzi, niente metodi, niente dettagli operativi.\n\n"
            "PARTE 4, DOMANDE: fino a 2 cose che i titoli lasciano aperte e che conviene cercare (per esempio se un contratto "
            "annunciato è poi stato firmato, o se un accordo è stato ratificato). Una riga per domanda:\n"
            "D | lingua in cui cercare (it, en, oppure la sigla della lingua del posto) | da 3 a 7 parole da cercare, senza "
            "virgolette | che cosa vuoi sapere, in italiano\n\n" + parte5 +
            "RILEVANZA, nelle righe A, C, I, F e G: scrivi R e un numero da 1 a 5 (per esempio R4), quanto conta il fatto per la "
            "difesa e la sicurezza. R5 = cambia gli equilibri tra Stati o in una regione (un'alleanza nuova, un grande contratto "
            "pluriennale, un cambio al vertice dei servizi dopo uno scandalo); R3 = importante per lo Stato; R1 = fatto minore o "
            "di routine.\n\n"
            "Regole. La data è quella del titolo più recente che ne parla, scritta AAAA-MM-GG. Lo stesso fatto una volta sola: se ne "
            "parlano più titoli, metti tutti i loro numeri. Lo stesso accordo o lo stesso contratto è UNA riga anche quando i "
            "titoli ne raccontano tappe diverse (annuncio, trattativa, firma): scrivi lo stato più avanzato, la data della tappa "
            "più recente e i numeri di tutti i titoli. Non scrivere note, commenti o rimandi («vedi sotto») dentro le righe. Niente giudizi, niente previsioni, niente dettagli operativi. Se un "
            "titolo riporta un'accusa o una voce, scrivi «secondo» e chi lo dice. Le notizie che non sono né accordi né appalti né "
            "fatti sui servizi" + ((" né fatti delle parti 5 e 6" if pz2 else " né fatti della parte 5") if pz else "") + " ignorale. Se una parte è vuota scrivi «A | nessuno», «C | nessuno» oppure «I | nessuno». Scrivi solo le righe, senza titoli e senza "
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
    """Legge le righe del cervello: «A | …» accordi, «C | …» appalti, «I | …» fatti sui servizi, «D | …» domande aperte.
    Una riga senza il numero di almeno un titolo vero viene scartata: nell'archivio entra solo ciò che ha una fonte."""
    def data_di(testo, fonti):
        m = re.search(r"(19|20)\d\d-\d\d-\d\d", testo or "")
        return m.group(0) if m else max((f[2] for f in fonti if f[2]), default="")

    def stato_di(testo, ammessi):
        t = (testo or "").lower().strip(" .")
        return next((a for a in sorted(ammessi, key=len, reverse=True) if a in t), "annunciato" if t else "")

    accordi, appalti, intel, domande_ = [], [], [], []
    _piano_leggi.puzzle = []  # le righe F (il tema del giro): le legge passo_piano, che sa di quale tema si tratta
    _piano_leggi.puzzle2 = []  # le righe G (il secondo tema, dalla 2.26)
    ril_rx = re.compile(r"(?i)r(?:ilevanza)?\s*[:=]?\s*([1-5])(?:\s*/\s*5)?")
    for riga in (risposta or "").splitlines():
        p = [x.strip(" *`") for x in riga.strip().lstrip("-•* ").split("|")]
        sigla = p[0].upper().strip(" .:)") if p else ""
        # la rilevanza (R1…R5) si toglie prima di leggere le colonne: il suo numero non va mai preso per il numero di un titolo
        ril = None
        if sigla in ("A", "C", "I", "F", "G"):
            resto = []
            for x in p[1:]:
                m_r = ril_rx.fullmatch(x.strip())
                if m_r and ril is None:
                    ril = int(m_r.group(1))
                else:
                    resto.append(x)
            p = p[:1] + resto
            minimo = {"A": 6, "C": 8, "I": 6, "F": 4, "G": 4}[sigla]
            if ril is None and len(p) > minimo and re.fullmatch(r"\s*[1-5]\s*", p[-1]):
                ril, p = int(p[-1].strip()), p[:-1]  # rilevanza scritta senza la R, in fondo alla riga
        if sigla in ("A", "C", "I", "F", "G"):  # niente note o rimandi dentro le righe: «… nota: il titolo riguarda…, vedi sotto»
            p = [_piano_senza_note(x) for x in p]
        if sigla == "A" and len(p) >= 6:
            fonti = _piano_fonti(p[5], titoli)
            if fonti and len(p[3]) > 8:
                accordi.append({"d": data_di(p[1], fonti), "con": pulisci(p[2], 120), "cosa": pulisci(p[3], 300),
                                "st": stato_di(p[4], PIANO_STATI_ACCORDO), "f": fonti, "r": ril})
        elif sigla == "C" and len(p) >= 8:
            fonti = _piano_fonti(p[7], titoli)
            if fonti and len(p[4]) > 5:
                appalti.append({"d": data_di(p[1], fonti), "acq": pulisci(p[2], 80), "forn": pulisci(p[3], 120),
                                "ogg": pulisci(p[4], 300), "val": "" if p[5].strip(" -–—") == "" else pulisci(p[5], 60),
                                "st": stato_di(p[6], PIANO_STATI_APPALTO), "f": fonti, "r": ril})
        elif sigla == "I" and len(p) >= 6:
            fonti = _piano_fonti(p[5], titoli)
            if fonti and len(p[3]) > 8:
                ente = pulisci(p[2], 100).strip(" -–—")
                intel.append({"d": data_di(p[1], fonti), "ente": ente, "cosa": pulisci(p[3], 300),
                              "tipo": next((t for t in PIANO_TIPI_INTEL if t in p[4].lower()), "altro"), "f": fonti, "r": ril})
        elif sigla in ("F", "G") and len(p) >= 4:
            fonti = _piano_fonti(p[3], titoli)
            if fonti and len(p[2]) > 8:
                (_piano_leggi.puzzle if sigla == "F" else _piano_leggi.puzzle2).append({"d": data_di(p[1], fonti), "cosa": pulisci(p[2], 300), "f": fonti, "r": ril})
        elif sigla == "D" and len(p) >= 4:
            q = " ".join(re.sub(r'[<>{}\\"«»()]|https?:\S*', " ", p[2]).split())
            if 2 <= len(q.split()) <= 9 and len(q) <= 110:
                domande_.append({"l": re.sub(r"[^a-zA-Z-]", "", p[1])[:5].lower() or "en", "q": q, "perche": pulisci(p[3], 200)})
    return accordi, appalti, intel, domande_[:2]


PIANO_NOTA = re.compile(r"\s*(?:…|\.\.\.|[;,(\-–—])?\s*\b(?:nota|n\.b\.|nb)\s*:|\s*[,;(]?\s*\bvedi (?:sotto|sopra)\b", re.I)


def _piano_senza_note(testo):
    """Toglie le note che il cervello a volte lascia dentro una riga («… nota: il titolo riguarda…», «vedi sotto»)."""
    testo = testo or ""
    return PIANO_NOTA.split(testo, 1)[0].strip(" (…") if len(testo) > 20 and PIANO_NOTA.search(testo) else testo


# parole che non dicono di quale fatto si parla: non bastano a dire che due righe sono lo stesso fatto
PIANO_GENERICHE = {"accor", "difes", "coope", "milit", "sicur", "firma", "gover", "minis", "paese", "paesi", "stato", "stati", "nuovo",
                   "nuova", "nuovi", "nuove", "contr", "acqui", "forni", "annun", "tratt", "intes", "parte", "ampia", "defin",
                   "final", "cessi", "titol", "rigua", "sotto", "sopra", "dichi", "incon", "visit", "relaz", "bilat", "strat",
                   "partn", "memor", "proto", "second", "dopo", "prima", "anche", "della", "delle", "degli", "nella", "nelle",
                   "sulla", "sulle", "dalla", "dalle", "quest", "primo", "prima", "unita", "milio", "milia", "dolla", "euro",
                   "press", "verso", "senza", "entro", "circa", "oltre", "conse", "ordin", "vendi", "compr", "servi", "agenz",
                   "diret", "capo", "legge", "rappo", "relaz", "pubbl", "anno", "anni", "mese", "mesi"}
PIANO_ORDINE_STATO = ("in vigore", "ratificato", "consegnato", "in consegna", "firmato", "approvato", "in trattativa", "annunciato",
                      "sospeso", "disdetto", "annullato", "")


def _piano_radici(testo, fuori=()):
    """Le parole che contano di una riga, ridotte alla radice (prime 5 lettere): «fregate» e «fregata» sono la stessa."""
    parole = re.findall(r"[a-zà-ÿ0-9][a-zà-ÿ0-9-]{3,}", (testo or "").lower())
    return {w[:5] for w in parole if w[:5] not in PIANO_GENERICHE and w[:5] not in fuori}


def _piano_stesso(a, b, campo):
    """Vero se due righe parlano dello stesso fatto, anche se i titoli ne raccontano tappe diverse (annuncio, trattativa,
    firma): stessa controparte (o stesso ente, stesso tema), date vicine e almeno una parola che conta in comune.
    Senza controparte serve che i testi si somiglino molto."""
    chi = lambda x: re.sub(r"\W+", " ", " ".join(str(x.get(k) or "") for k in ("con", "acq", "forn", "ente", "tema")).lower()).strip()
    ca, cb = chi(a), chi(b)
    fuori = {w[:5] for w in (ca + " " + cb).split()}
    ra, rb = _piano_radici(a.get(campo), fuori), _piano_radici(b.get(campo), fuori)
    if not ra or not rb:
        return False
    comuni = ra & rb
    if len(comuni) >= 0.6 * min(len(ra), len(rb)) and len(comuni) >= 2:
        return True  # testi quasi uguali
    try:
        giorni = abs((datetime.fromisoformat(a.get("d") or "") - datetime.fromisoformat(b.get("d") or "")).days)
    except ValueError:
        return False
    # nei pezzi del puzzle la «controparte» è solo il tema: lì servono due parole in comune, non una
    soglia = 2 if (a.get("tema") or b.get("tema")) and not (a.get("con") or a.get("ente")) else 1
    return bool(ca) and ca == cb and giorni <= 45 and len(comuni) >= soglia


def _piano_fondi(a, b, campo):
    """Due righe sullo stesso fatto diventano una: resta la tappa più avanti (firmato batte annunciato) o, a parità, la più
    recente; le fonti si sommano, la rilevanza è la più alta, le tappe precedenti restano in «tappe»."""
    pos = lambda x: PIANO_ORDINE_STATO.index(x.get("st") or "") if (x.get("st") or "") in PIANO_ORDINE_STATO else len(PIANO_ORDINE_STATO)
    nota = lambda x: bool(PIANO_NOTA.search(x.get(campo) or ""))  # a parità di stato, una riga con una nota dentro perde
    capo, altro = (a, b) if (pos(a), nota(a), b.get("d") or "") <= (pos(b), nota(b), a.get("d") or "") else (b, a)
    capo = dict(capo)
    viste = {f[1] for f in capo.get("f") or []}
    capo["f"] = (capo.get("f") or []) + [f for f in (altro.get("f") or []) if f[1] not in viste]
    capo["f"] = capo["f"][:5]
    capo["d"] = max(capo.get("d") or "", altro.get("d") or "")
    if capo.get("r") or altro.get("r"):
        capo["r"] = max(capo.get("r") or 0, altro.get("r") or 0)
    tappe = (capo.get("tappe") or []) + [[altro.get("d") or "", altro.get("st") or "", altro.get(campo) or ""]] + (altro.get("tappe") or [])
    capo["tappe"] = sorted({(t[0], t[2]): t for t in tappe if t[2] != capo.get(campo)}.values(), key=lambda t: t[0], reverse=True)[:5]
    if not capo["tappe"]:
        del capo["tappe"]
    return capo


def _piano_unisci(vecchi, nuovi, campo, massimo=30):
    """Aggiunge i fatti nuovi a quelli delle passate precedenti; in cima i più recenti. Lo stesso fatto resta una riga sola
    anche quando più titoli ne raccontano tappe diverse (vedi _piano_stesso): le righe si fondono, con tutte le fonti."""
    uniti = []
    for x in list(nuovi) + list(vecchi or []):
        for i, y in enumerate(uniti):
            if _piano_stesso(x, y, campo):
                uniti[i] = _piano_fondi(y, x, campo)
                break
        else:
            uniti.append(x)
    return sorted(uniti, key=lambda x: x.get("d") or "", reverse=True)[:massimo]


def passo_piano(cfg, chiavi, paesi, leggero, errori, notizia=None):
    """Lavoro a piano (dentro il giro, non un secondo ciclo): uno Stato alla volta, blocco per blocco a partire dall'Europa.
    Per ogni Stato: tre domande sulla stampa (accordi e patti, appalti e contratti, e una nella lingua del posto), poi il
    cervello legge i titoli, tira fuori accordi e appalti ognuno con le sue fonti, e scrive che cosa resta da chiarire.
    Le domande rimaste aperte vengono fatte nei giri dopo. Finiti tutti gli Stati ricomincia: la seconda passata aggiorna.
    Dalla 2.22 c'è un terzo tema, l'intelligence: una domanda in inglese e una nella lingua del posto sui servizi dello
    Stato; il cervello ne tira fuori i fatti pubblici (nomine, leggi, relazioni, espulsioni, processi), ognuno con la fonte.
    Restituisce [Stati lavorati in questo giro, accordi trovati, appalti trovati]; i fatti sui servizi stanno in passo_piano.intel."""
    imp = cfg.get("piano", {})
    perc = os.path.join(DATI, "piano.json")
    P = leggi_json(perc, {})
    adesso = datetime.now(timezone.utc)
    for campo, valore in (("stati", {}), ("i", 0), ("passata", 1), ("inizio", adesso.isoformat()), ("ultimi", [])):
        P.setdefault(campo, valore)
    if P.get("riordinato") != VERSIONE and P["stati"]:  # una volta per versione: lo stesso fatto resta una riga sola
        for sch_ in P["stati"].values():
            _piano_nomi(sch_.get("accordi"), paesi)  # dalla 2.25: «Stati Uniti» → «USA», «Türkiye» → «Turchia»…
            _piano_nomi(sch_.get("appalti"), paesi)
            for campo_, chiave_, max_ in (("accordi", "cosa", 30), ("appalti", "ogg", 30), ("intel", "cosa", 20), ("puzzle", "cosa", 40)):
                if sch_.get(campo_):
                    sch_[campo_] = _piano_unisci([], sch_[campo_], chiave_, max_)
                    for riga_ in sch_[campo_]:
                        riga_[chiave_] = _piano_senza_note(riga_.get(chiave_))
                        for tappa_ in riga_.get("tappe") or []:
                            tappa_[2] = _piano_senza_note(tappa_[2])
        P["riordinato"] = VERSIONE
        scrivi_json(perc, P)
    ordine = piano_ordine(cfg, paesi)
    riposo = P.get("riposo", "") > adesso.isoformat()  # dopo un rifiuto di Google News (429) Google riposa tre quarti d'ora
    _piano_titoli.bing = 0
    if not ordine or (riposo and not imp.get("bing", True)):
        return [0, 0, 0]
    base = leggi_json(os.path.join(QUI, "piano_base.json"), {})
    giorni, imp_c = imp.get("giorni", 120), cfg.get("cervello", {})
    con_cervello = bool(chiavi.get("anthropic_key")) and imp_c.get("attivo", True)
    conto = _conto_cervello()
    fatti = n_acc = n_app = n_int = n_pz = 0
    passo_piano.intel = passo_piano.puzzle = 0
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
            if imp.get("intelligence", True):
                dom.append(("intelligence", "en", PIANO_Q_INTEL["en"].format(n=en)))
                lg_i = lg if lg in PIANO_Q_INTEL else "it"  # la lingua del posto; dove non c'è, la stampa italiana
                if lg_i != "en":
                    dom.append(("intelligence", lg_i, PIANO_Q_INTEL[lg_i].format(n=loc[1] if lg_i == lg else paesi[stato][0])))
            # puzzle: un tema in più per Stato a rotazione (dalla 2.26 due, opposti: in due passate tutti e quattro)
            n_temi = max(1, min(2, imp.get("puzzle_temi", 1)))
            temi_p = [PUZZLE_ORDINE[(P["i"] + P["passata"] + 2 * k_) % len(PUZZLE_ORDINE)] for k_ in range(n_temi)] \
                if imp.get("puzzle", True) else []
            tema_p = temi_p[0] if temi_p else None
            for t_p in temi_p:
                q_p = PIANO_PUZZLE[t_p]["q"]
                dom.append((t_p, "en", q_p["en"].format(n=en)))
                lg_p = lg if lg in q_p else "it"
                if lg_p != "en":
                    dom.append((t_p, lg_p, q_p[lg_p].format(n=loc[1] if lg_p == lg else paesi[stato][0])))
            vecchio = P["stati"].get(stato, {})
            dom += [("aperta", d["l"], d["q"] if _nome_in_lingua(stato, d["l"], paesi).lower() in d["q"].lower()
                     else '"%s" %s' % (_nome_in_lingua(stato, d["l"], paesi), d["q"]))
                    for d in vecchio.get("aperte", []) if not d.get("fatta")][:1]
            bq = [(k_, BING_Q[k_].format(n=en)) for k_ in dict.fromkeys(x[0] for x in dom) if k_ in BING_Q] if imp.get("bing", True) else []
            titoli, fatte, fallite = _piano_titoli([] if riposo else dom, giorni, errori, imp.get("pausa", 1.0), bq)
            if fallite and any("429" in e for e in errori[-fallite:]):
                P["riposo"] = (adesso + timedelta(minutes=45)).isoformat()  # Google News sta rifiutando: basta per ora
                riposo = True
            if not titoli and (riposo or fallite >= len(dom)):
                break  # né Google News né Bing hanno risposto: si riprova più tardi, dallo stesso Stato
            titoli.sort(key=lambda x: x["iso"], reverse=True)
            # i titoli sui servizi hanno un loro tetto: non tolgono posto ad accordi e appalti, e viceversa
            titoli = [x for x in titoli if x["k"] != "intelligence" and x["k"] not in PIANO_PUZZLE][:imp.get("titoli_max", 70)] + \
                     [x for x in titoli if x["k"] == "intelligence"][:imp.get("titoli_intelligence", 25)] + \
                     [x for x in titoli if x["k"] in PIANO_PUZZLE][:imp.get("titoli_puzzle", 20) * max(1, len(temi_p))]
            if notizia:  # i titoli della settimana entrano anche tra le notizie dal vivo
                for x in (y for y in titoli if y["iso"] and y["k"] != "intelligence" and y["k"] not in PIANO_PUZZLE):
                    notizia("Industria e appalti" if x["k"] == "appalti" else "Alleanze e diplomazia", x["t"], x["u"], x["iso"],
                            x["f"], forza=stato, lingua=x["l"])
            scheda = {"blocco": blocco, "quando": adesso.isoformat(), "passata": P["passata"], "titoli": len(titoli), "domande": fatte,
                      "accordi": vecchio.get("accordi", []), "appalti": vecchio.get("appalti", []),
                      "intel": vecchio.get("intel", []), "puzzle": vecchio.get("puzzle", []), "aperte": [],
                      "risposte": vecchio.get("risposte", [])[-6:], "cervello": False}
            if vecchio.get("sintesi"):
                scheda["sintesi"] = vecchio["sintesi"]
            if titoli and con_cervello:
                b_ = base.get(stato, {})
                noti = [str(x) for x in b_.get("tr", []) + b_.get("ap", [])] + \
                       [x["cosa"] for x in vecchio.get("accordi", [])[:6]] + [x["ogg"] for x in vecchio.get("appalti", [])[:6]] + \
                       [x["cosa"] for x in vecchio.get("intel", [])[:5]] + \
                       [x["cosa"] for x in vecchio.get("puzzle", []) if x.get("tema") in temi_p][:8]
                try:
                    risposta = chiedi_claude(chiavi, cfg, _piano_domanda(stato, titoli, giorni, noti, tema_p,
                                                                         temi_p[1] if len(temi_p) > 1 else None), 3600, conto)
                    conto["chiamate"] = conto.get("chiamate", 0) + 1
                except Exception as e:
                    errori.append("Claude (lavoro a piano): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:160])
                    break  # il cervello non ha risposto: stesso Stato al prossimo giro
                acc, app, intel, aperte = _piano_leggi(risposta, titoli)
                _piano_nomi(acc, paesi)
                _piano_nomi(app, paesi)
                pezzi = ([dict(x, tema=tema_p) for x in _piano_leggi.puzzle] if tema_p else []) + \
                        ([dict(x, tema=temi_p[1]) for x in _piano_leggi.puzzle2] if len(temi_p) > 1 else [])
                scheda.update({"accordi": _piano_unisci(vecchio.get("accordi"), acc, "cosa"),
                               "appalti": _piano_unisci(vecchio.get("appalti"), app, "ogg"),
                               "intel": _piano_unisci(vecchio.get("intel"), intel, "cosa", 20),
                               "puzzle": _piano_unisci(vecchio.get("puzzle"), pezzi, "cosa", 40), "aperte": aperte, "cervello": True})
                scheda["nuovi"] = [len(acc), len(app), len(intel), len(pezzi)]
                scheda["tema"], scheda["temi"] = tema_p, temi_p
                n_acc, n_app, n_int, n_pz = n_acc + len(acc), n_app + len(app), n_int + len(intel), n_pz + len(pezzi)
                if imp.get("sintesi", True) and (acc or app or intel or pezzi or not scheda.get("sintesi")) \
                        and _cervello_libero(conto, imp_c):
                    s_ = sintesi_stato(chiavi, cfg, stato, scheda, leggi_json(os.path.join(DATI, "memoria.json"), {}).get(stato, []),
                                       conto, errori)
                    if s_:
                        scheda["sintesi"] = s_
            elif titoli:  # senza cervello: restano i titoli da leggere a mano, divisi per domanda
                scheda["da_leggere"] = [[x["t"], x["u"], x["f"], x["d"], x["k"]] for x in titoli[:16]]
            P["stati"][stato] = scheda
            P["ultimi"] = ([s for s in P["ultimi"] if s != stato] + [stato])[-40:]
            P["i"] += 1
            if P["i"] >= len(ordine):
                P["i"], P["passata"] = 0, P["passata"] + 1
            fatti += 1
        # sintesi degli Stati studiati prima della 2.25 (o con fatti più nuovi della sintesi): una per giro, senza ricerche
        for _ in range(imp.get("sintesi_per_giro", 1) if (con_cervello and imp.get("sintesi", True)) else 0):
            if not _cervello_libero(conto, imp_c):
                break
            scelta = next((s for s in list(reversed(P["ultimi"])) + [x for x in P["stati"] if x not in P["ultimi"]]
                           if P["stati"].get(s, {}).get("cervello") and P["stati"][s].get("quando") != adesso.isoformat()
                           and (P["stati"][s].get("sintesi") or {}).get("quando", "") < P["stati"][s].get("quando", "")), None)
            if not scelta:
                break
            s_ = sintesi_stato(chiavi, cfg, scelta, P["stati"][scelta],
                               leggi_json(os.path.join(DATI, "memoria.json"), {}).get(scelta, []), conto, errori)
            if not s_:
                P["stati"][scelta]["sintesi"] = {"quando": adesso.isoformat(), "righe": [], "fatti": 0}  # non riprovare subito
                break
            P["stati"][scelta]["sintesi"] = s_
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
    passo_piano.intel, passo_piano.puzzle = n_int, n_pz
    scrivi_json(perc, P)
    scrivi_json(os.path.join(DATI, "cervello.json"), conto)
    try:  # dalla 2.26: piano.js leggero per la pagina e un file pieno per ogni Stato (web/piano/ISO.json)
        scrivi_piano_web(P, cfg, len(ordine))
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
            "intel": sum(len(v.get("intel", [])) for v in S.values()),
            "sintesi": sum(1 for v in S.values() if (v.get("sintesi") or {}).get("righe")),
            "puzzle": {t: sum(1 for v in S.values() for x in v.get("puzzle", []) if x.get("tema") == t) for t in PUZZLE_ORDINE},
            "ultimi": [[s, S[s].get("quando", ""), len(S[s].get("accordi", [])), len(S[s].get("appalti", [])), S[s].get("titoli", 0),
                        S[s].get("blocco", ""), len(S[s].get("intel", []))] for s in ult[:10]],
            "domande": [[s] + list(d) for s in ult[:5] for d in S[s].get("domande", [])][:16],
            "aperte": [[s, d.get("l", ""), d.get("q", ""), d.get("perche", ""), bool(d.get("fatta"))] for s in ult[:12]
                       for d in S[s].get("aperte", [])][:12],
            "risposte": sorted(([s, r.get("perche") or r.get("q", ""), r.get("r", ""), r.get("f", []), r.get("quando", "")]
                                for s in ult for r in S[s].get("risposte", [])), key=lambda x: x[4], reverse=True)[:8]}


# ----------------------------------------------------------------------------- nomi degli Stati uniformi (dalla 2.25)

# varianti che il cervello scrive al posto del nome italiano usato da PanGeo: con il nome giusto i fatti di due Stati
# si collegano (l'accordo Italia–Grecia compare in tutte e due le cartelle)
NOMI_VARIANTI = {
    "stati uniti": "USA", "stati uniti d'america": "USA", "united states": "USA", "united states of america": "USA",
    "us": "USA", "u.s.": "USA", "u.s.a.": "USA", "america": "USA", "turkiye": "Turchia", "turkey": "Turchia",
    "moldova": "Moldavia", "czechia": "Repubblica Ceca", "cechia": "Repubblica Ceca", "czech republic": "Repubblica Ceca",
    "uk": "Regno Unito", "u.k.": "Regno Unito", "gran bretagna": "Regno Unito", "inghilterra": "Regno Unito",
    "united kingdom": "Regno Unito", "britain": "Regno Unito", "federazione russa": "Russia", "russian federation": "Russia",
    "repubblica popolare cinese": "Cina", "rpc": "Cina", "prc": "Cina", "olanda": "Paesi Bassi", "netherlands": "Paesi Bassi",
    "eau": "Emirati Arabi", "uae": "Emirati Arabi", "emirati": "Emirati Arabi", "emirati arabi uniti": "Emirati Arabi",
    "united arab emirates": "Emirati Arabi", "south korea": "Corea del Sud", "repubblica di corea": "Corea del Sud",
    "north korea": "Corea del Nord", "rdc": "RD Congo", "repubblica democratica del congo": "RD Congo",
    "dr congo": "RD Congo", "drc": "RD Congo", "birmania": "Myanmar", "burma": "Myanmar", "macedonia": "Macedonia del Nord",
    "bosnia": "Bosnia ed Erzegovina", "ivory coast": "Costa d’Avorio", "cote d'ivoire": "Costa d’Avorio",
    "costa d'avorio": "Costa d’Avorio", "arabia": "Arabia Saudita", "saudi arabia": "Arabia Saudita",
    "taiwan (repubblica di cina)": "Taiwan", "repubblica di cina": "Taiwan", "vietnam": "Vietnam", "viet nam": "Vietnam",
}
NOMI_NESSUNO = re.compile(r"^\(?\s*(nessun[oa]?\b|non (?:indicat|specificat|nominat)|sconosciut|ignot|ungenannt|unbekannt|"
                          r"unknown|unnamed|not (?:named|specified)|n\.?\s?d\.?$|-+$|–$)", re.I)


def _chiave_nome(testo):
    import unicodedata
    t = unicodedata.normalize("NFKD", (testo or "").replace("’", "'")).encode("ascii", "ignore").decode()
    return " ".join(t.lower().strip(" .").split())


def _alias_stati(paesi):
    if getattr(_alias_stati, "fatto", None) is paesi:
        return _alias_stati.mappa
    m = {}
    for it_, nomi in (paesi or {}).items():
        for n in nomi:  # le varianti di paesi.json (nomi, capitali, aggettivi): prima le altre, poi il nome stesso
            k = _chiave_nome(n)
            if len(k) > 3 and k not in m:
                m[k] = it_
    m.update({_chiave_nome(k): v for k, v in NOMI_VARIANTI.items() if v in (paesi or {})})
    for it_ in (paesi or {}):
        m[_chiave_nome(it_)] = it_
    _alias_stati.fatto, _alias_stati.mappa = paesi, m
    return m


def nome_controparte(testo, paesi):
    """«Stati Uniti», «Türkiye (MKE)», «Moldova / UE» → «USA», «Turchia (MKE)», «Moldavia, UE». Ciò che non è uno
    Stato (alleanze, aziende, enti) resta com'è; «nessuno indicato» e simili diventano vuoti."""
    t = " ".join((testo or "").split()).strip(" .;,")
    if not t or NOMI_NESSUNO.match(t):
        return ""
    alias = _alias_stati(paesi)
    if _chiave_nome(t) in alias:
        return alias[_chiave_nome(t)]
    fuori, pezzi, prof, buf = [], [], 0, ""
    for ch in t:  # si divide solo fuori dalle parentesi: «Italia (Segretariato / Direzione)» resta intero
        prof += (ch == "(") - (ch == ")")
        if ch in "/,;+" and prof <= 0:
            pezzi.append(buf.strip())
            buf = ""
        else:
            buf += ch
    pezzi.append(buf.strip())
    for p in pezzi:
        if not p or NOMI_NESSUNO.match(p):
            continue
        m = re.match(r"^([^()]+?)\s*(\(.*\))?$", p)
        testa, coda = (m.group(1), m.group(2) or "") if m else (p, "")
        c = alias.get(_chiave_nome(testa))
        fuori.append((c + (" " + coda if coda else "")) if c else p)
    return ", ".join(dict.fromkeys(fuori))


def _piano_nomi(righe, paesi):
    """Mette i nomi giusti nelle righe del piano (controparte, acquirente, fornitore)."""
    for r in righe or []:
        for campo in ("con", "acq", "forn"):
            if r.get(campo):
                nuovo = nome_controparte(r[campo], paesi)
                r[campo] = nuovo if (nuovo or campo == "con") else r[campo]
    return righe


# ----------------------------------------------------------------------------- sintesi di ogni Stato (dalla 2.25)

SINTESI_SEZIONI = ("Alleanze e accordi", "Difesa e appalti", "Intelligence", "Energia e risorse", "Quadro")


def _sintesi_fatti(scheda, memoria_stato, massimo=40):
    """I fatti che il programma ha già salvato su uno Stato, numerati, con la loro prima fonte: è la sola base della sintesi."""
    fatti = []
    for campo, chiave, etichetta, n in (("accordi", "cosa", "accordo", 12), ("appalti", "ogg", "appalto", 12),
                                        ("intel", "cosa", "intelligence", 8), ("puzzle", "cosa", "risorse", 8)):
        righe = sorted(scheda.get(campo) or [], key=lambda x: (x.get("r") or 0, x.get("d") or ""), reverse=True)[:n]
        for r in righe:
            altro = r.get("con") or (" → ".join(x for x in (r.get("forn"), r.get("acq")) if x)) or r.get("ente") or r.get("tema") or ""
            f = (r.get("f") or [[""]])[0]
            fatti.append([etichetta, r.get("d", ""), (altro + ": " if altro else "") + (r.get(chiave) or ""), f[0] if f else "",
                          f[1] if len(f) > 1 else ""])
    for x in (memoria_stato or [])[:8]:  # [data, testo, fonte, n. fonti, link, parole, livello]
        fatti.append(["confermato", x[0], x[1], x[2], x[4] if len(x) > 4 else ""])
    return fatti[:massimo]


def _sintesi_domanda(stato, fatti):
    righe = "\n".join(f"{i + 1}. [{f[0]}] {f[1] or 'senza data'} – {f[2]}" for i, f in enumerate(fatti))
    return (f"Ecco i fatti che un archivio pubblico ha raccolto su {stato}, ciascuno con la sua fonte:\n{righe}\n\n"
            "Scrivi in italiano semplice una sintesi di questi fatti, da 3 a 6 righe, ognuna così:\n"
            "S | sezione | frase | numeri dei fatti usati\n"
            "Sezioni possibili: " + ", ".join(SINTESI_SEZIONI) + ".\n"
            "Regole: usa SOLO i fatti dell'elenco, con le date quando ci sono; frasi brevi; niente giudizi, previsioni o "
            "consigli; un'accusa sempre con la replica, se c'è nell'elenco, altrimenti lasciala fuori; non ripetere lo "
            "stesso fatto in due righe. Nella sezione Quadro, al massimo una riga, metti solo un collegamento che si vede "
            "dai fatti (per esempio due accordi con lo stesso Stato). Nessun altro testo prima o dopo le righe.")


def _sintesi_leggi(risposta, fatti):
    righe = []
    for riga in (risposta or "").splitlines():
        p = [x.strip(" *`") for x in riga.strip().lstrip("-•* ").split("|")]
        if len(p) < 4 or p[0].upper().strip(" .:") != "S":
            continue
        numeri = [int(n) for n in re.findall(r"\d+", p[3]) if 1 <= int(n) <= len(fatti)]
        frase = _piano_senza_note(pulisci(p[2], 320))
        if not numeri or len(frase) < 15:
            continue  # una frase senza i fatti da cui viene non entra
        sez = next((s for s in SINTESI_SEZIONI if s.lower() in p[1].lower()), "Quadro")
        fonti = []
        for n in numeri[:4]:
            f = fatti[n - 1]
            if f[4] and [f[3], f[4]] not in fonti:
                fonti.append([f[3], f[4]])
        righe.append([sez, frase, fonti, [fatti[n - 1][1] for n in numeri[:4]]])
    return righe[:6]


def sintesi_stato(chiavi, cfg, stato, scheda, memoria_stato, conto, errori):
    """Una chiamata breve al cervello: la sintesi dei fatti già salvati su uno Stato (accordi, appalti, servizi, puzzle,
    fatti confermati). Ogni frase porta i numeri dei fatti da cui viene, quindi le sue fonti; senza fatti non si scrive."""
    fatti = _sintesi_fatti(scheda, memoria_stato)
    if len(fatti) < 3:
        return None
    try:
        risposta = chiedi_claude(chiavi, cfg, _sintesi_domanda(stato, fatti), 700, conto)
        conto["chiamate"] = conto.get("chiamate", 0) + 1
    except Exception as e:
        errori.append("Claude (sintesi di " + stato + "): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:160])
        return None
    righe = _sintesi_leggi(risposta, fatti)
    if not righe:
        return None
    return {"quando": datetime.now(timezone.utc).isoformat(), "righe": righe, "fatti": len(fatti)}


# ----------------------------------------------------------------------------- magazzino sul telefono (dalla 2.26)

# Il telefono di Savo è dedicato a PanGeo: tutto ciò che il programma raccoglie resta sul telefono, compresso, per anni.
#   dati/magazzino/notizie/AAAA-MM-GG.jsonl.xz   ogni notizia di quel giorno (titolo, traduzione, fonte, Stati, livello,
#                                                 conferma), scritta quando il giorno è «maturo» (2 giorni dopo: conferme e
#                                                 traduzioni fatte) e riscritta se arrivano notizie o conferme in più
#   dati/magazzino/giorni/AAAA-MM-GG/*.json.xz    una copia al giorno di memoria, piano, quadro e calore: la storia di che
#                                                 cosa sapeva l'archivio quel giorno
#   dati/magazzino/indice.json                    che cosa c'è, quanto pesa
# Tetto: config.json › magazzino › max_gb (60) e spazio libero minimo sul telefono (min_libero_gb, 10): oltre, si tolgono
# per primi i giorni più vecchi. Copia di sicurezza nella memoria condivisa (~/storage/shared/PanGeo), che resta anche se
# Termux si disinstalla: si accende con  termux-setup-storage.

def MAG(*p):
    return os.path.join(DATI, "magazzino", *p)


def _mag_scrivi(percorso, righe):
    """Righe → JSON Lines compresso con xz (circa un sesto del peso); se xz manca, gzip."""
    dati = ("\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in righe) + "\n").encode("utf-8")
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    tmp = percorso + ".tmp"
    try:
        import lzma
        with lzma.open(tmp, "wb", preset=6) as f:
            f.write(dati)
    except ImportError:
        with gzip.open(tmp, "wb", compresslevel=9) as f:
            f.write(dati)
    os.replace(tmp, percorso)


def _mag_apri(percorso):
    with open(percorso, "rb") as f:
        testa = f.read(6)
    if testa.startswith(b"\xfd7zXZ"):
        import lzma
        return lzma.open(percorso, "rt", encoding="utf-8")
    if testa.startswith(b"\x1f\x8b"):
        return gzip.open(percorso, "rt", encoding="utf-8")
    return open(percorso, encoding="utf-8")


def _mag_leggi(percorso):
    try:
        with _mag_apri(percorso) as f:
            for riga in f:
                riga = riga.strip()
                if riga:
                    try:
                        yield json.loads(riga)
                    except ValueError:
                        continue
    except (OSError, EOFError):
        return


def _notizia_corta(k, v):
    r = {"k": k, "t": v.get("t"), "it": v.get("it"), "u": v.get("u"), "f": v.get("fonte"), "d": v.get("data_iso"),
         "p": v.get("paesi"), "tm": v.get("tema"), "lv": v.get("lv"), "c": 1 if v.get("conf") else 0, "nf": v.get("nf"),
         "lg": v.get("lg")}
    return {a: b for a, b in r.items() if b not in (None, "", [], 0) or a == "c"}


def _mag_peso():
    tot = 0
    for radice, _, nomi in os.walk(MAG()):
        for n in nomi:
            try:
                tot += os.path.getsize(os.path.join(radice, n))
            except OSError:
                pass
    return tot


def _mag_copia_dir(imp):
    return os.path.expanduser(imp.get("copia", "~/storage/shared/PanGeo"))


def _mag_pulisci(I, imp):
    """Tiene il magazzino sotto il tetto e lascia libero lo spazio minimo sul telefono: via i giorni più vecchi."""
    copia = bool(I.get("copia"))
    tetto = imp.get("max_gb", 60) * 1e9 / (2 if copia else 1)  # la copia di sicurezza pesa quanto il magazzino
    minimo = imp.get("min_libero_gb", 10) * 1e9
    peso = _mag_peso()
    try:
        libero = shutil.disk_usage(DATI).free
    except OSError:
        libero = minimo + 1
    tolti = 0
    for d in sorted(I.get("giorni", {})):
        if peso <= tetto and libero >= minimo:
            break
        for p in (MAG("notizie", d + ".jsonl.xz"), os.path.join(_mag_copia_dir(imp), "magazzino", "notizie", d + ".jsonl.xz")):
            if os.path.exists(p):
                b = os.path.getsize(p)
                os.remove(p)
                if p.startswith(MAG()):
                    peso -= b
                libero += b
        del I["giorni"][d]
        tolti += 1
    # copie giornaliere di memoria e piano: le ultime N, più la prima di ogni mese
    tieni = imp.get("istantanee_giorni", 30)
    giorni_ist = sorted(os.listdir(MAG("giorni"))) if os.path.isdir(MAG("giorni")) else []
    mesi_visti = set()
    for d in giorni_ist[:-tieni] if len(giorni_ist) > tieni else []:
        if d[:7] not in mesi_visti:
            mesi_visti.add(d[:7])
            continue
        shutil.rmtree(MAG("giorni", d), ignore_errors=True)
        tolti += 1
    I["peso"], I["libero"] = _mag_peso(), libero
    if tolti:
        I["tolti"] = I.get("tolti", 0) + tolti
    return tolti


def _mag_copia(I, imp, adesso):
    """Copia di sicurezza nella memoria condivisa del telefono (fuori da Termux), una volta al giorno, solo i file nuovi."""
    dest = _mag_copia_dir(imp)
    if not imp.get("copia_attiva", True) or not os.path.isdir(os.path.dirname(dest)):
        I["copia"] = ""  # serve  termux-setup-storage  (una volta sola)
        return
    oggi = adesso.date().isoformat()
    if I.get("copia_il") == oggi:
        return
    n = 0
    for radice, _, nomi in os.walk(MAG()):
        for nome in nomi:
            if nome.endswith(".tmp"):
                continue
            src = os.path.join(radice, nome)
            dst = os.path.join(dest, "magazzino", os.path.relpath(src, MAG()))
            try:
                if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src):
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst + ".tmp")
                os.replace(dst + ".tmp", dst)
                n += 1
            except OSError:
                continue
    I["copia"], I["copia_il"], I["copia_file"] = dest, oggi, n


def magazzino(archivio, cfg, adesso):
    """A ogni giro: i giorni maturi nel magazzino (pochi a giro), la copia del giorno, la pulizia, la copia di sicurezza."""
    imp = cfg.get("magazzino", {})
    if not imp.get("attivo", True):
        return None
    os.makedirs(MAG(), exist_ok=True)
    I = leggi_json(MAG("indice.json"), {}) or {}
    I.setdefault("giorni", {})
    per = {}
    for k, v in (archivio.get("notizie") or {}).items():
        d = (v.get("data_iso") or "")[:10]
        if len(d) == 10:
            per.setdefault(d, {})[k] = v
    maturo = (adesso - timedelta(days=imp.get("maturi_giorni", 2))).date().isoformat()
    scritti = 0
    for d in sorted(per, reverse=True):
        if d > maturo:
            continue
        nuove, gia = per[d], I["giorni"].get(d) or {}
        conf = sum(1 for v in nuove.values() if v.get("conf"))
        trad = sum(1 for v in nuove.values() if v.get("it"))
        if gia and gia.get("visti", 0) >= len(nuove) and gia.get("conf_a", 0) >= conf and gia.get("trad_a", 0) >= trad:
            continue
        perc = MAG("notizie", d + ".jsonl.xz")
        tutte = {r.get("k"): r for r in _mag_leggi(perc)} if os.path.exists(perc) else {}
        for k, v in nuove.items():
            tutte[k] = _notizia_corta(k, v)
        _mag_scrivi(perc, list(tutte.values()))
        I["giorni"][d] = {"n": len(tutte), "conf": sum(1 for r in tutte.values() if r.get("c")), "byte": os.path.getsize(perc),
                          "visti": len(nuove), "conf_a": conf, "trad_a": trad}
        scritti += 1
        if scritti >= imp.get("giorni_per_giro", 2):
            break
    oggi = adesso.date().isoformat()
    if I.get("istantanea") != oggi:
        for nome in ("memoria.json", "piano.json", "quadro.json", "calore_zone.json", "servizi.json", "basi_wd.json"):
            src = os.path.join(DATI, nome)
            if os.path.exists(src):
                try:
                    _mag_scrivi(MAG("giorni", oggi, nome + ".xz"), [leggi_json(src, {})])
                except Exception:
                    pass
        I["istantanea"] = oggi
    _mag_pulisci(I, imp)
    _mag_copia(I, imp, adesso)
    I["agg"] = adesso.isoformat()
    scrivi_json(MAG("indice.json"), I)
    return [round(I.get("peso", 0) / 1e6, 1), len(I["giorni"]), sum(g.get("n", 0) for g in I["giorni"].values()),
            round(I.get("libero", 0) / 1e9, 1), 1 if I.get("copia") else 0]


def _norm(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(t or "").replace("’", "'")).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9/'-]+", " ", t.lower()).split())


def cerca(q, stato=None, giorni=3650, massimo=60):
    """Cerca in tutto ciò che il telefono conserva: fatti confermati, notizie degli ultimi 7 giorni, lavoro a piano e il
    magazzino, dal giorno più recente. Tutte le parole devono esserci (senza accenti e maiuscole)."""
    parole_q = [w for w in _norm(q).split() if len(w) > 1]
    if not parole_q:
        return []
    try:  # dalla 2.29: l'indice istantaneo (SQLite), se c'è; altrimenti si legge tutto come prima
        r_ = indice_cerca(q, stato, massimo)
        if r_:
            return r_
    except Exception:
        pass
    va = lambda testo: all(w in _norm(testo) for w in parole_q)
    fuori, visti = [], set()

    def metti(r):
        k = r.get("u") or r.get("t")
        if k in visti or len(fuori) >= massimo:
            return
        visti.add(k)
        fuori.append(r)
    for st_, l in (leggi_json(os.path.join(DATI, "memoria.json"), {}) or {}).items():
        if stato and st_ != stato:
            continue
        for x in l:
            if va(x[1]):
                metti({"d": x[0], "t": x[1], "f": x[2], "u": x[4], "p": [st_], "dove": "fatto confermato", "c": 1})
    P = (leggi_json(os.path.join(DATI, "piano.json"), {}) or {}).get("stati", {})
    for st_, s in P.items():
        if stato and st_ != stato:
            continue
        for campo, chiave in (("accordi", "cosa"), ("appalti", "ogg"), ("intel", "cosa"), ("puzzle", "cosa")):
            for x in s.get(campo) or []:
                testo = " ".join(str(x.get(c) or "") for c in (chiave, "con", "acq", "forn", "ente"))
                if va(testo):
                    f = (x.get("f") or [["", ""]])[0]
                    metti({"d": x.get("d", ""), "t": x.get(chiave, ""), "f": f[0], "u": f[1] if len(f) > 1 else "",
                           "p": [st_], "dove": "lavoro a piano: " + campo})
    recenti = sorted((leggi_json(os.path.join(DATI, "archivio.json"), {}) or {}).get("notizie", {}).items(),
                     key=lambda kv: kv[1].get("data_iso", ""), reverse=True)
    for k, v in recenti:
        if stato and stato not in (v.get("paesi") or []):
            continue
        if va((v.get("it") or "") + " " + (v.get("t") or "")):
            metti({"d": (v.get("data_iso") or "")[:10], "t": v.get("it") if va(v.get("it") or "") else v.get("t"), "f": v.get("fonte"), "u": v.get("u"),
                   "p": v.get("paesi") or [], "dove": "notizia", "c": 1 if v.get("conf") else 0})
    limite = (datetime.now(timezone.utc) - timedelta(days=giorni)).date().isoformat()
    for d in sorted((leggi_json(MAG("indice.json"), {}) or {}).get("giorni", {}), reverse=True):
        if d < limite or len(fuori) >= massimo:
            break
        for r in _mag_leggi(MAG("notizie", d + ".jsonl.xz")):
            if stato and stato not in (r.get("p") or []):
                continue
            if va((r.get("it") or "") + " " + (r.get("t") or "")):
                metti({"d": (r.get("d") or "")[:10], "t": r.get("it") if va(r.get("it") or "") else r.get("t"), "f": r.get("f"), "u": r.get("u"),
                       "p": r.get("p") or [], "dove": "notizia (magazzino)", "c": r.get("c", 0)})
    return sorted(fuori, key=lambda r: str(r.get("d") or ""), reverse=True)


# ----------------------------------------------------------------------------- seconda fonte di ricerca: Bing News (dalla 2.26)

# domande semplici in inglese (Bing non regge le domande lunghe con OR e parentesi): una per tipo
BING_Q = {"accordi": '"{n}" defence agreement', "appalti": '"{n}" military contract', "intelligence": '"{n}" intelligence service',
          "energia": '"{n}" energy grid', "ia": '"{n}" military artificial intelligence', "trasporti": '"{n}" port railway',
          "cibo": '"{n}" food security'}


def _motori():
    return leggi_json(os.path.join(DATI, "motori.json"), {}) or {}


def motore_ok(M, nome, tipo, adesso):
    """Il programma impara quali motori rendono: un motore che sbaglia 5 volte di fila riposa 2 ore; per un tipo di
    domanda che con quel motore non porta quasi niente (dopo 6 prove, meno di un titolo a domanda) si riprova solo una
    volta su sei."""
    m = M.get(nome) or {}
    if m.get("pausa", "") > adesso.isoformat():
        return False
    r = (m.get("tipi") or {}).get(tipo)
    if r and r[0] >= 6 and r[1] < r[0]:
        r[2] = (r[2] if len(r) > 2 else 0) + 1
        if r[2] % 6:
            return False
    return True


def motore_esito(M, nome, tipo, titoli, errore, adesso):
    m = M.setdefault(nome, {"prove": 0, "titoli": 0, "errori": 0, "di_fila": 0, "tipi": {}})
    m["prove"] += 1
    m["titoli"] += titoli
    r = m["tipi"].setdefault(tipo, [0, 0, 0])
    r[0] += 1
    r[1] += titoli
    if errore:
        m["errori"] += 1
        m["ultimo_errore"] = [adesso.isoformat(), str(errore)[:140]]
    if errore or not titoli:
        m["di_fila"] = m.get("di_fila", 0) + 1
        if m["di_fila"] >= 5:
            m["pausa"], m["di_fila"] = (adesso + timedelta(hours=2)).isoformat(), 0
    else:
        m["di_fila"] = 0
    m["agg"] = adesso.isoformat()


def bing_news(q, giorni=30):
    """Notizie da Bing News (RSS gratuito): stesso formato di google_news, con l'indirizzo vero dell'articolo."""
    url = "https://www.bing.com/news/search?" + urllib.parse.urlencode(
        {"q": q, "format": "rss", "setlang": "en", "qft": 'interval="8"' if giorni <= 7 else 'interval="9"'})
    testo = scarica(url, timeout=30, intestazioni={"User-Agent": "PanGeo/" + VERSIONE + " (archivio personale; lettore RSS)"}
                    ).decode("utf-8", "replace")
    if "<rss" not in testo[:800]:  # dal telefono, con l'intestazione di un browser, Bing mandava la sua pagina web
        raise ValueError("Bing ha mandato una pagina web invece del feed RSS")
    limite = datetime.now(timezone.utc) - timedelta(days=giorni)
    voci = []
    for it in re.findall(r"<item>(.*?)</item>", testo, re.S):
        def g(tag):
            m = re.search(r"<%s>(.*?)</%s>" % (re.escape(tag), re.escape(tag)), it, re.S)
            return html.unescape(re.sub(r"^<!\[CDATA\[|\]\]>$", "", m.group(1).strip())) if m else ""
        link = g("link")
        vero = (urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("url") or [link])[0]
        try:
            quando = email.utils.parsedate_to_datetime(g("pubDate")).astimezone(timezone.utc)
        except (TypeError, ValueError):
            quando = None
        if quando and quando < limite:
            continue
        voci.append((pulisci(g("title"), 240), vero, quando.isoformat() if quando else "", g("News:Source") or dominio(vero), dominio(vero)))
    return voci


# ----------------------------------------------------------------------------- file per Stato per il sito (dalla 2.26)

def _file_stato(nome, cfg):
    iso = (cfg.get("siti_militari", {}).get("iso") or {}).get(nome)
    return iso or re.sub(r"[^a-z0-9]+", "-", _norm(nome)).strip("-") or "x"


def _scrivi_se_cambia(percorso, testo):
    try:
        if open(percorso, encoding="utf-8").read() == testo:
            return False
    except OSError:
        pass
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    with open(percorso + ".tmp", "w", encoding="utf-8") as f:
        f.write(testo)
    os.replace(percorso + ".tmp", percorso)
    return True


def scrivi_memoria_web(M, cfg):
    """memoria.js leggero (gli ultimi 8 fatti di ogni Stato, quanti sono in tutto e il nome del file) più un file per Stato
    con tutti i fatti (web/memoria/ISO.json): la pagina scarica solo quello dello Stato che apri."""
    riga = lambda x: [x[0], x[1], x[2], x[3], x[4], x[6] if len(x) > 6 else ""]
    file_ = {k: _file_stato(k, cfg) for k in M}
    corto = {k: [riga(x) for x in l[:8]] for k, l in M.items()}
    _scrivi_se_cambia(os.path.join(WEB, "memoria.js"),
                      "window.MEMORIA=" + json.dumps(corto, ensure_ascii=False, separators=(",", ":")) + ";window.MEMORIA_N="
                      + json.dumps({k: len(l) for k, l in M.items()}, separators=(",", ":")) + ";window.MEMORIA_FILE="
                      + json.dumps(file_, ensure_ascii=False, separators=(",", ":")) + ";")
    for k, l in M.items():
        _scrivi_se_cambia(os.path.join(WEB, "memoria", file_[k] + ".json"),
                          json.dumps({"stato": k, "fatti": [riga(x) for x in l]}, ensure_ascii=False, separators=(",", ":")))


def _piano_corto(s):
    """La scheda del piano per piano.js: una fonte per riga, tappe brevi, niente titoli da leggere né domande fatte."""
    c = {k: v for k, v in s.items() if k not in ("domande", "da_leggere")}
    c["risposte"] = (s.get("risposte") or [])[-2:]
    for campo in ("accordi", "appalti", "intel", "puzzle"):
        l = []
        for r in s.get(campo) or []:
            r = dict(r)
            r["nf"] = len(r.get("f") or [])
            r["f"] = [f[:2] for f in (r.get("f") or [])[:1]]
            if r.get("tappe"):
                r["tappe"] = [[t[0], t[1], str(t[2])[:110]] for t in r["tappe"] if len(t) > 2]
            l.append(r)
        c[campo] = l
    c["pieno"] = False
    return c


def scrivi_piano_web(P, cfg, totale):
    file_ = {k: _file_stato(k, cfg) for k in P["stati"]}
    _scrivi_se_cambia(os.path.join(WEB, "piano.js"), "window.PIANO=" + json.dumps(
        {"agg": P["agg"], "passata": P["passata"], "i": P["i"], "totale": totale, "blocchi": cfg.get("piano", {}).get("blocchi", []),
         "ultimi": P["ultimi"], "file": file_, "stati": {k: _piano_corto(v) for k, v in P["stati"].items()}},
        ensure_ascii=False, separators=(",", ":")) + ";")
    for k, v in P["stati"].items():
        _scrivi_se_cambia(os.path.join(WEB, "piano", file_[k] + ".json"),
                          json.dumps(dict(v, stato=k, pieno=True), ensure_ascii=False, separators=(",", ":")))


# ----------------------------------------------------------------------------- officina: attrezzi gratuiti sul telefono (dalla 2.27)

# Il programma spende il credito di Claude soprattutto per tradurre e scegliere i titoli. Il telefono di Savo è dedicato
# a PanGeo: dove può, il lavoro lo fa il telefono, gratis, con attrezzi che il programma si installa e si prova da solo.
#   1. conta quanto costa ogni lavoro del cervello (cervello.json › lavori_oggi, lavori_mese)
#   2. si installa llama.cpp (pkg install llama-cpp) e scarica un modello piccolo e aperto (Qwen3 4B, licenza
#      Apache 2.0, circa 2,5 GB), solo in carica e in Wi-Fi
#   3. lo prova: traduce titoli che il cervello ha già tradotto e confronta, lingua per lingua, e misura la velocità
#   4. se va bene, traduce lui i titoli di quelle lingue, solo in carica e sotto i 38 gradi; il resto lo fa il cervello
#   Ogni settimana si riprova. Gli attrezzi sono scritti qui: codice nuovo arriva sempre con «approva».

LAVORI_CERVELLO = (("Traduci in italiano questi titoli", "traduzioni"), ("Traduci in italiano questi testi", "traduzioni del sapere"),
                   ("Sono titoli di giornali", "sala d'attesa"), ("Sei il redattore", "da sapere adesso"),
                   ("Lavori a un archivio", "lavoro a piano"), ("Ecco i fatti", "sintesi"), ("Domanda", "domande e risposte"),
                   ("Sei il revisore", "revisore"), ("Sei lo storico", "storia"))


def lavoro_di(testo):
    t = (testo or "")[:80]
    for inizio, nome in LAVORI_CERVELLO:
        if t.startswith(inizio):
            return nome
    if "QUADRO" in (testo or "")[:3000] or "scaletta" in (testo or "")[:1500]:
        return "quadro"
    if "servizi di intelligence" in (testo or "")[:400] or "servizio di" in (testo or "")[:300]:
        return "servizi"
    return "altro"


OFFICINA_MODELLO = {"nome": "Qwen3 4B Instruct 2507 (Q4_K_M)", "licenza": "Apache 2.0", "byte": 2497281120,
                    "url": "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"}
# provato il 20 novembre 2026 su 12 titoli in 9 lingue: traduzioni buone (Qwen2.5 1.5B invece no: lasciava il francese
# in francese e l'arabo in arabo). Sul telefono servono circa 3 GB di memoria mentre lavora.
OFF = lambda *p: os.path.join(DATI, "officina", *p)
NOMI_LINGUE = {"ru": "russo", "uk": "ucraino", "ar": "arabo", "fa": "persiano", "he": "ebraico", "tr": "turco", "zh": "cinese",
               "ja": "giapponese", "ko": "coreano", "hi": "hindi", "id": "indonesiano", "es": "spagnolo", "pt": "portoghese",
               "fr": "francese", "de": "tedesco", "en": "inglese", "pl": "polacco", "sr": "serbo", "hr": "croato", "bg": "bulgaro",
               "ro": "rumeno", "hu": "ungherese", "cs": "ceco", "nl": "olandese", "el": "greco", "vi": "vietnamita", "th": "thai"}


def _lingua_di(v):
    return v.get("lg") or lingua_titolo(v.get("t") or "")


def _off_stato():
    return leggi_json(OFF("stato.json"), {}) or {}


def _off_salva(S):
    os.makedirs(OFF(), exist_ok=True)
    scrivi_json(OFF("stato.json"), S)


def _wifi():
    """Vero se il telefono è in Wi-Fi (app Termux:API); se non si sa, falso: il modello pesa 2,5 GB."""
    if not shutil.which("termux-wifi-connectioninfo"):
        return False
    try:
        r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=20)
        w = json.loads(r.stdout or "{}")
        return w.get("supplicant_state") == "COMPLETED" and w.get("ip") not in (None, "", "0.0.0.0")
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


def _vivo_pid(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def _e_llama(pid):
    """Vero se il processo è davvero llama-server: su Android i numeri dei processi tornano presto a un altro
    programma, e un numero vecchio faceva credere che il traduttore fosse già acceso (dalla 2.29)."""
    try:
        with open(f"/proc/{int(pid)}/cmdline", "rb") as f:
            return b"llama-server" in f.read()
    except (OSError, ValueError, TypeError):
        return bool(pid) and _vivo_pid(pid) and not os.path.isdir("/proc/self")


def _coda_log(nome, righe=3):
    try:
        with open(OFF(nome), "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4000))
            return " | ".join(r.strip() for r in f.read().decode("utf-8", "replace").splitlines()[-righe:] if r.strip())[:300]
    except OSError:
        return ""


def _off_server_su(S, porta):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/health", timeout=3) as r:
            return r.status == 200
    except OSError:
        return False


def _off_ferma_traduttore(S):
    """Spegne solo il traduttore (llama-server con il modello grande), non il modello dei significati."""
    if S.get("pid_server") and _vivo_pid(S["pid_server"]) and _e_llama(S["pid_server"]):
        try:
            os.kill(int(S["pid_server"]), signal.SIGTERM)
        except OSError:
            pass
    S["pid_server"] = None


def _off_ferma(S):
    for k_ in ("pid_sig",):  # dalla 2.29 anche il server dei significati
        if S.get(k_) and _vivo_pid(S[k_]) and _e_llama(S[k_]):  # mai un altro programma con lo stesso numero
            try:
                os.kill(int(S[k_]), signal.SIGTERM)
            except OSError:
                pass
        S[k_] = None
    if S.get("pid_server") and _vivo_pid(S["pid_server"]) and _e_llama(S["pid_server"]):
        try:
            os.kill(int(S["pid_server"]), signal.SIGTERM)
        except OSError:
            pass
    S["pid_server"] = None


def _off_traduci_uno(testo, porta, attesa=60):
    corpo = json.dumps({"messages": [
        {"role": "system", "content": "Sei un traduttore. Traduci in italiano il titolo di giornale che ti viene dato. Traduzione "
                                      "fedele e completa; nomi di persone, luoghi, sigle e numeri restano come sono. Rispondi "
                                      "solo con la traduzione, su una riga, senza virgolette e senza commenti."},
        {"role": "user", "content": testo}], "temperature": 0.1, "max_tokens": 90, "stream": False}).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{porta}/v1/chat/completions", data=corpo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=attesa) as r:
        d = json.loads(r.read())
    t = ((d.get("choices") or [{}])[0].get("message") or {}).get("content", "")
    t = t.strip().splitlines()[0].strip().strip('"«»“”') if t.strip() else ""
    return pulisci(t, 300)


def _somiglia(a, b):
    pa = {w for w in re.findall(r"\w+", _norm(a)) if len(w) > 2}
    pb = {w for w in re.findall(r"\w+", _norm(b)) if len(w) > 2}
    return len(pa & pb) / max(len(pa | pb), 1)


def officina(cfg, tel, archivio, errori, adesso):
    """A ogni giro, un passo: installa, scarica, accende o spegne, prova. Mai con il telefono caldo o la batteria bassa."""
    imp = cfg.get("officina", {})
    if not imp.get("attivo", True) or not _su_termux():
        return None
    S = _off_stato()
    S.setdefault("fase", "da installare")
    porta = imp.get("porta", 8091)
    if not imp.get("traduttore", True):  # dalla 2.30.2: il traduttore si può spegnere da solo (il resto dell'officina lavora)
        _off_ferma_traduttore(S)
        S["fase"] = "traduttore spento in config.json (" + str(imp.get("perche_spento") or "scelta di Savo") + ")"
        _off_salva(S)
        return S
    # dalla 2.28.2 il telefono è dedicato a PanGeo: il traduttore lavora anche fuori carica, finché la batteria non scende
    # sotto la soglia (config.json › officina › batteria_min_fuori_carica) e il telefono resta al fresco
    fuori_ok_ = imp.get("lavora_senza_carica", True) and (tel.get("batteria") or 0) >= imp.get("batteria_min_fuori_carica", 35)
    ok_tel = (bool(tel.get("in_carica")) and (tel.get("batteria") or 0) >= 20 or fuori_ok_) \
        and (tel.get("temp") or 99) < imp.get("temp_max", 38)
    S["ok_tel"] = ok_tel
    if not ok_tel:
        _off_ferma(S)  # fuori carica o caldo: il traduttore si spegne e lavora il cervello
        _off_salva(S)
        return S
    # 1. llama.cpp dal repository di Termux (una volta; se non riesce, si riprova il giorno dopo)
    if not shutil.which("llama-server"):
        if S.get("pkg_provato") == adesso.date().isoformat():
            _off_salva(S)
            return S
        S["pkg_provato"], S["fase"] = adesso.date().isoformat(), "installo llama.cpp"
        _off_salva(S)
        try:
            r = subprocess.run(["pkg", "install", "-y", "llama-cpp"], capture_output=True, text=True, timeout=1200,
                               stdin=subprocess.DEVNULL, env=dict(os.environ, DEBIAN_FRONTEND="noninteractive"))
            if r.returncode or not shutil.which("llama-server"):
                S["errore"] = "pkg install llama-cpp: " + (r.stderr or r.stdout or "")[-200:]
                errori.append("Officina: llama.cpp non si è installato (riprovo domani)")
        except (OSError, subprocess.SubprocessError) as e:
            S["errore"] = str(e)[:200]
        S["fase"] = "da scaricare" if shutil.which("llama-server") else "da installare"
        _off_salva(S)
        return S
    # 2. il modello, scaricato in sottofondo con curl (riprende da dove era rimasto), solo in Wi-Fi
    mod = OFF("modello.gguf")
    if not os.path.exists(mod) or os.path.getsize(mod) != OFFICINA_MODELLO["byte"]:
        mb_ = round(os.path.getsize(mod + ".part") / 1e6) if os.path.exists(mod + ".part") else 0
        tot_ = round(OFFICINA_MODELLO["byte"] / 1e6)
        sc_ = _scarico_fresco()
        if sc_ and sc_.get("cuore"):  # dalla 2.28 scarica il cuore di PanGeo, che resta acceso tra un giro e l'altro
            S["fase"] = (f"scarico il modello ({sc_.get('mb', mb_)} MB su {tot_}"
                         + (f", {sc_['vel']} MB/s)" if sc_.get("vel") and sc_.get("stato") == "scarico" else ")")
                         + ("" if sc_.get("stato") in ("scarico", None) else f" · {sc_['stato']}"))
            if sc_.get("errore"):
                S["errore"] = "scarico: " + sc_["errore"]
        elif S.get("pid_curl") and _vivo_pid(S["pid_curl"]):
            S["fase"] = f"scarico il modello ({mb_} MB su {tot_}, con curl)"
        elif os.path.exists(mod + ".part") and os.path.getsize(mod + ".part") == OFFICINA_MODELLO["byte"]:
            os.replace(mod + ".part", mod)
        elif _wifi() or imp.get("scarica_senza_wifi", False):
            blocco_ = _blocco_scarico()  # riserva: se il cuore non scarica (versione vecchia), lo fa curl
            if blocco_:
                try:
                    if not shutil.which("curl"):
                        subprocess.run(["pkg", "install", "-y", "curl"], capture_output=True, timeout=600, stdin=subprocess.DEVNULL)
                    os.makedirs(OFF(), exist_ok=True)
                    p = subprocess.Popen(["curl", "-sSfL", "-C", "-", "--retry", "5", "--retry-delay", "10", "-o", mod + ".part",
                                          OFFICINA_MODELLO["url"]], stdout=subprocess.DEVNULL,
                                         stderr=open(OFF("curl.log"), "ab"), start_new_session=True)
                    S["pid_curl"], S["fase"] = p.pid, f"scarico il modello ({mb_} MB su {tot_}, con curl)"
                    _off_salva(S)
                finally:
                    blocco_.close()
            else:
                S["fase"] = f"scarico il modello ({mb_} MB su {tot_})"
        else:
            S["fase"] = f"aspetto il Wi-Fi per scaricare il modello ({mb_} MB su {tot_} già scaricati)"
        _off_salva(S)
        return S
    # 3. il server locale: acceso solo in carica e al fresco
    if not _off_server_su(S, porta):
        vivo_ = S.get("pid_server") and _vivo_pid(S["pid_server"]) and _e_llama(S["pid_server"])
        try:
            da_ = (adesso - datetime.fromisoformat(S.get("acceso_da") or adesso.isoformat())).total_seconds() / 60
        except ValueError:
            da_ = 0
        if vivo_ and da_ > 12:  # acceso da più di 12 minuti ma non risponde: si spegne, si legge il registro e si riprova
            S["errore"] = "il traduttore non risponde: " + _coda_log("server.log")
            _off_ferma(S)
            vivo_ = False
        if not vivo_:
            if S.get("acceso_da") and da_ > 1:
                S["errore"] = "il traduttore si è chiuso: " + _coda_log("server.log")
            log = open(OFF("server.log"), "ab")
            p = subprocess.Popen(["llama-server", "-m", mod, "--host", "127.0.0.1", "--port", str(porta), "-c", "1024",
                                  "-t", str(imp.get("thread", 4))], stdout=log, stderr=log,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
            S["pid_server"], S["acceso_da"] = p.pid, adesso.isoformat()
        S["fase"] = "accendo il traduttore"
        _off_salva(S)
        return S  # il modello si carica in qualche secondo: si usa dal giro dopo
    S.pop("acceso_da", None)
    # 4. la prova (la prima volta e poi ogni settimana): titoli già tradotti dal cervello, lingua per lingua
    prova = S.get("prova") or {}
    if not prova.get("quando") or prova["quando"] < (adesso - timedelta(days=7)).isoformat():
        campione = [v for v in archivio.get("notizie", {}).values() if v.get("it") and v.get("tr") != "telefono"
                    and _lingua_di(v) not in ("it", "", None)]
        per_lingua = {}
        for v in sorted(campione, key=lambda x: x.get("data_iso") or "", reverse=True):
            if len(per_lingua.setdefault(_lingua_di(v), [])) < 4:
                per_lingua[_lingua_di(v)].append(v)
        scelti = [v for l in per_lingua.values() for v in l][:imp.get("prova_titoli", 24)]
        esiti, t0 = {}, time.time()
        for v in scelti:
            if time.time() - t0 > imp.get("secondi_per_giro", 150):
                break
            try:
                tr = _off_traduci_uno(v["t"], porta)
            except (OSError, ValueError) as e:
                errori.append(f"Officina (prova): {str(e)[:100]}")
                break
            esiti.setdefault(_lingua_di(v), []).append(round(_somiglia(tr, v["it"]), 2))
        fatti = sum(len(l) for l in esiti.values())
        if fatti:
            sec = (time.time() - t0) / fatti
            soglia = imp.get("somiglianza_minima", 0.45)
            S["prova"] = {"quando": adesso.isoformat(), "titoli": fatti, "secondi_a_titolo": round(sec, 1),
                          "lingue": {lg: round(sum(l) / len(l), 2) for lg, l in esiti.items()},
                          "buone": sorted(lg for lg, l in esiti.items() if len(l) >= 2 and sum(l) / len(l) >= soglia)}
            S["fase"] = "attivo" if S["prova"]["buone"] and sec <= imp.get("secondi_max_a_titolo", 20) else "provato: non abbastanza buono"
        _off_salva(S)
        return S
    S["fase"] = "attivo" if prova.get("buone") and prova.get("secondi_a_titolo", 99) <= imp.get("secondi_max_a_titolo", 20) \
        else "provato: non abbastanza buono"
    _off_salva(S)
    return S


def officina_traduci(da_tradurre, cfg, ric, errori):
    """Prima del cervello: il telefono traduce gratis i titoli delle lingue che ha superato la prova. Restituisce quelli
    rimasti da tradurre, che vanno al cervello come prima."""
    imp = cfg.get("officina", {})
    S = _off_stato()
    if S.get("fase") != "attivo" or not S.get("ok_tel") or not _off_server_su(S, imp.get("porta", 8091)):
        return da_tradurre
    buone, porta = set((S.get("prova") or {}).get("buone") or []), imp.get("porta", 8091)
    resto, fatti, t0 = [], 0, time.time()
    for i, v in enumerate(da_tradurre):
        if time.time() - t0 > imp.get("secondi_per_giro", 150) or fatti >= imp.get("per_giro", 40):
            resto.extend(da_tradurre[i:])
            break
        if _lingua_di(v) not in buone:
            resto.append(v)
            continue
        try:
            tr = _off_traduci_uno(v["t"], porta)
        except (OSError, ValueError) as e:
            errori.append(f"Officina (traduzioni): {str(e)[:100]}")
            resto.extend(da_tradurre[i:])
            break
        if len(tr) < 8 or tr.strip().lower() == v["t"].strip().lower():
            resto.append(v)
            continue
        v["it"], v["tr"] = tr, "telefono"
        fatti += 1
        for p in ric.trova(tr):
            if p not in v["paesi"]:
                v["paesi"].append(p)
    S["tradotti_oggi"] = (S.get("tradotti_oggi", 0) if S.get("giorno") == datetime.now().date().isoformat() else 0) + fatti
    S["giorno"], S["tradotti_tutti"] = datetime.now().date().isoformat(), S.get("tradotti_tutti", 0) + fatti
    _off_salva(S)
    officina_traduci.fatti = fatti
    return resto


# ----------------------------------------------------------------------------- quadro: scaletta e collegamenti (dalla 2.23)

# ----------------------------------------------------------------------------- scaricatore (dalla 2.28)
# Fino alla 2.27.1 il modello lo scaricava curl, lanciato a ogni giro: sul telefono Android lo chiudeva prima della fine
# e il download ripartiva a ogni giro. Dalla 2.28 lo scarica il cuore di PanGeo (la pagina «serve», sempre accesa), un
# pezzo alla volta, riprendendo da dove era rimasto; se il cuore è di una versione vecchia, resta curl come riserva.

def _scarico_scrivi(**campi):
    os.makedirs(OFF(), exist_ok=True)
    sc = leggi_json(OFF("scarico.json"), {}) or {}
    sc.update(campi, quando=datetime.now(timezone.utc).isoformat(), cuore=VERSIONE)
    scrivi_json(OFF("scarico.json"), sc)


def _scarico_fresco(minuti=10):
    """Lo stato del download scritto dal cuore, se è recente (altrimenti None)."""
    sc = leggi_json(OFF("scarico.json"), {}) or {}
    try:
        eta = (datetime.now(timezone.utc) - datetime.fromisoformat(sc.get("quando", ""))).total_seconds() / 60
    except ValueError:
        return None
    return sc if eta <= minuti else None


def spinta(cfg, tel=None):
    """Dalla 2.32: quanto si spinge il telefono. In carica e fresco («piena»): download in parallelo al massimo, giri più
    fitti, vettori dei significati con il numero di thread più veloce misurato e anche sulle notizie non ancora confermate.
    Fuori carica o al caldo: metà dei download e vettori solo dei fatti confermati, così la batteria dura e il cuore
    (raccolta e conferme) ha sempre la precedenza."""
    sp = cfg.get("spinta", {}) or {}
    if tel is None:
        tel = _tel_ultimo() or {}
    attiva = bool(sp.get("attiva", True))
    carica = bool(tel.get("in_carica"))
    fresco = (tel.get("temp") or 99) < sp.get("temp_max", 37)
    piena = attiva and carica and fresco
    par = int(sp.get("paralleli_carica", 8) if piena else sp.get("paralleli", 4)) if attiva else 1
    perche = ("in carica e fresco" if piena else "spinta spenta in config.json" if not attiva else
              "fuori carica: si risparmia la batteria" if not carica else "telefono caldo: si va piano")
    return {"piena": piena, "paralleli": max(1, min(par, 16)), "carica": carica, "fresco": fresco, "perche": perche,
            "ogni_minuti": int(sp.get("ogni_minuti_carica", 10)) if piena else None}


def _tel_ultimo():
    """Temperatura, batteria e carica scritte nel diario dall'ultimo giro (se è di meno di 40 minuti fa)."""
    d = (leggi_json(os.path.join(DATI, "diario.json"), []) or [{}])[-1]
    try:
        eta = (datetime.now(timezone.utc) - datetime.fromisoformat(d.get("iso", ""))).total_seconds() / 60
    except ValueError:
        return None
    t = d.get("tel") or []
    if eta > 40 or len(t) < 3:
        return None
    return {"temp": t[0], "batteria": t[1], "in_carica": t[2]}


def _scarico_ok(imp):
    tel = _tel_ultimo()
    if not tel:
        return False, "aspetto il prossimo giro per sapere carica e temperatura"
    if not tel.get("in_carica"):
        if not imp.get("scarica_senza_carica", True):
            return False, "il telefono non è in carica"
        if (tel.get("batteria") or 0) < imp.get("batteria_min_scarico", 30):
            return False, f"batteria al {tel.get('batteria')}% e fuori carica"
    if (tel.get("temp") or 99) >= imp.get("temp_max", 38):
        return False, f"il telefono è caldo ({tel.get('temp')} °C)"
    if not (_wifi() or imp.get("scarica_senza_wifi", False)):
        return False, "aspetto il Wi-Fi"
    return True, ""


def _blocco_scarico():
    """Un solo scaricatore alla volta (cuore o curl). Restituisce il file aperto e bloccato, oppure None."""
    import fcntl
    os.makedirs(OFF(), exist_ok=True)
    f = open(OFF("scarico.lock"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        f.close()
        return None


def scarica_modello(imp=None, max_secondi=None, modello=None):
    """Un tratto di download di un modello dell'officina (il traduttore o, dalla 2.29, quello dei significati).
    Restituisce i secondi da aspettare prima del prossimo tratto."""
    imp = imp if imp is not None else leggi_json(os.path.join(QUI, "config.json"), {}).get("officina", {})
    if not imp.get("attivo", True):
        return 900
    M_ = modello or OFFICINA_MODELLO
    mod, tot = OFF(M_.get("file", "modello.gguf")), M_["byte"]
    parte = mod + ".part"
    if os.path.exists(mod) and os.path.getsize(mod) == tot:
        return 1800
    blocco = _blocco_scarico()
    if not blocco:
        return 120  # sta scaricando qualcun altro
    try:
        S = _off_stato()
        if modello is None and S.get("pid_curl") and _vivo_pid(S["pid_curl"]):
            return 120  # c'è ancora il curl della versione di prima: si aspetta che finisca o che si chiuda
        ok, perche = _scarico_ok(imp)
        fatto = os.path.getsize(parte) if os.path.exists(parte) else 0
        if not ok:
            _scarico_scrivi(stato="in pausa: " + perche, mb=round(fatto / 1e6))
            return 300
        if fatto > tot:
            os.remove(parte)
            fatto = 0
        if fatto == tot:
            os.replace(parte, mod)
            _scarico_scrivi(stato="finito", mb=round(tot / 1e6), errore=None)
            return 60
        req = urllib.request.Request(M_["url"], headers={
            "User-Agent": "PanGeo/" + VERSIONE + " (archivio personale)", "Range": f"bytes={fatto}-"})
        inizio = time.time()
        controllo, letto = inizio + 300, 0
        _scarico_scrivi(stato="scarico", mb=round(fatto / 1e6), errore=None, modello=M_.get("nome"), tot=round(tot / 1e6))
        with urllib.request.urlopen(req, timeout=60) as r:
            modo = "ab"
            if fatto and getattr(r, "status", 200) != 206:  # il server non riprende da metà: si ricomincia
                fatto, modo = 0, "wb"
            with open(parte, modo) as f:
                ultimo = inizio
                while True:
                    pezzo = r.read(1 << 20)
                    if not pezzo:
                        break
                    f.write(pezzo)
                    letto += len(pezzo)
                    adesso_ = time.time()
                    if adesso_ - ultimo >= 30:
                        f.flush()
                        ultimo = adesso_
                        _scarico_scrivi(stato="scarico", mb=round((fatto + letto) / 1e6),
                                        vel=round(letto / 1e6 / max(adesso_ - inizio, 1), 2))
                    if adesso_ >= controllo:  # ogni 5 minuti: ancora in carica, al fresco e in Wi-Fi?
                        controllo = adesso_ + 300
                        ok, perche = _scarico_ok(imp)
                        if not ok:
                            _scarico_scrivi(stato="in pausa: " + perche, mb=round((fatto + letto) / 1e6))
                            return 300
                    if max_secondi and adesso_ - inizio > max_secondi:
                        return 1
        fatto_ = os.path.getsize(parte)
        if fatto_ == tot:
            os.replace(parte, mod)
            _scarico_scrivi(stato="finito", mb=round(tot / 1e6), errore=None)
            return 60
        _scarico_scrivi(stato="interrotto, riprendo", mb=round(fatto_ / 1e6))
        return 30
    except Exception as e:
        _scarico_scrivi(stato="errore, riprovo tra 5 minuti", errore=str(e)[:200])
        return 300
    finally:
        blocco.close()


def _scaricatore():
    """Thread del cuore: quando l'officina aspetta il modello, lo scarica (vedi scarica_modello)."""
    time.sleep(120)
    while True:
        pausa_ = 600
        try:
            if _su_termux() and shutil.which("llama-server"):
                pausa_ = scarica_modello()
                imp_ = leggi_json(os.path.join(QUI, "config.json"), {}).get("officina", {})
                if pausa_ == 1800 and imp_.get("significato", True):  # dalla 2.29: poi il modello dei significati
                    pausa_ = scarica_modello(imp_, modello=SIGNIFICATO_MODELLO)
        except Exception as e:
            print("Scaricatore:", e)
        time.sleep(max(pausa_, 1))


# ----------------------------------------------------------------------------- filtro che impara (dalla 2.28)
# La sala d'attesa manda al cervello i titoli delle testate locali: il cervello ne tiene circa 3 su 10 e scarta il resto
# (sport, spettacolo, cronaca). Ogni sua scelta diventa un esempio. Con gli esempi il telefono si costruisce da solo un
# classificatore gratuito (pezzi di tre lettere e parole, in tutte le lingue e gli alfabeti, più il nome della testata) e:
#  - mette in testa alla coda i titoli che con più probabilità interessano;
#  - scarta da solo SOLO i titoli che il classificatore sa inutili con un errore misurato sotto la soglia (1%);
#  - ne manda comunque 1 su 20 al cervello come controllo: se il controllo dà più del 3% di errori, si spegne.

FILTRO_FILE, ESEMPI_FILE = (lambda: OFF("filtro.json")), (lambda: OFF("esempi.jsonl"))


def _filtro_tratti(testo, fonte=""):
    import unicodedata
    t = " " + " ".join(unicodedata.normalize("NFKC", str(testo or "")).lower().replace("’", "'").split()) + " "
    g = {t[i:i + 3] for i in range(len(t) - 2)}
    g.update("w:" + w for w in re.findall(r"\w+", t) if len(w) > 2)
    if fonte:
        g.add("f:" + famiglia_fonte(fonte))
    return g


def _chiave_esempio(testo):
    return int(hashlib.md5((testo or "").encode("utf-8")).hexdigest()[:8], 16)


def filtro_esempio(testo, tenuto, fonte="", controllo=False):
    """Scrive una scelta del cervello (tenuto o scartato) tra gli esempi del filtro."""
    if not testo:
        return
    os.makedirs(OFF(), exist_ok=True)
    with open(ESEMPI_FILE(), "a", encoding="utf-8") as f:
        f.write(json.dumps([testo[:300], 1 if tenuto else 0, fonte or ""], ensure_ascii=False) + "\n")
    if controllo:
        F = leggi_json(FILTRO_FILE(), {}) or {}
        c = F.setdefault("controlli", [0, 0])
        c[0 if not tenuto else 1] += 1  # [giusti, sbagliati]: un titolo da scartare che il cervello ha tenuto è un errore
        scrivi_json(FILTRO_FILE(), F)


def _filtro_esempi(massimo=25000):
    righe = []
    try:
        with open(ESEMPI_FILE(), encoding="utf-8") as f:
            for r in f:
                try:
                    x = json.loads(r)
                    if isinstance(x, list) and len(x) >= 2:
                        righe.append(x)
                except ValueError:
                    pass
    except OSError:
        return []
    if len(righe) > massimo * 1.2:  # il file non cresce senza fine: restano gli esempi più recenti
        righe = righe[-massimo:]
        with open(ESEMPI_FILE(), "w", encoding="utf-8") as f:
            f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in righe)
    visti, unici = set(), []
    for x in reversed(righe[-massimo:]):  # lo stesso titolo una volta sola (vale la scelta più recente)
        if x[0] not in visti:
            visti.add(x[0])
            unici.append(x)
    return unici


def _filtro_impara(esempi):
    conti, docs = {}, [0, 0]
    for testo, lab, *resto in esempi:
        docs[lab] += 1
        for g in _filtro_tratti(testo, resto[0] if resto else ""):
            c = conti.get(g)
            if c is None:
                conti[g] = c = [0, 0]
            c[lab] += 1
    return {"conti": conti, "docs": docs}


def _filtro_punteggio(M, testo, fonte=""):
    """Logaritmo di quanto è più probabile «interessa» che «da scartare» (Bayes ingenuo, con lisciatura)."""
    d0, d1 = M["docs"]
    if not d0 or not d1:
        return 0.0
    s = math.log(d1 / d0)
    conti = M["conti"]
    for g in _filtro_tratti(testo, fonte):
        c = conti.get(g)
        if c:
            s += math.log((c[1] + 0.5) / (d1 + 1)) - math.log((c[0] + 0.5) / (d0 + 1))
    return s


def filtro_addestra(imp=None, forza=False):
    """Impara dagli esempi e misura sugli esempi messi da parte (1 su 5) la soglia per scartare da solo."""
    imp = imp if imp is not None else leggi_json(os.path.join(QUI, "config.json"), {}).get("cervello", {}).get("filtro", {})
    F = leggi_json(FILTRO_FILE(), {}) or {}
    esempi = _filtro_esempi(imp.get("esempi_max", 25000))
    oggi_ = datetime.now().date().isoformat()
    if not forza and F.get("addestrato") == oggi_ and len(esempi) < F.get("esempi", 0) * 1.2:
        return F
    prova = [x for x in esempi if _chiave_esempio(x[0]) % 5 == 0]
    scuola = [x for x in esempi if _chiave_esempio(x[0]) % 5 != 0]
    pos = sum(1 for x in esempi if x[1])
    F.update(addestrato=oggi_, esempi=len(esempi), tenuti=pos, scartati=len(esempi) - pos, soglia=None, copre=0,
             errore=None, prova=len(prova), controlli=[0, 0], attivo=False)
    if pos < imp.get("min_per_tipo", 200) or len(esempi) - pos < imp.get("min_per_tipo", 200):
        F["perche"] = f"pochi esempi ({pos} tenuti, {len(esempi) - pos} scartati): imparo ancora"
        scrivi_json(FILTRO_FILE(), F)
        return F
    M = _filtro_impara(scuola)
    punti = sorted((_filtro_punteggio(M, x[0], x[2] if len(x) > 2 else ""), x[1]) for x in prova)
    errore_max, min_scarti = imp.get("errore_max", 0.01), imp.get("min_prova", 100)
    neg_tot = sum(1 for _, l in punti if not l) or 1
    soglia, presi, sbagliati, finestra = None, 0, 0, []
    largo = max(int(imp.get("finestra", 50)), 10)
    for i, (sc, lab) in enumerate(punti):  # dal più «inutile» in su, finché l'errore resta sotto la soglia
        presi += 1
        sbagliati += lab
        finestra = (finestra + [lab])[-largo:]
        # si taglia solo dopo un titolo davvero da scartare, con l'errore sotto la soglia sia in tutto sia negli ultimi
        # titoli presi (così il confine non entra tra i titoli che interessano)
        if (not lab and presi >= min_scarti and sbagliati / presi <= errore_max
                and sum(finestra) <= max(1, int(largo * errore_max * 2))):
            soglia = sc
            F.update(copre=round((presi - sbagliati) / neg_tot, 3), errore=round(sbagliati / presi, 4))
        elif presi >= min_scarti and (sbagliati / presi > errore_max * 2 or sum(finestra) > largo * errore_max * 4):
            break
    F["soglia"] = soglia
    F["attivo"] = soglia is not None
    F["perche"] = "" if soglia is not None else f"sugli esempi messi da parte non scarta abbastanza titoli con meno dell'{round(errore_max * 100)}% di errori"
    os.makedirs(OFF(), exist_ok=True)
    M_tutto = _filtro_impara(esempi)  # per lavorare usa tutti gli esempi; la soglia viene dalla prova
    scrivi_json(OFF("filtro_modello.json"), {"docs": M_tutto["docs"],
                                             "conti": {g: c for g, c in M_tutto["conti"].items() if c[0] + c[1] >= 2}})
    scrivi_json(FILTRO_FILE(), F)
    return F


def filtro_attesa(in_coda, cfg, errori):
    """Ordina la coda della sala d'attesa (prima i titoli che interessano) e toglie quelli sicuramente inutili.
    in_coda: lista di (chiave, voce). Restituisce (coda, scartati_dal_filtro)."""
    imp = cfg.get("cervello", {}).get("filtro", {})
    if not imp.get("attivo", True) or not in_coda:
        return in_coda, 0
    try:
        F = filtro_addestra(imp)
        M = leggi_json(OFF("filtro_modello.json"), None)
    except Exception as e:
        errori.append(f"Filtro della sala d'attesa: {str(e)[:100]}")
        return in_coda, 0
    if not M or not M.get("docs") or not all(M["docs"]):
        return in_coda, 0
    c_ = F.get("controlli") or [0, 0]
    spento = c_[0] + c_[1] >= 30 and c_[1] / (c_[0] + c_[1]) > imp.get("errore_controlli", 0.03)
    if spento and F.get("attivo"):
        F["attivo"], F["perche"] = False, f"i controlli hanno dato {c_[1]} errori su {c_[0] + c_[1]}: spento fino a domani"
        scrivi_json(FILTRO_FILE(), F)
    soglia = F.get("soglia") if F.get("attivo") and imp.get("scarta", True) else None
    ogni_ = max(int(imp.get("controllo_ogni", 20)), 2)
    tenuti, scartati = [], 0
    for k, v in in_coda:
        sc = _filtro_punteggio(M, v.get("t", ""), v.get("fonte", ""))
        v["fp"] = round(sc, 2)
        if soglia is not None and sc <= soglia:
            if _chiave_esempio(k) % ogni_ == 0:
                v["ctrl"] = True  # controllo: lo giudica comunque il cervello
            else:
                v["no"], v["filtro"] = True, True
                scartati += 1
                continue
        tenuti.append((k, v))
    tenuti.sort(key=lambda kv: (-kv[1].get("fp", 0), kv[1].get("data_iso") or ""))  # prima quelli che interessano
    F = leggi_json(FILTRO_FILE(), {}) or {}
    oggi_ = datetime.now().date().isoformat()
    if F.get("giorno") != oggi_:
        F["giorno"], F["scartati_oggi"] = oggi_, 0
    F["scartati_oggi"] = F.get("scartati_oggi", 0) + scartati
    F["scartati_tutti"] = F.get("scartati_tutti", 0) + scartati
    scrivi_json(FILTRO_FILE(), F)
    return tenuti, scartati


def filtro_primi_esempi(archivio):
    """La prima volta: gli esempi vengono dalle scelte già fatte dal cervello e ancora nella sala d'attesa."""
    if os.path.exists(ESEMPI_FILE()):
        return 0
    n_ = 0
    att_, notizie_ = archivio.get("attesa", {}), archivio.get("notizie", {})
    os.makedirs(OFF(), exist_ok=True)
    with open(ESEMPI_FILE(), "a", encoding="utf-8") as f:
        for k, v in att_.items():
            if not v.get("no") or v.get("filtro"):
                continue
            if v.get("t"):
                f.write(json.dumps([v["t"][:300], 0, v.get("fonte", "")], ensure_ascii=False) + "\n")
                n_ += 1
            elif k in notizie_ and notizie_[k].get("t"):
                f.write(json.dumps([notizie_[k]["t"][:300], 1, notizie_[k].get("fonte", "")], ensure_ascii=False) + "\n")
                n_ += 1
    return n_


# ----------------------------------------------------------------------------- 2.29: andamento, fatti in schede, avvisi,
# indice istantaneo e ricerca per significato. Tutto gratis, sul telefono, anche senza rete.

# 1. Fatti in schede: da ogni notizia confermata il telefono tira fuori tipo, Stati, numeri e data con regole fisse
# (sul testo italiano). Nessun cervello: è gratis, veloce e sempre uguale, quindi i conteggi si possono confrontare.
SCHEDE_TIPI = (  # (tipo, nome, regola): conta il primo che corrisponde, in quest'ordine
    ("tregua", "Tregue e negoziati di pace", r"tregua|cessate il fuoco|armistizi|accordo di pace|negoziati di pace|colloqui di pace"),
    ("disastro", "Disastri ed emergenze", r"terremoto|alluvion|uragan|tifone|incendi|frana|eruzion|epidemi|siccità"),
    ("terrorismo", "Terrorismo e attentati", r"terroris|attentat|kamikaze|jihadist|ostagg"),
    ("attacco", "Attacchi e bombardamenti", r"attacc|bombard|raid|missil[ei] .{0,40}(lanciat|cadut|colpit|abbattut|intercettat)|"
                                            r"droni? .{0,30}(colpit|abbattut|intercettat|lanciat)|esplosion|razzi|offensiv|"
                                            r"colpisc|colpito|colpita|uccis|morti|vittime"),
    ("scontri", "Combattimenti e scontri armati", r"combattiment|scontri armati|battaglia|ribelli|milizi|insorti|guerriglier|avanzat"),
    ("cyber", "Attacchi informatici", r"informatic|hacker|cyber|ransomware"),
    ("nucleare", "Nucleare e missili strategici", r"nuclear|atomic|uranio|test missilistic|missile balistic|icbm|ipersonic"),
    ("esercitazione", "Esercitazioni militari", r"esercitazion|manovre|addestrament|wargame"),
    ("acquisto", "Acquisti, appalti e forniture di armi", r"acquist|compra|commess|appalt|contratto|fornitur|consegn|ordin[ea] |vende|vendita"),
    ("accordo", "Accordi, trattati e alleanze", r"accordo|intesa|firma|memorandum|patto|trattat|partenariat|alleanza|cooperazione"),
    ("sanzioni", "Sanzioni e dazi", r"sanzion|dazi|embargo|tariff"),
    ("proteste", "Proteste e scioperi", r"protest|manifestan|manifestazion|sciopero|rivolt"),
    ("politica", "Governi, elezioni e nomine", r"elezion|voto|governo|dimission|nominat|nomina|premier|parlamento|colpo di stato|golpe|"
                                              r"presidente|ministro"),
    ("diplomazia", "Diplomazia e vertici", r"ambasciat|vertice|incontr|colloqui|visita|negoziat|diplomat"),
)
_RX_TIPI = None
_NUMERO = r"(\d{1,3}(?:[.\s]\d{3})+|\d+(?:,\d+)?)"
_RX_NUMERI = (
    ("morti", re.compile(_NUMERO + r"\s+(?:morti|vittime|uccis[ie]|persone uccise|civili uccisi|soldati uccisi)")),
    ("feriti", re.compile(_NUMERO + r"\s+feriti")),
    ("droni", re.compile(_NUMERO + r"\s+droni")),
    ("missili", re.compile(_NUMERO + r"\s+(?:missili|razzi)")),
    ("valore", re.compile(_NUMERO + r"\s*(miliardi|mld|milioni|mln)\s*(?:di\s+)?(euro|dollari|€|\$|sterline)")),
)


def _numero(s):
    s = s.replace(" ", "").replace(".", "") if re.search(r"\d[.\s]\d{3}", s) else s
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def scheda_di(v):
    """La scheda di un fatto: tipo, Stati, numeri (morti, feriti, droni, missili, valore in milioni) e data."""
    global _RX_TIPI
    if _RX_TIPI is None:
        _RX_TIPI = [(t, re.compile(r)) for t, _, r in SCHEDE_TIPI]
    testo = (v.get("it") or v.get("t") or "")
    basso = testo.lower()
    tipo = next((t for t, rx in _RX_TIPI if rx.search(basso)), "altro")
    num = {}
    for nome, rx in _RX_NUMERI:
        m = rx.search(basso)
        if not m:
            continue
        n = _numero(m.group(1))
        if n is None:
            continue
        if nome == "valore":
            n = n * (1000 if m.group(2) in ("miliardi", "mld") else 1)
            num["valore"] = [round(n, 1), {"euro": "€", "€": "€", "dollari": "$", "$": "$"}.get(m.group(3), m.group(3))]
        else:
            num[nome] = int(n)
    return {"d": (v.get("data_iso") or "")[:10], "tipo": tipo, "p": list(v.get("paesi") or [])[:6], "num": num,
            "t": testo[:220], "u": v.get("u", ""), "f": v.get("fonte", ""), "nf": v.get("nf") or 1}


def schede_fatti(archivio, adesso, cfg):
    """Mette in schede le notizie confermate nuove. dati/schede.json: {chiave: scheda}, per un anno (al massimo 80.000)."""
    perc = os.path.join(DATI, "schede.json")
    S = leggi_json(perc, {}) or {}
    nuove = 0
    for k, v in archivio.get("notizie", {}).items():
        if v.get("conf") and k not in S and v.get("paesi"):
            S[k] = scheda_di(v)
            nuove += 1
    limite = (adesso - timedelta(days=cfg.get("schede", {}).get("giorni", 365))).date().isoformat()
    S = {k: s for k, s in S.items() if s.get("d", "") >= limite}
    if len(S) > 80000:
        S = dict(sorted(S.items(), key=lambda kv: kv[1].get("d", ""))[-80000:])
    if nuove:
        scrivi_json(perc, S)
    return S, nuove


def scrivi_schede_web(S, adesso):
    """schede.js per la pagina: conteggi per Stato e tipo (30 giorni e un anno), per mese, e le ultime schede con numeri."""
    trenta = (adesso - timedelta(days=30)).date().isoformat()
    conta, mesi = {}, {}
    for s in S.values():
        for p in s.get("p") or []:
            c = conta.setdefault(p, {}).setdefault(s["tipo"], [0, 0])
            c[1] += 1
            if s.get("d", "") >= trenta:
                c[0] += 1
            m = mesi.setdefault(p, {}).setdefault(s.get("d", "")[:7], {})
            m[s["tipo"]] = m.get(s["tipo"], 0) + 1
    gravi = sorted((s for s in S.values() if s.get("num")), key=lambda s: s.get("d", ""), reverse=True)[:400]
    _scrivi_se_cambia(os.path.join(WEB, "schede.js"), "window.SCHEDE_FATTI=" + json.dumps(
        {"agg": adesso.astimezone().strftime("%d/%m/%Y %H:%M"), "tipi": [[t, n] for t, n, _ in SCHEDE_TIPI] + [["altro", "Altro"]],
         "conta": conta, "mesi": mesi, "ultime": gravi, "totale": len(S)}, ensure_ascii=False, separators=(",", ":")) + ";")


# 2. Andamento: per ogni Stato e ogni giorno quante notizie, quante confermate, quanti fatti con morti o feriti,
# quanto calore dal satellite e quanti aerei in volo (il massimo del giorno). dati/andamento.json, per un anno.
def andamento(archivio, adesso, S_schede):
    perc = os.path.join(DATI, "andamento.json")
    A = leggi_json(perc, {}) or {}
    G = A.setdefault("giorni", {})  # {data: {Stato: [notizie, confermate, gravi, calore, cielo]}}
    conta = {}
    for v in archivio.get("notizie", {}).values():
        d = (v.get("data_iso") or "")[:10]
        if not d:
            continue
        for p in v.get("paesi") or []:
            c = conta.setdefault(d, {}).setdefault(p, [0, 0, 0, None, None])
            c[0] += 1
            c[1] += 1 if v.get("conf") else 0
    for s in S_schede.values():
        num_ = s.get("num") or {}
        if num_.get("morti") or num_.get("feriti"):
            for p in s.get("p") or []:
                c = conta.setdefault(s.get("d", ""), {}).setdefault(p, [0, 0, 0, None, None])
                c[2] += 1
    for d, stati in conta.items():
        g = G.setdefault(d, {})
        for p, c in stati.items():
            vecchio = g.get(p) or [0, 0, 0, None, None]
            # l'archivio tiene 7 giorni e poi li toglie: per i giorni vecchi vale il massimo visto
            g[p] = [max(vecchio[0], c[0]), max(vecchio[1], c[1]), max(vecchio[2], c[2]), vecchio[3], vecchio[4]]
    zone_ = (leggi_json(os.path.join(DATI, "calore_zone.json"), {}) or {}).get("giorni", {})
    for d, z in zone_.items():
        for p, val in (z.get("s") or {}).items():
            r = G.setdefault(d, {}).setdefault(p, [0, 0, 0, None, None])
            r[3] = val[0] if isinstance(val, list) and val else r[3]
    for p, serie in (leggi_json(os.path.join(DATI, "cielo_storico.json"), {}) or {}).items():
        for x in serie or []:
            if isinstance(x, list) and len(x) > 1 and isinstance(x[1], (int, float)):
                d = str(x[0])[:10]
                r = G.setdefault(d, {}).setdefault(p, [0, 0, 0, None, None])
                r[4] = max(r[4] or 0, x[1])
    limite = (adesso - timedelta(days=366)).date().isoformat()
    A["giorni"] = {d: g for d, g in G.items() if d >= limite}
    A["agg"] = adesso.isoformat()
    scrivi_json(perc, A)
    return A


def scrivi_andamento_web(A, adesso, giorni=120):
    date_ = [(adesso - timedelta(days=i)).date().isoformat() for i in range(giorni - 1, -1, -1)]
    G = A.get("giorni", {})
    stati = sorted({p for d in date_ for p in (G.get(d) or {})})
    serie = {}
    for p in stati:
        righe = [[(G.get(d) or {}).get(p, [0, 0, 0, None, None])[i] for d in date_] for i in range(5)]
        if any(any(x for x in r if x) for r in righe):
            serie[p] = righe
    _scrivi_se_cambia(os.path.join(WEB, "andamento.js"), "window.ANDAMENTO=" + json.dumps(
        {"agg": adesso.astimezone().strftime("%d/%m/%Y %H:%M"), "date": date_, "serie": serie,
         "voci": ["notizie", "confermate", "fatti con morti o feriti", "fonti di calore", "aerei in volo"]},
        ensure_ascii=False, separators=(",", ":")) + ";")


# 3. Avvisi: quando uno Stato si accende (molte più notizie confermate del solito, fatti con molti morti, cielo che si
# svuota, calore in forte aumento). Vanno in cima alla pagina, come notifica sul telefono e, se Savo lo vuole, sul suo
# telefono personale con l'app gratuita ntfy (python castello.py chiave ntfy_canale) o con il suo bot Telegram.
# Dalla 2.31 avvisano anche altri fatti gravi, non solo i morti: ogni regola vale per i fatti confermati di oggi e di ieri,
# con almeno «fonti» testate diverse; un avviso solo per tipo, Stato e giorno (il racconto con più fonti).
AVVISI_REGOLE = (
    ("guerra", "Guerra, legge marziale o mobilitazione", 2, 2,
     r"dichiara\w* (?:lo stato di )?guerra|legge marziale|mobilitazione generale|stato di guerra"),
    ("golpe", "Colpo di Stato", 2, 2, r"colpo di stato|golpe|giunta militare"),
    ("truppe", "Movimenti di truppe", 3, 1,
     r"(?:truppe|soldati|carri armati|mezzi corazzati|blindati|navi da guerra|portaerei|sottomarin\w*|caccia|bombardieri)\b.{0,60}"
     r"(?:schierat|ammassat|al confine|dispiegat|inviat|rinforz|mobilitat|in movimento|si avvicin|entrat|attravers)|"
     r"(?:schieramento|ammassamento|dispiegamento|movimenti|concentramento) di (?:truppe|forze|mezzi)|truppe al confine"),
    ("intelligence", "Spionaggio e servizi segreti", 3, 1,
     r"\bspi[ae]\b|spionaggio|servizi segreti|agenti segreti|sabotaggi|diplomatici espulsi|(?:espuls|espell)\w* .{0,30}(?:diplomatic|ambasciator)"),
    ("esplosioni", "Esplosioni e incendi gravi", 3, 1,
     r"(?:esplosion\w*|incendi\w*|in fiamme).{0,50}(?:deposito|arsenale|munizioni|raffineria|base|porto|centrale|fabbrica|impianto)|"
     r"deposito di munizioni"),
    ("spazio aereo", "Spazio aereo chiuso", 3, 1, r"spazio aereo .{0,25}chius|chiude\w* lo spazio aereo|no-fly|voli sospesi"),
    ("terrorismo", "Attentati", 3, 2, r"attentat|kamikaze|attacco terroristico"),
    ("missili", "Test nucleari e missili strategici", 3, 2,
     r"test nucleare|esperimento nucleare|lanci\w* .{0,30}missil\w* balistic|missile balistico intercontinentale|\bicbm\b"),
    ("emergenza", "Stato di emergenza e coprifuoco", 3, 1, r"stato di emergenza|coprifuoco"),
)
_RX_AVVISI = None
_RIC_AVVISI = None
# dalla 2.32.1: niente avviso per processi, sentenze, anniversari o frasi riferite (un «colpo di Stato» detto da qualcuno)
AVVISI_FUORI = {
    "guerra": r"process|sentenz|condann|colpevol|impeachment|tribunal|giudic|corte suprema|anniversario|ex premier|ex president",
    "golpe": r"process|sentenz|condann|colpevol|tribunal|anniversario|propaganda|smentisc|afferma|accus\w* di|teoria|tentato golpe del \d",
    "terrorismo": r"process|sentenz|condann|colpevol|tribunal|anniversario|ergastolo",
    "missili": r"anniversario|museo",
    "intelligence": r"in giudizio|azionisti|process[oi]\b|sentenz|condann|anniversario",
    "morti": r"condann|sentenz|process[oi]\b|anniversario|commemora",
}
_RX_FUORI = {t: re.compile(rx) for t, rx in AVVISI_FUORI.items()}
# per gli avvisi lo Stato si riconosce anche da aggettivi e capitali («carri armati israeliani», «attacco a Riad»)
AVVISI_ALIAS = {
    "Israele": r"israelian\w*|gerusalemme|tel aviv", "Palestina": r"gaza|cisgiordania|palestines\w*|hamas",
    "Russia": r"\brus(?:so|sa|si|se)\b|mosca|cremlino", "Ucraina": r"ucrain\w*|kiev|kyiv|kharkiv|odessa",
    "Germania": r"tedesc\w*|berlino", "Francia": r"frances[ei]\b|parigi|eliseo", "Regno Unito": r"britannic\w*|londra",
    "USA": r"statunitens\w*|american[oaie]\b|washington|casa bianca|pentagono", "Cina": r"cines[ei]\b|pechino",
    "Iran": r"iranian\w*|teheran", "Turchia": r"turc[oaih]\b|ankara", "Arabia Saudita": r"saudit\w*|riad\b|riyadh",
    "Emirati Arabi": r"emiratin\w*|emirati arabi|abu dhabi|dubai", "Siria": r"sirian\w*|damasco", "Libano": r"libanes\w*|beirut|hezbollah",
    "Iraq": r"irachen\w*|baghdad", "Yemen": r"yemenit\w*|houthi|sanaa", "Egitto": r"egizian\w*|il cairo",
    "Libia": r"libic[oaih]\b|tripoli", "Sudan": r"sudanes\w*|khartoum", "Somalia": r"somal[oaie]\b|mogadiscio",
    "Haiti": r"haitian\w*|port-au-prince", "Venezuela": r"venezuelan\w*|caracas", "Afghanistan": r"afghan\w*|kabul|talebani",
    "Pakistan": r"pakistan\w*|islamabad", "India": r"\bindian[oaie]\b|nuova delhi", "Corea del Nord": r"nordcorean\w*|pyongyang",
    "Corea del Sud": r"sudcorean\w*|seul", "Giappone": r"giappones\w*|tokyo", "Taiwan": r"taiwanes\w*|taipei",
    "Polonia": r"polacc\w*|varsavia", "Bielorussia": r"bielorus\w*|minsk", "Mali": r"malian\w*|bamako",
}
_RX_AVVISI_ALIAS = [(st, re.compile(r"(?<![\w])(?:" + rx + r")", re.I)) for st, rx in AVVISI_ALIAS.items()]


def _avvisi_prepara():
    global _RX_AVVISI, _RIC_AVVISI
    if _RX_AVVISI is None:
        _RX_AVVISI = [(t, nome, fonti, liv, re.compile(rx)) for t, nome, fonti, liv, rx in AVVISI_REGOLE]
    if _RIC_AVVISI is None:
        try:
            _RIC_AVVISI = Riconoscitore(leggi_json(os.path.join(QUI, "paesi.json"), {}) or {})
        except Exception:
            _RIC_AVVISI = False


def _titolo_avviso(a):
    m_ = re.match(r"^(.*?): (.*?)(?: \(\d+ fonti\))?$", a.get("testo", ""))
    return m_.group(2) if m_ else a.get("testo", "")


def avvisi_ripulisci(elenco):
    """Dalla 2.33: rilegge con le regole nuove gli avvisi già scritti. Lo stesso fatto raccontato da più titoli resta un
    solo avviso (con «simili»: quanti titoli in più lo raccontano), lo Stato diventa quello nominato nel titolo, e gli
    avvisi nati da processi, sentenze o frasi riferite (o senza nessuno Stato nominato) si tolgono."""
    _avvisi_prepara()
    tenuti, per_giorno = [], {}
    for a in elenco:
        if a.get("tipo") != "fatto":
            tenuti.append(a)
            continue
        m_ = re.match(r"^(.*?): (.*?)(?: \((\d+) fonti\))?$", a.get("testo", ""))
        titolo = m_.group(2) if m_ else a.get("testo", "")
        sotto = a.get("sotto") or ""
        if sotto in _RX_FUORI and _RX_FUORI[sotto].search(titolo.lower()):
            continue
        nominati = _stati_nominati(titolo)
        if a.get("stato") not in nominati:
            if not nominati:
                continue
            a = dict(a, stato=nominati[0], testo=nominati[0] + ": " + titolo + (f" ({m_.group(3)} fonti)" if m_ and m_.group(3) else ""),
                     id=f"fatto:{sotto}:{nominati[0]}:" + (a.get("id", "").rsplit(":", 1)[-1] or (a.get("quando") or "")[:10]))
        parole_ = _parole_avviso(titolo)
        giorno_ = (a.get("quando") or "")[:10]
        # lo stesso fatto: parole quasi uguali, oppure stesso tipo di avviso per lo stesso Stato nello stesso giorno
        doppio = next((x for x in per_giorno.get(giorno_, []) if _stesso_fatto(parole_, x[0])
                       or (x[1].get("sotto") == sotto and x[1].get("stato") == a.get("stato"))), None)
        if doppio:
            doppio[1]["simili"] = doppio[1].get("simili", 0) + 1
            continue
        per_giorno.setdefault(giorno_, []).append((parole_, a))
        tenuti.append(a)
    return tenuti


def _stati_nominati(testo):
    trovati = _RIC_AVVISI.trova(testo) if _RIC_AVVISI else []
    for st, rx in _RX_AVVISI_ALIAS:
        if st not in trovati and rx.search(testo):
            trovati.append(st)
    return trovati


_PAROLE_VUOTE = set("dopo contro mentre sono della delle dello degli dell nella nelle negli sulla sulle sugli alla alle agli "
                    "anche come perché ancora oltre circa secondo verso senza fonti fonte dice dicono".split())


def _parole_avviso(testo):
    return {w for w in re.findall(r"[a-zà-ù0-9]{4,}", testo.lower()) if w not in _PAROLE_VUOTE}


def _stesso_fatto(a, b):
    """Due titoli raccontano lo stesso fatto se almeno il 60% delle parole del più corto sta anche nell'altro."""
    return bool(a and b) and len(a & b) / min(len(a), len(b)) >= 0.6


def _avvisi_fatti(S_schede, oggi, ieri, imp):
    """Avvisi dai fatti in schede: morti (dal numero nel titolo) e le regole di AVVISI_REGOLE. Dalla 2.32.1: lo Stato
    dell'avviso deve essere nominato nel titolo (non basta il Paese della testata), un fatto dà un solo avviso anche se lo
    raccontano titoli diversi, e processi, sentenze e frasi riferite non fanno scattare guerra, golpe o attentati."""
    _avvisi_prepara()
    fuori, visti, testi, fatti_ = [], set(), set(), []
    for k, s in sorted(S_schede.items(), key=lambda kv: -(kv[1].get("nf") or 1)):
        if s.get("d") not in (oggi, ieri):
            continue
        testo = s.get("t", "")
        nominati = _stati_nominati(testo)
        # lo Stato dell'avviso: il primo della notizia che il titolo nomina davvero; se nessuno, il primo nominato nel titolo;
        # se il titolo non nomina nessuno Stato, niente avviso (il Paese della testata non basta)
        p = next((x for x in (s.get("p") or []) if x in nominati), None) or (nominati[0] if nominati else None)
        if not p:
            continue
        firma = re.sub(r"[^a-zà-ù0-9]+", " ", testo.lower())[:60]
        if firma in testi:
            continue  # lo stesso titolo ripetuto da più testate
        parole_ = _parole_avviso(testo)
        if any(_stesso_fatto(parole_, x) for x in fatti_):
            continue  # lo stesso fatto raccontato con altre parole
        m_ = (s.get("num") or {}).get("morti") or 0
        scelta = None
        if m_ >= imp.get("morti_minimi", 10) and not _RX_FUORI["morti"].search(testo.lower()):
            scelta = ("morti", "Fatti con molti morti", 2 if m_ >= 50 else 1, f"{p}:{m_}")
        else:
            basso = testo.lower()
            for t, nome, fonti, liv, rx in _RX_AVVISI:
                if (s.get("nf") or 1) >= fonti and rx.search(basso) and not (t in _RX_FUORI and _RX_FUORI[t].search(basso)):
                    scelta = (t, nome, liv, p)
                    break
        if not scelta or (scelta[0], scelta[3], s.get("d")) in visti:
            continue
        visti.add((scelta[0], scelta[3], s.get("d")))
        testi.add(firma)
        fatti_.append(parole_)
        try:  # dalla 2.33: i precedenti storici (colpi di Stato, conflitti armati) dello stesso Stato
            prec_ = precedenti(p, scelta[0])
        except Exception:
            prec_ = ""
        fuori.append({"id": f"fatto:{scelta[0]}:{scelta[3]}:{s.get('d')}", "tipo": "fatto", "sotto": scelta[0], "nome": scelta[1],
                      "stato": p, "livello": scelta[2], "testo": f"{p}: {testo}" + (f" ({s.get('nf')} fonti)" if (s.get("nf") or 1) > 1 else ""),
                      "u": s.get("u", ""), "f": s.get("f", ""), **({"prec": prec_} if prec_ else {})})
    return fuori


def calcola_avvisi(A, S_schede, dati_cielo, dati_calore, adesso, cfg):
    imp = cfg.get("avvisi", {})
    oggi = adesso.date().isoformat()
    ieri = (adesso - timedelta(days=1)).date().isoformat()
    G = A.get("giorni", {})
    prima = [(adesso - timedelta(days=i)).date().isoformat() for i in range(2, 16)]
    # dalla 2.33.3 contano solo i giorni «pieni» (almeno metà delle notizie del giorno più ricco): i giorni ricostruiti
    # dall'archivio di 7 giorni hanno poche notizie e facevano credere che Russia o USA abbiano «di solito 0» notizie
    tot_ = {d: sum((v or [0])[0] for v in (G.get(d) or {}).values()) for d in prima}
    pieno_ = max(tot_.values(), default=0)
    pieni = [d for d in prima if pieno_ and tot_[d] >= 0.5 * pieno_]
    # e dalla 2.33.4 serve anche che lo Stato pesi più del doppio del solito sul totale delle confermate: se il programma
    # raccoglie di più (fonti nuove, giro più veloce) crescono tutti insieme e non è un picco
    conf_tot = {d: sum((v or [0, 0])[1] for v in (G.get(d) or {}).values()) for d in pieni + [oggi]}
    nuovi = []
    for p in sorted({p for d in (oggi, ieri) for p in (G.get(d) or {})}):
        c_oggi = max(((G.get(oggi) or {}).get(p) or [0, 0])[1], 0)
        storia = sorted(((G.get(d) or {}).get(p) or [0, 0])[1] for d in pieni)
        mediana = storia[len(storia) // 2] if storia else 0
        giorni_noti = len(pieni)
        quote_ = sorted(((G.get(d) or {}).get(p) or [0, 0])[1] / conf_tot[d] for d in pieni if conf_tot.get(d))
        quota_solita = quote_[len(quote_) // 2] if quote_ else 0
        quota_oggi = c_oggi / conf_tot[oggi] if conf_tot.get(oggi) else 0
        if giorni_noti >= imp.get("giorni_minimi", 5) and c_oggi >= max(imp.get("picco_minimo", 6), 3 * max(mediana, 1)) \
                and quota_oggi >= 2 * max(quota_solita, 0.002):
            # perché: i titoli confermati da più fonti dello Stato, oggi
            primi_ = sorted((x for x in S_schede.values() if x.get("d") == oggi and p in (x.get("p") or [])),
                            key=lambda x: -(x.get("nf") or 1))[:2]
            nuovi.append({"id": f"picco:{p}:{oggi}", "tipo": "picco", "stato": p, "livello": 2 if c_oggi >= 6 * max(mediana, 1) else 1,
                          "testo": f"{p}: {c_oggi} notizie confermate oggi, di solito {mediana} al giorno."
                                   + (" In primo piano: " + "; ".join(x.get("t", "")[:110] for x in primi_) + "." if primi_ else "")})
    nuovi += _avvisi_fatti(S_schede, oggi, ieri, imp)
    for p, v in ((dati_cielo or {}).get("paesi") or {}).items():
        # dalla 2.31 solo i cieli che si svuotano davvero (non i cali), dove di solito volano almeno 20 aerei
        if isinstance(v, list) and len(v) > 2 and v[2] == "vuoto" and (v[1] or 0) >= imp.get("cielo_minimo", 20):
            nuovi.append({"id": f"cielo:{p}:{oggi}", "tipo": "cielo", "stato": p, "livello": 1,
                          "testo": f"{p}: cielo {'vuoto' if v[2] == 'vuoto' else 'in forte calo'} ({v[0]} aerei in volo, di solito {v[1]}). "
                                   "Può essere uno spazio aereo chiuso, ma anche meteo o ricevitori spenti."})
    for p, v in ((dati_calore or {}).get("paesi") or {}).items():
        # dalla 2.31 solo un calore almeno 4 volte la media e almeno 100 fonti (gli incendi agricoli di stagione restano fuori)
        if isinstance(v, list) and len(v) > 2 and v[2] and (v[0] or 0) >= imp.get("calore_minimo", 100) \
                and (v[0] or 0) >= imp.get("calore_volte", 4) * max(v[1] or 0, 1):
            nuovi.append({"id": f"calore:{p}:{oggi}", "tipo": "calore", "stato": p, "livello": 1,
                          "testo": f"{p}: fonti di calore da satellite in forte aumento ({v[0]} in 24 ore, media {v[1]}). "
                                   "Possono essere incendi, industria o attacchi: da confermare con le notizie."})
    return nuovi


def avvisi(A, S_schede, dati_cielo, dati_calore, adesso, cfg, chiavi):
    """Aggiorna dati/avvisi.json (gli ultimi 80) e manda solo quelli nuovi. Restituisce [nuovi, attivi]."""
    perc = os.path.join(DATI, "avvisi.json")
    V = leggi_json(perc, {}) or {}
    elenco = V.setdefault("elenco", [])
    visti = {a["id"] for a in elenco}  # anche gli avvisi tolti dalla pulizia restano «visti»: non tornano
    if V.get("ripulito") != "2.33":  # una volta: gli avvisi scritti prima della 2.32.1 passano dalle regole nuove
        elenco = avvisi_ripulisci(elenco)
        V["ripulito"] = "2.33"
        visti |= {a["id"] for a in elenco}
    calcolati_ = calcola_avvisi(A, S_schede, dati_cielo, dati_calore, adesso, cfg)
    try:
        calcolati_ += avvisi_economia(cfg, adesso)  # dalla 2.30: monete e titoli di Stato
    except Exception:
        pass
    # dalla 2.33.5: avviso quando la spesa totale del cervello supera una soglia in euro (config › avvisi › spesa_eur)
    try:
        conto_s = leggi_json(os.path.join(DATI, "cervello.json"), {}) or {}
        tot_usd = conto_s.get("usd_totale", conto_s.get("usd_mese", 0)) or 0
        st_v = ((leggi_json(os.path.join(DATI, "economia.json"), {}) or {}).get("valute") or {}).get("storia") or {}
        eur_ = (st_v[max(st_v)] or {}).get("EUR") if st_v else None
        eur_ = eur_ or 0.92
        mesi_ = ", ".join(f"{m[5:]}/{m[:4]} {v:.2f} $" for m, v in sorted((conto_s.get("mesi") or {}).items()))
        soglie_ = [(x, x, "$") for x in cfg.get("avvisi", {}).get("spesa_usd", [])] + \
                  [(x / eur_, x, "€") for x in cfg.get("avvisi", {}).get("spesa_eur", [])]
        for soglia_usd, soglia_, mon_ in soglie_:
            if tot_usd >= soglia_usd:
                calcolati_.append({"id": f"spesa:{soglia_}{mon_}", "tipo": "spesa", "nome": "Spesa del cervello", "stato": "", "livello": 2,
                                   "testo": f"Spesa del cervello: superati {soglia_} {mon_} in totale ({tot_usd:.2f} $, circa {tot_usd * eur_:.2f} €). "
                                            + (f"Mese per mese: {mesi_}. " if mesi_ else f"Questo mese: {conto_s.get('usd_mese', 0):.2f} $. ")
                                            + f"Tetto del programma: {cfg.get('cervello', {}).get('max_usd_mese', 45)} $ al mese."})
    except Exception:
        pass
    nuovi = [dict(a, quando=adesso.isoformat()) for a in calcolati_ if a["id"] not in visti]
    # dalla 2.33: un fatto già avvisato nei 2 giorni prima non torna come avviso nuovo, anche se arriva con altre parole
    # (e lo stesso tipo di avviso per lo stesso Stato non torna prima di 24 ore: «uno per tipo, Stato e giorno»)
    due_ = (adesso - timedelta(days=2)).isoformat()
    un_g = (adesso - timedelta(hours=24)).isoformat()
    gia_ = [_parole_avviso(_titolo_avviso(a)) for a in elenco if a.get("tipo") == "fatto" and a.get("quando", "") >= due_]
    gia_ts = {(a.get("sotto"), a.get("stato")) for a in elenco if a.get("tipo") == "fatto" and a.get("quando", "") >= un_g}
    nuovi = [a for a in nuovi if a.get("tipo") != "fatto" or not (
        (a.get("sotto"), a.get("stato")) in gia_ts or any(_stesso_fatto(_parole_avviso(_titolo_avviso(a)), x) for x in gia_))]
    # dalla 2.32.1: al massimo «massimo_nuovi» avvisi nuovi per giro (prima i più gravi); gli altri tornano al giro dopo
    # se sono ancora del giorno
    nuovi.sort(key=lambda a: -(a.get("livello") or 1))
    nuovi = nuovi[:int(cfg.get("avvisi", {}).get("massimo_nuovi", 10))]
    elenco = (elenco + nuovi)[-300:]
    V.update(elenco=elenco, agg=adesso.isoformat())
    scrivi_json(perc, V)
    os.makedirs(WEB, exist_ok=True)
    scrivi_json(os.path.join(WEB, "avvisi.json"), V)
    imp = cfg.get("avvisi", {})
    da_mandare = [a for a in nuovi if a.get("livello", 1) >= imp.get("livello_notifica", 1)][:imp.get("massimo_per_giro", 5)]
    if da_mandare and imp.get("attivi", True):
        testo = "\n".join("• " + a["testo"][:200] for a in da_mandare)
        if cfg.get("notifiche", True) and shutil.which("termux-notification"):
            subprocess.run(["termux-notification", "--id", "pangeo-avvisi", "--title", f"PanGeo: {len(da_mandare)} avvisi",
                            "--content", testo[:900], "--action", "termux-open-url http://127.0.0.1:8080/#avvisi"],
                           check=False, timeout=30)
        if chiavi.get("ntfy_canale"):
            try:
                req = urllib.request.Request("https://ntfy.sh/" + urllib.parse.quote(chiavi["ntfy_canale"]), data=testo.encode("utf-8"),
                                             headers={"Title": f"PanGeo: {len(da_mandare)} avvisi", "Tags": "warning",
                                                      "Click": SITO_PUBBLICO + "/#avvisi"})
                urllib.request.urlopen(req, timeout=20).read()
            except Exception as e:
                print("  - avviso con ntfy non partito:", str(e)[:80])
        if chiavi.get("telegram_bot") and chiavi.get("telegram_chat") and imp.get("telegram", True):
            bot_telegram(chiavi, "PanGeo – avvisi\n" + testo)
    return [len(nuovi), len([a for a in elenco if a.get("quando", "") >= (adesso - timedelta(hours=24)).isoformat()])]


# 4. Indice istantaneo: tutte le notizie (anche quelle già nel magazzino), i fatti confermati e il lavoro a piano in un
# indice SQLite con ricerca a parole (FTS5). Cerca in tutto in pochi millisecondi, anche con decine di GB e senza rete.
def _indice_apri():
    import sqlite3
    os.makedirs(MAG(), exist_ok=True)
    db = sqlite3.connect(MAG("indice.sqlite"), timeout=30)
    db.execute("CREATE TABLE IF NOT EXISTS visti (k TEXT PRIMARY KEY)")
    db.execute("CREATE TABLE IF NOT EXISTS info (k TEXT PRIMARY KEY, v TEXT)")
    tab = db.execute("SELECT name FROM sqlite_master WHERE name='testi'").fetchone()
    if not tab:
        for motore in ("fts5", "fts4"):
            try:
                opz = "tokenize='unicode61 remove_diacritics 2'" if motore == "fts5" else "tokenize=unicode61"
                db.execute(f"CREATE VIRTUAL TABLE testi USING {motore}(testo, d, p, f, u, dove, c, {opz})")
                db.execute("INSERT OR REPLACE INTO info VALUES ('motore', ?)", (motore,))
                break
            except Exception:
                continue
    return db


def indice_aggiorna(archivio, adesso, cfg, secondi=60):
    """Mette nell'indice ciò che non c'è ancora. La prima volta anche tutti i giorni del magazzino (a pezzi, per giro)."""
    if not cfg.get("indice", {}).get("attivo", True):
        return None
    t0 = time.time()
    db = _indice_apri()
    if not db.execute("SELECT name FROM sqlite_master WHERE name='testi'").fetchone():
        return {"errore": "SQLite senza ricerca a parole"}
    nuovi = 0

    def metti(k, testo, d, p, f, u, dove, c):
        nonlocal nuovi
        if db.execute("SELECT 1 FROM visti WHERE k=?", (k,)).fetchone():
            return
        db.execute("INSERT INTO visti VALUES (?)", (k,))
        db.execute("INSERT INTO testi (testo, d, p, f, u, dove, c) VALUES (?,?,?,?,?,?,?)",
                   (testo, d, "|".join(p or []), f or "", u or "", dove, c))
        nuovi += 1
    for k, v in archivio.get("notizie", {}).items():
        metti("n:" + k, ((v.get("it") or "") + " · " + (v.get("t") or "")).strip(" ·"), (v.get("data_iso") or "")[:10],
              v.get("paesi"), v.get("fonte"), v.get("u"), "notizia", 1 if v.get("conf") else 0)
    P = (leggi_json(os.path.join(DATI, "piano.json"), {}) or {}).get("stati", {})
    for st_, s in P.items():
        for campo, chiave in (("accordi", "cosa"), ("appalti", "ogg"), ("intel", "cosa"), ("puzzle", "cosa")):
            for x in s.get(campo) or []:
                testo = " · ".join(str(x.get(c) or "") for c in (chiave, "con", "acq", "forn", "ente") if x.get(c))
                f = (x.get("f") or [["", ""]])[0]
                metti("p:" + hashlib.md5((st_ + campo + testo).encode()).hexdigest()[:16], testo, x.get("d", ""), [st_],
                      f[0] if f else "", f[1] if len(f) > 1 else "", "lavoro a piano: " + campo, 1)
    # il magazzino: un giorno alla volta, dal più recente, finché c'è tempo
    fatti_ = set(json.loads((db.execute("SELECT v FROM info WHERE k='giorni_mag'").fetchone() or ["[]"])[0]))
    for d in sorted((leggi_json(MAG("indice.json"), {}) or {}).get("giorni", {}), reverse=True):
        if d in fatti_ or d >= adesso.date().isoformat():
            continue
        if time.time() - t0 > secondi:
            break
        for r in _mag_leggi(MAG("notizie", d + ".jsonl.xz")):
            metti("n:" + str(r.get("k") or r.get("u") or r.get("t")), ((r.get("it") or "") + " · " + (r.get("t") or "")).strip(" ·"),
                  (r.get("d") or "")[:10], r.get("p"), r.get("f"), r.get("u"), "notizia (magazzino)", r.get("c", 0))
        fatti_.add(d)
        db.execute("INSERT OR REPLACE INTO info VALUES ('giorni_mag', ?)", (json.dumps(sorted(fatti_)),))
    db.commit()
    tot = db.execute("SELECT count(*) FROM visti").fetchone()[0]
    motore = (db.execute("SELECT v FROM info WHERE k='motore'").fetchone() or ["?"])[0]
    db.close()
    return {"nuovi": nuovi, "totale": tot, "motore": motore, "secondi": round(time.time() - t0, 1)}


def indice_cerca(q, stato=None, massimo=60):
    """Ricerca istantanea: tutte le parole (anche l'inizio di una parola con *), dalla più pertinente e più recente."""
    if not os.path.exists(MAG("indice.sqlite")):
        return None
    parole_q = [w for w in re.findall(r"[\w*]+", q or "", re.U) if len(w.strip("*")) > 1][:8]
    if not parole_q:
        return []
    db = _indice_apri()
    motore = (db.execute("SELECT v FROM info WHERE k='motore'").fetchone() or ["fts5"])[0]
    domanda = " ".join('"' + w.strip("*").replace('"', "") + '"' + ("*" if w.endswith("*") else "") for w in parole_q)
    ordine = "bm25(testi)" if motore == "fts5" else "d DESC"
    sql = f"SELECT testo, d, p, f, u, dove, c FROM testi WHERE testi MATCH ? {'AND p LIKE ?' if stato else ''} ORDER BY {ordine} LIMIT ?"
    arg = [domanda] + (["%" + stato + "%"] if stato else []) + [massimo * 3]
    try:
        righe = db.execute(sql, arg).fetchall()
    except Exception:
        db.close()
        return None
    db.close()
    fuori, visti = [], set()
    for testo, d, p, f, u, dove, c in righe:
        if (u or testo) in visti:
            continue
        visti.add(u or testo)
        it_ = testo.split(" · ")[0]
        fuori.append({"d": d, "t": it_, "f": f, "u": u, "p": [x for x in (p or "").split("|") if x], "dove": dove, "c": c})
    fuori.sort(key=lambda r: (str(r.get("d") or "")), reverse=True)
    return fuori[:massimo]


# 5. Ricerca per significato: un secondo modello piccolo (Qwen3 Embedding 0.6B, Apache 2.0) trasforma ogni fatto
# confermato in un vettore. Cerchi «carri armati alla Polonia» e trova anche la notizia in russo o in coreano che lo dice
# con altre parole. Gira sul telefono (porta 8092), anche senza rete; i vettori stanno nel magazzino (512 numeri a fatto).
SIGNIFICATO_MODELLO = {"nome": "Qwen3 Embedding 0.6B (Q8_0)", "licenza": "Apache 2.0", "byte": 639150592, "file": "significato.gguf",
                       "url": "https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/main/Qwen3-Embedding-0.6B-Q8_0.gguf"}
SIG_DIM = 512  # i primi 512 numeri del vettore: provato il 20/11, metà spazio e quasi la stessa precisione
SIG_ISTRUZIONE = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:"


def _sig_thread(imp, tel=None):
    """Dalla 2.32: quanti thread usa il modello dei significati. Fuori carica o al caldo: officina › thread (4). In carica e
    fresco: si provano a turno i numeri di spinta › prove_thread (4, 6, 8) misurando quanti vettori al secondo fanno, poi si
    usa il più veloce. Le misure valgono 7 giorni, poi si rifanno (il telefono cambia: aggiornamenti, caldo, batteria)."""
    base = int(imp.get("thread", 4))
    cfg_ = leggi_json(os.path.join(QUI, "config.json"), {}) or {}
    if not spinta(cfg_, tel)["piena"]:
        return base
    n_cpu = os.cpu_count() or 8
    prove = [int(t) for t in (cfg_.get("spinta", {}) or {}).get("prove_thread", [4, 6, 8]) if 1 <= int(t) <= n_cpu] or [base]
    mis = _off_stato().get("sig_velocita") or {}
    vecchie = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    for t in prove:
        m = mis.get(str(t)) or {}
        if m.get("n", 0) < 2 or m.get("quando", "") < vecchie:
            return t
    return max(prove, key=lambda t: mis[str(t)]["v"])


def _sig_misura(nuovi, secondi):
    """Vettori al secondo con il numero di thread acceso adesso (media delle ultime 5 misure)."""
    if nuovi < 32 or secondi < 20:
        return
    S = _off_stato()
    t = str(S.get("sig_thread") or "")
    if not t:
        return
    m = S.setdefault("sig_velocita", {}).setdefault(t, {})
    if m.get("quando", "") < (datetime.now(timezone.utc) - timedelta(days=7)).isoformat():
        m.clear()
    n = min(m.get("n", 0), 4)
    m["v"] = round((m.get("v", 0) * n + nuovi / secondi) / (n + 1), 3)
    m["n"], m["quando"] = n + 1, datetime.now(timezone.utc).isoformat()
    _off_salva(S)


def _sig_server(imp, accendi=True, tel=None):
    """Il server dei vettori: acceso se serve (in carica, o fuori carica con batteria buona), spento se no. Dalla 2.32 si
    riaccende da solo quando cambia il numero di thread (in carica ne usa di più)."""
    porta = imp.get("porta_significato", 8092)
    S = _off_stato()
    sano = False
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/health", timeout=3) as r:
            sano = r.status == 200
    except Exception:
        pass
    if sano and not accendi:
        return porta
    t_ = _sig_thread(imp, tel)
    if sano:
        if int(S.get("sig_thread") or imp.get("thread", 4)) == t_ or not (S.get("pid_sig") and _vivo_pid(S["pid_sig"]) and _e_llama(S["pid_sig"])):
            return porta  # stesso numero di thread (o un server che non abbiamo acceso noi: lo si lascia stare)
        _sig_ferma()
        for _ in range(10):
            time.sleep(1)
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{porta}/health", timeout=2)
            except Exception:
                break
        S = _off_stato()
    mod = OFF(SIGNIFICATO_MODELLO["file"])
    if not accendi or not shutil.which("llama-server") or not os.path.exists(mod) or os.path.getsize(mod) != SIGNIFICATO_MODELLO["byte"]:
        return None
    if not (S.get("pid_sig") and _vivo_pid(S["pid_sig"]) and _e_llama(S["pid_sig"])):
        log = open(OFF("significato.log"), "ab")
        p = subprocess.Popen(["llama-server", "-m", mod, "--embedding", "--pooling", "last", "--host", "127.0.0.1", "--port", str(porta),
                              "-c", "2048", "-ub", "2048", "-t", str(t_)], stdout=log, stderr=log,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        S["pid_sig"], S["sig_thread"] = p.pid, t_
        _off_salva(S)
    for _ in range(40):  # il modello piccolo si carica in pochi secondi
        time.sleep(1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{porta}/health", timeout=3) as r:
                if r.status == 200:
                    return porta
        except Exception:
            continue
    return None


def _sig_ferma():
    S = _off_stato()
    if S.get("pid_sig") and _vivo_pid(S["pid_sig"]) and _e_llama(S["pid_sig"]):
        try:
            os.kill(int(S["pid_sig"]), signal.SIGTERM)
        except OSError:
            pass
    S["pid_sig"] = None
    _off_salva(S)


def _sig_vettori(testi, porta):
    req = urllib.request.Request(f"http://127.0.0.1:{porta}/v1/embeddings", data=json.dumps({"input": testi}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    fuori = []
    for x in sorted(d["data"], key=lambda x: x.get("index", 0)):
        v = x["embedding"][:SIG_DIM]  # i primi numeri bastano (il modello è fatto per accorciarli)
        n = math.sqrt(sum(a * a for a in v)) or 1.0
        fuori.append(bytes((max(-127, min(127, round(a / n * 127))) & 0xFF) for a in v))
    return fuori


def _sig_file(dove, quale):
    """Due magazzini di vettori: «fatti» (confermati e memoria, per sempre) e «recenti» (tutte le notizie, 7 giorni)."""
    pre = {"fatti": ("vettori.bin", "testi.jsonl"), "recenti": ("recenti.bin", "recenti.jsonl")}[dove]
    return MAG("significato", pre[0] if quale == "bin" else pre[1])


def _sig_chiavi(dove):
    visti = set()
    try:
        with open(_sig_file(dove, "testi"), encoding="utf-8") as f:
            for r in f:
                try:
                    visti.add(json.loads(r)[0])
                except (ValueError, IndexError):
                    pass
    except OSError:
        pass
    return visti


def _sig_blocco():
    """Un solo lavoratore alla volta sui vettori (il giro o il cuore)."""
    import fcntl
    os.makedirs(MAG("significato"), exist_ok=True)
    f = open(MAG("significato", "lock"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        f.close()
        return None


def _sig_pota_recenti(giorni=7):
    """Le notizie non confermate restano nei vettori 7 giorni: una volta al giorno si riscrive il magazzino «recenti»."""
    limite = (datetime.now(timezone.utc) - timedelta(days=giorni)).date().isoformat()
    try:
        dati = open(_sig_file("recenti", "bin"), "rb").read()
        righe = open(_sig_file("recenti", "testi"), encoding="utf-8").read().splitlines()
    except OSError:
        return 0
    n = min(len(dati) // SIG_DIM, len(righe))
    tieni_b, tieni_t = [], []
    for i in range(n):
        try:
            d = json.loads(righe[i])[1]
        except (ValueError, IndexError):
            continue
        if d >= limite:
            tieni_b.append(dati[i * SIG_DIM:(i + 1) * SIG_DIM])
            tieni_t.append(righe[i])
    with open(_sig_file("recenti", "bin") + ".tmp", "wb") as f:
        f.write(b"".join(tieni_b))
    with open(_sig_file("recenti", "testi") + ".tmp", "w", encoding="utf-8") as f:
        f.write("\n".join(tieni_t) + ("\n" if tieni_t else ""))
    os.replace(_sig_file("recenti", "bin") + ".tmp", _sig_file("recenti", "bin"))
    os.replace(_sig_file("recenti", "testi") + ".tmp", _sig_file("recenti", "testi"))
    return n - len(tieni_t)


def _tel_ok_sig(imp, tel):
    return (bool(tel.get("in_carica")) or (tel.get("batteria") or 0) >= imp.get("batteria_min_fuori_carica", 35)) \
        and (tel.get("temp") or 99) < imp.get("temp_max", 38)


def significato_aggiorna(archivio, cfg, tel, errori, secondi=None, tutte=False, misura=False):
    """Mette nei vettori i fatti confermati che mancano (prima i più recenti), finché c'è tempo. Con tutte=True (lo fa il
    cuore, dalla 2.31, nel tempo libero tra un giro e l'altro) anche tutte le notizie degli ultimi 7 giorni."""
    imp = cfg.get("officina", {})
    if not imp.get("significato", True) or not _su_termux():
        return None
    if not _tel_ok_sig(imp, tel):
        _sig_ferma()
        return {"fase": "in pausa (batteria o temperatura)"}
    blocco = _sig_blocco()
    if not blocco:
        return {"fase": "lavora il cuore"}
    try:
        return _sig_aggiorna(archivio, cfg, imp, errori, secondi, tutte, misura, tel or None)
    finally:
        blocco.close()


def _sig_aggiorna(archivio, cfg, imp, errori, secondi, tutte, misura=False, tel=None):
    os.makedirs(MAG("significato"), exist_ok=True)
    visti = _sig_chiavi("fatti")
    if len(visti) > 3000:  # con tanti vettori serve numpy (pacchetto di Termux): si prova a installarlo una volta al giorno
        try:
            import numpy  # noqa: F401
        except ImportError:
            S_n = _off_stato()
            if S_n.get("numpy_provato") != datetime.now().date().isoformat():
                S_n["numpy_provato"] = datetime.now().date().isoformat()
                _off_salva(S_n)
                try:
                    subprocess.run(["pkg", "install", "-y", "python-numpy"], capture_output=True, timeout=900, stdin=subprocess.DEVNULL,
                                   env=dict(os.environ, DEBIAN_FRONTEND="noninteractive"))
                except (OSError, subprocess.SubprocessError):
                    pass
    da_fare = sorted(((k, v) for k, v in archivio.get("notizie", {}).items() if v.get("conf") and "n:" + k not in visti),
                     key=lambda kv: kv[1].get("data_iso") or "", reverse=True)
    M_ = leggi_json(os.path.join(DATI, "memoria.json"), {}) or {}
    for st_, l in M_.items():
        for x in l:
            k_ = "m:" + hashlib.md5((st_ + x[1]).encode()).hexdigest()[:16]
            if k_ not in visti:
                da_fare.append((k_, {"it": x[1], "data_iso": x[0], "paesi": [st_], "fonte": x[2], "u": x[4] if len(x) > 4 else ""}))
    lavori = [("fatti", da_fare)]
    if tutte:
        visti_r = _sig_chiavi("recenti")
        sette = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recenti = sorted(((k, v) for k, v in archivio.get("notizie", {}).items()
                          if not v.get("conf") and (v.get("data_iso") or "") >= sette and "n:" + k not in visti_r and "n:" + k not in visti),
                         key=lambda kv: kv[1].get("data_iso") or "", reverse=True)
        lavori.append(("recenti", recenti))
    if not any(l for _, l in lavori):
        return {"fase": "pronto", "fatti": len(visti), "nuovi": 0}
    porta = _sig_server(imp, tel=tel)
    if not porta:
        return {"fase": "accendo il modello dei significati" if os.path.exists(OFF(SIGNIFICATO_MODELLO["file"])) else "aspetto il modello",
                "fatti": len(visti)}
    t0, fatti = time.time(), 0
    limite = secondi if secondi is not None else imp.get("secondi_significato", 120)
    for dove, lista in lavori:
        with open(_sig_file(dove, "bin"), "ab") as fv, open(_sig_file(dove, "testi"), "a", encoding="utf-8") as ft:
            for i in range(0, len(lista), 32):
                if time.time() - t0 > limite:
                    break
                gruppo = lista[i:i + 32]
                try:
                    vett = _sig_vettori([(v.get("it") or v.get("t") or "")[:400] for _, v in gruppo], porta)
                except Exception as e:
                    errori.append(f"Ricerca per significato: {str(e)[:100]}")
                    break
                for (k, v), b in zip(gruppo, vett):
                    k_ = k if k.startswith("m:") else "n:" + k
                    fv.write(b)
                    ft.write(json.dumps([k_, (v.get("data_iso") or "")[:10], (v.get("it") or v.get("t") or "")[:300], v.get("paesi") or [],
                                         v.get("fonte", ""), v.get("u", "")], ensure_ascii=False) + "\n")
                    fatti += 1
                fv.flush()
                ft.flush()
    sec_ = round(time.time() - t0, 1)
    if misura:
        _sig_misura(fatti, sec_)
    return {"fase": "pronto", "fatti": len(_sig_chiavi("fatti")), "recenti": len(_sig_chiavi("recenti")),
            "nuovi": fatti, "secondi": sec_, "thread": _off_stato().get("sig_thread"),
            "al_secondo": round(fatti / sec_, 2) if sec_ else None}


def _sig_carica(dove):
    try:
        dati = open(_sig_file(dove, "bin"), "rb").read()
    except OSError:
        return b"", []
    testi = []
    try:
        with open(_sig_file(dove, "testi"), encoding="utf-8") as f:
            for r in f:
                try:
                    testi.append(json.loads(r))
                except ValueError:
                    testi.append(None)
    except OSError:
        pass
    return dati, testi


def significato_cerca(q, stato=None, massimo=30):
    if not os.path.exists(_sig_file("fatti", "bin")) and not os.path.exists(_sig_file("recenti", "bin")):
        return None
    imp = leggi_json(os.path.join(QUI, "config.json"), {}).get("officina", {})
    porta = _sig_server(imp)
    if not porta:
        return {"errore": "il modello dei significati non è acceso (batteria, temperatura o modello non ancora scaricato)"}
    qv = _sig_vettori([SIG_ISTRUZIONE + q[:300]], porta)[0]
    qi = [b - 256 if b > 127 else b for b in qv]
    tutti = []
    for dove in ("fatti", "recenti"):
        dati, testi = _sig_carica(dove)
        n = min(len(dati) // SIG_DIM, len(testi))
        if not n:
            continue
        try:
            import numpy as np
            V = np.frombuffer(dati[:n * SIG_DIM], dtype=np.int8).reshape(n, SIG_DIM).astype(np.int32)
            punti = (V @ np.array(qi, dtype=np.int32)).tolist()
        except ImportError:  # senza numpy: più lento, ma funziona
            import array
            A_ = array.array("b", dati[:n * SIG_DIM])
            punti = [sum(a * b for a, b in zip(A_[i * SIG_DIM:(i + 1) * SIG_DIM], qi)) for i in range(n)]
        tutti += [(punti[i], testi[i], dove) for i in range(n) if testi[i]]
    tutti.sort(key=lambda x: -x[0])
    fuori, visti = [], set()
    for pt, r, dove in tutti:
        if (stato and stato not in (r[3] or [])) or (r[5] or r[2]) in visti:
            continue
        visti.add(r[5] or r[2])
        fuori.append({"d": r[1], "t": r[2], "p": r[3], "f": r[4], "u": r[5], "dove": "per significato" + (" (notizia non ancora confermata)" if dove == "recenti" else ""),
                      "s": round(pt / (127 * 127), 3), "c": 1 if dove == "fatti" else 0})
        if len(fuori) >= massimo:
            break
    return fuori


def _lavoratore_significati():
    """Thread del cuore (dalla 2.31): il processore che non serve al traduttore lavora ai vettori tra un giro e l'altro,
    finché c'è arretrato: prima i fatti confermati, poi tutte le notizie degli ultimi 7 giorni."""
    time.sleep(240)
    archivio, mtime, potato = {}, 0, ""
    while True:
        pausa_ = 600
        try:
            cfg = leggi_json(os.path.join(QUI, "config.json"), {})
            imp = cfg.get("officina", {})
            tel = _tel_ultimo() or {}
            if (_su_termux() and imp.get("significato", True) and imp.get("significato_continuo", True) and tel
                    and _tel_ok_sig(imp, tel) and os.path.exists(OFF(SIGNIFICATO_MODELLO["file"]))):
                perc = os.path.join(DATI, "archivio.json")
                m_ = os.path.getmtime(perc) if os.path.exists(perc) else 0
                if m_ != mtime:
                    try:
                        archivio, mtime = leggi_json(perc, {}) or {}, m_
                    except Exception:
                        pass
                oggi_ = datetime.now().date().isoformat()
                if potato != oggi_:
                    b_ = _sig_blocco()
                    if b_:
                        try:
                            _sig_pota_recenti()
                            potato = oggi_
                        finally:
                            b_.close()
                sp_ = spinta(cfg, tel)
                tutte_ = sp_["piena"] or bool((cfg.get("spinta", {}) or {}).get("recenti_fuori_carica"))
                r_ = significato_aggiorna(archivio, cfg, tel, [], secondi=imp.get("secondi_significato_cuore", 240), tutte=tutte_,
                                          misura=True) or {}
                r_["spinta"] = sp_["perche"]
                # in carica si lavora quasi di continuo; fuori carica una pausa di un minuto tra un lavoro e l'altro
                pausa_ = (20 if sp_["piena"] else int((cfg.get("spinta", {}) or {}).get("pausa_fuori_carica", 60))) if r_.get("nuovi") else 300
                S_ = _off_stato()
                S_["cuore_significati"] = dict(r_, quando=datetime.now(timezone.utc).isoformat())
                _off_salva(S_)
        except Exception as e:
            print("Lavoratore dei significati:", e)
        time.sleep(pausa_)



# ----------------------------------------------------------------------------- 2.30: economia e canali che si trovano da soli
# Economia: dati pubblici e gratuiti, senza chiavi. Banca Mondiale (PIL, commercio, investimenti esteri, debito, spesa
# militare, inflazione, armi), tassi dei titoli di Stato a 10 anni (OCSE, da FRED), valute (ExchangeRate-API, gratuito con
# citazione), materie prime (FRED), partner commerciali e commercio di armi per Stato (UN Comtrade, capitolo 93 delle dogane).
WB_INDICATORI = (
    ("NY.GDP.MKTP.CD", "pil", "PIL (dollari)"),
    ("NE.IMP.GNFS.CD", "import", "Importazioni di beni e servizi (dollari)"),
    ("NE.EXP.GNFS.CD", "export", "Esportazioni di beni e servizi (dollari)"),
    ("NE.IMP.GNFS.ZS", "import_pil", "Importazioni, % del PIL"),
    ("NE.EXP.GNFS.ZS", "export_pil", "Esportazioni, % del PIL"),
    ("BX.KLT.DINV.CD.WD", "ide", "Investimenti diretti esteri in entrata (dollari)"),
    ("GC.DOD.TOTL.GD.ZS", "debito_pil", "Debito del governo centrale, % del PIL"),
    ("DT.DOD.DECT.CD", "debito_estero", "Debito estero (dollari)"),
    ("MS.MIL.XPND.GD.ZS", "mil_pil", "Spesa militare, % del PIL"),
    ("MS.MIL.XPND.CD", "mil", "Spesa militare (dollari)"),
    ("FP.CPI.TOTL.ZG", "inflazione", "Inflazione, % all’anno"),
    ("BN.CAB.XOKA.GD.ZS", "conto_corrente", "Saldo del conto corrente, % del PIL"),
    ("MS.MIL.MPRT.KD", "armi_import", "Importazioni di armi (indice SIPRI)"),
    ("MS.MIL.XPRT.KD", "armi_export", "Esportazioni di armi (indice SIPRI)"),
)
TASSI_ISO2 = ("US", "DE", "IT", "FR", "ES", "GB", "JP", "CA", "AU", "NL", "BE", "AT", "PT", "GR", "IE", "FI", "SE", "DK", "NO", "CH",
              "PL", "CZ", "HU", "SK", "SI", "LT", "LV", "EE", "LU", "IS", "IL", "KR", "MX", "CL", "CO", "NZ", "TR", "ZA", "IN", "CN", "RU", "BR")
MATERIE = (("DCOILBRENTEU", "brent", "Petrolio Brent (dollari al barile)"), ("PNGASEUUSDM", "gas", "Gas naturale in Europa (dollari per milione di BTU)"),
           ("PWHEAMTUSDM", "grano", "Grano (dollari alla tonnellata)"), ("PCOPPUSDM", "rame", "Rame (dollari alla tonnellata)"))
ECO_FONTI = {"bm": "Banca Mondiale (api.worldbank.org)", "tassi": "OCSE, tassi a lungo termine, da FRED (St. Louis Fed)",
             "valute": "Rates By Exchange Rate API (exchangerate-api.com)", "materie": "FRED (St. Louis Fed) e Banca Mondiale",
             "comtrade": "UN Comtrade (Nazioni Unite), anteprima pubblica"}


def _eco_scade(quando, giorni=0, ore=0):
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(quando) > timedelta(days=giorni, hours=ore)
    except (TypeError, ValueError):
        return True


def _fred(serie, timeout=30):
    """Una serie di FRED in CSV, senza chiave: [[data, valore], ...]."""
    # FRED chiude la connessione ai programmi che si presentano come browser: qui ci si presenta come strumento (provato il 20/11)
    testo = scarica("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + serie, timeout=timeout,
                    intestazioni={"User-Agent": "Python-urllib/3 PanGeo " + VERSIONE + " (archivio personale)"}).decode("utf-8", "replace")
    righe = []
    for r in testo.splitlines()[1:]:
        p = r.split(",")
        if len(p) >= 2 and p[1] not in (".", ""):
            try:
                righe.append([p[0][:10], round(float(p[1]), 4)])
            except ValueError:
                pass
    if not righe:
        raise ValueError("serie vuota")
    return righe


def economia(cfg, adesso, errori, secondi=90):
    """Un passo di raccolta economica a giro, con un tempo massimo. dati/economia.json."""
    imp = cfg.get("economia", {})
    if not imp.get("attiva", True):
        return None
    t0 = time.time()
    perc = os.path.join(DATI, "economia.json")
    E = leggi_json(perc, {}) or {}
    cod = cfg.get("codici", {})
    iso3 = {v[0]: k for k, v in cod.items()}
    fatti = []
    # 1. Banca Mondiale: un indicatore a giro (tutti gli Stati in una chiamata), ognuno ogni 7 giorni
    bm = E.setdefault("bm", {})
    agg_bm = E.setdefault("bm_agg", {})
    for ind, chiave, _ in WB_INDICATORI:
        if not _eco_scade(agg_bm.get(chiave), giorni=imp.get("banca_mondiale_giorni", 7)):
            continue
        try:
            d = json.loads(scarica(f"https://api.worldbank.org/v2/country/all/indicator/{ind}?format=json&date=2010:{adesso.year}&per_page=20000",
                                   timeout=60))
            serie = {}
            for r in (d[1] if isinstance(d, list) and len(d) > 1 and d[1] else []):
                st_ = iso3.get(r.get("countryiso3code"))
                if st_ and r.get("value") is not None:
                    serie.setdefault(st_, []).append([int(r["date"]), round(float(r["value"]), 3)])
            bm[chiave] = {k: sorted(v) for k, v in serie.items()}
            agg_bm[chiave] = adesso.isoformat()
            fatti.append("Banca Mondiale: " + chiave)
        except Exception as e:
            errori.append(f"Economia (Banca Mondiale {chiave}): {str(e)[:80]}")
            agg_bm[chiave] = (adesso - timedelta(days=imp.get("banca_mondiale_giorni", 7)) + timedelta(hours=6)).isoformat()
        break
    # 2. valute: una volta al giorno, tutte insieme
    val = E.setdefault("valute", {"storia": {}})
    if _eco_scade(val.get("agg"), ore=imp.get("valute_ore", 20)) and time.time() - t0 < secondi:
        try:
            d = json.loads(scarica("https://open.er-api.com/v6/latest/USD", timeout=30))
            if d.get("result") == "success":
                usate = {v[3] for v in cod.values() if v[3]}
                val["storia"][adesso.date().isoformat()] = {k: v for k, v in d.get("rates", {}).items() if k in usate}
                val["storia"] = dict(sorted(val["storia"].items())[-400:])
                val["agg"] = adesso.isoformat()
                fatti.append("valute")
        except Exception as e:
            errori.append(f"Economia (valute): {str(e)[:80]}")
            val["agg"] = (adesso - timedelta(hours=imp.get("valute_ore", 20)) + timedelta(hours=3)).isoformat()
    # 3. materie prime: una volta al giorno
    mat = E.setdefault("materie", {})
    for serie, chiave, _ in MATERIE:
        if time.time() - t0 > secondi or not _eco_scade((mat.get(chiave) or {}).get("agg"), ore=imp.get("materie_ore", 20)):
            continue
        try:
            mat[chiave] = {"agg": adesso.isoformat(), "s": _fred(serie)[-400:]}
            fatti.append(chiave)
        except Exception as e:
            mat[chiave] = dict(mat.get(chiave) or {}, agg=adesso.isoformat())
            errori.append(f"Economia ({chiave}): {str(e)[:80]}")
    # 4. tassi dei titoli di Stato a 10 anni (OCSE, mensili): pochi a giro, ognuno ogni 5 giorni
    tas = E.setdefault("tassi", {})
    i2 = {v[1]: k for k, v in cod.items()}
    fatti_t = 0
    for c in TASSI_ISO2:
        st_ = i2.get(c)
        if not st_ or fatti_t >= imp.get("tassi_per_giro", 6) or time.time() - t0 > secondi:
            continue
        x = tas.get(st_) or {}
        if not _eco_scade(x.get("agg"), giorni=30 if x.get("manca") else imp.get("tassi_giorni", 5)):
            continue
        fatti_t += 1
        try:
            tas[st_] = {"agg": adesso.isoformat(), "s": _fred(f"IRLTLT01{c}M156N")[-180:]}
        except Exception as e:
            tas[st_] = dict(x, agg=adesso.isoformat(), manca=str(e)[:60])
        time.sleep(0.5)
    if fatti_t:
        fatti.append(f"tassi {fatti_t}")
    # 5. commercio (UN Comtrade): pochi Stati a giro, ognuno ogni 120 giorni; totale e armi (capitolo 93), import ed export
    com = E.setdefault("comtrade", {})
    fatti_c = 0
    da_fare = sorted((k for k, v in cod.items() if v[2]), key=lambda k: (com.get(k) or {}).get("agg", ""))
    # l'anteprima pubblica di Comtrade ha un limite al giorno: se dice «troppe richieste» si riposa 6 ore
    pausa_c = E.get("comtrade_pausa", "") > adesso.isoformat()
    for st_ in ([] if pausa_c else da_fare):
        if fatti_c >= imp.get("comtrade_per_giro", 1) or time.time() - t0 > secondi:
            break
        if not _eco_scade((com.get(st_) or {}).get("agg"), giorni=imp.get("comtrade_giorni", 120)):
            break
        fatti_c += 1
        r_ = {"agg": adesso.isoformat()}
        try:
            for anno in (adesso.year - 2, adesso.year - 3):  # l'anno appena chiuso arriva tardi per quasi tutti gli Stati
                ok_ = False
                for flusso, cmd, chiave in (("M", "TOTAL", "M"), ("X", "TOTAL", "X"), ("M", "93", "M93"), ("X", "93", "X93")):
                    d = json.loads(scarica(f"https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode={cod[st_][2]}&period={anno}"
                                           f"&flowCode={flusso}&cmdCode={cmd}&includeDesc=true", timeout=40))
                    righe = [x for x in d.get("data") or [] if x.get("partnerCode") and not x.get("partner2Code")
                             and x.get("motCode", 0) == 0 and x.get("customsCode", "C00") == "C00" and x.get("primaryValue")]
                    tot = sum(x.get("primaryValue") or 0 for x in d.get("data") or [] if x.get("partnerCode") == 0
                              and not x.get("partner2Code") and x.get("motCode", 0) == 0)
                    if righe:
                        ok_ = True
                    per = {}
                    for x in righe:
                        nome = iso3.get(x.get("partnerISO")) or x.get("partnerDesc") or str(x.get("partnerCode"))
                        per[nome] = per.get(nome, 0) + x["primaryValue"]
                    r_[chiave] = [[k, round(v)] for k, v in sorted(per.items(), key=lambda kv: -kv[1])[:12]]
                    r_[chiave + "_tot"] = round(tot) if tot else None
                    time.sleep(2.5)
                    if not ok_ and chiave == "M":
                        break  # nessun dato per quell'anno: si prova l'anno prima
                if ok_:
                    r_["anno"] = anno
                    break
            com[st_] = r_
        except Exception as e:
            if "429" in str(e) or "403" in str(e) or "Quota" in str(e):
                E["comtrade_pausa"] = (adesso + timedelta(hours=6)).isoformat()  # si riprova lo stesso Stato più tardi
                break
            com[st_] = dict(com.get(st_) or {}, agg=adesso.isoformat(), errore=str(e)[:80])
    if fatti_c:
        fatti.append(f"commercio {fatti_c}")
    E["agg"] = adesso.isoformat()
    scrivi_json(perc, E)
    return {"fatti": fatti, "secondi": round(time.time() - t0, 1), "bm": len(bm), "tassi": sum(1 for v in tas.values() if v.get("s")),
            "valute": len(val.get("storia", {})), "comtrade": sum(1 for v in com.values() if v.get("anno"))}


def _var_valuta(storia, cur, giorni):
    date_ = sorted(storia)
    if not date_ or cur not in storia[date_[-1]]:
        return None
    oggi_ = storia[date_[-1]][cur]
    obiettivo = (datetime.fromisoformat(date_[-1]) - timedelta(days=giorni)).date().isoformat()
    prima_ = [d for d in date_ if d <= obiettivo and cur in storia[d]]
    if not prima_:
        return None
    vecchio = storia[prima_[-1]][cur]
    return round((vecchio / oggi_ - 1) * 100, 2) if oggi_ else None  # quanto vale la moneta rispetto al dollaro: + si rafforza


def scrivi_economia_web(cfg, adesso):
    E = leggi_json(os.path.join(DATI, "economia.json"), {}) or {}
    cod = cfg.get("codici", {})
    S = {}
    for chiave, serie in (E.get("bm") or {}).items():
        for st_, l in serie.items():
            z = S.setdefault(st_, {}).setdefault("bm", {})
            z[chiave] = l[-1]
            if chiave in ("mil_pil", "debito_pil", "import_pil", "export_pil", "armi_import", "armi_export", "inflazione"):
                S[st_].setdefault("serie", {})[chiave] = l[-12:]
    for st_, x in (E.get("tassi") or {}).items():
        if x.get("s"):
            S.setdefault(st_, {})["tasso"] = [[d[:7], v] for d, v in x["s"][-36:]]
    storia = (E.get("valute") or {}).get("storia") or {}
    if storia:
        ult = storia[sorted(storia)[-1]]
        for st_, c in cod.items():
            if c[3] and c[3] in ult and c[3] != "USD":
                S.setdefault(st_, {})["valuta"] = [c[3], ult[c[3]], _var_valuta(storia, c[3], 7), _var_valuta(storia, c[3], 30),
                                                   _var_valuta(storia, c[3], 365)]
    for st_, x in (E.get("comtrade") or {}).items():
        if x.get("anno"):
            S.setdefault(st_, {})["commercio"] = {k: x.get(k) for k in ("anno", "M", "X", "M93", "X93", "M_tot", "X_tot", "M93_tot", "X93_tot")}
    mat = {k: {"nome": n, "s": ((E.get("materie") or {}).get(k) or {}).get("s", [])[-250:]} for _, k, n in MATERIE}
    _scrivi_se_cambia(os.path.join(WEB, "economia.js"), "window.ECONOMIA=" + json.dumps(
        {"agg": adesso.astimezone().strftime("%d/%m/%Y %H:%M"), "stati": S, "materie": mat, "fonti": ECO_FONTI,
         "nomi": {k: n for _, k, n in WB_INDICATORI}}, ensure_ascii=False, separators=(",", ":")) + ";")


def avvisi_economia(cfg, adesso):
    """Avvisi economici: una moneta che perde l'8% o più in una settimana, un tasso a 10 anni che sale di un punto in un mese."""
    E = leggi_json(os.path.join(DATI, "economia.json"), {}) or {}
    cod, fuori = cfg.get("codici", {}), []
    storia = (E.get("valute") or {}).get("storia") or {}
    oggi_ = adesso.date().isoformat()
    soglia_v = cfg.get("avvisi", {}).get("valuta_settimana", -8)
    for st_, c in cod.items():
        v7 = _var_valuta(storia, c[3], 7) if c[3] and c[3] != "USD" else None
        if v7 is not None and v7 <= soglia_v:
            fuori.append({"id": f"valuta:{c[3]}:{oggi_}", "tipo": "valuta", "stato": st_, "livello": 2 if v7 <= 2 * soglia_v else 1,
                          "testo": f"{st_}: la moneta ({c[3]}) ha perso il {abs(v7):.1f}% sul dollaro in una settimana."})
    for st_, x in (E.get("tassi") or {}).items():
        s = x.get("s") or []
        if len(s) >= 2 and s[-1][1] - s[-2][1] >= cfg.get("avvisi", {}).get("tasso_mese", 1.0):
            fuori.append({"id": f"tasso:{st_}:{s[-1][0]}", "tipo": "tasso", "stato": st_, "livello": 1,
                          "testo": f"{st_}: il tasso dei titoli di Stato a 10 anni è salito da {s[-2][1]:.2f}% a {s[-1][1]:.2f}% in un mese ({s[-1][0][:7]})."})
    return fuori


# Canali: salute (quelli che non rispondono si spengono da soli e si riprovano una volta al giorno) e canali YouTube trovati
# da soli (citati nei messaggi dei canali Telegram seguiti).
def canale_ok(auto, nome, cfg):
    s = (auto.get("salute_canali") or {}).get(nome) or {}
    if s.get("spento") and not _eco_scade(s.get("spento"), ore=cfg.get("canali_salute", {}).get("riprova_ore", 24)):
        return False
    return True


def canale_esito(auto, nome, ok, cfg, adesso):
    S = auto.setdefault("salute_canali", {})
    s = S.setdefault(nome, {"ok": 0, "fila": 0})
    if ok:
        s.update(ok=s.get("ok", 0) + 1, fila=0, ultimo_ok=adesso.isoformat())
        s.pop("spento", None)
    else:
        s["fila"] = s.get("fila", 0) + 1
        if s["fila"] >= cfg.get("canali_salute", {}).get("spegni_dopo", 12):
            s["spento"] = adesso.isoformat()


def youtube_da_link(testo_html, citati, da):
    """I video e i canali YouTube citati in un messaggio: {chiave: set(di chi li cita)}."""
    for m in re.finditer(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})|youtube\.com/(@[A-Za-z0-9_.-]{3,40}|channel/UC[0-9A-Za-z_-]{22})", testo_html):
        chiave = ("v:" + m.group(1)) if m.group(1) else ("c:" + m.group(2).replace("channel/", ""))
        citati.setdefault(chiave, set()).add(da)


def scopri_youtube(auto, citati, cfg, adesso, errori):
    """Dai video citati risale al canale; un canale citato da almeno 2 canali seguiti entra (con il suo feed provato)."""
    imp = cfg.get("scoperta_youtube", {})
    if not imp.get("attiva", True):
        return []
    C = auto.setdefault("youtube_citati", {})
    visti_v = auto.setdefault("youtube_video_visti", {})
    cache_h = auto.setdefault("youtube_handle", {})  # @nome → UC… (una sola richiesta per canale)
    letti = 0
    for chiave, da in sorted(citati.items(), key=lambda kv: -len(kv[1])):
        cid, nome = None, ""
        if chiave.startswith("c:"):
            cid = chiave[2:] if chiave[2:].startswith("UC") else None
            nome = chiave[2:]
            if not cid:
                if chiave[2:] in cache_h and not cache_h[chiave[2:]]:
                    continue
                try:
                    cid = cache_h.get(chiave[2:]) or id_canale(chiave[2:], cache_h)
                except Exception:
                    cache_h[chiave[2:]] = None
                    continue
        else:
            vid = chiave[2:]
            if vid in visti_v:
                cid, nome = visti_v[vid]
            elif letti < imp.get("video_per_giro", 4):
                letti += 1
                try:  # oEmbed: chi ha pubblicato il video (leggero, senza la pagina del video)
                    o = json.loads(scarica("https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v=" + vid, timeout=20))
                    h_ = re.search(r"youtube\.com/(@[A-Za-z0-9_.-]+|channel/UC[0-9A-Za-z_-]{22})", o.get("author_url", ""))
                    if h_:
                        cid = h_.group(1).replace("channel/", "") if "channel/" in h_.group(1) else (cache_h.get(h_.group(1)) or id_canale(h_.group(1), cache_h))
                        nome = o.get("author_name") or h_.group(1)
                        visti_v[vid] = [cid, nome]
                    else:
                        visti_v[vid] = [None, ""]
                except Exception:
                    visti_v[vid] = [None, ""]
                    continue
        if not cid:
            continue
        z = C.setdefault(cid, {"nome": nome, "da": [], "volte": 0, "primo": adesso.isoformat()})
        z["volte"] += 1
        z["da"] = sorted(set(z["da"]) | set(da))[:12]
        if nome and not z.get("nome", "").strip():
            z["nome"] = nome
    if len(visti_v) > 3000:
        auto["youtube_video_visti"] = dict(list(visti_v.items())[-2000:])
    gia = {c.lower() for c in cfg.get("youtube", [])} | {x["cid"] for x in auto.get("youtube", [])}
    nuovi = []
    for cid, z in sorted(C.items(), key=lambda kv: -len(kv[1]["da"])):
        if len(auto.get("youtube", [])) >= imp.get("max_canali", 60):
            break
        if cid in gia or len(z["da"]) < imp.get("min_citazioni", 2) or z.get("provato"):
            continue
        z["provato"] = adesso.isoformat()
        try:
            n_ = len(leggi_rss(scarica("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid, timeout=20)))
        except Exception:
            n_ = 0
        if n_ >= 3:
            auto.setdefault("youtube", []).append({"cid": cid, "nome": z.get("nome") or cid, "da": z["da"][:5],
                                                   "aggiunta": adesso.date().isoformat()})
            nuovi.append(z.get("nome") or cid)
    if len(C) > 5000:
        auto["youtube_citati"] = dict(sorted(C.items(), key=lambda kv: -len(kv[1]["da"]))[:3000])
    return nuovi


def canali_stato(cfg, mie, auto, adesso):
    """Per la pagina e il rapporto: quanti canali, quali trovati da soli negli ultimi giorni, quali spenti."""
    tre = (adesso - timedelta(days=3)).date().isoformat()
    S = auto.get("salute_canali") or {}
    return {"telegram": len(cfg.get("telegram", []) + mie.get("telegram", [])) + len(auto.get("telegram", [])),
            "youtube": len(cfg.get("youtube", []) + mie.get("youtube", [])) + len(auto.get("youtube", [])),
            "tg_trovati": [[c["canale"], c.get("aggiunta", "")] for c in auto.get("telegram", [])],
            "yt_trovati": [[c["nome"], c.get("aggiunta", ""), c["cid"]] for c in auto.get("youtube", [])],
            "nuovi_tg": [c["canale"] for c in auto.get("telegram", []) if c.get("aggiunta", "") >= tre],
            "nuovi_yt": [c["nome"] for c in auto.get("youtube", []) if c.get("aggiunta", "") >= tre],
            "spenti": sorted(k for k, v in S.items() if v.get("spento"))}


# 6. Lettura degli articoli (dalla 2.32): il telefono «naviga». Per le notizie confermate degli ultimi 2 giorni apre la
# pagina della testata e ne tiene il testo (solo i paragrafi), che va nell'indice istantaneo: la ricerca trova anche ciò
# che il titolo non dice. Gratis (solo dati). Il testo resta sul telefono e non va mai sul sito pubblico: lì restano
# titolo e collegamento. Pagine a pagamento o con la richiesta dei cookie danno poco testo: vengono segnate e lasciate.
ARTICOLI_SALTA = ("news.google.com", "t.me", "youtube.com", "youtu.be", "x.com", "twitter.com", "facebook.com", "instagram.com")


def testo_articolo(grezzo, massimo=4000):
    """I paragrafi di una pagina HTML, senza menu, pubblicità e script."""
    if not grezzo:
        return ""
    m = re.search(rb'charset=["\']?([\w-]+)', grezzo[:3000], re.I)
    try:
        h_ = grezzo.decode(m.group(1).decode() if m else "utf-8", errors="replace")
    except LookupError:
        h_ = grezzo.decode("utf-8", errors="replace")
    # molte testate mettono il testo intero nei dati strutturati (JSON-LD «articleBody»), anche quando la pagina lo
    # disegna con JavaScript: se c'è, si prende quello
    for m_ in re.finditer(r'"articleBody"\s*:\s*("(?:[^"\\]|\\.)*")', h_):
        try:
            corpo_ = re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", json.loads(m_.group(1))))).strip()
        except ValueError:
            continue
        if len(corpo_) >= 300:
            return corpo_[:massimo]
    h_ = re.sub(r"(?is)<(script|style|noscript|nav|header|footer|aside|form|figure|svg)\b.*?</\1>", " ", h_)
    corpo = re.search(r"(?is)<article\b.*?</article>", h_)
    pezzi = re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", corpo.group(0) if corpo and len(corpo.group(0)) > 1500 else h_)
    fuori, n = [], 0
    for x in pezzi:
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", x))).strip()
        if len(t) < 60 or re.search(r"(?i)cookie|newsletter|abbonati|subscribe|sign up|iscriviti|all rights reserved|©", t):
            continue
        fuori.append(t)
        n += len(t) + 1
        if n >= massimo:
            break
    return "\n".join(fuori)[:massimo]


def leggi_articoli(archivio, adesso, cfg, tel, errori):
    """Legge le pagine delle notizie confermate più importanti (più fonti, più recenti), al massimo 2 per gruppo di notizie
    sullo stesso fatto. In carica e al fresco (spinta piena) ne legge di più."""
    ca = cfg.get("articoli", {}) or {}
    if not ca.get("attivo", True) or not RETE["su"]:
        return None
    sp = spinta(cfg, tel)
    quanti = int(ca.get("per_giro_carica", 12) if sp["piena"] else ca.get("per_giro", 4))
    limite_t = (adesso - timedelta(hours=int(ca.get("ore", 48)))).isoformat()
    # le pagine già aperte stanno in un file piccolo a parte (l'archivio è grande e non si riscrive per questo)
    perc_l = os.path.join(DATI, "articoli.json")
    L_ = leggi_json(perc_l, {}) or {}
    gia = L_.get("letti") or {}
    vecchi_ = (adesso - timedelta(days=4)).date().isoformat()
    gia = {k: x for k, x in gia.items() if x and x[0] >= vecchi_}
    cand, per_gruppo = [], {}
    for k, v in archivio.get("notizie", {}).items():
        u = v.get("u") or ""
        if not v.get("conf") or k in gia or not u.startswith("http") or (v.get("data_iso") or "") < limite_t:
            continue
        host = urllib.parse.urlparse(u).netloc.lower()
        if any(host == x or host.endswith("." + x) for x in ARTICOLI_SALTA):
            continue
        cand.append((k, v))
    cand.sort(key=lambda kv: (kv[1].get("nf") or 1, kv[1].get("data_iso") or ""), reverse=True)
    scelti = []
    for k, v in cand:
        g = v.get("gr") or k
        if per_gruppo.get(g, 0) >= 2:
            continue
        per_gruppo[g] = per_gruppo.get(g, 0) + 1
        scelti.append((k, v))
        if len(scelti) >= quanti:
            break
    if not scelti:
        return {"letti": 0, "poco_testo": 0, "provati": 0, "in_coda": 0, "totale": L_.get("totale", 0)}

    def _uno(u):
        try:
            return testo_articolo(scarica(u, timeout=20), int(ca.get("caratteri", 4000)))
        except Exception as e:
            return e
    letti = poco = 0
    db = None
    try:
        db = _indice_apri()
        if not db.execute("SELECT name FROM sqlite_master WHERE name='testi'").fetchone():
            db.close()
            db = None
    except Exception:
        db = None
    pool_ = concurrent.futures.ThreadPoolExecutor(max_workers=sp["paralleli"])
    try:
        futuri = [(k, v, pool_.submit(_uno, v["u"])) for k, v in scelti]
        fine_ = time.time() + int(ca.get("secondi_carica", 90) if sp["piena"] else ca.get("secondi", 40))
        for k, v, fu in futuri:
            try:
                t_ = fu.result(timeout=max(1, fine_ - time.time()))
            except concurrent.futures.TimeoutError:
                break
            if isinstance(t_, SenzaRete):
                break
            if isinstance(t_, Exception):
                gia[k] = [adesso.date().isoformat(), -1]
                continue
            gia[k] = [adesso.date().isoformat(), len(t_)]
            if len(t_) < int(ca.get("minimo", 300)):
                poco += 1
                continue
            letti += 1
            if db is not None:
                kk = "a:" + k
                if not db.execute("SELECT 1 FROM visti WHERE k=?", (kk,)).fetchone():
                    db.execute("INSERT INTO visti VALUES (?)", (kk,))
                    db.execute("INSERT INTO testi (testo, d, p, f, u, dove, c) VALUES (?,?,?,?,?,?,?)",
                               ((v.get("it") or v.get("t") or "") + " · " + t_, (v.get("data_iso") or "")[:10],
                                "|".join(v.get("paesi") or []), v.get("fonte") or "", v["u"], "articolo letto", 1))
    finally:
        pool_.shutdown(wait=False, cancel_futures=True)
        if db is not None:
            db.commit()
            db.close()
        L_["totale"] = L_.get("totale", 0) + letti
        L_["letti"] = gia
        scrivi_json(perc_l, L_)
    return {"letti": letti, "poco_testo": poco, "provati": len(scelti), "in_coda": max(0, len(cand) - len(scelti)),
            "totale": L_["totale"]}


# 7. Storia (dalla 2.33): il programma studia il passato di ogni Stato e lo collega al presente.
#   - archivi accademici gratuiti, scaricati una volta alla settimana (pochi KB): UCDP/PRIO dell'Università di Uppsala
#     (conflitti armati dal 1946, violenza contro i civili, scontri tra gruppi armati) e l'elenco dei colpi di Stato di
#     Powell e Thyne (dal 1950, aggiornato più volte l'anno);
#   - la cronologia di ogni Stato: il cervello la scrive SOLO da quelle fonti, dall'introduzione storica del World Factbook,
#     dalla voce di Wikipedia (appoggio) e dai fatti confermati degli ultimi mesi; una tappa entra solo se l'anno sta davvero
#     nella fonte che cita (controllo fatto dal programma, non dal cervello);
#   - i precedenti negli avvisi: un colpo di Stato o una guerra di oggi portano con sé quelli di prima.
STORIA_FONTI = {
    "U": ["UCDP/PRIO, conflitti armati dal 1946 (Università di Uppsala)", "https://ucdp.uu.se/downloads/"],
    "G": ["Powell e Thyne, colpi di Stato dal 1950", "https://jonathanmpowell.com/coups/"],
    "F": ["CIA World Factbook, introduzione storica (copia d'archivio, febbraio 2026)", "https://github.com/factbook/factbook.json"],
    "W": ["Wikipedia, voce sulla storia (enciclopedia di appoggio, affidabilità media)", ""],
    "R": ["Fatti confermati da più fonti nell'archivio di PanGeo", ""],
}
# nomi usati dagli archivi che non sono quelli di oggi (si tiene anche il nome storico, scritto nel dato)
NOMI_STORICI = {
    "bosnia-herzegovina": "Bosnia ed Erzegovina", "cambodia (kampuchea)": "Cambogia", "dr congo (zaire)": "RD Congo",
    "madagascar (malagasy)": "Madagascar", "myanmar (burma)": "Myanmar", "russia (soviet union)": "Russia",
    "serbia (yugoslavia)": "Serbia", "south vietnam": "Vietnam", "south yemen": "Yemen", "united states of america": "USA",
    "vietnam (north vietnam)": "Vietnam", "yemen (north yemen)": "Yemen", "zimbabwe (rhodesia)": "Zimbabwe",
    "democratic republic of the congo": "RD Congo", "republic of vietnam": "Vietnam", "yemen arab republic; n. yemen": "Yemen",
    "yemen people's republic; s. yemen": "Yemen", "hyderabad": "India",
}
STORIA_TIPI = {"1": "coloniale", "2": "tra Stati", "3": "interno", "4": "interno con intervento straniero"}
STORIA_POSTA = {"1": "territorio", "2": "governo", "3": "territorio e governo"}


def _storia_nomi(paesi):
    m = {k: v for k, v in NOMI_STORICI.items()}
    for st, nomi in (paesi or {}).items():
        for n in nomi:
            m.setdefault(n.lower(), st)
    return m


def _storia_csv(grezzo):
    """Un CSV, anche dentro uno zip (il primo file .csv)."""
    import csv
    import io
    import zipfile
    if grezzo[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(grezzo)) as z:
            nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            grezzo = z.read(nome)
    return list(csv.DictReader(io.StringIO(grezzo.decode("utf-8-sig", errors="replace"))))


def _storia_link(pagina, rx):
    """L'indirizzo più recente di un file nella pagina dei download (il numero di versione cambia)."""
    h = scarica(pagina, timeout=40).decode("utf-8", errors="replace")
    trovati = sorted(set(re.findall(rx, h)))
    if not trovati:
        raise ValueError("file non trovato nella pagina " + pagina)
    u = trovati[-1]
    return u if u.startswith("http") else urllib.parse.urljoin(pagina, u)


def _storia_conflitti(righe, nomi):
    """UCDP/PRIO: da una riga per conflitto e anno a un conflitto con i suoi anni, per ogni Stato in cui si combatte."""
    per_c = {}
    for r in righe:
        c = per_c.setdefault(r.get("conflict_id"), {"loc": r.get("location", ""), "a": r.get("side_a", ""), "b": r.get("side_b", ""),
                                                      "a2": r.get("side_a_2nd", ""), "terr": r.get("territory_name", ""),
                                                      "inc": r.get("incompatibility", ""), "tipo": r.get("type_of_conflict", ""),
                                                      "anni": set(), "guerra": set()})
        try:
            a_ = int(r.get("year") or 0)
        except ValueError:
            continue
        c["anni"].add(a_)
        if str(r.get("intensity_level")) == "2":
            c["guerra"].add(a_)
        c["tipo"] = r.get("type_of_conflict") or c["tipo"]
    fuori = {}
    for cid, c in per_c.items():
        if not c["anni"]:
            continue
        a2_ = [x.strip().replace("Government of ", "") for x in (c["a2"] or "").split(",") if x.strip()]
        c["a2"] = ", ".join(a2_) if len(a2_) <= 4 else ", ".join(a2_[:3]) + f" e altri {len(a2_) - 3}"
        for x in c["loc"].split(","):
            st = nomi.get(x.strip().lower())
            if not st:
                continue
            fuori.setdefault(st, []).append([min(c["anni"]), max(c["anni"]), STORIA_TIPI.get(str(c["tipo"]), ""), c["a"], c["b"],
                                             c["terr"], STORIA_POSTA.get(str(c["inc"]), ""), len(c["guerra"]), len(c["anni"]),
                                             c["a2"], x.strip(), cid])
    for l in fuori.values():
        l.sort(key=lambda x: (-x[1], -x[0]))
    return fuori


def _storia_vittime(righe, nomi, campo_nome):
    """UCDP: violenza contro i civili (un attore) o scontri tra gruppi armati (due attori), sommati per Stato e attore."""
    agg = {}
    for r in righe:
        try:
            a_, m_ = int(r.get("year") or 0), int(float(r.get("best_fatality_estimate") or 0))
        except ValueError:
            continue
        for x in (r.get("location") or "").split(","):
            st = nomi.get(x.strip().lower())
            if not st:
                continue
            chi = campo_nome(r)
            g = agg.setdefault(st, {}).setdefault(chi, [a_, a_, 0, r.get("is_government_actor", "")])
            g[0], g[1], g[2] = min(g[0], a_), max(g[1], a_), g[2] + m_
    return {st: sorted(([chi] + v for chi, v in d.items()), key=lambda x: -x[3])[:12] for st, d in agg.items()}


def storia_archivi(cfg, adesso, errori):
    """Scarica (una volta ogni «giorni_archivi» giorni) gli archivi UCDP e i colpi di Stato. dati/magazzino/storia/archivi.json."""
    imp = cfg.get("storia", {}) or {}
    perc = MAG("storia", "archivi.json")
    A = leggi_json(perc, {}) or {}
    if A.get("quando", "") > (adesso - timedelta(days=int(imp.get("giorni_archivi", 7)))).isoformat():
        return A
    nomi = _storia_nomi(leggi_json(os.path.join(QUI, "paesi.json"), {}))
    nuovo, versioni = {"stati": {}}, {}
    try:
        pag_u = "https://ucdp.uu.se/downloads/"
        u_acd = _storia_link(pag_u, r'href="([^"]*ucdp-prio-acd-\d+-csv\.zip)"')
        conf = _storia_conflitti(_storia_csv(scarica(u_acd, timeout=60)), nomi)
        versioni["U"] = u_acd.rsplit("/", 1)[-1]
        civ = gru = {}
        try:
            u_os = _storia_link(pag_u, r'href="([^"]*ucdp-onesided-\d+-csv\.zip)"')
            civ = _storia_vittime(_storia_csv(scarica(u_os, timeout=60)), nomi, lambda r: r.get("actor_name", ""))
            u_ns = _storia_link(pag_u, r'href="([^"]*ucdp-nonstate-\d+-csv\.zip)"')
            gru = _storia_vittime(_storia_csv(scarica(u_ns, timeout=60)), nomi,
                                  lambda r: (r.get("side_a_name") or "") + " contro " + (r.get("side_b_name") or ""))
        except Exception as e:
            errori.append(f"Storia (UCDP, civili e gruppi): {str(e)[:100]}")
        for st in set(conf) | set(civ) | set(gru):
            s_ = nuovo["stati"].setdefault(st, {})
            if conf.get(st):
                s_["conflitti"] = conf[st]
            if civ.get(st):
                s_["civili"] = civ[st]
            if gru.get(st):
                s_["gruppi"] = gru[st]
    except SenzaRete:
        raise
    except Exception as e:
        errori.append(f"Storia (UCDP): {str(e)[:100]}")
        return A
    try:
        u_pt = _storia_link("https://jonathanmpowell.com/coups/", r'href="([^"]*/pt_\d+[^"]*\.csv)"')
        for r in _storia_csv(scarica(u_pt, timeout=60)):
            st = nomi.get((r.get("country") or "").strip().lower())
            if not st:
                continue
            try:
                d_ = "%04d-%02d-%02d" % (int(r["year"]), int(r.get("month") or 1), int(r.get("day") or 1))
            except (KeyError, ValueError):
                continue
            nuovo["stati"].setdefault(st, {}).setdefault("golpe", []).append([d_, 1 if str(r.get("coup")) == "2" else 0, r.get("country", "")])
        for s_ in nuovo["stati"].values():
            if s_.get("golpe"):
                s_["golpe"].sort(reverse=True)
        versioni["G"] = u_pt.rsplit("/", 1)[-1]
    except SenzaRete:
        raise
    except Exception as e:
        errori.append(f"Storia (colpi di Stato): {str(e)[:100]}")
        for st, s_ in (A.get("stati") or {}).items():  # si tiene l'elenco della volta prima
            if s_.get("golpe"):
                nuovo["stati"].setdefault(st, {})["golpe"] = s_["golpe"]
    nuovo.update(quando=adesso.isoformat(), versioni=versioni, fonti={k: STORIA_FONTI[k] for k in ("U", "G")})
    os.makedirs(os.path.dirname(perc), exist_ok=True)
    scrivi_json(perc, nuovo)
    return nuovo


_STORIA_CACHE = {"m": 0, "A": None}


def _storia_carica():
    perc = MAG("storia", "archivi.json")
    try:
        m_ = os.path.getmtime(perc)
    except OSError:
        return {}
    if _STORIA_CACHE["m"] != m_:
        _STORIA_CACHE.update(m=m_, A=leggi_json(perc, {}) or {})
    return _STORIA_CACHE["A"] or {}


def precedenti(stato, tipo):
    """Una riga con i precedenti storici di un fatto di oggi (per gli avvisi), oppure ''."""
    tutti_ = _storia_carica().get("stati") or {}
    if not tutti_:
        return ""  # archivi non ancora scaricati
    s = tutti_.get(stato) or {}
    if tipo == "golpe":
        g = s.get("golpe") or []
        if not g:
            return "Precedenti: nessun colpo di Stato registrato dal 1950 (Powell e Thyne)."
        ok_ = [x for x in g if x[1]]
        return (f"Precedenti: {len(ok_)} colpi di Stato riusciti e {len(g) - len(ok_)} falliti dal 1950, l'ultimo nel {g[0][0][:4]}"
                f" ({'riuscito' if g[0][1] else 'fallito'}; Powell e Thyne).")
    if tipo in ("guerra", "truppe", "missili", "terrorismo", "esplosioni", "morti", "spazio aereo"):
        c = s.get("conflitti") or []
        if not c:
            return "Precedenti: nessun conflitto armato registrato dal 1946 (UCDP)."
        guerra_ = sum(x[7] for x in c)
        return (f"Precedenti: {len(c)} conflitti armati registrati dal 1946, l'ultimo attivo nel {max(x[1] for x in c)}"
                + (f", {guerra_} anni con più di mille morti" if guerra_ else "") + " (UCDP).")
    return ""


def _storia_factbook(stato, cfg, errori):
    """L'introduzione storica del World Factbook (copia d'archivio), tenuta in cache sul telefono."""
    perc = MAG("storia", "factbook", re.sub(r"[^\w]+", "_", stato) + ".txt")
    try:
        return open(perc, encoding="utf-8").read()
    except OSError:
        pass
    p_ = (cfg.get("sapere", {}).get("factbook") or {}).get(stato)
    if not p_:
        return ""
    try:
        d = json.loads(scarica("https://raw.githubusercontent.com/factbook/factbook.json/master/" + p_ + ".json", timeout=30))
        t = testo_factbook(((d.get("Introduction") or {}).get("Background")))
    except SenzaRete:
        raise
    except Exception as e:
        errori.append(f"Storia (Factbook, {stato}): {str(e)[:80]}")
        return ""
    os.makedirs(os.path.dirname(perc), exist_ok=True)
    with open(perc, "w", encoding="utf-8") as f:
        f.write(t or "")
    return t or ""


def _storia_domanda(stato, fonti):
    pezzi = []
    if fonti.get("F"):
        pezzi.append("F = CIA World Factbook, introduzione storica:\n" + fonti["F"])
    if fonti.get("W"):
        pezzi.append("W = Wikipedia, voce sulla storia (enciclopedia di appoggio):\n" + fonti["W"])
    if fonti.get("U"):
        pezzi.append("U = UCDP, conflitti armati dal 1946 (anni · tipo · parti · posta in gioco · anni con più di mille morti):\n" + fonti["U"])
    if fonti.get("G"):
        pezzi.append("G = colpi di Stato dal 1950 (Powell e Thyne):\n" + fonti["G"])
    if fonti.get("R"):
        pezzi.append("R = fatti confermati da più fonti negli ultimi mesi (archivio):\n" + fonti["R"])
    return (f"Sei lo storico di un archivio pubblico su difesa e geopolitica. Stato: {stato}.\n"
            "Fonti (usa SOLO queste):\n\n" + "\n\n".join(pezzi) + "\n\n"
            f"Scrivi la cronologia di {stato}: da 12 a 30 tappe, dalla più antica alla più recente, una per riga, così:\n"
            "T | anno | tappa | fonte\n"
            "- anno: un anno (1960), un intervallo (1960-1962) o un secolo (XIV secolo), come risulta dalla fonte;\n"
            "- tappa: in italiano semplice, al massimo 25 parole, solo fatti, senza giudizi né previsioni;\n"
            "- fonte: una sola lettera tra " + ", ".join(k for k in "FWUGR" if fonti.get(k)) + ".\n"
            "Metti le tappe che servono a capire lo Stato di oggi: origini, indipendenza, regimi e costituzioni, guerre e "
            "conflitti interni, colpi di Stato, trattati e alleanze, crisi recenti. Per i conflitti usa U e G, per gli ultimi "
            "mesi R. Niente che non stia nelle fonti. Nessun altro testo prima o dopo le righe.")


def _storia_anni(anno):
    """Gli anni scritti in una tappa: (primo, ultimo) oppure (None, None) per un secolo."""
    a = [int(x) for x in re.findall(r"\b(\d{3,4})\b", anno or "")]
    if a:
        return min(a), max(a)
    return None, None


def _storia_secolo(anno):
    """Per mettere in ordine i secoli: «XIV secolo» → 1300, «IX secolo a.C.» → -900 (dalla 2.33.3)."""
    m = re.search(r"\b([IVXL]+)\b", anno or "")
    if not m:
        return -5000
    v, prima_ = 0, 0
    for c in reversed(m.group(1)):
        x = {"I": 1, "V": 5, "X": 10, "L": 50}[c]
        v, prima_ = (v - x, prima_) if x < prima_ else (v + x, x)
    return -v * 100 if re.search(r"a\.?\s?c\.?|\bbc\b|avanti", anno, re.I) else (v - 1) * 100


def _storia_controlla(righe, fonti, conflitti, golpe, recenti_anni):
    """Tiene solo le tappe il cui anno sta davvero nella fonte citata."""
    tenute, viste = [], set()
    for riga in (righe or "").splitlines():
        # dalla 2.33.2 si accettano anche le righe a tabella («| T | 1861 | … | F |») e quelle senza la «T» davanti
        p = [x.strip(" *`") for x in riga.strip().lstrip("-•* ").strip("|").split("|")]
        if p and p[0].upper().strip(" .:") == "T":
            p = p[1:]
        if len(p) < 3 or not re.search(r"\d{3,4}|secol|century", p[0], re.I):
            continue
        anno, tappa = p[0][:30], pulisci(p[1], 260)
        fw = p[2].strip().lower()
        f = ("G" if fw.startswith(("g", "pow", "colp")) else "U" if fw.startswith(("u", "ucdp")) else "F" if fw.startswith(("f", "cia", "world"))
             else "W" if fw.startswith(("w", "wiki")) else "R" if fw.startswith(("r", "fatt", "arch")) else "")
        if f not in "FWUGR" or not fonti.get(f) or len(tappa) < 12:
            continue
        a0, a1 = _storia_anni(anno)
        if a0 is None:
            if not (f in "FW" and re.search(r"secol|century|centuries|\bsec\.", anno + " " + fonti[f], re.I)):
                continue
        elif f in "FW":
            if str(a0) not in fonti[f] or str(a1) not in fonti[f]:
                continue
        elif f == "U":
            if not any(c[0] - 1 <= a0 and a1 <= c[1] + 1 for c in conflitti):
                continue
        elif f == "G":
            if a0 not in {int(g[0][:4]) for g in golpe}:
                continue
        elif f == "R":
            if a0 not in recenti_anni:
                continue
        chiave = (a0, tappa[:40].lower())
        if chiave in viste:
            continue
        viste.add(chiave)
        tenute.append([anno, tappa, f, a0 if a0 is not None else _storia_secolo(anno)])
    tenute.sort(key=lambda x: x[3])
    return [x[:3] for x in tenute[:30]]


def storia_studia(chiavi, cfg, adesso, tel, errori, A=None):
    """Il cervello scrive la cronologia di pochi Stati a giro (prima quelli con avvisi recenti, poi nell'ordine del piano).
    Si rifà dopo «giorni_cronologia» giorni o quando gli archivi portano conflitti o colpi di Stato nuovi."""
    imp = cfg.get("storia", {}) or {}
    ic = cfg.get("cervello", {}) or {}
    if not imp.get("cronologia", True) or not chiavi.get("anthropic_key") or not ic.get("attivo", True):
        return {"fatti": 0, "perche": "cervello spento o senza chiave"}
    conto = _conto_cervello()
    if not _cervello_libero(conto, ic) or conto.get("passo"):
        return {"fatti": 0, "perche": "tetto di spesa o spesa a passo"}
    A = A or _storia_carica()
    perc = MAG("storia", "cronologie.json")
    K = leggi_json(perc, {}) or {}
    paesi = leggi_json(os.path.join(QUI, "paesi.json"), {}) or {}
    ordine = [s for _, l in (cfg.get("piano", {}).get("blocchi") or []) for s in l] or sorted(paesi)
    V_ = leggi_json(os.path.join(DATI, "avvisi.json"), {}) or {}
    due_g = (adesso - timedelta(days=2)).isoformat()
    caldi = [a.get("stato") for a in reversed(V_.get("elenco", [])) if a.get("quando", "") >= due_g and a.get("stato")]
    vecchia = (adesso - timedelta(days=int(imp.get("giorni_cronologia", 180)))).isoformat()

    def firma(st):
        s = (A.get("stati") or {}).get(st, {})
        return [len(s.get("conflitti") or []), len(s.get("golpe") or [])]
    da_fare = []
    for st in list(dict.fromkeys(caldi + ordine)):
        if st not in paesi:
            continue
        k_ = K.get(st) or {}
        if not k_.get("tappe"):
            if k_.get("riprova", "") <= adesso.isoformat() and not (k_.get("nota") == "fonti insufficienti" and k_.get("firma") == firma(st)):
                da_fare.append(st)
        elif k_.get("quando", "") < vecchia or k_.get("firma") != firma(st):
            da_fare.append(st)
    quanti = int(imp.get("stati_per_giro_carica", 3) if spinta(cfg, tel)["piena"] else imp.get("stati_per_giro", 1))
    S_ = leggi_json(os.path.join(DATI, "sapere.json"), {}) or {}
    M_ = leggi_json(os.path.join(DATI, "memoria.json"), {}) or {}
    fatti, ultimo_ = 0, None
    for st in da_fare[:quanti]:
        s = (A.get("stati") or {}).get(st, {})
        conf = s.get("conflitti") or []
        gol = s.get("golpe") or []
        fonti = {"F": _storia_factbook(st, cfg, errori)[:4000]}
        w_ = (S_.get(st) or {}).get("storia") or {}
        fonti["W"] = (w_.get("testo") or "")[:1500]
        fonti["U"] = "\n".join(f"{c[0]}-{c[1]} · {c[2]} · {c[3]} contro {c[4]}" + (f" ({c[5]})" if c[5] else "") + f" · {c[6]} · {c[7]}"
                               + (f" · con l'appoggio di {c[9]}" if c[9] else "") for c in conf[:40])
        fonti["G"] = "; ".join(f"{g[0]} {'riuscito' if g[1] else 'fallito'}" for g in gol[:40])
        mem_ = sorted(M_.get(st) or [], key=lambda x: x[0], reverse=True)[:12]
        fonti["R"] = "\n".join(f"{x[0]} – {x[1]} ({x[2]})" for x in mem_)
        if sum(len(v) for v in fonti.values()) < 200:
            K[st] = {"quando": adesso.isoformat(), "tappe": [], "firma": firma(st), "nota": "fonti insufficienti"}
            continue
        try:
            risposta = chiedi_claude(chiavi, cfg, _storia_domanda(st, fonti), 1800, conto)
            conto["chiamate"] = conto.get("chiamate", 0) + 1
        except SenzaRete:
            raise
        except Exception as e:
            errori.append("Claude (storia di " + st + "): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:160])
            break
        tappe = _storia_controlla(risposta, fonti, conf, gol, {int(x[0][:4]) for x in mem_ if x[0][:4].isdigit()})
        proposte_ = sum(1 for r__ in (risposta or "").splitlines() if r__.count("|") >= 2 and re.search(r"\d{3,4}|secol", r__))
        ultimo_ = [st, proposte_, len(tappe)]
        if not tappe:  # per capire che cosa non va: l'inizio della prima riga proposta finisce nel diario
            ultimo_.append(next((r__.strip()[:140] for r__ in (risposta or "").splitlines() if r__.count("|") >= 2), (risposta or "")[:140]))
        if not tappe:  # nessuna tappa tenuta: si riprova tra un giorno (e si tiene l'inizio della risposta per capire)
            K[st] = {"quando": "", "riprova": (adesso + timedelta(days=1)).isoformat(), "tappe": [], "firma": firma(st),
                     "proposte": proposte_, "risposta": (risposta or "")[:1500]}
            fatti += 1
            continue
        K[st] = {"quando": adesso.isoformat(), "tappe": tappe, "firma": firma(st), "proposte": proposte_,
                 "fonti": {"W": w_.get("url", ""), "F": "https://github.com/factbook/factbook.json/blob/master/"
                           + ((cfg.get("sapere", {}).get("factbook") or {}).get(st) or "") + ".json"},
                 "scartate": max(0, len(re.findall(r"(?m)^\s*[-•*]?\s*T\s*\|", risposta or "")) - len(tappe))}
        fatti += 1
    scrivi_json(os.path.join(DATI, "cervello.json"), conto)
    os.makedirs(os.path.dirname(perc), exist_ok=True)
    scrivi_json(perc, K)
    return {"fatti": fatti, "in_coda": max(0, len(da_fare) - fatti), "con_cronologia": sum(1 for v in K.values() if v.get("tappe")),
            "ultimo": ultimo_}


def scrivi_storia_web(adesso):
    """storia.js per la pagina: per ogni Stato la cronologia, i conflitti (i 40 più recenti), i colpi di Stato, la violenza
    contro i civili e gli scontri tra gruppi armati, e un riassunto."""
    A = _storia_carica()
    K = leggi_json(MAG("storia", "cronologie.json"), {}) or {}
    stati = {}
    for st in set(A.get("stati") or {}) | set(K):
        s = (A.get("stati") or {}).get(st, {})
        c = s.get("conflitti") or []
        g = s.get("golpe") or []
        k = K.get(st) or {}
        stati[st] = {"t": k.get("tappe") or [], "tq": (k.get("quando") or "")[:10], "tf": k.get("fonti") or {},
                     "c": [x[:10] for x in c[:40]], "g": [x[:2] for x in g], "v": (s.get("civili") or [])[:8], "n": (s.get("gruppi") or [])[:8],
                     "r": [len(c), sum(x[7] for x in c), sum(1 for x in g if x[1]), sum(1 for x in g if not x[1]),
                           max((x[1] for x in c), default=None)]}
    if not stati:
        return False
    return _scrivi_se_cambia(os.path.join(WEB, "storia.js"), "window.STORIA=" + json.dumps(
        {"agg": adesso.date().isoformat(), "fonti": STORIA_FONTI, "versioni": A.get("versioni") or {}, "stati": stati},
        ensure_ascii=False, separators=(",", ":")) + ";")


def storia_passo(chiavi, cfg, adesso, tel, errori, leggero):
    """Il lavoro sulla storia dentro il giro: archivi (una volta alla settimana), cronologie (poche a giro), storia.js."""
    imp = cfg.get("storia", {}) or {}
    if not imp.get("attiva", True):
        return None
    A = storia_archivi(cfg, adesso, errori)
    r_ = storia_studia(chiavi, cfg, adesso, tel, errori, A) or {}
    if not leggero or r_.get("fatti"):
        scrivi_storia_web(adesso)
    s_ = A.get("stati") or {}
    r_.update(stati=len(s_), conflitti=sum(len(x.get("conflitti") or []) for x in s_.values()),
              golpe=sum(len(x.get("golpe") or []) for x in s_.values()), archivi=(A.get("quando") or "")[:10])
    return r_


def lavoro_229(archivio, adesso, cfg, chiavi, dati_cielo, dati_calore, tel, errori, leggero):
    """Il lavoro della 2.29 dentro il giro: schede, andamento, avvisi, indice e vettori. Nulla di questo ferma il giro."""
    esito = {}
    S_ = {}
    try:
        S_, esito["schede"] = schede_fatti(archivio, adesso, cfg)
    except Exception as e:
        errori.append(f"Schede dei fatti: {str(e)[:100]}")
    A_ = {}
    try:
        A_ = andamento(archivio, adesso, S_)
    except Exception as e:
        errori.append(f"Andamento: {str(e)[:100]}")
    try:  # dalla 2.30: economia (Banca Mondiale, tassi, valute, materie prime, commercio)
        esito["economia"] = economia(cfg, adesso, errori, secondi=cfg.get("economia", {}).get("secondi", 90))
    except Exception as e:
        errori.append(f"Economia: {str(e)[:100]}")
    try:
        esito["avvisi"] = avvisi(A_, S_, dati_cielo, dati_calore, adesso, cfg, chiavi)
    except Exception as e:
        errori.append(f"Avvisi: {str(e)[:100]}")
    try:  # dalla 2.32: il telefono apre e legge le pagine delle notizie confermate
        esito["articoli"] = leggi_articoli(archivio, adesso, cfg, tel, errori)
    except Exception as e:
        errori.append(f"Lettura degli articoli: {str(e)[:100]}")
    try:  # dalla 2.33: la storia di ogni Stato (archivi UCDP e colpi di Stato, cronologie scritte dal cervello)
        esito["storia"] = storia_passo(chiavi, cfg, adesso, tel, errori, leggero)
    except Exception as e:
        errori.append(f"Storia: {str(e)[:100]}")
    try:
        esito["indice"] = indice_aggiorna(archivio, adesso, cfg, secondi=cfg.get("indice", {}).get("secondi", 45))
    except Exception as e:
        errori.append(f"Indice: {str(e)[:100]}")
    try:
        esito["significato"] = significato_aggiorna(archivio, cfg, tel, errori)
    except Exception as e:
        errori.append(f"Ricerca per significato: {str(e)[:100]}")
    if not leggero:
        try:
            scrivi_schede_web(S_, adesso)
            scrivi_andamento_web(A_, adesso)
            scrivi_economia_web(cfg, adesso)
        except Exception as e:
            errori.append(f"Schede e andamento per la pagina: {str(e)[:100]}")
    S2 = _off_stato()
    S2["lavoro_229"] = {k: v for k, v in esito.items()}
    _off_salva(S2)
    return esito


def _cerca_e_rispondi(chiavi, cfg, conto, errori, chi, perche, q, lingua, giorni=30, pausa=1.0):
    """Cerca una domanda su Google News e fa rispondere il cervello con i soli titoli trovati.
    Restituisce l'esito, oppure None se Google News o il cervello non hanno risposto (si riprova al giro dopo)."""
    titoli, _fatte, fallite = _piano_titoli([("aperta", lingua, q)], giorni, errori, pausa)
    if fallite:
        return None
    titoli = sorted(titoli, key=lambda x: x["iso"], reverse=True)[:30]
    esito = {"q": q, "l": lingua, "perche": perche, "n": len(titoli), "quando": datetime.now(timezone.utc).isoformat(),
             "r": "nessun titolo trovato", "f": []}
    if not titoli:
        return esito
    try:
        risposta = chiedi_claude(chiavi, cfg, (
            f"Domanda ({chi}): {perche or q}\nTitoli trovati cercando «{q}» (numero. data – titolo – fonte):\n" +
            "\n".join(f"{i + 1}. {x['d'] or 'senza data'} – {x['t']} – {x['f']}" for i, x in enumerate(titoli)) +
            "\n\nRispondi in italiano con una riga sola, usando SOLO quello che dicono i titoli, senza giudizi:\n"
            "R | risposta in una o due frasi | numeri dei titoli usati\n"
            "Se i titoli non bastano per rispondere scrivi: R | i titoli non bastano | -"), 500, conto)
        conto["chiamate"] = conto.get("chiamate", 0) + 1
    except Exception as e:
        errori.append("Claude (domanda di un collegamento): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:160])
        return None
    esito["r"] = "i titoli non bastano"
    for riga in risposta.splitlines():
        p = [x.strip(" *`") for x in riga.strip().lstrip("-•* ").split("|")]
        if len(p) >= 2 and p[0].upper().strip(" .:") == "R" and len(p[1]) > 5:
            esito["r"], esito["f"] = pulisci(p[1], 400), _piano_fonti(p[2] if len(p) > 2 else "", titoli, 3)
            break
    return esito


def _quadro_voci(archivio, P, adesso, imp):
    """Le voci che il cervello mette in ordine: notizie confermate da più fonti (ultime 24 ore, una per fatto)
    e fatti del lavoro a piano (ultimi 30 giorni), prima i più rilevanti."""
    voci, visti = [], set()
    da_ = (adesso - timedelta(hours=imp.get("ore_notizie", 24))).isoformat()
    conf = sorted((v for v in archivio.get("notizie", {}).values() if v.get("conf") and (v.get("data_iso") or "") >= da_),
                  key=lambda v: ((v.get("nf") or 1), v.get("data_iso") or ""), reverse=True)
    for v in conf:
        g = v.get("gr") or v.get("u")
        if g in visti:
            continue
        visti.add(g)
        voci.append({"tipo": "notizia", "t": pulisci(v.get("it") or v.get("t", ""), 220), "u": v.get("u", ""),
                     "fonte": v.get("fonte", ""), "d": (v.get("data_iso") or "")[:10], "paesi": (v.get("paesi") or [])[:3],
                     "nf": v.get("nf") or 1})
        if len(voci) >= imp.get("notizie", 60):
            break
    limite = (adesso - timedelta(days=imp.get("giorni_piano", 30))).date().isoformat()
    fatti = []
    for st_, sch in (P.get("stati") or {}).items():
        for campo, tipo in (("accordi", "accordo"), ("appalti", "appalto"), ("intel", "intelligence"), ("puzzle", "puzzle")):
            for x in sch.get(campo, []):
                if (x.get("d") or "") < limite:
                    continue
                if campo == "puzzle":
                    tipo, t = x.get("tema") or "puzzle", x.get("cosa", "")
                elif campo == "accordi":
                    t = (x.get("con", "") + ": " if x.get("con") else "") + x.get("cosa", "")
                elif campo == "appalti":
                    t = f"{x.get('acq', '')} da {x.get('forn', '')}: {x.get('ogg', '')}" + (f" ({x['val']})" if x.get("val") else "")
                else:
                    t = (x.get("ente", "") + ": " if x.get("ente") else "") + x.get("cosa", "")
                f0 = (x.get("f") or [["", "", "", ""]])[0]
                fatti.append({"tipo": tipo, "t": pulisci(t, 260), "u": f0[1] if len(f0) > 1 else "", "fonte": f0[0] if f0 else "",
                              "d": x.get("d", ""), "paesi": [st_], "r": x.get("r")})
    fatti.sort(key=lambda x: (x.get("r") or 0, x["d"]), reverse=True)
    return voci + fatti[:imp.get("fatti_piano", 50)]


def quadro(chiavi, cfg, archivio, leggero, errori):
    """Il cervello guarda il quadro intero, ogni 3 ore (nei giri completi): mette in scaletta le notizie e i fatti più
    rilevanti, cerca che cosa li collega e, per ogni collegamento, scrive la domanda da verificare. Nei giri dopo il
    programma cerca quelle domande su Google News e scrive la risposta con le fonti, una o due a giro.
    Restituisce [voci in scaletta, collegamenti nuovi, domande cercate]."""
    imp, imp_c = cfg.get("quadro", {}), cfg.get("cervello", {})
    esito = [0, 0, 0]
    if not imp.get("attivo", True) or not chiavi.get("anthropic_key") or not imp_c.get("attivo", True):
        return esito
    perc = os.path.join(DATI, "quadro.json")
    Q = leggi_json(perc, {})
    Q.setdefault("collegamenti", [])
    conto = _conto_cervello()
    adesso = datetime.now(timezone.utc)
    ultimo = Q.get("iso", "")
    dovuto = ultimo < (adesso - timedelta(hours=imp.get("ore", 3) * (1.4 if leggero else 0.8))).isoformat()
    P = leggi_json(os.path.join(DATI, "piano.json"), {})
    # 1. scaletta e collegamenti
    if dovuto and _cervello_libero(conto, imp_c):
        voci = _quadro_voci(archivio, P, adesso, imp)
        if len(voci) >= 8:
            gia = [c["testo"] for c in Q["collegamenti"][:12]]
            domanda = (
                "Sei l'analista di un archivio pubblico di difesa e geopolitica. Qui sotto ci sono le notizie confermate da più "
                "fonti nelle ultime 24 ore e i fatti che il programma ha trovato sulla stampa negli ultimi 30 giorni (accordi, "
                "appalti, intelligence, energia, trasporti, cibo e risorse, IA militare). Sono i pezzi di un puzzle: cerca "
                "soprattutto i collegamenti tra temi e Stati diversi. Formato: numero. [tipo] data – Stati – testo – fonte. Usa SOLO queste voci: non "
                "aggiungere nulla che sai per conto tuo.\n\n"
                "PARTE 1, SCALETTA: scegli da 10 a 15 voci, le più rilevanti per la difesa e la sicurezza, in ordine dalla più "
                "importante. Una riga per voce:\n"
                "R | numero | rilevanza da 1 a 5 | perché conta, in una frase in italiano\n"
                "(5 = cambia gli equilibri tra Stati o in una regione; 3 = importante per uno Stato; 1 = minore).\n\n"
                "PARTE 2, COLLEGAMENTI: fino a 5 collegamenti tra voci diverse, ognuno con almeno due numeri. Per esempio lo "
                "stesso Stato o la stessa azienda in fatti diversi, un accordo e un appalto che si spiegano a vicenda, una mossa "
                "di uno Stato e la risposta di un altro. Una riga per collegamento:\n"
                "K | numeri delle voci collegate | Stati coinvolti | il collegamento in una frase in italiano | da 3 a 7 parole "
                "da cercare, senza virgolette | lingua in cui cercare (it, en, oppure la sigla della lingua del posto) | che "
                "cosa vuoi sapere, in italiano\n\n"
                "Regole. Un collegamento è ciò che le voci mostrano, non un'ipotesi: se è solo possibile, comincia con "
                "«possibile collegamento:» e la domanda serve a verificarlo. Niente giudizi, niente previsioni, niente dettagli "
                "operativi, niente nomi di persone private. Non ripetere i collegamenti già trovati. Scrivi solo le righe, "
                "senza titoli e senza commenti.\n" +
                ("\nGIÀ TROVATI:\n" + "\n".join("· " + g for g in gia) + "\n" if gia else "") +
                "\nVOCI\n" + "\n".join(
                    f"{i + 1}. [{v['tipo']}] {v['d'] or 'senza data'} – {', '.join(v['paesi']) or '-'} – {v['t']} – {v['fonte']}"
                    + (f" ({v['nf']} fonti)" if v.get("nf", 1) > 1 else "") for i, v in enumerate(voci)))
            try:
                risposta = chiedi_claude(chiavi, cfg, domanda, 2200, conto)
                conto["chiamate"] = conto.get("chiamate", 0) + 1
            except Exception as e:
                errori.append("Claude (quadro): " + re.sub(r"sk-ant-[A-Za-z0-9_-]+", "***", str(e))[:160])
                risposta = None
            if risposta is not None:
                scaletta, nuovi, presi = [], [], set()
                for riga in risposta.splitlines():
                    p = [x.strip(" *`") for x in riga.strip().lstrip("-•* ").split("|")]
                    sigla = p[0].upper().strip(" .:)") if p else ""
                    if sigla == "R" and len(p) >= 4:
                        n_ = re.search(r"\d+", p[1])
                        r_ = re.search(r"[1-5]", p[2])
                        if n_ and r_ and 0 < int(n_.group(0)) <= len(voci) and int(n_.group(0)) not in presi and len(p[3]) > 8:
                            presi.add(int(n_.group(0)))
                            scaletta.append(dict(voci[int(n_.group(0)) - 1], r=int(r_.group(0)), perche=pulisci(p[3], 240)))
                    elif sigla == "K" and len(p) >= 7:
                        nums = list(dict.fromkeys(int(x) for x in re.findall(r"\d+", p[1]) if 0 < int(x) <= len(voci)))
                        q = " ".join(re.sub(r'[<>{}\\"«»()]|https?:\S*', " ", p[4]).split())
                        if len(nums) >= 2 and len(p[3]) > 15 and 2 <= len(q.split()) <= 9 and len(q) <= 110:
                            nuovi.append({"iso": adesso.isoformat(), "stati": pulisci(p[2], 120), "testo": pulisci(p[3], 300),
                                          "voci": [{k: voci[i - 1].get(k) for k in ("tipo", "t", "u", "fonte", "d", "paesi")}
                                                   for i in nums[:5]],
                                          "q": q, "l": re.sub(r"[^a-zA-Z-]", "", p[5])[:5].lower() or "en",
                                          "perche": pulisci(p[6], 200)})
                if scaletta or nuovi:
                    Q["iso"], Q["agg"] = adesso.isoformat(), datetime.now().strftime("%d/%m %H:%M")
                    if scaletta:
                        Q["scaletta"] = scaletta[:15]
                    Q["collegamenti"] = (nuovi[:5] + Q["collegamenti"])[:imp.get("tieni", 40)]
                    esito[:2] = [len(scaletta), len(nuovi[:5])]
                else:
                    errori.append(f"Claude (quadro): risposta senza righe R o K ({len(risposta)} caratteri)")
    # 2. le domande dei collegamenti: si cercano e si risponde, poche a giro
    riposo = P.get("riposo", "") > adesso.isoformat()  # Google News sta rifiutando: aspetta anche il quadro
    for _ in range(0 if riposo else imp.get("risposte_per_giro", 1)):
        c = next((c for c in reversed(Q["collegamenti"]) if c.get("q") and not c.get("risposta")), None)
        if not c or not _cervello_libero(conto, imp_c):
            break
        try:
            r = _cerca_e_rispondi(chiavi, cfg, conto, errori, c.get("stati") or "collegamento", c.get("perche") or c["testo"],
                                  c["q"], c.get("l", "en"), imp.get("giorni_risposte", 30), cfg.get("piano", {}).get("pausa", 1.0))
        except SenzaRete:
            errori.append("rete assente: le domande dei collegamenti riprendono al prossimo giro")
            break
        if r is None:
            break
        c["risposta"] = r
        esito[2] += 1
    if esito != [0, 0, 0]:
        scrivi_json(perc, Q)
    scrivi_json(os.path.join(DATI, "cervello.json"), conto)  # anche una richiesta andata male si paga: il conto resta giusto
    return esito


def quadro_pagina():
    """Il quadro per la pagina (live.json): la scaletta e gli ultimi collegamenti con domande e risposte."""
    Q = leggi_json(os.path.join(DATI, "quadro.json"), {})
    if not Q.get("scaletta") and not Q.get("collegamenti"):
        return None
    return {"agg": Q.get("agg", ""), "iso": Q.get("iso", ""), "scaletta": Q.get("scaletta", []), "collegamenti": Q.get("collegamenti", [])[:15]}


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
    Q_ = leggi_json(os.path.join(DATI, "quadro.json"), {})
    if Q_.get("collegamenti"):
        print("\n6. Collegamenti tra i fatti (quadro delle " + Q_.get("agg", "") + ") e le domande per verificarli:")
        for c in Q_["collegamenti"][:8]:
            r_ = (c.get("risposta") or {}).get("r")
            print(f"   {c.get('stati', '')}: {c['testo']}\n      domanda [{c.get('l', '')}] {c['q']} — " + (f"→ {r_}" if r_ else "da cercare"))
    if Q_.get("scaletta"):
        print("\n7. Le più rilevanti adesso (scaletta del cervello):")
        for v in Q_["scaletta"][:10]:
            print(f"   R{v.get('r', '?')} {v.get('t', '')} ({v.get('fonte', '')}) — {v.get('perche', '')}")
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
    print(f"Trovati finora: {rs['accordi']} accordi e patti, {rs['appalti']} appalti e contratti, {rs.get('intel', 0)} fatti sui "
          f"servizi di intelligence, in {rs['con_scheda']} Stati.")
    print("Prossimi:", ", ".join(rs["prossimi"]))
    print("Ultimi lavorati (accordi / appalti / intelligence / titoli letti):")
    for riga_ in rs["ultimi"]:
        s, _q, a, c, t = riga_[:5]
        print(f"   {s:<24} {a:>3} / {c:>3} / {(riga_[6] if len(riga_) > 6 else 0):>3} / {t:>3}")
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
            cfg_r = leggi_json(os.path.join(QUI, "config.json"), {})
            passo_ = passo_minuti(cfg_r)
            sp_r = spinta(cfg_r)  # dalla 2.32: in carica e al fresco i giri sono più fitti (spinta › ogni_minuti_carica)
            if sp_r["ogni_minuti"]:
                passo_ = min(passo_, sp_r["ogni_minuti"])
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


def _offline_locale(adesso):
    """Senza rete il telefono non sta fermo (dalla 2.27.2): a ogni giro traduce con l'officina i titoli rimasti (se il
    traduttore è acceso: in carica e al fresco), mette nel magazzino i giorni maturi e scrive il rapporto se è l'ora.
    Tutto resta sul telefono e va su GitHub quando la rete torna."""
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    fatto, errori = {}, []
    try:
        archivio = leggi_json(os.path.join(DATI, "archivio.json"), {"notizie": {}})
        S = officina(cfg, telefono(), archivio, errori, adesso)
        if S and S.get("fase") == "attivo" and S.get("ok_tel"):
            ric = Riconoscitore(leggi_json(os.path.join(QUI, "paesi.json"), {}))
            da = sorted((v for v in archivio.get("notizie", {}).values() if not v.get("it") and not v.get("gia_it")
                         and (NON_LATINO.search(v.get("t") or "") or v.get("lg") or lingua_titolo(v.get("t") or "") != "it")),
                        key=lambda v: v.get("data_iso") or "", reverse=True)
            o_ = cfg.get("officina", {})
            cfg_o = dict(cfg, officina=dict(o_, secondi_per_giro=o_.get("secondi_offline", 420), per_giro=o_.get("per_giro_offline", 120)))
            officina_traduci.fatti = 0
            officina_traduci(da, cfg_o, ric, errori)
            fatto["tradotti"] = getattr(officina_traduci, "fatti", 0)
            if fatto["tradotti"]:
                scrivi_json(os.path.join(DATI, "archivio.json"), archivio)
        fatto["magazzino"] = magazzino(archivio, cfg, adesso)
        fatto["rapporto"] = bool(rapporto_12(cfg))
    except Exception as e:
        fatto["errore"] = str(e)[:120]
    if errori:
        fatto["avvisi"] = errori[:3]
    return fatto


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
    locale_ = _offline_locale(adesso)
    st_r["locale"] = {"quando": adesso.isoformat(), **{k: v for k, v in locale_.items() if k != "magazzino"}}
    if locale_.get("tradotti"):
        st_r["tradotti_offline"] = st_r.get("tradotti_offline", 0) + locale_["tradotti"]
    if st_r.get("lavoro", "") >= (adesso - timedelta(minutes=55)).isoformat():
        scrivi_json(perc_r, st_r)
        print(f"Rete assente dal {da_}. Intanto il telefono ha tradotto {locale_.get('tradotti', 0)} titoli con l'officina"
              f"{' e ha scritto il rapporto' if locale_.get('rapporto') else ''}; il resto del lavoro senza rete è già fatto "
              f"in quest'ora: riprovo al prossimo giro.")
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
            v["conf"] = confermata(fonti, v.get("fonte"))
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
                 "offline": [confermate_dopo - confermate_prima, nuovi_m, st_r.get("tradotti_offline", 0)],
                 "mag": locale_.get("magazzino")})
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
    st_r["tradotti_offline"] = 0  # contati nel diario: si riparte da zero per l'ora dopo
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
    # dalla 2.32 i feed si scaricano in parallelo (spinta: 8 alla volta in carica, 4 fuori carica; allo stesso sito sempre
    # una richiesta ogni 2 secondi) e si leggono uno alla volta, nell'ordine di sempre
    sp_giro = spinta(cfg)
    da_leggere = []
    for f in elenco_fonti(cfg, mie, auto):
        st = auto["stato"].get(f["url"], {})
        if da_saltare(f, st, adesso, leggero):
            continue
        if a_ritmo and leggero and st.get("prossimo", "") > adesso.isoformat():
            saltate_ritmo += 1
            continue
        # nei giri leggeri si chiede al sito «solo se è cambiato» (risposta 304: nessun dato scaricato);
        # nei giri completi si rilegge sempre tutto, così un sito che risponde male non resta fermo
        cond_ = {}
        if leggero and st.get("etag"):
            cond_["If-None-Match"] = st["etag"]
        if leggero and st.get("lm"):
            cond_["If-Modified-Since"] = st["lm"]
        da_leggere.append((f, cond_))

    def _prendi(f, cond_):
        r_ = {}
        try:
            return "ok", scarica(f["url"], intestazioni=cond_ or None, risposta=r_), r_
        except urllib.error.HTTPError as e_:
            return ("304", None, r_) if e_.code == 304 else ("errore", e_, r_)
        except Exception as e_:  # anche SenzaRete: la si rilancia sotto, nel posto di sempre
            return "errore", e_, r_

    t_feed = time.time()
    pool_feed = concurrent.futures.ThreadPoolExecutor(max_workers=sp_giro["paralleli"])
    futuri_feed = [pool_feed.submit(_prendi, f, c_) for f, c_ in da_leggere]
    for (f, cond_), fu_ in zip(da_leggere, futuri_feed):
        esito_, val_, risp_ = fu_.result()
        st = auto["stato"].get(f["url"], {})
        prima_ult = st.get("ultimo", "")
        st["ultimo"] = adesso.isoformat()
        contati_f = contati
        try:
            if esito_ == "errore":
                raise val_
            grezzo_ = val_ if esito_ == "ok" else None
            if esito_ == "304":
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
    pool_feed.shutdown(wait=False, cancel_futures=True)
    secondi_feed = round(time.time() - t_feed)

    tappa("feed")
    # 3. Telegram: canali pubblici ufficiali (dichiarazioni di parte, non conferme)
    tg_citati = {}
    auto.setdefault("telegram", [])
    leggi_tg = dovuto("telegram")
    yt_citati = {}
    for c in (cfg.get("telegram", []) + mie.get("telegram", [])) if leggi_tg else []:
        if not canale_ok(auto, "tg:" + c["canale"], cfg):
            continue  # dalla 2.30: un canale che non risponde da 12 giri si riprova una volta al giorno
        try:
            for t, link, data in telegram(c["canale"], tg_citati, yt_citati):
                notizia(c.get("tema", "Voci ufficiali (Telegram)"), t, link, data, "Telegram · " + c.get("chi", c["canale"]),
                        livello="di parte", lv="C")
            canale_esito(auto, "tg:" + c["canale"], True, cfg, adesso)
        except Exception as e:
            canale_esito(auto, "tg:" + c["canale"], False, cfg, adesso)
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
            if not canale_ok(auto, "tg:" + c["canale"], cfg):
                continue
            try:
                for t, link, data in telegram(c["canale"], None, yt_citati)[-12:]:
                    if FILTRO.search(t) or NON_LATINO.search(t):
                        notizia("Telegram: canali trovati da soli (da valutare)", t, link, data, "Telegram · " + c["chi"],
                                livello="da valutare", lv="D")
                canale_esito(auto, "tg:" + c["canale"], True, cfg, adesso)
            except Exception as e:
                canale_esito(auto, "tg:" + c["canale"], False, cfg, adesso)
                errori.append(f"Telegram {c['canale']}: {e}")
            time.sleep(1)
    try:  # dalla 2.30: canali YouTube citati nei messaggi Telegram
        yt_nuovi_giro = scopri_youtube(auto, yt_citati, cfg, adesso, errori) if leggi_tg else []
    except Exception as e:
        yt_nuovi_giro = []
        errori.append(f"Scoperta YouTube: {str(e)[:80]}")

    tappa("telegram")
    # 4. YouTube: feed dei canali, senza chiave
    for h in (cfg.get("youtube", []) + mie.get("youtube", []) + [x["cid"] for x in auto.get("youtube", [])]) if dovuto("video") else []:
        if not canale_ok(auto, "yt:" + h, cfg):
            continue
        try:
            cid = h if h.startswith("UC") else id_canale(h, canali)
            for titolo, link, data, autore, _ in leggi_rss(scarica("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid)):
                aggiungi("video", {"t": titolo, "u": solo_http(link), "data_iso": data or adesso.isoformat(),
                                   "canale": autore or h, "paesi": ric.trova(titolo)})
            canale_esito(auto, "yt:" + h, True, cfg, adesso)
        except Exception as e:
            canale_esito(auto, "yt:" + h, False, cfg, adesso)
            errori.append(f"YouTube {h}: {e}")

    tappa("video")
    # 4b. Sapere: pochi Stati a giro studiati su Wikipedia (forze armate e storia); dalla 2.23 anche i servizi di intelligence
    stati_studiati = sapere(cfg, paesi, errori, adesso)
    try:
        studia_servizi(cfg, errori, adesso)
    except Exception as e:  # i servizi non devono mai fermare il giro
        errori.append(f"Servizi: {e}")
    stati_basi = 0
    try:  # siti militari: uno Stato a giro, da Wikidata
        stati_basi = siti_militari(cfg, paesi, errori, adesso)
    except Exception as e:
        errori.append(f"Siti militari: {e}")

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
    try:  # dalla 2.27: l'officina fa un passo (installa, scarica, accende, prova) solo in carica e al fresco
        stato_off = officina(cfg, telefono(), archivio, errori, adesso)
    except Exception as e:
        stato_off = None
        errori.append(f"Officina: {str(e)[:120]}")
    officina_traduci.fatti = 0
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
    try:  # dalla 2.26: tutto resta sul telefono, compresso (magazzino), con tetto, pulizia e copia di sicurezza
        stato_mag = magazzino(archivio, cfg, adesso)
    except Exception as e:
        stato_mag = None
        errori.append(f"Magazzino: {str(e)[:120]}")
    analisi["segnali"] = segnali_stati(archivio, recente, analisi, dati_cielo, dati_calore)
    analisi["peggiora"] = andamento_stati(archivio)
    analisi["miglioratore"] = miglioratore(cfg, chiavi, analisi, auto, errori)
    scrivi_json(os.path.join(DATI, "fonti_auto.json"), auto)  # con i siti proposti dal cervello
    mem_nuovi, mem_totale = memoria_stati(archivio, adesso, cfg)
    scrivi_json(os.path.join(DATI, "analisi.json"), analisi)
    try:  # dalla 2.29: schede dei fatti, andamento per Stato, avvisi, indice istantaneo e ricerca per significato
        esito_229 = lavoro_229(archivio, adesso, cfg, chiavi, dati_cielo, dati_calore, telefono(), errori, leggero)
    except Exception as e:
        esito_229 = {}
        errori.append(f"Lavoro 2.29: {str(e)[:120]}")
    # 6b. Quadro (dalla 2.23): scaletta di rilevanza, collegamenti tra i fatti e le domande per verificarli
    try:
        quadro_giro = quadro(chiavi, cfg, archivio, leggero, errori)
    except SenzaRete:
        quadro_giro = [0, 0, 0]
    except Exception as e:  # il quadro non deve mai fermare il giro
        quadro_giro = [0, 0, 0]
        errori.append(f"Quadro: {e}")

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
        "quadro": quadro_pagina(),
        "servizi": sum(1 for v_ in leggi_json(os.path.join(DATI, "servizi.json"), {}).values() if v_.get("sintesi")),
        "motori": {k_: {c_: v_.get(c_) for c_ in ("prove", "titoli", "errori", "pausa", "ultimo_errore")} for k_, v_ in _motori().items()},
        "spesa_lavori": {k_: leggi_json(os.path.join(DATI, "cervello.json"), {}).get(k_) or {} for k_ in ("lavori_oggi", "lavori_mese")},
        "canali": canali_stato(cfg, mie, auto, adesso),
        "officina": dict({k_: _off_stato().get(k_) for k_ in ("fase", "prova", "tradotti_oggi", "tradotti_tutti", "errore")},
                         economia=(_off_stato().get("lavoro_229") or {}).get("economia"),
                         filtro={k_: (leggi_json(FILTRO_FILE(), {}) or {}).get(k_) for k_ in
                                 ("attivo", "esempi", "tenuti", "scartati", "copre", "errore", "scartati_oggi", "scartati_tutti",
                                  "controlli", "perche", "addestrato")}),
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
        "spinta": [int(sp_giro["piena"]), sp_giro["paralleli"], len(da_leggere), secondi_feed],
        "passo": bool(conto_c.get("passo")), "sosp": [len(sosp_), sum(x[1] for x in sosp_)],
        "piano": piano_giro + [rs_p.get("i", 0), rs_p.get("totale", 0), rs_p.get("passata", 0)],
        "intel": [getattr(passo_piano, "intel", 0), rs_p.get("intel", 0)],
        "quadro": quadro_giro, "servizi": live.get("servizi", 0),
        "puzzle": [getattr(passo_piano, "puzzle", 0), sum((rs_p.get("puzzle") or {}).values())], "basi": stati_basi,
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
        "mag": stato_mag, "bing": getattr(_piano_titoli, "bing", 0),
        "off": [(stato_off or {}).get("fase", ""), getattr(officina_traduci, "fatti", 0)] if stato_off else None,
        "articoli": [(esito_229.get("articoli") or {}).get(c_) for c_ in ("letti", "poco_testo", "provati", "in_coda", "totale")],
        "storia": [(esito_229.get("storia") or {}).get(c_) for c_ in ("fatti", "con_cronologia", "in_coda", "stati", "conflitti", "golpe", "ultimo")],
        "x229": [esito_229.get("schede"), (esito_229.get("avvisi") or [None])[0], (esito_229.get("indice") or {}).get("totale"),
                 (esito_229.get("significato") or {}).get("fatti"), (esito_229.get("significato") or {}).get("fase")],
    })
    scrivi_json(os.path.join(DATI, "diario.json"), diario[-120:])
    live["diario"] = [{k: v for k, v in x.items() if k not in ("ricerche", "siti")} for x in diario[-60:]]  # per la pagina
    try:
        shutil.copyfile(os.path.join(DATI, "diario.json"), os.path.join(WEB, "diario.json"))
        scrivi_memoria_web(leggi_json(os.path.join(DATI, "memoria.json"), {}), cfg)
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
    # dalla 2.29 le notifiche sul telefono le manda avvisi() (dentro lavoro_229), con i picchi e i fatti gravi
    avvisa_bot(chiavi, live, segnali)
    try:
        r_ = rapporto_12(cfg)
        if r_:
            print("Rapporto delle 12 ore scritto:", r_["verdetto"])
    except Exception as e:  # il rapporto non deve mai fermare il giro
        print("  - rapporto delle 12 ore:", e)
    if cfg.get("repo_git") or chiavi.get("repo_git") or cfg.get("repo_pubblico"):
        sincronizza(cfg, chiavi, solo_diario=leggero, nel_giro=True)


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


def _js_dati(percorso):
    """Legge un file di dati del sito («window.NOME = {...};») e ne restituisce il contenuto."""
    with open(percorso, encoding="utf-8") as f:
        testo = f.read()
    # il primo oggetto dopo «=»: dalla 2.26 memoria.js ne contiene tre (MEMORIA, MEMORIA_N, MEMORIA_FILE)
    return json.JSONDecoder().raw_decode(testo, testo.index("{"))[0]


def _iso_da_mostra(testo, adesso):
    """Il contrario di mostra_data: «19/11 16:08» (ora del telefono) torna una data ISO; l'anno è il più vicino nel passato."""
    m = re.match(r"^(\d\d)/(\d\d) (\d\d):(\d\d)$", testo or "")
    if not m:
        return None
    g, me, h, mi = map(int, m.groups())
    qui = adesso.astimezone()
    for anno in (qui.year, qui.year - 1):
        try:
            d = datetime(anno, me, g, h, mi).astimezone()
        except (ValueError, OverflowError, OSError):
            continue
        if d <= qui + timedelta(hours=1):
            return d.astimezone(timezone.utc).isoformat()
    return None


def ricostruisci(cartella="", dentro_giro=False):
    """Dopo una reinstallazione (Termux disinstallato, telefono nuovo): rimette sul telefono la pagina e i dati che il
    programma aveva già mandato su GitHub: diario, memoria degli Stati, sapere, ultime notizie con le loro traduzioni,
    lavoro a piano, fonti scoperte, conto della spesa e la copia di riserva dei file di lavoro. Le chiavi no: non escono
    mai dal telefono e vanno rimesse a mano. Ciò che il telefono ha di più nuovo resta: i dati si uniscono, non si
    sostituiscono. Si può lanciare più volte senza danni."""
    os.makedirs(DATI, exist_ok=True)
    os.makedirs(WEB, exist_ok=True)
    cfg = leggi_json(os.path.join(QUI, "config.json"), {})
    # da dove: la cartella indicata, lo scambio con GitHub, il repository scaricato a mano; se no lo scarica (è pubblico)
    candidati = [cartella, os.path.join(DATI, "repo"), os.path.dirname(QUI), os.path.expanduser("~/pangeo")]
    R = next((os.path.abspath(c) for c in candidati if c and os.path.exists(os.path.join(c, "diario.json"))
              and os.path.exists(os.path.join(c, "index.html"))), "")
    if not R:
        pubblico = cfg.get("repo_pubblico", "")
        if not pubblico:
            print("Non trovo i dati salvati. Indica la cartella del repository scaricato:  python castello.py ricostruisci ~/pangeo")
            return False
        R = os.path.join(DATI, "repo")
        try:
            os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
            shutil.rmtree(R, ignore_errors=True)
            subprocess.run(["git", "clone", "--depth", "1", pubblico, R], check=True)
        except (OSError, subprocess.CalledProcessError) as e:
            print("Non riesco a scaricare da GitHub i dati salvati (rete assente, o git non installato):", str(e)[:120])
            return False
    blocco = os.path.join(DATI, "aggiorna.lock")
    if not dentro_giro:  # mai insieme a un giro: scriverebbero gli stessi file
        avvisato = False
        for _ in range(360):
            try:
                with open(blocco, encoding="utf-8") as f:
                    chi_ = f.read().strip()
                if time.time() - os.path.getmtime(blocco) >= 45 * 60 or (chi_.isdigit() and not _vivo_pid(chi_)):
                    break
            except OSError:
                break
            if not avvisato:
                print("Un giro è in corso: aspetto che finisca, poi rimetto i dati. Può volerci un quarto d'ora: lascia Termux aperto.", flush=True)
                avvisato = True
            time.sleep(5)
        else:
            print("Il giro in corso non finisce: riprova tra qualche minuto.")
            return False
        with open(blocco, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    try:
        return _ricostruisci(R, cfg)
    finally:
        if not dentro_giro:
            try:
                os.remove(blocco)
            except OSError:
                pass


def _ricostruisci(R, cfg):
    adesso = datetime.now(timezone.utc)
    fatto = []

    def passo(nome, funzione):  # un pezzo che non riesce non ferma gli altri
        try:
            esito = funzione()
            if esito:
                fatto.append(esito)
        except Exception as e:
            print(f"  {nome}: non riuscito ({str(e)[:110]}). Il resto continua.")

    D = leggi_json(os.path.join(DATI, "diario.json"), [])
    noti_ = {x.get("iso") for x in D}
    prima = sorted((x for x in leggi_json(os.path.join(R, "diario.json"), [])
                    if isinstance(x, dict) and x.get("iso") and x["iso"] not in noti_), key=lambda x: x["iso"])
    nuovo = bool(prima) and len(D) < 6  # telefono appena (re)installato: i suoi file di lavoro valgono meno della copia di riserva

    def _pagina():
        n = 0
        for nome in ["index.html", "tabelle.html"] + APP_FILE:
            if os.path.exists(os.path.join(R, nome)):
                shutil.copyfile(os.path.join(R, nome), os.path.join(WEB, nome))
                n += 1
        if os.path.isdir(os.path.join(R, "tabelle")):
            shutil.copytree(os.path.join(R, "tabelle"), os.path.join(WEB, "tabelle"), dirs_exist_ok=True)
        return f"la pagina con le tabelle ({n} file)" if n else ""

    def _diario():
        if not prima:
            return ""
        scrivi_json(os.path.join(DATI, "diario.json"), sorted(D + prima, key=lambda x: x.get("iso") or "")[-120:])
        shutil.copyfile(os.path.join(DATI, "diario.json"), os.path.join(WEB, "diario.json"))
        return f"il diario ({len(prima)} giri di prima)"

    def _conto():
        # la spesa del cervello fatta prima della reinstallazione si somma a quella di adesso: i tetti restano veri.
        # I contatori nel diario salgono soltanto: vale il più alto del mese (e di oggi) tra i giri che qui mancavano.
        if not prima:
            return ""
        perc = os.path.join(DATI, "cervello.json")
        conto = _conto_cervello()
        if conto.get("ricostruito") == prima[-1]["iso"]:
            return ""
        mese, oggi_, del_mese, di_oggi = datetime.now().strftime("%Y-%m"), datetime.now().date(), 0.0, 0.0
        for x in prima:
            try:
                quando_ = datetime.fromisoformat(x["iso"]).astimezone()
            except ValueError:
                continue
            if quando_.strftime("%Y-%m") == mese:
                del_mese = max(del_mese, x.get("usd_mese") or 0)
            if quando_.date() == oggi_:
                di_oggi = max(di_oggi, x.get("usd_oggi") or 0)
        if conto.get("mese") != mese:
            conto["mese"], conto["usd_mese"] = mese, 0.0
        conto["usd_mese"] = round((conto.get("usd_mese") or 0.0) + del_mese, 5)
        conto["usd_oggi"] = round((conto.get("usd_oggi") or 0.0) + di_oggi, 5)
        conto["ricostruito"] = prima[-1]["iso"]
        scrivi_json(perc, conto)
        if not del_mese:
            return ""
        return f"il conto della spesa ({conto['usd_oggi']:.2f} $ oggi, {conto['usd_mese']:.2f} $ nel mese)"

    def _sapere():
        S_r = _js_dati(os.path.join(R, "sapere.js"))
        S_ = leggi_json(os.path.join(DATI, "sapere.json"), {})
        n = 0
        for st_, v in S_r.items():
            if not isinstance(v, dict):
                continue
            mio = S_.get(st_)
            if not isinstance(mio, dict) or len(v) > len(mio):
                S_[st_] = v
                n += 1
                continue
            for k in ("forze", "storia", "factbook"):  # la stessa voce era già tradotta: la traduzione non si paga due volte
                a, b = mio.get(k), v.get(k)
                if isinstance(a, dict) and isinstance(b, dict) and b.get("testo_it") and not a.get("testo_it") \
                        and a.get("testo") == b.get("testo"):
                    a["testo_it"] = b["testo_it"]
                    n += 1
        if n:
            scrivi_sapere(S_)
        return f"il sapere ({sum(1 for v in S_.values() if len(v) > 1)} Stati studiati)" if n else ""

    def _memoria():
        M_r = _js_dati(os.path.join(R, "memoria.js"))
        for f_ in glob.glob(os.path.join(R, "memoria", "*.json")):  # dalla 2.26: tutti i fatti stanno nei file per Stato
            x_ = leggi_json(f_, {})
            if x_.get("stato") and isinstance(x_.get("fatti"), list):
                M_r[x_["stato"]] = x_["fatti"]
        perc = os.path.join(DATI, "memoria.json")
        M = leggi_json(perc, {})
        n = 0
        for st_, righe in M_r.items():
            mie_ = list(M.get(st_, []))
            url_ = {x[4] for x in mie_ if len(x) > 4 and x[4]}
            parole_ = [set(x[5].split()) for x in mie_ if len(x) > 5]
            for x in righe if isinstance(righe, list) else []:
                if not isinstance(x, list) or len(x) < 5 or (x[4] and x[4] in url_):
                    continue
                p_ = parole(x[1])
                if any(len(p_ & q) >= 0.4 * max(len(p_ | q), 1) for q in parole_):
                    continue  # lo stesso fatto c'è già
                mie_.append([x[0], x[1], x[2], x[3], x[4], " ".join(sorted(p_)), x[5] if len(x) > 5 else ""])
            if mie_:  # si contano solo i fatti che restano davvero (al massimo 40 per Stato, i più recenti)
                dopo_ = sorted(mie_, key=lambda x: x[0], reverse=True)[:cfg.get("memoria_per_stato", 40)]
                n += sum(1 for x in dopo_ if x not in M.get(st_, []))
                M[st_] = dopo_
        if n:
            scrivi_json(perc, M)
            scrivi_memoria_web(M, cfg)
        return f"la memoria degli Stati ({n} fatti confermati)" if n else ""

    def _archivio():
        live_r = leggi_json(os.path.join(R, "live.json"), {})
        perc = os.path.join(DATI, "archivio.json")
        arch = leggi_json(perc, None)
        if not isinstance(arch, dict) or "notizie" not in arch:
            arch = {"notizie": {}, "video": {}, "attesa": {}}
        limite = (adesso - timedelta(days=cfg.get("giorni_archivio", 7))).isoformat()
        n = tradotte = 0
        for tipo in ("notizie", "video"):
            arch.setdefault(tipo, {})
            for w in live_r.get(tipo) or []:
                iso = _iso_da_mostra(w.get("data"), adesso)
                if not iso or iso < limite or not w.get("u") or not w.get("t"):
                    continue
                k = hashlib.sha1((w["u"] + w["t"]).encode("utf-8")).hexdigest()[:16]
                if k in arch[tipo]:
                    if w.get("it") and not arch[tipo][k].get("it"):  # la traduzione fatta prima è già pagata: resta
                        arch[tipo][k]["it"] = w["it"]
                        tradotte += 1
                    continue
                v = {a: b for a, b in w.items() if a != "data"}
                v["data_iso"], v["visto"] = iso, iso
                arch[tipo][k] = v
                (arch.get("attesa") or {}).pop(k, None)  # era già stata scelta dal cervello: non torna in sala d'attesa
                n += 1
        if n or tradotte:
            scrivi_json(perc, arch)
        if not os.path.exists(os.path.join(DATI, "live.json")) and live_r.get("notizie"):
            # telefono senza ancora un giro: la pagina mostra subito gli ultimi dati salvati (segnati come vecchi, così il giro parte)
            for nome, dove in (("live.json", DATI), ("live.js", WEB)):
                if os.path.exists(os.path.join(R, nome)):
                    shutil.copyfile(os.path.join(R, nome), os.path.join(dove, nome))
                    os.utime(os.path.join(dove, nome), (time.time() - 7200, time.time() - 7200))
        return f"le ultime notizie ({n}, con le traduzioni già fatte)" if n else ""

    def _riserva():
        ris = leggi_json(os.path.join(R, "riserva.json"), {})
        n = 0
        for nome, cont in (ris.get("file") or {}).items():
            if nome not in RISERVA + RISERVA_STORICI or nome == "cervello.json" or not isinstance(cont, (dict, list)):
                continue
            perc = os.path.join(DATI, nome)
            mio = leggi_json(perc, None)
            if mio is None:
                scrivi_json(perc, cont)
            elif nome in RISERVA_STORICI and isinstance(mio, dict) and isinstance(cont, dict):
                aggiunti = 0  # i campioni di prima tornano accanto a quelli nuovi: il confronto con «di solito» riparte subito
                for p_, serie in cont.items():
                    visti_ = {x[0] for x in mio.get(p_, [])}
                    in_piu = [x for x in serie if isinstance(x, list) and len(x) == 2 and x[0] not in visti_]
                    if in_piu:
                        mio[p_] = sorted(mio.get(p_, []) + in_piu)
                        aggiunti += len(in_piu)
                if not aggiunti:
                    continue
                scrivi_json(perc, mio)
            elif nome == "fonti_mie.json" and isinstance(mio, dict) and isinstance(cont, dict):
                cambiato = False  # le fonti aggiunte da te si uniscono sempre
                for tipo_, lista in cont.items():
                    for voce in lista if isinstance(lista, list) else []:
                        if voce not in mio.setdefault(tipo_, []):
                            mio[tipo_].append(voce)
                            cambiato = True
                if not cambiato:
                    continue
                scrivi_json(perc, mio)
            elif not nuovo or type(mio) is not type(cont):
                continue
            elif nome == "fonti_auto.json":
                viste = {f.get("url") for f in cont.get("scoperte", [])}
                cont["scoperte"] = cont.get("scoperte", []) + [f for f in mio.get("scoperte", []) if f.get("url") not in viste]
                cont["stato"] = dict(cont.get("stato", {}), **mio.get("stato", {}))
                scrivi_json(perc, cont)
            elif nome == "storico_stati.json":
                for p_, giorni in cont.items():
                    d_ = mio.setdefault(p_, {})
                    for g_, c_ in giorni.items():
                        d_[g_] = max(d_.get(g_, 0), c_)
                scrivi_json(perc, mio)
            else:
                scrivi_json(perc, cont)
            n += 1
        return f"la copia di riserva del {ris.get('giorno', '?')} ({n} file di lavoro)" if n else ""

    def _scoperte():
        # senza copia di riserva: le fonti trovate da solo si riprendono dall'elenco pubblicato con i dati live
        live_r = leggi_json(os.path.join(R, "live.json"), {})
        perc = os.path.join(DATI, "fonti_auto.json")
        auto = leggi_json(perc, {})
        auto.setdefault("scoperte", [])
        mie = leggi_json(os.path.join(DATI, "fonti_mie.json"), {})
        note = elenco_fonti(cfg, mie, auto)
        url_, dom_ = {f["url"] for f in note}, {dominio(f["url"]) for f in note}
        semi = {(st_, ente_) for st_, ente_, _u in cfg.get("scoperta", {}).get("semi", [])}
        n = 0
        for f in (live_r.get("fonti") or {}).get("scoperte") or []:
            u = solo_http(f.get("url"))
            if not u or u in url_ or dominio(u) in dom_:
                continue
            voce = {"nome": f.get("nome") or dominio(u), "url": u, "tema": "Scoperte automatiche (da valutare)",
                    "aggiunta": f.get("aggiunta", "")}
            m = re.match(r"^(.*) \(([^()]+)\)$", voce["nome"])
            if m and (m.group(2), m.group(1)) in semi:  # voce ufficiale di uno Stato: torna com'era
                voce.update(tema="Voci ufficiali e organismi internazionali", stato=m.group(2), lv="C", liv="di parte", ufficiale=True)
                lg_ = lingue_di(m.group(2))
                if lg_ and lg_[0][0] not in ("it", "en"):
                    voce["lingua"] = lg_[0][0]
            elif m and m.group(2) == "indirizzo nuovo":
                orig = next((x for x in cfg.get("rss", []) + mie.get("rss", []) if x.get("nome") == m.group(1)), None)
                if orig:
                    voce.update(tema=orig.get("tema", voce["tema"]), sostituisce=orig["url"])
                    if orig.get("stato"):
                        voce["stato"] = orig["stato"]
                    if orig.get("lv") in ("A", "B"):
                        voce["promossa"] = True
            auto["scoperte"].append(voce)
            url_.add(u)
            dom_.add(dominio(u))
            n += 1
        if n:
            scrivi_json(perc, auto)
        return f"le fonti trovate da solo ({n})" if n else ""

    def _piano():
        sorgente = os.path.join(R, "piano.js")
        if not os.path.exists(sorgente):
            return ""
        P_r = _js_dati(sorgente)
        for f_ in glob.glob(os.path.join(R, "piano", "*.json")):  # dalla 2.26 piano.js è leggero: le schede piene sono qui
            x_ = leggi_json(f_, {})
            if x_.get("stato") and (P_r.get("stati") or {}).get(x_["stato"]) is not None:
                P_r["stati"][x_["stato"]] = {k: v for k, v in x_.items() if k not in ("stato", "pieno")}
        perc = os.path.join(DATI, "piano.json")
        P = leggi_json(perc, {})
        if (P_r.get("passata", 1), len(P_r.get("stati") or {})) <= (P.get("passata", 1), len(P.get("stati") or {})):
            return ""
        P_n = {"stati": P_r.get("stati") or {}, "i": P_r.get("i", 0), "passata": P_r.get("passata", 1),
               "ultimi": P_r.get("ultimi") or [], "agg": P_r.get("agg", ""), "inizio": P.get("inizio") or adesso.isoformat()}
        for st_, v in (P.get("stati") or {}).items():  # ciò che il telefono ha lavorato dopo la reinstallazione resta
            P_n["stati"].setdefault(st_, v)
        scrivi_json(perc, P_n)
        scrivi_piano_web(P_n, cfg, len(piano_ordine(cfg, leggi_json(os.path.join(QUI, "paesi.json"), {}))) or 198)
        return f"il lavoro a piano (Stati già lavorati: {len(P_n['stati'])})"

    def _magazzino():  # dalla 2.26: il magazzino torna dalla copia di sicurezza nella memoria condivisa, se c'è
        copia_ = os.path.join(_mag_copia_dir(cfg.get("magazzino", {})), "magazzino")
        if not os.path.isdir(copia_):
            return ""
        n_ = 0
        for radice_, _, nomi_ in os.walk(copia_):
            for nome_m in nomi_:
                src_ = os.path.join(radice_, nome_m)
                dst_ = MAG(os.path.relpath(src_, copia_))
                if not os.path.exists(dst_):
                    os.makedirs(os.path.dirname(dst_), exist_ok=True)
                    shutil.copyfile(src_, dst_)
                    n_ += 1
        return f"il magazzino dalla copia di sicurezza ({n_} file)" if n_ else ""

    def _storici():
        if os.path.exists(os.path.join(WEB, "index.html")) and prima:
            ripristina(os.path.join(WEB, "index.html"))
        return ""

    for nome_, funzione_ in (("pagina", _pagina), ("diario", _diario), ("conto della spesa", _conto), ("sapere", _sapere),
                             ("memoria", _memoria), ("ultime notizie", _archivio), ("copia di riserva", _riserva),
                             ("fonti scoperte", _scoperte), ("lavoro a piano", _piano), ("magazzino", _magazzino),
                             ("storici", _storici)):
        passo(nome_, funzione_)
    if fatto:
        print("Rimesso dal salvataggio su GitHub: " + "; ".join(fatto) + ".")
    else:
        print("Niente da rimettere: il telefono ha già tutto ciò che c'è su GitHub.")
    ch_ = leggi_json(os.path.join(DATI, "chiavi.json"), {})
    mancano = [t_ for t_, k_ in (("la chiave di Claude  →  python castello.py chiave anthropic_key", "anthropic_key"),
                                 ("il token di GitHub  →  bash github.sh", "repo_git")) if not ch_.get(k_)]
    if mancano:
        print("Le chiavi non stanno su GitHub (per sicurezza) e vanno rimesse a mano. Mancano: " + ";  ".join(mancano) + ".")
    return True


# ----------------------------------------------------------------------------- comandi

def sincronizza(cfg=None, chiavi=None, solo_diario=False, nel_giro=False):
    """Scambia file con il repository su GitHub: scarica l'ultima versione della pagina e del programma e carica i dati
    live. Senza token (dopo una reinstallazione, prima di  bash github.sh) lavora in sola lettura sul repository pubblico:
    il telefono riceve pagina, tabelle e programma, ma non manda nulla."""
    cfg = cfg or leggi_json(os.path.join(QUI, "config.json"), {})
    chiavi = chiavi or leggi_json(os.path.join(DATI, "chiavi.json"), {})
    repo = chiavi.get("repo_git") or cfg.get("repo_git") or cfg.get("repo_pubblico")
    if not repo:
        print("Nessun repository: bash github.sh")
        return
    sola_lettura = "@" not in repo.split("//", 1)[-1].split("/", 1)[0]  # indirizzo senza token: si può solo leggere
    os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")  # un token scaduto dà un errore, mai una domanda che ferma il giro
    cartella = os.path.join(DATI, "repo")
    os.makedirs(WEB, exist_ok=True)
    try:
        if os.path.isdir(os.path.join(cartella, ".git")):  # il token può essere cambiato (o arrivato) dopo il primo scarico
            subprocess.run(["git", "-C", cartella, "remote", "set-url", "origin", repo], check=False)
        if not os.path.isdir(os.path.join(cartella, ".git")):
            shutil.rmtree(cartella, ignore_errors=True)
            subprocess.run(["git", "clone", "--depth", "1", repo, cartella], check=True)
        elif subprocess.run(["git", "-C", cartella, "pull", "--ff-only"]).returncode != 0:
            # la cartella di scambio si è disallineata (es. un invio non riuscito): si riallinea al repository.
            # Non si perde nulla: i dati del telefono vengono ricopiati qui sotto a ogni giro.
            subprocess.run(["git", "-C", cartella, "fetch", "--depth", "1", "origin"], check=True)
            subprocess.run(["git", "-C", cartella, "reset", "--hard", "FETCH_HEAD"], check=True)
        # nuove versioni del programma, se Claude le ha messe nel repository (cartella programma/)
        cambiati = []
        avvisato = False
        for nome in ("castello.py", "config.json", "paesi.json", "mappa.json", "LEGGIMI.txt", "piano_base.json") + tuple(sorted(SCRIPT)):
            src = os.path.join(cartella, "programma", nome)
            dst = os.path.join(QUI, nome)
            if os.path.exists(src) and (not os.path.exists(dst) or open(src, "rb").read() != open(dst, "rb").read()):
                try:  # controllo di salute: un file rotto non sostituisce mai quello che funziona
                    if nome.endswith(".py"):
                        compile(open(src, encoding="utf-8").read(), nome, "exec")
                    elif nome.endswith(".json"):
                        json.load(open(src, encoding="utf-8"))
                    elif nome.endswith(".sh") and not open(src, "rb").read(2) == b"#!":
                        raise ValueError("non inizia come uno script")
                except (SyntaxError, ValueError) as e:
                    print(f"Scartato {nome} arrivato da GitHub: non è valido ({str(e)[:80]}). Resta la versione di prima.")
                    continue
                e_codice = nome.endswith(".py") or (nome.endswith(".sh")
                                                    and hashlib.sha256(open(src, "rb").read()).hexdigest() != SCRIPT.get(nome))
                if e_codice and cfg.get("codice_nuovo", "chiedi") == "chiedi":
                    # l'umano resta l'interruttore: il codice nuovo aspetta il tuo sì
                    os.makedirs(os.path.join(DATI, "in_attesa"), exist_ok=True)
                    shutil.copyfile(src, os.path.join(DATI, "in_attesa", nome))
                    if not avvisato:
                        print("C'è una versione nuova del programma: NON è stata installata. Per accettarla:  python castello.py approva")
                        avvisato = True
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
        elif not sola_lettura and os.path.exists(os.path.join(WEB, "index.html")):
            # repository nuovo: ci mette il Castello del telefono, così il sito pubblico parte subito
            shutil.copyfile(os.path.join(WEB, "index.html"), nuova)
            subprocess.run(["git", "-C", cartella, "add", "index.html"], check=True)
        # file dell'app (icona, installazione, funzionamento senza rete): li aggiunge se mancano, da una parte o dall'altra
        for nome in APP_FILE:
            dest = os.path.join(cartella, nome)
            if os.path.exists(dest) and not os.path.exists(os.path.join(WEB, nome)):
                shutil.copyfile(dest, os.path.join(WEB, nome))
            if sola_lettura:
                continue
            if not os.path.exists(dest) and os.path.exists(os.path.join(WEB, nome)):
                shutil.copyfile(os.path.join(WEB, nome), dest)
                subprocess.run(["git", "-C", cartella, "add", nome], check=True)
        # tabelle aperte (CSV e JSON con date e fonti): sul sito pubblico si leggono senza account
        if os.path.exists(os.path.join(cartella, "tabelle.html")):  # le prepara Claude nel repository: il telefono le riceve
            shutil.copyfile(os.path.join(cartella, "tabelle.html"), os.path.join(WEB, "tabelle.html"))
            if os.path.isdir(os.path.join(cartella, "tabelle")):
                shutil.copytree(os.path.join(cartella, "tabelle"), os.path.join(WEB, "tabelle"), dirs_exist_ok=True)
        # telefono reinstallato: nel repository ci sono giri che qui mancano. Prima di mandare qualcosa si riprende ciò che
        # era stato salvato (diario, memoria, sapere, notizie): il sito pubblico non perde mai la sua storia.
        diario_qui = leggi_json(os.path.join(DATI, "diario.json"), [])
        if len(diario_qui) < 120 and {x.get("iso") for x in leggi_json(os.path.join(cartella, "diario.json"), [])
                                      if isinstance(x, dict)} - {x.get("iso") for x in diario_qui}:
            ricostruisci(cartella, dentro_giro=nel_giro)
        if sola_lettura:
            print("Sincronizzazione in sola lettura: pagina e programma sono aggiornati. Per mandare i dati al sito pubblico "
                  "serve il token:  bash github.sh")
            return
        # copia di riserva dei file di lavoro (niente chiavi), una volta al giorno o quando aggiungi una fonte tua:
        # con questa e con i dati qui sotto,  python castello.py ricostruisci  rimette tutto dopo una reinstallazione
        if not solo_diario:
            try:
                ris_v = leggi_json(os.path.join(cartella, "riserva.json"), {})
                oggi_r = datetime.now().date().isoformat()
                mie_r = leggi_json(os.path.join(DATI, "fonti_mie.json"), None)
                if ris_v.get("giorno") != oggi_r or (ris_v.get("file") or {}).get("fonti_mie.json") != mie_r:
                    ris_n = {"giorno": oggi_r, "versione": VERSIONE, "nota": "Copia di riserva dei file di lavoro di PanGeo "
                             "(niente chiavi): serve a ripartire dopo una reinstallazione.", "file": {}}
                    for nome in RISERVA:
                        cont_r = leggi_json(os.path.join(DATI, nome), None)
                        if cont_r is not None:
                            ris_n["file"][nome] = cont_r
                    for nome in RISERVA_STORICI:  # basta un campione all'ora per ritrovare «com'era di solito»
                        cont_r = leggi_json(os.path.join(DATI, nome), None)
                        if isinstance(cont_r, dict):
                            ris_n["file"][nome] = {p_: list({x[0][:13]: x for x in serie}.values())
                                                   for p_, serie in cont_r.items() if any(x[1] for x in serie)}
                    with open(os.path.join(cartella, "riserva.json"), "w", encoding="utf-8") as f:
                        json.dump(ris_n, f, ensure_ascii=False, separators=(",", ":"))
                    subprocess.run(["git", "-C", cartella, "add", "riserva.json"], check=True)
            except (OSError, ValueError, subprocess.CalledProcessError) as e:
                print("Copia di riserva non riuscita (il resto va avanti):", str(e)[:80])
        # dopo un giro leggero su GitHub va solo il diario (pochi KB): i dati grossi ci vanno ogni 3 ore, così il
        # repository non cresce tre volte più in fretta
        for nome in (("diario.json", "rapporto.json", "rapporti.json", "avvisi.json") if solo_diario else
                     ("live.json", "live.js", "sapere.js", "memoria.js", "piano.js", "servizi.js", "basi.js", "diario.json",
                      "rapporto.json", "rapporti.json", "avvisi.json", "andamento.js", "schede.js", "economia.js", "storia.js")):
            sorgente = os.path.join(DATI if nome.endswith(".json") else WEB, nome)
            if os.path.exists(sorgente):
                shutil.copyfile(sorgente, os.path.join(cartella, nome))
                subprocess.run(["git", "-C", cartella, "add", nome], check=True)
        for cart_ in (() if solo_diario else ("memoria", "piano")):  # dalla 2.26: un file per Stato (git manda solo i cambiati)
            if os.path.isdir(os.path.join(WEB, cart_)):
                shutil.copytree(os.path.join(WEB, cart_), os.path.join(cartella, cart_), dirs_exist_ok=True)
                subprocess.run(["git", "-C", cartella, "add", cart_], check=True)
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
        if self.path.split("?")[0] == "/api/cerca":  # dalla 2.26: la pagina sul telefono cerca in tutto il magazzino
            qs_ = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            try:
                if (qs_.get("modo") or [""])[0] == "significato":  # dalla 2.29: per significato, in tutte le lingue
                    ris_ = significato_cerca((qs_.get("q") or [""])[0][:200], (qs_.get("stato") or [None])[0],
                                             massimo=int((qs_.get("max") or ["30"])[0]))
                    ris_ = ris_ if ris_ is not None else {"errore": "la ricerca per significato non è ancora pronta"}
                else:
                    ris_ = cerca((qs_.get("q") or [""])[0][:120], (qs_.get("stato") or [None])[0],
                                 giorni=int((qs_.get("giorni") or ["120"])[0]), massimo=int((qs_.get("max") or ["60"])[0]))
            except Exception as e:
                ris_ = {"errore": str(e)[:120]}
            corpo = json.dumps(ris_, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
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
    threading.Thread(target=_scaricatore, daemon=True).start()  # dalla 2.28: il modello dell'officina
    threading.Thread(target=_lavoratore_significati, daemon=True).start()  # dalla 2.31: vettori nel tempo libero
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
        valore = getpass.getpass(f"Incolla la chiave «{a[1]}» e premi Invio (non si vede, è normale): ").strip().strip("'\"")
        if valore and a[1] == "anthropic_key" and not valore.startswith("sk-ant-"):
            # si dice solo di che tipo è, mai che cosa c'è scritto
            tipo_ = ("è l'ID della chiave (inizia con apikey_), non la chiave" if valore.startswith("apikey_") else
                     "è un token di GitHub" if valore.startswith(("ghp_", "github_pat_")) else
                     "è un indirizzo, non la chiave" if valore.startswith("http") else "non è una chiave di Claude")
            print(f"Quello che hai incollato {tipo_}: NON l'ho salvato. La chiave vera inizia con sk-ant- e si vede una volta\n"
                  "sola, quando la crei: https://platform.claude.com/settings/keys  →  «Create key»  →  «Copy». Poi rilancia questo comando.")
        elif valore:
            cmd_chiave(a[1], valore)
        else:
            print("Nessuna chiave: niente è cambiato.")
    elif comando == "approva":
        attesa_ = os.path.join(DATI, "in_attesa")
        src_ = os.path.join(attesa_, "castello.py")
        script_ = [n for n in sorted(os.listdir(attesa_)) if n.endswith(".sh")] if os.path.isdir(attesa_) else []
        if not os.path.exists(src_) and not script_:
            print("Nessuna versione in attesa.")
        else:
            os.makedirs(os.path.join(DATI, "copie"), exist_ok=True)
            for nome_ in script_:  # gli script arrivati con la versione: stessa regola, copia di quello di prima
                if os.path.exists(os.path.join(QUI, nome_)):
                    shutil.copyfile(os.path.join(QUI, nome_), os.path.join(DATI, "copie", nome_ + ".prima"))
                shutil.move(os.path.join(attesa_, nome_), os.path.join(QUI, nome_))
            if script_:
                print("Script aggiornati:", ", ".join(script_))
            if os.path.exists(src_):
                compile(open(src_, encoding="utf-8").read(), "castello.py", "exec")
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
            # si dice solo di che tipo è, mai che cosa c'è scritto (lo schermo finisce spesso in una foto)
            print("Chiave salvata:", "del tipo giusto (inizia con sk-ant-)" if k_.startswith("sk-ant-") else
                  "NON è una chiave di Claude" + (": è l'ID (apikey_...), non la chiave" if k_.startswith("apikey_") else "")
                  + ". Rimettila:  python castello.py chiave anthropic_key")
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
    elif comando == "cerca" and len(a) > 1:
        st_c = a[a.index("--stato") + 1] if "--stato" in a and a.index("--stato") + 1 < len(a) else None
        parole_c = [x for i_, x in enumerate(a[1:], 1) if x != "--stato" and not (i_ > 1 and a[i_ - 1] == "--stato")]
        ris_ = cerca(" ".join(parole_c), st_c, massimo=40)
        print(f"{len(ris_)} risultati per «{' '.join(parole_c)}»" + (f" ({st_c})" if st_c else "") + ":")
        for r_ in ris_:
            print(f"  {r_.get('d', '')} · {', '.join((r_.get('p') or [])[:3])} · {r_.get('dove', '')}" + (" · confermata" if r_.get("c") else ""))
            print(f"    {r_.get('t', '')}")
            print(f"    {r_.get('f') or ''} {r_.get('u') or ''}")
    elif comando == "officina":
        cfg_o = leggi_json(os.path.join(QUI, "config.json"), {})
        att_o = os.path.join(DATI, "in_attesa", "castello.py")
        v_att = ""
        if os.path.exists(att_o):
            m_ = re.search(r'^VERSIONE = "([^"]+)"', open(att_o, encoding="utf-8", errors="replace").read(), re.M)
            v_att = m_.group(1) if m_ else "?"
        print(f"PanGeo {VERSIONE}" + (f" · in attesa la {v_att}: scrivi «python castello.py approva»" if v_att and v_att != VERSIONE else ""))
        if len(a) > 1 and a[1] == "prova":  # prova subito; con «senza-carica» anche staccato dal caricatore (sempre al fresco)
            senza_c = "senza-carica" in a
            S_ = _off_stato()
            S_.pop("prova", None)
            _off_salva(S_)
            t0_, tel0_ = time.time(), telefono()
            print(f"Prima: batteria {tel0_.get('batteria')}%, {tel0_.get('temp')} gradi, in carica: {'sì' if tel0_.get('in_carica') else 'no'}")
            for _ in range(12):
                er_ = []
                tel_o = telefono()
                if senza_c:
                    tel_o = dict(tel_o, in_carica=True)  # solo per questa prova, chiesta a mano
                S_ = officina(cfg_o, tel_o, leggi_json(os.path.join(DATI, "archivio.json"), {}), er_, datetime.now(timezone.utc)) or {}
                parte_ = OFF("modello.gguf.part")
                mb_ = f" ({round(os.path.getsize(parte_) / 1e6)} MB su {round(OFFICINA_MODELLO['byte'] / 1e6)})" if os.path.exists(parte_) else ""
                print("Officina:", S_.get("fase", "spenta") + mb_, *(er_ or []))
                if S_.get("prova") or not S_.get("ok_tel") or "scarico" in S_.get("fase", "") or "aspetto" in S_.get("fase", ""):
                    break
                time.sleep(15)  # il traduttore si sta accendendo
            tel1_ = telefono()
            print(f"Dopo {round((time.time() - t0_) / 60, 1)} minuti: batteria {tel1_.get('batteria')}%, {tel1_.get('temp')} gradi")
            if senza_c:
                _off_ferma(S_)  # staccato dal caricatore il traduttore non resta acceso
                _off_salva(S_)
        S_ = _off_stato()
        print("Officina del telefono:", S_.get("fase", "non ancora partita"), "· batteria e temperatura permettono di lavorare:",
              "sì" if S_.get("ok_tel") else "no")
        if S_.get("prova"):
            pr_ = S_["prova"]
            print(f"  prova del {pr_['quando'][:16]}: {pr_['titoli']} titoli, {pr_['secondi_a_titolo']} secondi a titolo")
            for lg_, v_ in sorted(pr_.get("lingue", {}).items(), key=lambda x: -x[1]):
                print(f"    {NOMI_LINGUE.get(lg_, lg_)}: somiglianza con il cervello {v_}" + ("  ← la fa il telefono" if lg_ in pr_.get("buone", []) else ""))
        if S_.get("tradotti_tutti"):
            print(f"  tradotti gratis dal telefono: {S_.get('tradotti_oggi', 0)} oggi, {S_['tradotti_tutti']} in tutto")
        if S_.get("errore"):
            print("  ultimo errore:", S_["errore"])
        sc_ = leggi_json(OFF("scarico.json"), {}) or {}
        if sc_ and not os.path.exists(OFF("modello.gguf")):
            print(f"  scarico del modello (lo fa il cuore di PanGeo): {sc_.get('stato')} · {sc_.get('mb', 0)} MB su "
                  f"{round(OFFICINA_MODELLO['byte'] / 1e6)}" + (f" · {sc_['vel']} MB/s" if sc_.get("vel") else "")
                  + f" · aggiornato alle {datetime.fromisoformat(sc_['quando']).astimezone().strftime('%H:%M')}"
                  + (f" · errore: {sc_['errore']}" if sc_.get("errore") else ""))
        fi_ = leggi_json(FILTRO_FILE(), {}) or {}
        if fi_:
            print(f"Filtro della sala d'attesa: {fi_.get('esempi', 0)} esempi ({fi_.get('tenuti', 0)} tenuti dal cervello, "
                  f"{fi_.get('scartati', 0)} scartati) · " + (f"scarta da solo il {round((fi_.get('copre') or 0) * 100)}% dei titoli "
                  f"inutili, errore misurato {round((fi_.get('errore') or 0) * 100, 1)}% · oggi {fi_.get('scartati_oggi', 0)} titoli "
                  f"risparmiati" if fi_.get("attivo") else "non scarta ancora: " + (fi_.get("perche") or "sta imparando")))
        l229_ = S_.get("lavoro_229") or {}
        if l229_:
            sig_ = l229_.get("significato") or {}
            ind_ = l229_.get("indice") or {}
            print(f"Ricerca per significato: {sig_.get('fase', 'non ancora partita')} · fatti con il vettore: {sig_.get('fatti', 0)}"
                  + (" · modello: " + ("pronto" if os.path.exists(OFF(SIGNIFICATO_MODELLO["file"])) else "da scaricare (lo fa il cuore)")))
            if ind_:
                print(f"Indice istantaneo: {ind_.get('totale', 0)} testi ({ind_.get('motore', '?')}), {ind_.get('nuovi', 0)} nuovi nell'ultimo giro")
            print(f"Schede dei fatti nuove nell'ultimo giro: {l229_.get('schede', 0)} · avvisi nuovi: {(l229_.get('avvisi') or [0])[0]}")
            so_ = l229_.get("storia") or {}
            if so_:
                print(f"Storia: archivi del {so_.get('archivi') or '?'} ({so_.get('conflitti', 0)} conflitti e {so_.get('golpe', 0)} colpi di Stato in "
                      f"{so_.get('stati', 0)} Stati) · cronologie scritte: {so_.get('con_cronologia', 0)}, in coda {so_.get('in_coda', 0)}"
                      + (f" · {so_['perche']}" if so_.get("perche") else ""))
            ar_ = l229_.get("articoli") or {}
            if ar_:
                print(f"Articoli letti nell'ultimo giro: {ar_.get('letti', 0)} su {ar_.get('provati', 0)} aperti ({ar_.get('poco_testo', 0)} con poco "
                      f"testo: pagamento o cookie) · in coda {ar_.get('in_coda', 0)} · in tutto {ar_.get('totale', 0)}")
        cs_ = S_.get("cuore_significati") or {}
        if cs_:  # dalla 2.32: il lavoro sui vettori tra un giro e l'altro (thread del cuore, dalla 2.31)
            try:
                ora_cs = datetime.fromisoformat(cs_["quando"]).astimezone().strftime("%H:%M")
            except (KeyError, ValueError):
                ora_cs = "?"
            print(f"  in sottofondo (alle {ora_cs}): {cs_.get('fase', '?')} · {cs_.get('nuovi', 0)} vettori nuovi"
                  + (f" in {cs_['secondi']} s ({cs_.get('al_secondo')} al secondo con {cs_.get('thread')} thread)" if cs_.get("secondi") else "")
                  + f" · fatti {cs_.get('fatti', 0)}, notizie recenti {cs_.get('recenti') or 0}" + (f" · {cs_['spinta']}" if cs_.get("spinta") else ""))
        vel_ = S_.get("sig_velocita") or {}
        if vel_:
            print("  velocità misurate: " + " · ".join(f"{k} thread {v.get('v')} vettori al secondo ({v.get('n')} misure)"
                                                      for k, v in sorted(vel_.items(), key=lambda x: int(x[0]))))
        sp_o = spinta(cfg_o)
        print(f"Spinta: {'PIENA' if sp_o['piena'] else 'normale'} ({sp_o['perche']}) · download in parallelo: {sp_o['paralleli']}"
              + (f" · giri ogni {sp_o['ogni_minuti']} minuti · vettori anche delle notizie non confermate, con "
                 f"{_sig_thread(cfg_o.get('officina', {}))} thread" if sp_o["piena"] else " · vettori solo dei fatti confermati"))
        if sc_ and sc_.get("modello") == SIGNIFICATO_MODELLO["nome"] and not os.path.exists(OFF(SIGNIFICATO_MODELLO["file"])):
            print(f"  scarico del modello dei significati: {sc_.get('stato')} · {sc_.get('mb', 0)} MB su {sc_.get('tot', 639)}")
        c_ = leggi_json(os.path.join(DATI, "cervello.json"), {})
        if c_.get("lavori_mese"):
            print("Spesa del cervello questo mese, per lavoro: " + " · ".join(f"{k} {v:.2f} $" for k, v in sorted(c_["lavori_mese"].items(), key=lambda x: -x[1])))
        if c_.get("usd_totale") is not None or c_.get("mesi"):  # dalla 2.33.6: la spesa nel tempo
            print(f"Spesa del cervello: oggi {c_.get('usd_oggi', 0):.2f} $ · mese {c_.get('usd_mese', 0):.2f} $ · in totale "
                  f"{c_.get('usd_totale', c_.get('usd_mese', 0)):.2f} $" + ("" if not c_.get("mesi") else " · mese per mese: " + ", ".join(
                      f"{m[5:]}/{m[:4]} {v:.2f} $" for m, v in sorted(c_["mesi"].items()))))
    elif comando == "storia":  # dalla 2.33: la storia di uno Stato (o il riassunto di tutti)
        A_s = _storia_carica()
        K_s = leggi_json(MAG("storia", "cronologie.json"), {}) or {}
        nome_s = " ".join(a[1:]).strip()
        if not nome_s:
            print(f"Archivi storici del {(A_s.get('quando') or 'mai')[:10]}: {len(A_s.get('stati') or {})} Stati · cronologie scritte: "
                  f"{sum(1 for v in K_s.values() if v.get('tappe'))} su 198")
            print("Per uno Stato:  python castello.py storia Mali")
        else:
            st_s = next((x for x in sorted(set(A_s.get("stati") or {}) | set(K_s)) if x.lower() == nome_s.lower()), nome_s)
            s_s = (A_s.get("stati") or {}).get(st_s, {})
            k_s = K_s.get(st_s) or {}
            print(f"{st_s}: cronologia del {(k_s.get('quando') or 'mai')[:10]}")
            for t_ in k_s.get("tappe") or []:
                print(f"  {t_[0]:>12}  {t_[1]}  [{t_[2]}]")
            c_s, g_s = s_s.get("conflitti") or [], s_s.get("golpe") or []
            print(f"Conflitti armati dal 1946 (UCDP): {len(c_s)}")
            for c_ in c_s[:12]:
                print(f"  {c_[0]}-{c_[1]} · {c_[2]} · {c_[3]} contro {c_[4]}" + (f" ({c_[5]})" if c_[5] else "") + (f" · {c_[7]} anni di guerra" if c_[7] else ""))
            print(f"Colpi di Stato dal 1950 (Powell e Thyne): {len(g_s)}" + ("" if not g_s else " · " + ", ".join(
                f"{g_[0][:4]} {'riuscito' if g_[1] else 'fallito'}" for g_ in g_s[:12])))
            print("Lettere delle fonti: " + " · ".join(f"{k} = {v[0]}" for k, v in STORIA_FONTI.items()))
    elif comando == "avvisi":  # dalla 2.29: gli avvisi delle ultime 48 ore
        V_ = leggi_json(os.path.join(DATI, "avvisi.json"), {}) or {}
        da_ = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        l_ = [x for x in V_.get("elenco", []) if x.get("quando", "") >= da_]
        print(f"Avvisi delle ultime 48 ore: {len(l_)}" + ("" if l_ else " (nessuno)"))
        for x_ in reversed(l_[-20:]):
            print(f"  {datetime.fromisoformat(x_['quando']).astimezone().strftime('%d/%m %H:%M')} · {x_['testo'][:160]}")
    elif comando == "significato":  # dalla 2.29: python castello.py significato carri armati alla Polonia
        r_ = significato_cerca(" ".join(a[1:]))
        if r_ is None or isinstance(r_, dict):
            print("La ricerca per significato non è ancora pronta:", (r_ or {}).get("errore", "manca l'indice dei vettori"))
        else:
            for x_ in r_[:20]:
                print(f"  {x_['d']} · {', '.join(x_['p'][:3])} · {x_['t'][:140]} ({x_['f']})")
    elif comando == "magazzino":
        I_ = leggi_json(MAG("indice.json"), {}) or {}
        g_ = I_.get("giorni", {})
        print(f"Magazzino: {round(_mag_peso() / 1e6, 1)} MB · {len(g_)} giorni ({min(g_) if g_ else '-'} → {max(g_) if g_ else '-'}) · "
              f"{sum(x.get('n', 0) for x in g_.values())} notizie, {sum(x.get('conf', 0) for x in g_.values())} confermate")
        try:
            print(f"Spazio libero sul telefono: {round(shutil.disk_usage(DATI).free / 1e9, 1)} GB · tetto del magazzino: "
                  f"{leggi_json(os.path.join(QUI, 'config.json'), {}).get('magazzino', {}).get('max_gb', 60)} GB")
        except OSError:
            pass
        print("Copia di sicurezza: " + (f"{I_['copia']} (ultima il {I_.get('copia_il', '?')})" if I_.get("copia") else
                                        "spenta. Per accenderla, una volta sola:  termux-setup-storage  (e consenti l'accesso)"))
    elif comando == "rapporto12":
        r_ = rapporto_12(leggi_json(os.path.join(QUI, "config.json"), {}), forza=len(a) > 1 and a[1] == "scrivi") if len(a) > 1 \
            else rapporto_dati(leggi_json(os.path.join(DATI, "diario.json"), []), leggi_json(os.path.join(DATI, "live.json"), {}),
                               leggi_json(os.path.join(DATI, "basi_wd.json"), {}), leggi_json(os.path.join(DATI, "rapporto.json"), {}) or None,
                               cfg=leggi_json(os.path.join(QUI, "config.json"), {}), piano=leggi_json(os.path.join(DATI, "piano.json"), {}))
        print(r_["testo"] if r_ else "Rapporto già scritto per questo turno.")
    elif comando == "rapporto":
        rapporto(int(a[1]) if len(a) > 1 and a[1].isdigit() else 24)
    elif comando == "salute":
        salute()
    elif comando == "bot":
        bot_chat(leggi_json(os.path.join(DATI, "chiavi.json"), {}))
    elif comando == "sincronizza":
        sincronizza()
    elif comando == "ricostruisci":
        sys.exit(0 if ricostruisci(a[1] if len(a) > 1 else "") else 1)
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

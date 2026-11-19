#!/usr/bin/env python3
"""Scrive dentro programma/castello.py l'impronta (SHA-256) degli script .sh di questa versione.
Va lanciato ogni volta che cambia uno script, prima di mandare la versione su GitHub: il telefono installa da solo
solo gli script la cui impronta sta nel programma che hai approvato; gli altri aspettano un nuovo «approva»."""
import hashlib
import os
import re

QUI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "programma")
NOMI = ["avvia.sh", "github.sh", "installa.sh", "ripara.sh"]
firme = {n: hashlib.sha256(open(os.path.join(QUI, n), "rb").read()).hexdigest() for n in NOMI}
perc = os.path.join(QUI, "castello.py")
testo = open(perc, encoding="utf-8").read()
riga = "SCRIPT = {" + ", ".join('"%s": "%s"' % (n, firme[n]) for n in NOMI) + "}"
nuovo, quante = re.subn(r"^SCRIPT = \{.*\}$", riga, testo, count=1, flags=re.M)
assert quante == 1, "riga SCRIPT non trovata in castello.py"
compile(nuovo, perc, "exec")
open(perc, "w", encoding="utf-8").write(nuovo)
print("impronte scritte:", {n: f[:10] for n, f in firme.items()})

#!/usr/bin/env python3
"""Riunisce le due copie della pagina di PanGeo.

Le attività notturne e la rassegna del mattino scrivono sulla pagina di claude.ai (artifact «Castello mentale»):
blocchi «Aggiornamento notturno», righe nuove nei blocchi «Governi aggiornati», AGG. Le estensioni della pagina
(build30, build31…) vanno invece solo nel repository GitHub, dopo la riga-àncora. Le due parti non si toccano:

    prima dell'àncora  → si prende la pagina di claude.ai (dati, schede, blocchi notturni, istantanea)
    dall'àncora in poi → si tiene la pagina del repository (codice e estensioni)

Prima di scrivere controlla che la parte presa da claude.ai contenga tutta quella del repository: nessun blocco
già presente su GitHub deve sparire. Uso:

    python3 tools/riunisci.py index.html pagina_claude_ai.html index.html
"""
import re
import sys

ANCORA = "const $ = s => document.querySelector(s);"
SNAP = re.compile(r"// Istantanea live \(programma Castello\) - inizio.*?// Istantanea live \(programma Castello\) - fine", re.S)
BLOCCO = re.compile(r"^// (Aggiornamento notturno[^\n]*|[A-Z][a-zà]+ estensione[^\n]*|Rassegna[^\n]*)", re.M)


def parti(html):
    s = html.index("<script>") + len("<script>")
    e = html.index("</script>", s)
    js = html[s:e]
    i = js.index(ANCORA)
    return html[:s], js[:i], js[i:], html[e:]


def main(repo_path, claude_path, out_path):
    g = open(repo_path, encoding="utf-8").read()
    a = open(claude_path, encoding="utf-8").read()
    g_testa, g_dati, g_codice, g_coda = parti(g)
    _, a_dati, a_codice, _ = parti(a)
    blocchi_g = set(m.group(1) for m in BLOCCO.finditer(g_dati))
    blocchi_a = set(m.group(1) for m in BLOCCO.finditer(a_dati))
    persi = sorted(blocchi_g - blocchi_a)
    if persi:
        sys.exit("FERMO: la pagina di claude.ai non ha questi blocchi del repository: " + "; ".join(persi))
    # ogni riga della parte dati del repository (tolta l'istantanea) deve esserci anche nella pagina di claude.ai,
    # salvo AGG e le righe che i giri notturni riscrivono di proposito
    righe_a = set(SNAP.sub("", a_dati).splitlines())
    mancano = [r for r in SNAP.sub("", g_dati).splitlines()
               if r.strip() and r not in righe_a and not r.startswith("const AGG")]
    if len(mancano) > 40:
        sys.exit(f"FERMO: {len(mancano)} righe del repository non sono nella pagina di claude.ai (prima: {mancano[0][:120]})")
    nuovi = sorted(blocchi_a - blocchi_g)
    out = g_testa + a_dati + g_codice + g_coda
    open(out_path, "w", encoding="utf-8").write(out)
    print(f"Riunite. Blocchi presi da claude.ai: {len(nuovi)}" + ("".join("\n  " + x[:110] for x in nuovi)))
    if mancano:
        print(f"Righe del repository riscritte dalla pagina di claude.ai: {len(mancano)}")
        for r in mancano[:10]:
            print("  -", r.strip()[:140])
    agg = re.search(r"const AGG = '([^']*)'", a_dati)
    print("AGG:", agg.group(1) if agg else "?")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])

# copy_html.py — kopierer HTML fra Nedlastinger til repo
import shutil, pathlib, sys

# Prover begge mappenavn (norsk og engelsk Windows)
candidates = [
    pathlib.Path(r"C:\Users\HalvardNordang\Nedlastinger\Geopolitisk_Systemanalyse_Investor_2026.html"),
    pathlib.Path(r"C:\Users\HalvardNordang\Downloads\Geopolitisk_Systemanalyse_Investor_2026.html"),
]

src = next((p for p in candidates if p.exists()), None)
dst = pathlib.Path(r"C:\Users\HalvardNordang\Documents\geopolitisk-modell\index.html")

if src:
    shutil.copy2(src, dst)
    print(f"OK: kopiert fra {src.parent.name} til {dst}")
else:
    print("Ikke funnet i Nedlastinger eller Downloads")
    print("Last ned filen fra Claude.ai og prøv igjen")
    sys.exit(1)

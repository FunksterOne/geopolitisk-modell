# Kopiering av HTML til repo (kjøres én gang)
import shutil, pathlib

src = pathlib.Path(r"C:\Users\HalvardNordang\Downloads\Geopolitisk_Systemanalyse_Investor_2026.html")
dst = pathlib.Path(r"C:\Users\HalvardNordang\Documents\geopolitisk-modell\index.html")

if src.exists():
    shutil.copy2(src, dst)
    print(f"OK: kopiert til {dst}")
else:
    print(f"Ikke funnet: {src}")
    print("Last ned filen fra Claude.ai og legg den i Downloads")

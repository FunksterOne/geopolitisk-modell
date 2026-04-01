# Synkroniser daglig brief til GitHub
# Kjøres kl. 06:02 via Windows Task Scheduler (3 min før GitHub Action)
# Plasser dette skriptet der du vil, og pek Task Scheduler mot det.

import shutil
from datetime import date
from pathlib import Path

# ── Konfigurer disse stiene ───────────────────────────────────────────────────
KILDE_MAPPE = Path(r"C:\Users\HalvardNordang\Downloads\Geopolitiske oppdateringer daglig")
REPO_MAPPE  = Path(r"C:\Users\HalvardNordang\Documents\geopolitisk-modell")
# ─────────────────────────────────────────────────────────────────────────────

import subprocess

today     = date.today()
iso_date  = today.strftime("%Y-%m-%d")
filnavn   = f"Geopolitisk oppdatering {iso_date}.md"
kilde     = KILDE_MAPPE / filnavn
maal      = REPO_MAPPE / "briefs" / filnavn

if not kilde.exists():
    print(f"Ingen brief funnet: {kilde}")
    exit(0)

# Kopier brief til repo
shutil.copy2(kilde, maal)
print(f"Kopiert: {filnavn}")

# Git add + commit + push
try:
    subprocess.run(["git", "-C", str(REPO_MAPPE), "add", f"briefs/{filnavn}"], check=True)
    subprocess.run(["git", "-C", str(REPO_MAPPE), "commit", "-m", f"Brief {iso_date}"], check=True)
    subprocess.run(["git", "-C", str(REPO_MAPPE), "push"], check=True)
    print(f"Pushet til GitHub: {filnavn}")
except subprocess.CalledProcessError as e:
    print(f"Git-feil: {e}")

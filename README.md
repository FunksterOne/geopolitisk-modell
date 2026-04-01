# Geopolitisk Systemanalyse Investor 2026

Interaktiv analytisk investormodell som oppdateres daglig med geopolitiske nyheter.

**Live:** https://halvard.github.io/geopolitisk-modell

## Struktur

```
geopolitisk-modell/
├── index.html              ← Selve modellen (publiseres som GitHub Pages)
├── briefs/                 ← Daglige .md-filer, én per dag
│   └── Geopolitisk oppdatering YYYY-MM-DD.md
├── scripts/
│   ├── build.py            ← Bygger ny index.html fra dagens brief
│   └── sync_brief.py       ← Kopierer brief fra lokal mappe og pusher til GitHub
└── .github/workflows/
    └── daglig.yml          ← GitHub Action: kjøres kl. 06:05 automatisk
```

## Daglig flyt

```
Kl. 06:00  Brief genereres til C:\Users\HalvardNordang\Downloads\Geopolitiske oppdateringer daglig\
Kl. 06:02  sync_brief.py kjøres via Task Scheduler → kopierer og pusher til GitHub
Kl. 06:05  GitHub Action kjøres → build.py integrerer brief i index.html → pusher ny HTML
Kl. 06:06  Oppdatert modell er live på https://halvard.github.io/geopolitisk-modell
```

## Oppsett (én gang)

### 1. Opprett repository på GitHub
- Gå til github.com → New repository
- Navn: `geopolitisk-modell`
- Public
- Ikke initialiser med README (vi pusher selv)

### 2. Initialiser lokalt og push
```powershell
cd C:\Users\HalvardNordang\Documents\geopolitisk-modell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/DITT-BRUKERNAVN/geopolitisk-modell.git
git push -u origin main
```

### 3. Aktiver GitHub Pages
- Gå til repository → Settings → Pages
- Source: `Deploy from a branch`
- Branch: `main` / `/ (root)`
- Klikk Save

### 4. Opprett .github/workflows/-mappen på GitHub
- Kopier innholdet fra `github-workflows-daglig.yml`
- Opprett filen `.github/workflows/daglig.yml` i repositoryet via GitHub-nettstedet

### 5. Sett opp Windows Task Scheduler for sync_brief.py
- Åpne Task Scheduler → Create Basic Task
- Navn: `Geopolitisk brief sync`
- Trigger: Daily kl. 06:02
- Action: Start a program
  - Program: `python`
  - Arguments: `C:\Users\HalvardNordang\Documents\geopolitisk-modell\scripts\sync_brief.py`

## Manuell oppdatering
```powershell
cd C:\Users\HalvardNordang\Documents\geopolitisk-modell
python scripts/build.py
git add index.html && git commit -m "Manuell oppdatering" && git push
```

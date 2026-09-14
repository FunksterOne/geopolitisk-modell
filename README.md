# Geopolitisk Systemanalyse Investor 2026

Interaktiv analytisk investormodell for Hormuz-krisen 2026: kalkulator, scenarier,
Trumpometer, makrodata og nyheter, bygget på en syntese av seks rammeverk
(Goodspeed, Fishman, Miran, NDS, NSS og Taleb).

## Struktur

```
geopolitisk-modell/
├── index.html          ← Hele modellen (én fil: HTML, CSS og JavaScript)
├── api/proxy.js        ← Vercel serverless CORS-proxy for RSS-feeder og markedsdata
├── vercel.json         ← Vercel-konfigurasjon (rewrites og CORS-headere for /api)
├── push.bat            ← Manuell publisering fra Windows (git add/commit/push)
└── .github/workflows/
    └── daglig.yml      ← GitHub Action som verifiserer index.html daglig
```

## Slik henger delene sammen

- **Live data** (Brent, WTI, gull, VIX, valuta, RSS-nyheter og Truth Social) hentes i
  nettleseren via `/api/proxy?url=…`. Proxyen slipper bare gjennom vertsnavn på en
  fast liste og følger inntil tre omdirigeringer. Siden må derfor kjøre på Vercel
  for at live-data skal fungere; åpnes filen lokalt eller fra GitHub Pages, viser
  modellen «anslag» og «ingen data» i stedet for å henge.
- **Hormuz-kalkulatoren** bruker live Brent som basispris. Mangler live-pris,
  brukes et statisk anslag (108 $) som merkes tydelig i grensesnittet.
- **Oljeprisgrafen** (dashboard-overlay og Hormuz-modal) regnes av én felles
  funksjon, `hzPricePath()`, slik at alle visninger gir samme forløp.
- **Trumpometer** scorer Trump-relaterte nyheter 0–100. Speedometrene bruker
  `pathLength="100"`, slik at bue-fyllingen alltid er lik scoren.

## Mobil

Alle paneler og modaler brytes til én kolonne under 860 px bredde. Tabeller får
horisontal rulling, tooltips åpnes ved å trykke på «?», og oljeprisgrafen vises
som en egen blokk under kalkulatoren.

## Manuell oppdatering

```powershell
cd C:\Users\HalvardNordang\Documents\geopolitisk-modell
push.bat
```

`push.bat` legger til `index.html`, committer med tidsstempel og pusher til `main`.
Vercel bygger og publiserer automatisk ved push.

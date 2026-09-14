# Geopolitisk Systemanalyse Investor 2026

Interaktiv analytisk investormodell for Hormuz-krisen 2026: kalkulator, scenarier,
raffineringsmarginer, Trumpometer, makrodata og nyheter, bygget på en syntese av seks
rammeverk (Goodspeed, Fishman, Miran, NDS, NSS og Taleb).

## Bokstruktur

Siten leses som en bok. Forsiden «I dag» kommer først, deretter kapitlene i
leserekkefølge:

| Nr | Kapittel | Innhold |
|----|----------|---------|
| 0 | I dag | Dagens oppdatering (`DAGENS`), kalender (`KALENDER`), seks live-priser, Trumpometer, «Da og nå»-stripe, innhold |
| 1 | Krisen og rammeverket | Hva som skjedde, årsakskaskaden, de seks rammeverkene (tidligere guiden) |
| 2 | Da og nå | Grunnlinjen 31. mars mot i dag, hendelse for hendelse |
| 3 | Raffineringsmarginer | Kapasitet, crack-marginer, prognoser, Norge, inflasjon og renter, appendiks |
| 4 | Hormuz-kalkulatoren | Kalkulator, oljeprisgraf, Hormuz-analysen og scenariene A/B/C (tidligere popup-vinduer) |
| 5 | Makrodata | Alle elleve live-markeder og makrokortene |
| 6 | Kinas posisjon | Tidligere Kina-popup |
| 7 | Investeringstips | Tidligere Investeringstips-popup |
| 8 | Nyheter og Trumpometer | Live RSS og Trumpometer i to faner |
| 9 | Om modellen | Rammeverk, Taleb, syntese, analysedokument og «Slik bruker du siten» |

Kapittellisten `KAPITLER` i skript-blokken `book-js` nederst i `index.html` er den
eneste kilden: innholdsfortegnelsen (venstre spalte over 1100 px), kapittellinjen med
«Innhold»-ark og forrige/neste (mobil og nettbrett), kapittelføttene og hash-rutingen
(`#idag`, `#krisen`, `#da-og-naa`, `#raffinering`, `#kalkulator`, `#makro`, `#kina`,
`#kapital`, `#nyheter`, `#om`) genereres derfra. Tilbakeknappen i nettleseren går til
forrige kapittel, og en lenke med hash åpner kapittelet direkte.

Dagens oppdatering på forsiden ligger i objektet `DAGENS` (tittel, ingress, «nytt siste
uke», «hva det betyr», lenker videre) og kalenderen i `KALENDER`, begge i `book-js`.

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
- **Oljeprisgrafen** (ved siden av kalkulatoren og i Hormuz-analysens graf-fane)
  regnes av én felles funksjon, `hzPricePath()`, slik at alle visninger gir samme forløp.
- **Trumpometer** scorer Trump-relaterte nyheter 0–100. Speedometrene bruker
  `pathLength="100"`, slik at bue-fyllingen alltid er lik scoren.

## Grunnlinje og «Da og nå»

Analysen ble skrevet 31. mars 2026 (dag 31 av Hormuz-krisen) og bevares uendret som
modellens grunnlinje. Alt som er datert «31. mars» i Om modellen, Makrodata og
analysedokumentet, refererer til det tidspunktet.

Situasjonen i dag ligger i ett JavaScript-objekt, `SITUASJON`, i `index.html`
(skript-blokken `situasjon-js`). Objektet inneholder

- `grunnlinje` og `naa`: de to datoene som sammenlignes
- `faser`: krisens faser (krig, våpenhvile, kronisk forstyrrelse)
- `indikatorer`: nøkkeltall med verdi ved grunnlinjen (`da`), i dag (`naa`), kilder og
  en kort tolkning
- `hendelser`: daterte hendelser fra februar til i dag
- `modelltest`: hva modellen sa 31. mars, og hva som faktisk skjedde

Alt som vises i kapittelet «Da og nå», stripen på forsiden, Makrodata-kortene,
situasjonsstatusen i Om modellen og kronologien i Hormuz-analysen regnes ut fra dette
objektet. Gruppen `raff` i `indikatorer` (dieselmarginer, lagre, gjennomkjøring,
pumpepriser) og hendelsene om raffinering er hentet fra presentasjonen
«Raffineringsmarginer, Hormuz, september 2026», som også er grunnlaget for kapittel 3. For å oppdatere siden med ny status: endre `naa.dato`, oppdater `naa`-verdiene
i `indikatorer`, og legg nye hendelser nederst i `hendelser`. Ingen annen kode må røres.

Kalkulatorens standardvarighet regnes ut fra faktiske uker siden 28. februar ganget med
en effektiv stengningsgrad (`SN_EFFEKTIV_GRAD`, 0,5 per IEA september 2026), fordi
modellen forutsetter full stengning mens den faktiske stengningen er delvis.

## Mobil

Under 1100 px erstattes innholdsfortegnelsen av en kapittellinje øverst med
«Innhold»-ark og forrige/neste. Under 860 px brytes alle kapitler til én kolonne,
tabeller får horisontal rulling, tooltips åpnes ved å trykke på «?», og oljeprisgrafen
vises som en egen blokk under kalkulatoren.

## Manuell oppdatering

```powershell
cd C:\Users\HalvardNordang\Documents\geopolitisk-modell
push.bat
```

`push.bat` legger til `index.html`, committer med tidsstempel og pusher til `main`.
Vercel bygger og publiserer automatisk ved push.

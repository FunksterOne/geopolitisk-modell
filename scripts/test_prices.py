"""
test_prices.py — Test priskall fra din maskin via Stooq.com
Kjøres manuelt:
    python scripts/test_prices.py
"""

import csv, io, urllib.request
from datetime import datetime

# symbol -> (navn, enhet, desimaler, divisor)
# divisor: COMEX kobber/sølv er i cent -> del på 100
TICKERS = {
    'cb.f':     ('Brent råolje',     '$',  2, 1),
    'cl.f':     ('WTI råolje',       '$',  2, 1),
    'ng.f':     ('Naturgass',        '$',  3, 1),
    'hg.f':     ('Kobber ($/lb)',    '$',  3, 100),
    'gc.f':     ('Gull ($/oz)',      '$',  0, 1),
    'si.f':     ('Sølv ($/oz)',      '$',  2, 100),
    'eurusd':   ('EUR/USD',          '',   4, 1),
    'usdnok':   ('USD/NOK',          '',   4, 1),
    '10yusy.b': ('US 10Y yield',     '%',  3, 1),
}

def fetch(sym):
    url = f'https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        text = r.read().decode('utf-8')
    rows = list(csv.reader(io.StringIO(text.strip())))
    if len(rows) < 2:
        return None, None
    val = rows[1][6]
    if val in ('', 'N/A', 'n/a', '-'):
        return None, rows[1][1]
    return float(val), rows[1][1]

print(f"\n{'─'*62}")
print(f"  Stooq pristest — {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
print(f"{'─'*62}")
print(f"  {'Symbol':<12} {'Navn':<22} {'Pris':>10}  Dato")
print(f"  {'─'*12} {'─'*22} {'─'*10}  {'─'*10}")

ok = err = 0
for sym, (navn, unit, dec, div) in TICKERS.items():
    try:
        raw, dato = fetch(sym)
        if raw is None:
            print(f"  {sym:<12} {navn:<22} {'N/A':>10}  {dato or '—'}")
            err += 1
            continue
        val = raw / div
        if unit == '$':   ps = f"${val:.{dec}f}"
        elif unit == '%': ps = f"{val:.{dec}f}%"
        else:             ps = f"{val:.{dec}f}"
        print(f"  {sym:<12} {navn:<22} {ps:>10}  {dato}")
        ok += 1
    except Exception as e:
        print(f"  {sym:<12} {navn:<22} {'FEIL':>10}  {str(e)[:25]}")
        err += 1

print(f"\n  Resultat: {ok} OK · {err} feil")
print(f"{'─'*62}\n")

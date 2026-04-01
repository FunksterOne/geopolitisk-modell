"""
build.py — Geopolitisk Systemanalyse Investor 2026
Henter priser fra Stooq.com og daglig brief, injiserer i index.html.

Kjøres av GitHub Actions kl. 04:05 UTC (06:05 norsk tid) og av Cowork lokalt.
    python scripts/build.py
"""

import csv, io, re, urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT     = Path(__file__).parent.parent
TEMPLATE = ROOT / "index.html"
BRIEFS   = ROOT / "briefs"
OUTPUT   = ROOT / "index.html"

today    = date.today()
iso_date = today.strftime("%Y-%m-%d")
MONTHS_NO = {
    "January":"januar","February":"februar","March":"mars","April":"april",
    "May":"mai","June":"juni","July":"juli","August":"august",
    "September":"september","October":"oktober","November":"november","December":"desember"
}
no_date = today.strftime("%d. %B %Y").lstrip("0")
for en, no in MONTHS_NO.items():
    no_date = no_date.replace(en, no)

# ── Stooq-tickere ─────────────────────────────────────────────────────────────
STOOQ_TICKERS = [
    ('cb.f',      'Brent',      '$',  2, 1),
    ('cl.f',      'WTI',        '$',  2, 1),
    ('ng.f',      'Naturgass',  '$',  3, 1),
    ('hg.f',      'Kobber',     '$',  3, 100),
    ('gc.f',      'Gull',       '$',  0, 1),
    ('si.f',      'Sølv',       '$',  2, 100),
    ('lad.f',     'Aluminium',  '$',  0, 1),
    ('eurusd',    'EUR/USD',    '',   4, 1),
    ('usdnok',    'USD/NOK',    '',   4, 1),
    ('eurnok',    'EUR/NOK',    '',   4, 1),
    ('10yusy.b',  'US 10Y',     '%',  3, 1),
    ('10ydeuy.b', 'Tysk 10Y',   '%',  3, 1),
]

CARD_MAP = {
    'cb.f':      'kap-brent',
    'gc.f':      'kap-gold',
    'hg.f':      'kap-copper',
    'lad.f':     'kap-alum',
    '10yusy.b':  'kap-us10y',
    '10ydeuy.b': 'kap-de10y',
    'eurusd':    'kap-eurusd',
    'usdnok':    'kap-usdnok',
    'eurnok':    'kap-eurnok',
}

def fetch_stooq(sym):
    url = f'https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        text = r.read().decode('utf-8')
    rows = list(csv.reader(io.StringIO(text.strip())))
    if len(rows) < 2:
        return None, None, None
    row, close, dato = rows[1], rows[1][6], rows[1][1]
    if close in ('', 'N/A', 'n/a', '-', 'N/D'):
        return None, None, dato
    try:
        open_p  = float(row[3])
        close_p = float(close)
        chg_pct = ((close_p - open_p) / open_p) * 100 if open_p else 0
    except:
        close_p, chg_pct = float(close), 0
    return close_p, chg_pct, dato

# ── Hent priser ───────────────────────────────────────────────────────────────
print(f"\n{'─'*55}")
print(f"  build.py — {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
print(f"{'─'*55}")
print("  Henter priser fra Stooq.com...")

prices, ts_dato = {}, None

for sym, navn, unit, dec, div in STOOQ_TICKERS:
    try:
        raw, chg, dato = fetch_stooq(sym)
        if raw is None:
            print(f"  {sym:<14} N/A")
            continue
        val = raw / div
        prices[sym] = {'val': val, 'chg': chg, 'unit': unit, 'dec': dec}
        if dato and not ts_dato:
            ts_dato = dato
        ps = f"{unit}{val:.{dec}f}" if unit == '$' else f"{val:.{dec}f}{unit}"
        print(f"  {sym:<14} {ps:>10}  ({chg:+.2f}%)")
    except Exception as e:
        print(f"  {sym:<14} FEIL: {e}")

print(f"  {len(prices)}/{len(STOOQ_TICKERS)} priser hentet · dato: {ts_dato}")

# ── Les HTML ──────────────────────────────────────────────────────────────────
html = TEMPLATE.read_text(encoding='utf-8')

# ── Fjern gammel injeksjonsblokk uansett format ───────────────────────────────
html = re.sub(
    r'// PRICES_INJECTED_START[\s\S]*?// PRICES_INJECTED_END\n?',
    '', html
)

# ── Bygg ny injeksjonsblokk pakket i DOMContentLoaded ────────────────────────
if prices:
    now_str  = datetime.now().strftime('%d.%m.%Y %H:%M')
    fn_lines = []

    for sym, el_id in CARD_MAP.items():
        if sym not in prices:
            continue
        p = prices[sym]
        v, c, u, d = p['val'], p['chg'], p['unit'], p['dec']
        if u == '$':   ps = f'${v:.{d}f}'
        elif u == '%': ps = f'{v:.{d}f}%'
        else:          ps = f'{v:.{d}f}'
        col = '#14532D' if c >= 0 else '#C53030'
        fn_lines.append(
            f"  var e=document.getElementById('{el_id}-val');"
            f"var s=document.getElementById('{el_id}-sub');"
            f"if(e)e.textContent='{ps}';"
            f"if(s)s.innerHTML='<span style=\"color:{col};font-weight:600\">{c:+.2f}%</span> &middot; Stooq {ts_dato}';"
        )

    if 'cb.f' in prices:
        fn_lines.append(f"  window._brentLive={prices['cb.f']['val']:.2f};")

    inject = (
        f'\n<script>\n'
        f'// PRICES_INJECTED_START\n'
        f'// build.py {iso_date} kl. {now_str}\n'
        f'document.addEventListener("DOMContentLoaded", function() {{\n'
        + '\n'.join(fn_lines) + '\n'
        f'}});\n'
        f'// PRICES_INJECTED_END\n'
        f'</script>\n'
    )

    # Injiser rett før </body>
    html = html.replace('</body>', inject + '</body>')
    print(f"  Priser injisert rett før </body>")
else:
    print("  Ingen priser — beholder fallback-verdier")

# ── Brief ─────────────────────────────────────────────────────────────────────
brief_file = BRIEFS / f"Geopolitisk oppdatering {iso_date}.md"
if brief_file.exists():
    md = brief_file.read_text(encoding='utf-8')

    def md_links_to_html(text):
        return re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            r'<a href="\2" target="_blank" rel="noopener" '
            r'style="color:var(--navy);text-decoration:underline">\1</a>',
            text
        )

    COLORS = {
        "hormuz":"#C53030","iran":"#C53030","olje":"#92400E","gass":"#92400E",
        "energi":"#92400E","kina":"#C63D2F","sjeldne":"#C63D2F","nato":"#1F3864",
        "marked":"#0E7490","makro":"#0E7490"
    }
    def sec_color(h):
        for kw, c in COLORS.items():
            if kw in h.lower(): return c
        return "#888780"

    sections_raw = re.findall(
        r'\*\*([^*]+?)[:\*]*\*\*\s*(.*?)(?=\n\n\*\*|\n\n###|\Z)', md, re.DOTALL
    )
    sections = [
        (h.strip(), md_links_to_html(b.strip()))
        for h, b in sections_raw
        if h.strip() != "Vurdering" and len(b.strip()) > 20
    ]
    vm = re.search(r'\*\*Vurdering[:\*]*\*\*\s*(.*?)$', md, re.DOTALL|re.MULTILINE)
    vurdering = md_links_to_html(vm.group(1).strip()) if vm else ""

    sec_html = ''.join(f'''
        <div style="border-left:3px solid {sec_color(h)};padding-left:12px">
          <div style="font-size:11px;font-weight:700;color:{sec_color(h)};text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">{h}</div>
          <div style="font-size:12px;line-height:1.7;color:var(--text)">{b}</div>
        </div>''' for h, b in sections)

    card = f"""  <!-- BRIEF — {no_date} -->
  <div style="margin-bottom:20px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
      <div style="font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#0E7490">{no_date}</div>
      <div style="flex:1;height:1px;background:var(--border)"></div>
      <div style="font-size:10px;color:var(--faint)">Daglig brief</div>
    </div>
    <div class="card">
      <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:10px">Geopolitisk nyhetsoppdatering — {no_date}</div>
      <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:12px">{sec_html}</div>
      {'<div style="font-size:11.5px;line-height:1.65;background:var(--navy-lt);border-radius:var(--radius);padding:10px 12px"><strong style="font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--navy-mid);display:block;margin-bottom:4px">Vurdering</strong>' + vurdering + '</div>' if vurdering else ''}
    </div>
  </div>
  <!-- INJECT_POINT -->"""

    if f"<!-- BRIEF — {no_date} -->" in html:
        html = re.sub(
            rf'<!-- BRIEF — {re.escape(no_date)} -->.*?<!-- INJECT_POINT -->',
            '<!-- INJECT_POINT -->', html, flags=re.DOTALL
        )
    html = html.replace('  <!-- INJECT_POINT -->', card)
    print(f"  Brief integrert: {no_date}")
else:
    print(f"  Ingen brief for {iso_date}")

OUTPUT.write_text(html, encoding='utf-8')
print(f"\n✓ index.html oppdatert ({len(html)//1024} KB)")
print(f"{'─'*55}\n")

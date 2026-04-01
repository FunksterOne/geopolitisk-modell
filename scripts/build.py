"""
build.py — Geopolitisk Systemanalyse Investor 2026
Henter priser fra Stooq.com og daglig brief, injiserer i index.html.

Kjøres av Cowork kl. 06:05 hver morgen:
    python scripts/build.py
"""

import csv, io, json, re, urllib.request
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
# (symbol, navn, enhet, desimaler, divisor)
# divisor=100: COMEX kobber/sølv er i cent -> del på 100 for $/lb og $/oz
STOOQ_TICKERS = [
    ('cb.f',     'Brent',          '$',  2, 1),
    ('cl.f',     'WTI',            '$',  2, 1),
    ('ng.f',     'Naturgass',      '$',  3, 1),
    ('hg.f',     'Kobber',         '$',  3, 100),
    ('gc.f',     'Gull',           '$',  0, 1),
    ('si.f',     'Sølv',           '$',  2, 100),
    ('eurusd',   'EUR/USD',        '',   4, 1),
    ('usdnok',   'USD/NOK',        '',   4, 1),
    ('10yusy.b', 'US 10Y',         '%',  3, 1),
]

def fetch_stooq(sym):
    url = f'https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        text = r.read().decode('utf-8')
    rows = list(csv.reader(io.StringIO(text.strip())))
    if len(rows) < 2:
        return None, None, None
    row   = rows[1]
    close = row[6]
    dato  = row[1]
    if close in ('', 'N/A', 'n/a', '-'):
        return None, None, dato
    # Beregn dagsendring i prosent fra Open (index 3) til Close (index 6)
    try:
        open_p  = float(row[3])
        close_p = float(close)
        chg_pct = ((close_p - open_p) / open_p) * 100 if open_p else 0
    except:
        close_p = float(close)
        chg_pct = 0
    return close_p, chg_pct, dato

# ── Hent alle priser ──────────────────────────────────────────────────────────
print(f"\n{'─'*55}")
print(f"  build.py — {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
print(f"{'─'*55}")
print("  Henter priser fra Stooq.com...")

prices = {}
ts_dato = None

for sym, navn, unit, dec, div in STOOQ_TICKERS:
    try:
        raw, chg, dato = fetch_stooq(sym)
        if raw is None:
            print(f"  {sym:<12} N/A")
            continue
        val = raw / div
        prices[sym] = {'val': val, 'chg': chg, 'unit': unit, 'dec': dec, 'navn': navn}
        if dato and not ts_dato:
            ts_dato = dato
        ps = f"{unit}{val:.{dec}f}" if unit == '$' else f"{val:.{dec}f}{unit}"
        print(f"  {sym:<12} {ps:>10}  ({chg:+.2f}%)")
    except Exception as e:
        print(f"  {sym:<12} FEIL: {e}")

print(f"  {len(prices)}/{len(STOOQ_TICKERS)} priser hentet · dato: {ts_dato}")

# ── Les HTML ──────────────────────────────────────────────────────────────────
html = TEMPLATE.read_text(encoding='utf-8')

# ── Injiser priser i Kapitalimplikasjoner-kortene ─────────────────────────────
if prices:
    # Bygg JS-blokk som oppdaterer de fem nøkkeltallskortene
    now_str = datetime.now().strftime('%d.%m.%Y %H:%M')

    # Hjelpefunksjon: formater pris
    def fmt(sym):
        if sym not in prices:
            return None, None
        p = prices[sym]
        v, c, u, d = p['val'], p['chg'], p['unit'], p['dec']
        if u == '$':
            ps = f'${v:.{d}f}'
        elif u == '%':
            ps = f'{v:.{d}f}%'
        else:
            ps = f'{v:.{d}f}'
        cs = f'{c:+.2f}%' if c is not None else ''
        return ps, cs

    # Mapper symbol -> HTML-element-ID i Kapitalimplikasjoner
    CARD_MAP = {
        'cb.f':     ('kap-brent',  'Brent råolje'),
        'cl.f':     ('kap-wti',    'WTI råolje'),
        'gc.f':     ('kap-gold',   'Gull spot'),
        'hg.f':     ('kap-copper', 'LME Kobber'),
        '10yusy.b': ('kap-us10y',  'US 10Y Treasury'),
    }

    js_lines = [f'// Priser injisert av build.py {iso_date} kl. {now_str}']
    for sym, (el_id, label) in CARD_MAP.items():
        ps, cs = fmt(sym)
        if ps:
            chg_color = '#14532D' if prices[sym]['chg'] >= 0 else '#C53030'
            js_lines.append(
                f'(function(){{'
                f'var v=document.getElementById("{el_id}-val");'
                f'var s=document.getElementById("{el_id}-sub");'
                f'if(v){{v.textContent="{ps}";v.title="Stooq {ts_dato}";}} '
                f'if(s){{s.innerHTML=\'<span style="color:{chg_color};font-weight:600">{cs}</span> · Stooq {ts_dato}\';}} '
                f'}})()'
            )

    # Brent til Hormuz-kalkulator
    if 'cb.f' in prices:
        js_lines.append(f'window._brentLive = {prices["cb.f"]["val"]:.2f};')

    inject_js = '\n'.join(js_lines)
    marker_s  = '// PRICES_INJECTED_START'
    marker_e  = '// PRICES_INJECTED_END'

    if marker_s in html:
        html = re.sub(
            rf'{re.escape(marker_s)}.*?{re.escape(marker_e)}',
            f'{marker_s}\n{inject_js}\n{marker_e}',
            html, flags=re.DOTALL
        )
        print(f"  Priser injisert (oppdaterte eksisterende blokk)")
    else:
        html = html.replace(
            'document.addEventListener(\'DOMContentLoaded\', initAnalyseProgress);',
            f'{marker_s}\n{inject_js}\n{marker_e}\n\n'
            'document.addEventListener(\'DOMContentLoaded\', initAnalyseProgress);',
            1
        )
        print(f"  Priser injisert (ny blokk)")

# ── Les og injiser brief ──────────────────────────────────────────────────────
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

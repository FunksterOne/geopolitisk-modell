"""
build.py — Geopolitisk Systemanalyse Investor 2026
Henter priser fra Stooq.com og daglig brief, injiserer i index.html.
Genererer automatisk brief-utkast fra RSS-feeds hvis ingen brief finnes.

Kjøres av GitHub Actions kl. 04:05 UTC (06:05 norsk tid) og lokalt.
    python scripts/build.py
"""

import csv, io, json, re, time, urllib.request, xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

ROOT     = Path(__file__).parent.parent
TEMPLATE = ROOT / "index.html"
BRIEFS   = ROOT / "briefs"
OUTPUT   = ROOT / "index.html"
CACHE    = ROOT / "scripts" / ".price_cache.json"

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

# ── Stooq-tickere ──────────────────────────────────────────────────────────────
STOOQ_TICKERS = [
    ('cb.f',      'Brent',      '$', 2, 1),
    ('cl.f',      'WTI',        '$', 2, 1),
    ('ng.f',      'Naturgass',  '$', 3, 1),
    ('hg.f',      'Kobber',     '$', 3, 100),
    ('gc.f',      'Gull',       '$', 0, 1),
    ('si.f',      'Solv',       '$', 2, 100),
    ('lad.f',     'Aluminium',  '$', 0, 1),
    ('eurusd',    'EUR/USD',    '',  4, 1),
    ('usdnok',    'USD/NOK',    '',  4, 1),
    ('eurnok',    'EUR/NOK',    '',  4, 1),
    ('10yusy.b',  'US 10Y',     '%', 3, 1),
    ('10ydeuy.b', 'Tysk 10Y',   '%', 3, 1),
]

CARD_MAP = {
    'cb.f':      'kap-brent',
    'cl.f':      'kap-wti',
    'ng.f':      'kap-gas',
    'hg.f':      'kap-copper',
    'gc.f':      'kap-gold',
    'si.f':      'kap-silver',
    'lad.f':     'kap-alum',
    '10yusy.b':  'kap-us10y',
    '10ydeuy.b': 'kap-de10y',
    'eurusd':    'kap-eurusd',
    'usdnok':    'kap-usdnok',
    'eurnok':    'kap-eurnok',
}

# ── RSS-kilder ─────────────────────────────────────────────────────────────────
RSS_SOURCES = [
    {'name': 'Reuters World',    'url': 'https://feeds.reuters.com/reuters/worldNews',    'label': 'Reuters'},
    {'name': 'Reuters Business', 'url': 'https://feeds.reuters.com/reuters/businessNews', 'label': 'Reuters'},
    {'name': 'Al Jazeera',       'url': 'https://www.aljazeera.com/xml/rss/all.xml',      'label': 'Al Jazeera'},
    {'name': 'EIA',              'url': 'https://www.eia.gov/rss/news.xml',               'label': 'EIA'},
    {'name': 'BBC World',        'url': 'https://feeds.bbci.co.uk/news/world/rss.xml',    'label': 'BBC'},
]

KEYWORDS = [
    'hormuz','iran','strait','oil','crude','brent','wti','opec','energy',
    'china','taiwan','rare earth','lithium','semiconductor','sanction',
    'nato','russia','ukraine','middle east','gulf','saudi',
    'fed','federal reserve','ecb','interest rate','inflation','recession',
    'trump','tariff','trade','dollar','yuan',
    'war','military','attack','strike','conflict','ceasefire',
    'norway','norges bank','equinor','lng','gas',
    'market','stock','bond','yield',
]

CATEGORIES = {
    'Hormuz og energi':  ['hormuz','strait','crude','brent','wti','opec','lng','gas','energy','oil'],
    'Iran og Midtosten': ['iran','middle east','gulf','saudi','israel','irak','iraq'],
    'Kina og ravarer':   ['china','taiwan','rare earth','lithium','semiconductor','yuan','beijing'],
    'NATO og allianser': ['nato','russia','ukraine','military','attack','strike','war','conflict'],
    'Markeder og makro': ['fed','federal reserve','ecb','inflation','recession','rate','yield','market','dollar','tariff','trade'],
    'Norge og Norden':   ['norway','norges bank','equinor','nordic','krone','nok'],
}


def fetch_rss(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        root = ET.fromstring(data)
        items = []
        for item in root.findall('.//item'):
            title = item.findtext('title', '').strip()
            link  = item.findtext('link',  '').strip()
            desc  = re.sub(r'<[^>]+>', '', item.findtext('description', '')).strip()
            if title:
                items.append((title, link, desc[:200]))
        return items
    except Exception:
        return []


def is_relevant(title, desc=''):
    text = (title + ' ' + desc).lower()
    return any(kw in text for kw in KEYWORDS)


def categorize(title, desc=''):
    text = (title + ' ' + desc).lower()
    for cat, kws in CATEGORIES.items():
        if any(kw in text for kw in kws):
            return cat
    return 'Markeder og makro'


def generate_brief(prices):
    brief_file = BRIEFS / f"Geopolitisk oppdatering {iso_date}.md"
    if brief_file.exists():
        print(f"  Brief finnes allerede for {iso_date} -- hopper over generering")
        return False

    print(f"  Genererer automatisk brief fra RSS-feeds...")
    BRIEFS.mkdir(exist_ok=True)

    all_articles = []
    for src in RSS_SOURCES:
        items = fetch_rss(src['url'])
        relevant = [(t, l, d, src['label']) for t, l, d in items if is_relevant(t, d)]
        all_articles.extend(relevant[:5])
        print(f"    {src['label']:<15} {len(relevant)}/{len(items)} relevante")
        time.sleep(0.3)

    if not all_articles:
        print(f"  Ingen relevante artikler -- ingen brief generert")
        return False

    seen = set()
    grouped = {cat: [] for cat in CATEGORIES}
    for title, link, desc, source in all_articles:
        key = title.lower()[:60]
        if key in seen:
            continue
        seen.add(key)
        cat = categorize(title, desc)
        if cat in grouped and len(grouped[cat]) < 4:
            grouped[cat].append((title, link, desc, source))

    cleaned = {cat: arts for cat, arts in grouped.items() if arts}

    brent = prices.get('cb.f', {}).get('val', None)
    brent_str = f"~{brent:.0f} $/fat" if brent else "ukjent"
    brent_chg = prices.get('cb.f', {}).get('chg', 0)
    brent_chg_str = f"{brent_chg:+.1f}%" if brent else ""

    lines = [
        f"# Geopolitisk oppdatering {no_date}",
        f"*Automatisk generert av build.py kl. {datetime.now().strftime('%H:%M')} UTC -- Gjennomga og juster for publisering*",
        "",
    ]

    for cat, arts in cleaned.items():
        lines.append(f"**{cat}**")
        for title, link, desc, source in arts:
            lines.append(f"- [{title}]({link}) ({source})" if link else f"- {title} ({source})")
            if desc and len(desc) > 30:
                lines.append(f"  {desc[:160]}")
        lines.append("")

    lines.append("**Vurdering**")
    lines.append(
        f"Brent handler i dag pa {brent_str} ({brent_chg_str}). "
        f"Hormuz-situasjonen og de tre Goodspeed-triggerne er fortsatt aktive. "
        f"Se Modellstatus-panelet for full sjekkliste. "
        f"*Dette er et automatisk utkast -- rediger og suppler med egne vurderinger.*"
    )

    brief_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f"  Brief-utkast generert: {brief_file.name} ({sum(len(a) for a in cleaned.values())} artikler)")
    return True


def fetch_stooq(sym, retries=3, delay=2):
    url = f'https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv'
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
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
            except Exception:
                close_p, chg_pct = float(close), 0
            return close_p, chg_pct, dato
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, None, None


def load_cache():
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def save_cache(prices, ts_dato):
    try:
        data = {sym: {**p, 'cached_dato': ts_dato} for sym, p in prices.items()}
        CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


# ── Hent priser ────────────────────────────────────────────────────────────────
print(f"\n{'─'*58}")
print(f"  build.py -- {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
print(f"{'─'*58}")
print("  Henter priser fra Stooq.com...")

cache   = load_cache()
prices  = {}
ts_dato = None

for sym, navn, unit, dec, div in STOOQ_TICKERS:
    raw, chg, dato = fetch_stooq(sym)
    if raw is None:
        if sym in cache:
            cached = cache[sym]
            val  = cached['val']
            chg  = cached.get('chg', 0)
            dato = cached.get('cached_dato', '(cache)')
            prices[sym] = {'val': val, 'chg': chg, 'unit': unit, 'dec': dec, 'cached': True}
            ps = f"{unit}{val:.{dec}f}" if unit == '$' else f"{val:.{dec}f}{unit}"
            print(f"  {sym:<14} {ps:>10}  (cache fra {dato})")
        else:
            print(f"  {sym:<14} {'N/A':>10}")
        continue
    val = raw / div
    prices[sym] = {'val': val, 'chg': chg, 'unit': unit, 'dec': dec, 'cached': False}
    if dato and not ts_dato:
        ts_dato = dato
    ps = f"{unit}{val:.{dec}f}" if unit == '$' else f"{val:.{dec}f}{unit}"
    print(f"  {sym:<14} {ps:>10}  ({chg:+.2f}%)")

fresh = sum(1 for p in prices.values() if not p.get('cached'))
print(f"  {fresh} ferske -- {len(prices)-fresh} fra cache -- dato: {ts_dato}")

fresh_prices = {sym: p for sym, p in prices.items() if not p.get('cached')}
if fresh_prices:
    save_cache(fresh_prices, ts_dato)

# ── Generer automatisk brief hvis ingen finnes ─────────────────────────────────
print(f"\n  Brief-sjekk...")
generate_brief(prices)

# ── Les HTML ───────────────────────────────────────────────────────────────────
html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'// PRICES_INJECTED_START[\s\S]*?// PRICES_INJECTED_END\n?', '', html)

# ── Injiser priser ─────────────────────────────────────────────────────────────
if prices:
    now_str  = datetime.now().strftime('%d.%m.%Y %H:%M')
    fn_lines = []

    for sym, el_id in CARD_MAP.items():
        if sym not in prices:
            continue
        p = prices[sym]
        v, c, u, d = p['val'], p['chg'], p['unit'], p['dec']
        cached = p.get('cached', False)

        if u == '$':   ps = f'${v:.{d}f}'
        elif u == '%': ps = f'{v:.{d}f}%'
        else:          ps = f'{v:.{d}f}'

        col      = '#14532D' if c >= 0 else '#C53030'
        dato_str = p.get('cached_dato', ts_dato) if cached else ts_dato
        sub_txt  = f'<span style="color:{col};font-weight:600">{c:+.2f}%</span> &middot; {"cache " if cached else ""}Stooq {dato_str}'

        fn_lines.append(
            f"  var e=document.getElementById('{el_id}-val');"
            f"var s=document.getElementById('{el_id}-sub');"
            f"if(e)e.textContent='{ps}';"
            f"if(s)s.innerHTML='{sub_txt}';"
        )

    if 'cb.f' in prices:
        fn_lines.append(f"  window._brentLive={prices['cb.f']['val']:.2f};")

    inject = (
        f'\n<script>\n'
        f'// PRICES_INJECTED_START\n'
        f'// build.py {iso_date} kl. {now_str} -- {fresh} ferske -- {len(prices)-fresh} fra cache\n'
        f'document.addEventListener("DOMContentLoaded", function() {{\n'
        + '\n'.join(fn_lines) + '\n'
        f'}});\n'
        f'// PRICES_INJECTED_END\n'
        f'</script>\n'
    )
    html = html.replace('</body>', inject + '</body>')
    print(f"\n  Priser injisert rett foer </body>")
else:
    print("\n  Ingen priser tilgjengelig")

# ── Integrer brief ─────────────────────────────────────────────────────────────
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

    is_draft = 'Automatisk generert' in md
    draft_banner = '''
      <div style="font-size:10px;background:#FEF08A;color:#713F12;padding:4px 10px;border-radius:3px;margin-bottom:8px;font-weight:600">
        Automatisk utkast -- ikke gjennomgatt av Halvard Nordang
      </div>''' if is_draft else ''

    sec_html = ''.join(f'''
        <div style="border-left:3px solid {sec_color(h)};padding-left:12px">
          <div style="font-size:11px;font-weight:700;color:{sec_color(h)};text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">{h}</div>
          <div style="font-size:12px;line-height:1.7;color:var(--text)">{b}</div>
        </div>''' for h, b in sections)

    card = f"""  <!-- BRIEF -- {no_date} -->
  <div style="margin-bottom:20px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
      <div style="font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#0E7490">{no_date}</div>
      <div style="flex:1;height:1px;background:var(--border)"></div>
      <div style="font-size:10px;color:var(--faint)">{'Automatisk utkast' if is_draft else 'Daglig brief'}</div>
    </div>
    <div class="card">
      {draft_banner}
      <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:10px">Geopolitisk nyhetsoppdatering -- {no_date}</div>
      <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:12px">{sec_html}</div>
      {'<div style="font-size:11.5px;line-height:1.65;background:var(--navy-lt);border-radius:var(--radius);padding:10px 12px"><strong style="font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--navy-mid);display:block;margin-bottom:4px">Vurdering</strong>' + vurdering + '</div>' if vurdering else ''}
    </div>
  </div>
  <!-- INJECT_POINT -->"""

    if f"<!-- BRIEF -- {no_date} -->" in html:
        html = re.sub(
            rf'<!-- BRIEF -- {re.escape(no_date)} -->.*?<!-- INJECT_POINT -->',
            '<!-- INJECT_POINT -->', html, flags=re.DOTALL
        )
    html = html.replace('  <!-- INJECT_POINT -->', card)
    print(f"  Brief integrert: {no_date}{' (automatisk utkast)' if is_draft else ''}")
else:
    print(f"  Ingen brief for {iso_date}")

OUTPUT.write_text(html, encoding='utf-8')
print(f"\n  index.html oppdatert ({len(html)//1024} KB)")
print(f"{'─'*58}\n")

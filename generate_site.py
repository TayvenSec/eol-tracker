"""
EOL Tracker — GitHub Pages site generator
Dashboard: what's going end-of-life soon, what recently ended, full product grid.

Built by Tayven Cyber Security (https://tayvensec.com) — MIT License
"""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
LIFECYCLE_PATH = ROOT / "data" / "lifecycles.json"
DOCS_DIR = ROOT / "docs"

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 16px; line-height: 1.6; color: #1a1a2e; background: #f8f9fa; }
header { background: #1a1a2e; color: #fff; padding: 2rem 1rem; text-align: center; }
header h1 { font-size: 1.8rem; letter-spacing: -0.5px; }
header p { color: #a0aec0; margin-top: 0.5rem; font-size: 0.95rem; }
.container { max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }
.stat-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
.stat { flex: 1; min-width: 150px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 1rem; text-align: center; }
.stat .num { font-size: 1.9rem; font-weight: 700; }
.stat .label { font-size: 0.8rem; color: #718096; text-transform: uppercase; letter-spacing: 0.05em; }
.n-warn { color: #c05621; } .n-dead { color: #c53030; } .n-ok { color: #2f855a; }
.section-title { font-size: 1.1rem; font-weight: 600; color: #4a5568; margin: 2rem 0 0.75rem;
  border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 8px; overflow: hidden; font-size: 0.88rem; }
th { text-align: left; padding: 0.55rem 0.75rem; background: #edf2f7; color: #4a5568;
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
td { padding: 0.6rem 0.75rem; border-top: 1px solid #e2e8f0; }
.pill { display: inline-block; padding: 0.1rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
.pill-warn { background: #fffaf0; color: #c05621; border: 1px solid #fbd38d; }
.pill-dead { background: #fff5f5; color: #c53030; border: 1px solid #feb2b2; }
.pill-ok   { background: #f0fff4; color: #2f855a; border: 1px solid #9ae6b4; }
.days { color: #718096; font-size: 0.8rem; }
details { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 0.6rem; }
summary { cursor: pointer; padding: 0.7rem 1rem; font-weight: 600; color: #2d3748; }
details table { border: none; border-top: 1px solid #e2e8f0; border-radius: 0; }
footer { text-align: center; padding: 2rem 1rem; color: #a0aec0; font-size: 0.82rem;
  border-top: 1px solid #e2e8f0; margin-top: 3rem; }
footer a { color: #718096; }
"""


def pill(status: str) -> str:
    return {
        "EOL_SOON": '<span class="pill pill-warn">EOL SOON</span>',
        "EOL": '<span class="pill pill-dead">END OF LIFE</span>',
        "SUPPORTED": '<span class="pill pill-ok">SUPPORTED</span>',
    }.get(status, status)


def build():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / ".nojekyll").write_text("")

    data = {}
    if LIFECYCLE_PATH.exists():
        try:
            data = json.loads(LIFECYCLE_PATH.read_text())
        except Exception:
            pass

    products = data.get("products", {})
    checked = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    eol_soon, recent_eol = [], []
    total_cycles = supported = 0

    for slug, prod in products.items():
        for c in prod.get("cycles", []):
            total_cycles += 1
            row = {**c, "display": prod["display"]}
            if c["status"] == "EOL_SOON":
                eol_soon.append(row)
            elif c["status"] == "SUPPORTED":
                supported += 1
            elif c["status"] == "EOL" and c.get("days_until_eol") is not None and c["days_until_eol"] >= -180:
                recent_eol.append(row)

    eol_soon.sort(key=lambda r: r.get("days_until_eol") if r.get("days_until_eol") is not None else 999)
    recent_eol.sort(key=lambda r: r.get("days_until_eol") if r.get("days_until_eol") is not None else 0, reverse=True)

    def rows(entries):
        out = []
        for r in entries:
            days = r.get("days_until_eol")
            days_txt = ""
            if days is not None:
                days_txt = f"in {days} days" if days >= 0 else f"{abs(days)} days ago"
            out.append(
                f"<tr><td><strong>{r['display']}</strong> {r.get('cycle','')}</td>"
                f"<td>{pill(r['status'])}</td>"
                f"<td>{r.get('eol','')} <span class='days'>{days_txt}</span></td>"
                f"<td>{r.get('latest','')}</td></tr>"
            )
        return "\n".join(out) or "<tr><td colspan='4'>None 🎉</td></tr>"

    # Full per-product grid (collapsible)
    product_blocks = []
    for slug, prod in sorted(products.items(), key=lambda kv: kv[1]["display"]):
        if prod.get("error"):
            product_blocks.append(f"<details><summary>⚠️ {prod['display']} — data unavailable</summary></details>")
            continue
        body = []
        for c in prod["cycles"]:
            days = c.get("days_until_eol")
            days_txt = ""
            if days is not None:
                days_txt = f"in {days} days" if days >= 0 else f"{abs(days)} days ago"
            body.append(
                f"<tr><td>{c.get('cycle','')}</td><td>{pill(c['status'])}</td>"
                f"<td>{c.get('eol','')} <span class='days'>{days_txt}</span></td>"
                f"<td>{c.get('latest','')}</td></tr>"
            )
        product_blocks.append(
            f"<details><summary>{prod['display']} ({len(prod['cycles'])} versions)</summary>"
            f"<table><thead><tr><th>Version</th><th>Status</th><th>End of Life</th><th>Latest</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table></details>"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EOL Tracker — End-of-Support Dashboard</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>📅 EOL Tracker</h1>
  <p>End-of-life &amp; end-of-support dates for {len(products)} products — checked {checked}</p>
</header>
<div class="container">
  <div class="stat-row">
    <div class="stat"><div class="num n-warn">{len(eol_soon)}</div><div class="label">EOL within 90 days</div></div>
    <div class="stat"><div class="num n-dead">{len(recent_eol)}</div><div class="label">Ended in last 180 days</div></div>
    <div class="stat"><div class="num n-ok">{supported}</div><div class="label">Supported versions</div></div>
    <div class="stat"><div class="num">{total_cycles}</div><div class="label">Versions tracked</div></div>
  </div>

  <p class="section-title">⏳ Reaching End of Life Within 90 Days</p>
  <table>
    <thead><tr><th>Product / Version</th><th>Status</th><th>EOL Date</th><th>Latest Release</th></tr></thead>
    <tbody>{rows(eol_soon)}</tbody>
  </table>

  <p class="section-title">🔴 Recently Reached End of Life (last 180 days)</p>
  <table>
    <thead><tr><th>Product / Version</th><th>Status</th><th>EOL Date</th><th>Latest Release</th></tr></thead>
    <tbody>{rows(recent_eol)}</tbody>
  </table>

  <p class="section-title">All Tracked Products</p>
  {''.join(product_blocks)}

  <p style="margin-top:2rem;font-size:0.85rem;color:#718096;">
    Running software past its end-of-life date means <strong>no more security patches</strong> —
    every vulnerability found after that date stays unpatched forever.
    Data: <a href="https://endoflife.date">endoflife.date</a>, checked daily.
  </p>
</div>
<footer>
  <p><a href="https://github.com/TayvenSec/eol-tracker">View on GitHub</a> ·
  <a href="https://tayvensec.com">Tayven Cyber Security</a> ·
  <a href="https://github.com/TayvenSec/patch-tuesday-tracker">Patch Tuesday Tracker</a> ·
  <a href="https://github.com/TayvenSec/kev-tracker">KEV Tracker</a></p>
</footer>
</body>
</html>"""

    (DOCS_DIR / "index.html").write_text(html)
    print(f"[SITE] Built index.html ({len(eol_soon)} EOL-soon, {len(recent_eol)} recent-EOL)")


if __name__ == "__main__":
    build()

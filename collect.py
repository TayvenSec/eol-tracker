"""
EOL Tracker — End-of-Life / End-of-Support monitoring
Source: endoflife.date public API (official, no auth, no scraping)
https://endoflife.date/docs/api

Built by Tayven Cyber Security (https://tayvensec.com) — MIT License

How it works:
  1. Fetches lifecycle data for a curated list of products
  2. Classifies every release cycle: SUPPORTED / EOL SOON (<=90 days) / END OF LIFE
  3. Diffs against yesterday's state — notifies when a cycle newly enters
     the 90-day warning window or newly reaches end of life
  4. Rebuilds the GitHub Pages dashboard
"""

import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

import requests

API_BASE = "https://endoflife.date/api"

# Curated product list — matches the platforms covered by the
# Tayven Cyber Security patch series, plus common infrastructure.
# Full catalog of trackable products: https://endoflife.date/api/all.json
PRODUCTS = {
    # OS / devices
    "windows":            "Windows",
    "windows-server":     "Windows Server",
    "macos":              "macOS",
    "ios":                "iOS",
    "android":            "Android",
    "ubuntu":             "Ubuntu",
    "debian":             "Debian",
    "rhel":               "Red Hat Enterprise Linux",
    # Network / infrastructure
    "pan-os":             "PAN-OS (Palo Alto)",
    "cisco-ios-xe":       "Cisco IOS XE",
    # Common server software (high patching relevance)
    "python":             "Python",
    "php":                "PHP",
    "nodejs":             "Node.js",
    "postgresql":         "PostgreSQL",
    "mysql":              "MySQL",
    "msexchange":    "Microsoft Exchange Server",
    "mssqlserver":         "Microsoft SQL Server",
    "office":             "Microsoft Office",
    "vmware-esxi":        "VMware ESXi",
}

WARNING_DAYS = 90   # "EOL SOON" window
RECENT_DAYS = 180   # how long a past EOL stays in the "recently ended" list

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
STATE_PATH = DATA_DIR / "eol-state.json"
LIFECYCLE_PATH = DATA_DIR / "lifecycles.json"
FLAG_PATH = ROOT / ".eol_alerts"


def parse_eol(value):
    """endoflife.date 'eol' can be a date string, True (already EOL), or False (no date)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return False
    return False


def classify(eol_value, today: date) -> tuple[str, int | None]:
    """Return (status, days_until_eol_or_None)."""
    eol = parse_eol(eol_value)
    if eol is True:
        return "EOL", None
    if eol is False:
        return "SUPPORTED", None
    days = (eol - today).days
    if days < 0:
        return "EOL", days
    if days <= WARNING_DAYS:
        return "EOL_SOON", days
    return "SUPPORTED", days


def fetch_product(slug: str) -> list | None:
    url = f"{API_BASE}/{slug}.json"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "eol-tracker (github.com/TayvenSec/eol-tracker)"})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[WARN] {slug}: {e}")
        return None


def collect() -> dict:
    today = date.today()
    lifecycles = {}

    for slug, display in PRODUCTS.items():
        cycles = fetch_product(slug)
        if cycles is None:
            lifecycles[slug] = {"display": display, "error": True, "cycles": []}
            continue

        parsed = []
        for c in cycles:
            status, days = classify(c.get("eol"), today)
            eol_raw = c.get("eol")
            parsed.append({
                "cycle": str(c.get("cycle", "")),
                "label": c.get("releaseLabel") or f"{display} {c.get('cycle','')}",
                "eol": eol_raw if isinstance(eol_raw, str) else ("yes" if eol_raw is True else "none"),
                "status": status,
                "days_until_eol": days,
                "latest": c.get("latest", ""),
            })
        lifecycles[slug] = {"display": display, "error": False, "cycles": parsed}
        counts = {}
        for p in parsed:
            counts[p["status"]] = counts.get(p["status"], 0) + 1
        print(f"[OK] {display}: {len(parsed)} cycles ({counts})")

    return {"checked_at": datetime.utcnow().isoformat() + "Z", "date": today.isoformat(), "products": lifecycles}


def build_alert_state(data: dict) -> dict:
    """State = the set of cycles currently in EOL_SOON or recently-EOL status."""
    state = {}
    today = date.today()
    for slug, prod in data["products"].items():
        for c in prod["cycles"]:
            key = f"{slug}:{c['cycle']}"
            if c["status"] == "EOL_SOON":
                state[key] = "EOL_SOON"
            elif c["status"] == "EOL" and c["days_until_eol"] is not None and c["days_until_eol"] >= -RECENT_DAYS:
                state[key] = "EOL"
    return state


def diff_alerts(new_state: dict, old_state: dict, data: dict) -> list:
    """Alert lines for cycles that newly entered EOL_SOON, or moved EOL_SOON/absent -> EOL."""
    alerts = []
    lookup = {}
    for slug, prod in data["products"].items():
        for c in prod["cycles"]:
            lookup[f"{slug}:{c['cycle']}"] = (prod["display"], c)

    for key, status in new_state.items():
        old = old_state.get(key)
        if old == status:
            continue
        display, c = lookup.get(key, ("?", {}))
        if status == "EOL_SOON" and old is None:
            alerts.append(f"- ⏳ **{display} {c.get('cycle','')}** reaches end of life on **{c.get('eol','')}** ({c.get('days_until_eol','?')} days away)")
        elif status == "EOL" and old != "EOL":
            alerts.append(f"- 🔴 **{display} {c.get('cycle','')}** is now **END OF LIFE** (as of {c.get('eol','')}) — no more security updates")
    return alerts


def main() -> int:
    print(f"\n{'='*60}\n  EOL Tracker — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n{'='*60}\n")

    data = collect()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LIFECYCLE_PATH.write_text(json.dumps(data, indent=2))
    print(f"\n[SAVE] {LIFECYCLE_PATH.name}")

    old_state = {}
    if STATE_PATH.exists():
        try:
            old_state = json.loads(STATE_PATH.read_text())
        except Exception:
            old_state = {}

    new_state = build_alert_state(data)
    first_run = not bool(old_state)
    alerts = [] if first_run else diff_alerts(new_state, old_state, data)

    STATE_PATH.write_text(json.dumps(new_state, indent=2, sort_keys=True))
    print(f"[SAVE] {STATE_PATH.name} ({len(new_state)} cycles in alert window)")

    if first_run:
        print("[INFO] First run — state seeded, no notifications (check the dashboard for current status).")

    if alerts:
        FLAG_PATH.write_text("\n".join(alerts))
        print(f"[FLAG] {len(alerts)} EOL alert(s) — notification will fire.")
    elif FLAG_PATH.exists():
        FLAG_PATH.unlink()

    from generate_site import build
    build()

    return 0


if __name__ == "__main__":
    sys.exit(main())

# 📅 EOL Tracker

Daily automated tracking of **end-of-life and end-of-support dates** for 20 operating systems, network platforms, and common server software — powered by the [endoflife.date](https://endoflife.date) API.

Software past its EOL date receives **no more security patches**. This tracker makes sure nothing in your stack quietly ages out of support.

**🌐 Live dashboard:** [https://tayvensec.github.io/eol-tracker/index.html](https://tayvensec.github.io/eol-tracker/index.html)

Part of the Tayven Cyber Security open-source suite, alongside the [Patch Tuesday Tracker](https://github.com/TayvenSec/patch-tuesday-tracker) and [KEV Tracker](https://github.com/TayvenSec/kev-tracker). Built for the [Patch Management Series](https://tayvensec.com/patch-management/).

---

## What It Tracks

**Operating systems & devices:** Windows, Windows Server, macOS, iOS, Android, Ubuntu, Debian, RHEL, ChromeOS

**Network & infrastructure:** PAN-OS, Cisco IOS XE, VMware ESXi

**Server software:** Python, PHP, Node.js, PostgreSQL, MySQL, Exchange Server, SQL Server, Microsoft Office

Adding a product is a one-line change to the `PRODUCTS` dict in `collect.py` — anything in the [endoflife.date catalog](https://endoflife.date) works.

## What It Does

Every day at 10:00 UTC:

1. Fetches lifecycle data for every tracked product (official API, no scraping)
2. Classifies each version: **SUPPORTED** / **EOL SOON** (≤90 days) / **END OF LIFE**
3. Rebuilds the dashboard: what's expiring within 90 days, what ended in the last 180 days, and a full collapsible per-product grid
4. Opens a **GitHub Issue notification** when a version *newly* enters the 90-day warning window (⏳) or *newly* reaches end of life (🔴)

No status changes → no commit, no issue, no noise. Since EOL dates are calendar-driven, expect notifications a handful of times per month at most.

The first run seeds the state silently — check the dashboard for the current picture; notifications track *changes* from then on.

## Setup

1. Fork/clone, push to GitHub
2. **Settings → Pages** → Deploy from branch → `main` / `docs`
3. **Actions** tab → enable workflows → run **Track EOL Dates** manually once
4. **Watch → All Activity** for email alerts

## Run Locally

```bash
pip install -r requirements.txt
python collect.py
```

## License

MIT — Copyright (c) 2026 Tayven Cyber Security (https://tayvensec.com)

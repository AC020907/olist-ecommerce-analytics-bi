"""Capture real screenshots of every demo tab for the README.

Requires the demo to be running (streamlit run demo/app.py) and Playwright
(pip install playwright). Uses the locally installed Microsoft Edge, so no
browser download is needed:  python scripts/capture_demo_screenshots.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT_DIR = Path(__file__).resolve().parent.parent / "images" / "demo"
TABS = {
    "Executive overview": "01_executive_overview.png",
    "Sales performance": "02_sales_performance.png",
    "Delivery & satisfaction": "03_delivery_satisfaction.png",
    "Insights & weekly KPIs": "04_insights_weekly_kpis.png",
    "How the numbers are built": "05_methodology.png",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
        page.goto(URL)
        page.get_by_text("From raw order data").wait_for(timeout=60_000)
        page.wait_for_timeout(3000)
        for tab, filename in TABS.items():
            page.get_by_role("tab", name=tab).click()
            page.wait_for_timeout(2500)
            # Streamlit scrolls inside its main container, so measure that and grow the viewport to fit.
            height = page.evaluate("document.querySelector('[data-testid=\"stMain\"]').scrollHeight")
            page.set_viewport_size({"width": 1440, "height": min(int(height) + 40, 3200)})
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT_DIR / filename))
            page.set_viewport_size({"width": 1440, "height": 900})
            print("saved", OUT_DIR / filename)
        browser.close()


if __name__ == "__main__":
    main()

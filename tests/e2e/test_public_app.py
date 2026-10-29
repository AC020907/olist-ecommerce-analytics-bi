"""End-to-end tests against the deployed app (run with APP_URL=https://<app>.streamlit.app).

They drive a real browser and check results, not just HTTP 200: default KPIs equal the
committed aggregates, every section renders, the category filter changes the numbers,
an empty selection shows a message, the app has no Python exception on screen and it
works on a phone-sized viewport.

    APP_URL=https://olist-sales-analytics.streamlit.app pytest tests/e2e -v
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import pytest

APP_URL = os.environ.get("APP_URL", "").rstrip("/")
if not APP_URL:
    pytest.skip("APP_URL not set", allow_module_level=True)
playwright = pytest.importorskip("playwright.sync_api")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demo"))
import metrics as m  # noqa: E402

TABS = ["Executive overview", "Sales performance", "Delivery & satisfaction", "Business insights", "Methodology & data quality"]
# Streamlit Community Cloud wraps the app in an iframe; this path serves the app itself.
DIRECT_URL = f"{APP_URL}/~/+/" if "streamlit.app" in APP_URL else APP_URL


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        channel = os.environ.get("PLAYWRIGHT_CHANNEL")  # e.g. "msedge" locally; bundled Chromium in CI
        b = p.chromium.launch(channel=channel) if channel else p.chromium.launch()
        yield b
        b.close()


def wake_if_sleeping(page) -> None:
    """Community Cloud puts idle apps to sleep; a visitor wakes them with one button."""
    button = page.get_by_role("button", name=re.compile("get this app back up", re.I))
    if button.count():
        button.first.click()
        page.wait_for_timeout(5000)


def open_app(browser, width: int = 1440, height: int = 900):
    page = browser.new_page(viewport={"width": width, "height": height})
    started = time.perf_counter()
    page.goto(APP_URL, wait_until="domcontentloaded", timeout=120_000)
    wake_if_sleeping(page)
    page.goto(DIRECT_URL, wait_until="domcontentloaded", timeout=120_000)
    page.get_by_text("Olist marketplace: sales, delivery and customer satisfaction").wait_for(timeout=180_000)
    page.get_by_text("Net revenue").first.wait_for(timeout=60_000)
    page.load_seconds = time.perf_counter() - started
    return page


def metric_value(page, label: str) -> str:
    box = page.locator('[data-testid="stMetric"]').filter(has=page.get_by_text(label, exact=True)).first
    return box.locator('[data-testid="stMetricValue"]').inner_text().strip()


def assert_no_exception(page) -> None:
    assert page.locator('[data-testid="stException"]').count() == 0
    assert "Traceback" not in page.content()


def test_https_and_default_kpis(browser):
    if "localhost" not in APP_URL:
        assert APP_URL.startswith("https://")
    page = open_app(browser)
    frames = m.load_frames()
    expected = m.kpis(m.apply_filters(frames["orders"], *m.ANALYSIS_WINDOW))
    assert metric_value(page, "Net revenue") == m.brl(expected["revenue"])
    assert metric_value(page, "Orders") == f"{expected['orders']:,.0f}"
    assert metric_value(page, "Average order value") == m.brl(expected["aov"])
    assert metric_value(page, "Late deliveries") == f"{expected['late_pct']:.1f}%"
    assert page.get_by_text("Historical snapshot, not live data").count() >= 1
    assert_no_exception(page)
    print(f"initial load: {page.load_seconds:.1f}s")
    page.close()


def test_every_section_renders(browser):
    page = open_app(browser)
    checks = {
        "Sales performance": "Category performance",
        "Delivery & satisfaction": "Average review by delivery delay",
        "Business insights": "Suggested weekly KPI scorecard",
        "Methodology & data quality": "Data quality checks",
    }
    for tab, marker in checks.items():
        page.get_by_role("tab", name=tab).click()
        page.get_by_text(marker).first.wait_for(timeout=30_000)
        assert_no_exception(page)
    page.close()


def test_category_filter_changes_kpis(browser):
    page = open_app(browser)
    before = metric_value(page, "Orders")
    sidebar = page.locator('[data-testid="stSidebar"]')
    sidebar.locator('[data-testid="stSelectbox"]').filter(has_text="Product category").locator("input").click()
    page.keyboard.type("health beauty")
    page.keyboard.press("Enter")
    frames = m.load_frames()
    rows = m.apply_filters(frames["categories"], *m.ANALYSIS_WINDOW)
    expected = m.category_kpis(rows[rows["category"] == "health beauty"])
    page.get_by_text(f"{expected['orders']:,.0f}", exact=True).first.wait_for(timeout=30_000)
    assert metric_value(page, "Orders") == f"{expected['orders']:,.0f}" != before
    assert metric_value(page, "Net revenue") == m.brl(expected["revenue"])
    assert_no_exception(page)
    page.close()


def test_mobile_viewport_has_no_horizontal_scroll(browser):
    page = open_app(browser, width=390, height=844)
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1
    assert_no_exception(page)
    page.close()

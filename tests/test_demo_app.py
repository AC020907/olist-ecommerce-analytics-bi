"""Headless smoke tests of the Streamlit demo across filter combinations."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")

from streamlit.testing.v1 import AppTest  # noqa: E402

from olist_bi.config import REPO_ROOT  # noqa: E402

APP = str(REPO_ROOT / "demo" / "app.py")
REFERENCE = json.loads((REPO_ROOT / "demo" / "data" / "kpi_reference.json").read_text(encoding="utf-8"))


def run_app() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    assert not app.exception, app.exception
    return app


def metric(app: AppTest, label: str):
    return next(m for m in app.metric if m.label == label)


def test_default_view_renders_every_tab():
    app = run_app()
    assert [t.label for t in app.tabs] == [
        "Executive overview", "Sales performance", "Delivery & satisfaction", "Insights & weekly KPIs", "How the numbers are built",
    ]
    assert metric(app, "Net revenue").value == "R$13.45M"  # Jan 2017 - Aug 2018 window
    assert metric(app, "Orders").value == "97,910"


def test_full_period_matches_sql_reference():
    app = run_app()
    app.select_slider[0].set_value(("2016-09", "2018-10")).run()
    assert not app.exception
    assert metric(app, "Orders").value == f"{REFERENCE['total_orders']:,.0f}"
    assert metric(app, "Average order value").value == f"R${REFERENCE['avg_order_value']:,.2f}"


def test_growth_delta_shown_when_prior_period_is_complete():
    app = run_app()
    app.select_slider[0].set_value(("2018-01", "2018-06")).run()
    assert not app.exception
    assert metric(app, "Net revenue").delta is not None


@pytest.mark.parametrize("region", ["Nordeste", "Norte"])
def test_region_filter_renders(region):
    app = run_app()
    app.multiselect[0].select(region).run()
    assert not app.exception
    assert metric(app, "Net revenue").value.startswith("R$")

"""Headless smoke tests of the Streamlit demo across filter combinations."""
from __future__ import annotations

import json
import sys

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")

from streamlit.testing.v1 import AppTest  # noqa: E402

from olist_bi.config import REPO_ROOT  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "demo"))

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
        "Executive overview", "Sales performance", "Delivery & satisfaction", "Business insights", "Methodology & data quality",
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


def test_empty_selection_shows_message_instead_of_failing():
    app = run_app()
    app.select_slider[0].set_value(("2016-09", "2016-09")).run()
    app.multiselect[0].select("Centro-Oeste").run()  # no orders there in Sep 2016
    assert not app.exception
    assert any("No valid orders match" in w.value for w in app.warning)


def test_category_filter_drives_kpis():
    import metrics as m

    app = run_app()
    app.selectbox(key="category").set_value("health beauty").run()
    assert not app.exception
    frames = m.load_frames()
    rows = m.apply_filters(frames["categories"], "2017-01", "2018-08")
    expected = m.category_kpis(rows[rows["category"] == "health beauty"])
    assert metric(app, "Orders").value == f"{expected['orders']:,.0f}"
    assert metric(app, "Net revenue").value == m.brl(expected["revenue"])


def test_combined_filters_and_reset():
    app = run_app()
    app.multiselect(key="regions").select("Sudeste").run()
    app.multiselect(key="states").select("SP").run()
    app.selectbox(key="category").set_value("bed bath table").run()
    app.select_slider[0].set_value(("2018-01", "2018-06")).run()
    assert not app.exception
    narrowed = metric(app, "Orders").value
    next(b for b in app.button if b.label == "Reset filters").click().run()
    assert not app.exception
    assert metric(app, "Orders").value == "97,910" != narrowed


def test_seller_profile_and_methodology_render():
    app = run_app()
    seller = next(sb for sb in app.selectbox if sb.key != "category")
    seller.select_index(1).run()
    assert not app.exception
    assert any(mt.label == "Passed" for mt in app.metric)


def test_app_recovers_from_stale_metrics_module():
    # Reproduces the Streamlit Cloud redeploy: the process keeps an older metrics module
    # (here: missing seller_profile) while the new app.py runs.
    import metrics

    del metrics.seller_profile
    app = run_app()
    assert not app.exception
    assert hasattr(metrics, "seller_profile")

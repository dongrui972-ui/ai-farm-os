from __future__ import annotations

from app.services.agronomy import advise_plot


def test_tomato_flowering_below_threshold_recommends_pulse() -> None:
    advice = advise_plot(
        crop_name="番茄",
        growth_stage="开花坐果",
        zone_type="greenhouse",
        moisture_pct=41,
        area_mu=4.1,
        health_status="stress",
        method="drip",
        zone_code="A3",
    )
    assert advice["data_source"] == "SIMULATION"
    assert advice["action"] == "irrigate"
    assert advice["control_enabled"] is False
    assert 8 <= advice["recommended_mm"] <= 12
    assert advice["volume_m3"] > 0
    assert advice["threshold_pct"] > 41
    assert any("阈值" in line for line in advice["reasons"])
    assert advice["kc"] == 1.10


def test_lettuce_harvest_holds_water() -> None:
    advice = advise_plot(
        crop_name="生菜",
        growth_stage="采收期",
        zone_type="open_field",
        moisture_pct=48,
        area_mu=7.8,
        health_status="healthy",
        method="sprinkler",
        zone_code="B2",
    )
    assert advice["action"] == "hold_for_harvest"
    assert advice["recommended_mm"] == 0
    assert advice["data_source"] == "SIMULATION"


def test_comfortable_moisture_holds_plan() -> None:
    advice = advise_plot(
        crop_name="番茄",
        growth_stage="开花坐果",
        zone_type="greenhouse",
        moisture_pct=62,
        area_mu=4.2,
        health_status="healthy",
        method="drip",
        zone_code="A1",
    )
    assert advice["action"] == "hold"
    assert advice["recommended_mm"] == 0
    assert advice["moisture_status"] in {"ok", "wet"}


def test_humid_cucumber_shortens_rather_than_flood() -> None:
    advice = advise_plot(
        crop_name="黄瓜",
        growth_stage="盛果期",
        zone_type="greenhouse",
        moisture_pct=58,
        area_mu=4.0,
        health_status="watch",
        method="drip",
        zone_code="A2",
    )
    assert advice["action"] == "shorten"
    assert advice["climate_action"] == "dehumidify"
    assert 0 < advice["recommended_mm"] <= 6
    assert advice["data_source"] == "SIMULATION"


def test_facility_zone_not_applicable() -> None:
    advice = advise_plot(
        crop_name=None,
        growth_stage=None,
        zone_type="facility",
        moisture_pct=None,
        area_mu=0.4,
    )
    assert advice["applicable"] is False
    assert advice["recommended_mm"] == 0
    assert advice["data_source"] == "SIMULATION"

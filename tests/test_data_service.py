from __future__ import annotations

import pandas as pd
import pytest

from app.config import DEMO_DORM
from app.data_service import compute_daily_table, compute_metrics, load_data


def sample_raw_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ts": "2026-01-05T10:00:00", "dorm": DEMO_DORM, "members": 4, "power_w": 400},
            {"ts": "2026-01-05T11:00:00", "dorm": DEMO_DORM, "members": 4, "power_w": 800},
            {"ts": "2026-01-05T18:00:00", "dorm": DEMO_DORM, "members": 4, "power_w": 300},
            {"ts": "2026-01-06T10:00:00", "dorm": DEMO_DORM, "members": 4, "power_w": 450},
            {"ts": "2026-01-06T11:00:00", "dorm": DEMO_DORM, "members": 4, "power_w": 900},
            {"ts": "2026-01-06T18:00:00", "dorm": DEMO_DORM, "members": 4, "power_w": 250},
            {"ts": "2026-01-05T10:00:00", "dorm": "Village East - 6F", "members": 6, "power_w": 300},
            {"ts": "2026-01-05T11:00:00", "dorm": "Village East - 6F", "members": 6, "power_w": 500},
            {"ts": "2026-01-05T18:00:00", "dorm": "Village East - 6F", "members": 6, "power_w": 700},
            {"ts": "2026-01-06T10:00:00", "dorm": "Village East - 6F", "members": 6, "power_w": 320},
            {"ts": "2026-01-06T11:00:00", "dorm": "Village East - 6F", "members": 6, "power_w": 520},
            {"ts": "2026-01-06T18:00:00", "dorm": "Village East - 6F", "members": 6, "power_w": 760},
        ]
    )


def write_sample_csv(tmp_path) -> str:
    csv_path = tmp_path / "sample.csv"
    sample_raw_data().to_csv(csv_path, index=False)
    return str(csv_path)


def test_load_data_adds_expected_columns(tmp_path):
    df = load_data(write_sample_csv(tmp_path))

    assert {"date", "window", "dt_s", "delta_kwh"}.issubset(df.columns)
    assert set(df["window"].unique()) == {"green", "busy"}
    assert (df["delta_kwh"] >= 0).all()
    assert (df.groupby("dorm").head(1)["delta_kwh"] == 0).all()


def test_load_data_validates_required_columns(tmp_path):
    csv_path = tmp_path / "invalid.csv"
    pd.DataFrame([{"ts": "2026-01-05T10:00:00", "dorm": DEMO_DORM}]).to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="missing columns"):
        load_data(str(csv_path))


def test_compute_metrics_returns_consistent_summary(tmp_path):
    df = load_data(write_sample_csv(tmp_path))
    daily = compute_daily_table(df)
    metrics = compute_metrics(df, daily, replay_idx=5, dorm=DEMO_DORM)

    assert metrics["members"] == 4
    assert metrics["weekly_total"] == 4
    assert len(metrics["weekly_challenges"]) == 4
    assert metrics["weekly_points"] >= metrics["weekly_bonus_points"] >= 0
    assert 0 <= metrics["pct_green"] <= 100
    assert 0 <= metrics["pct_busy"] <= 100
    assert metrics["rank"] == 1

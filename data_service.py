# data_service.py
from __future__ import annotations

from datetime import time
import pandas as pd

from config import (
    GREEN_START, GREEN_END,
    PEAK_START, PEAK_END,
    POINTS_GREEN, POINTS_NEUTRAL, POINTS_PEAK,
)

# -------------------------
# Time windows & scoring
# -------------------------
def in_window(t: time, start: time, end: time) -> bool:
    return start <= t < end


def score_kwh(ts: pd.Timestamp, kwh: float) -> float:
    """Convert energy (kWh) at timestamp ts into points."""
    t = ts.time()
    if in_window(t, GREEN_START, GREEN_END):
        return kwh * POINTS_GREEN
    if in_window(t, PEAK_START, PEAK_END):
        return kwh * POINTS_PEAK
    return kwh * POINTS_NEUTRAL


# -------------------------
# Load + preprocess
# -------------------------
def load_data(csv_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load raw smart-plug CSV and return:
      - data: per-sample rows with delta_kwh, window, delta_points, date
      - daily: per-home per-day aggregates with green_kwh, peak_kwh, neutral
    """
    raw = pd.read_csv(csv_path)
    if raw.empty:
        raise ValueError("CSV is empty. Generate it first (e.g., run make_csv.py).")

    required = {"ts", "home", "power_w"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"CSV missing columns: {sorted(missing)}. Required columns: {sorted(required)}"
        )

    data = compute_delta_kwh(raw)
    daily = compute_daily_table(data)
    return data, daily


def compute_delta_kwh(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds:
      - ts (datetime)
      - dt_s (seconds between samples per home)
      - delta_kwh (energy used during dt)
      - window in {green, peak, neutral}
      - delta_points
      - date
    """
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df.sort_values(["home", "ts"], inplace=True)

    # Delta time (seconds) between consecutive samples per home
    df["dt_s"] = df.groupby("home")["ts"].diff().dt.total_seconds().fillna(0)

    # energy = P(W) * dt(s) / (3600*1000) -> kWh
    df["delta_kwh"] = (df["power_w"] * df["dt_s"]) / (3600.0 * 1000.0)
    df["delta_kwh"] = df["delta_kwh"].clip(lower=0)

    def label_window(ts: pd.Timestamp) -> str:
        t = ts.time()
        if in_window(t, GREEN_START, GREEN_END):
            return "green"
        if in_window(t, PEAK_START, PEAK_END):
            return "peak"
        return "neutral"

    df["window"] = df["ts"].apply(label_window)
    df["delta_points"] = df.apply(lambda r: score_kwh(r["ts"], r["delta_kwh"]), axis=1)
    df["date"] = df["ts"].dt.date
    return df


def compute_daily_table(data: pd.DataFrame) -> pd.DataFrame:
    """
    Produces daily totals per home:
      columns: home, date, green_kwh, peak_kwh, neutral
    """
    daily = (
        data.pivot_table(
            index=["home", "date"],
            columns="window",
            values="delta_kwh",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    for col in ["green", "peak", "neutral"]:
        if col not in daily.columns:
            daily[col] = 0.0

    daily.rename(columns={"green": "green_kwh", "peak": "peak_kwh"}, inplace=True)
    return daily


# -------------------------
# Streaks + metrics
# -------------------------
def compute_streak(daily_home: pd.DataFrame) -> int:
    """
    Streak definition (MVP):
    Count consecutive most-recent days where green_kwh > peak_kwh.
    """
    if daily_home.empty:
        return 0

    daily_home = daily_home.sort_values("date")
    streak = 0
    for _, r in daily_home[::-1].iterrows():
        if float(r["green_kwh"]) > float(r["peak_kwh"]):
            streak += 1
        else:
            break
    return streak


def compute_metrics(data: pd.DataFrame, daily: pd.DataFrame, replay_idx: int, home: str) -> dict:
    """
    Compute dashboard metrics for a given 'home' (Alex),
    while leaderboard uses all homes.
    Metrics are computed for the *current replay day* only.
    """
    replay_idx = int(replay_idx)
    current_ts = data.iloc[replay_idx]["ts"]

    # Current day slice (makes replay + "Day X/7" coherent)
    current_date = current_ts.date()
    data_so_far = data[(data["date"] == current_date) & (data["ts"] <= current_ts)]

    # Selected home aggregates
    sel = data_so_far[data_so_far["home"] == home]
    green_kwh = float(sel.loc[sel["window"] == "green", "delta_kwh"].sum())
    peak_kwh = float(sel.loc[sel["window"] == "peak", "delta_kwh"].sum())
    score_pts = int(round(float(sel["delta_points"].sum())))

    # Streak over all days (not just replay day)
    sel_daily = daily[daily["home"] == home][["date", "green_kwh", "peak_kwh"]]
    streak = compute_streak(sel_daily)

    # Challenges (simple proxies)
    sel_green = sel[sel["window"] == "green"].copy()
    sel_green["hour"] = sel_green["ts"].dt.hour
    hours_active = sel_green.groupby("hour")["delta_kwh"].sum()
    solar_progress = min(int((hours_active > 0.05).sum()), 3)  # threshold proxy
    solar_completed = solar_progress >= 3

    peak_limit = 2.0
    peak_completed = peak_kwh <= peak_limit

    # Leaderboard across all homes (stable ordering)
    lb = (
        data_so_far.groupby("home")["delta_points"].sum()
        .reset_index()
        .rename(columns={"delta_points": "points"})
        .sort_values(["points", "home"], ascending=[False, True])
        .reset_index(drop=True)
    )

    # Home rank
    home_row = lb[lb["home"] == home]
    rank = int(home_row.index[0] + 1) if len(home_row) else None

    # Replay day progress
    all_days = sorted(data["date"].unique())
    day_num = all_days.index(current_date) + 1 if current_date in all_days else 1
    total_days = len(all_days)

    return {
        "current_ts": current_ts,
        "green_kwh": green_kwh,
        "peak_kwh": peak_kwh,
        "score_pts": score_pts,
        "streak": streak,
        "solar_progress": solar_progress,
        "solar_completed": solar_completed,
        "peak_limit": peak_limit,
        "peak_completed": peak_completed,
        "leaderboard": lb,
        "rank": rank,
        "homes_total": int(lb.shape[0]),
        "day_num": day_num,
        "total_days": total_days,
    }

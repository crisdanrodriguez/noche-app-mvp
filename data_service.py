from __future__ import annotations

from datetime import time
import pandas as pd

from config import (
    GREEN_START, GREEN_END,
    BUSY_START, BUSY_END,
    POINTS_GREEN, POINTS_NEUTRAL, POINTS_BUSY,
)

def in_window(t: time, start: time, end: time) -> bool:
    return start <= t < end

def score_kwh(ts: pd.Timestamp, kwh: float) -> float:
    t = ts.time()
    if in_window(t, GREEN_START, GREEN_END):
        return kwh * POINTS_GREEN
    if in_window(t, BUSY_START, BUSY_END):
        return kwh * POINTS_BUSY
    return kwh * POINTS_NEUTRAL

def load_data(csv_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(csv_path)
    if raw.empty:
        raise ValueError("CSV is empty. Run make_csv.py to generate demo data.")

    required = {"ts", "dorm", "members", "power_w"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    data = compute_delta_kwh(raw)
    daily = compute_daily_table(data)
    return data, daily

def compute_delta_kwh(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df.sort_values(["dorm", "ts"], inplace=True)

    df["dt_s"] = df.groupby("dorm")["ts"].diff().dt.total_seconds().fillna(0)
    df["delta_kwh"] = (df["power_w"] * df["dt_s"]) / (3600.0 * 1000.0)
    df["delta_kwh"] = df["delta_kwh"].clip(lower=0)

    def label_window(ts: pd.Timestamp) -> str:
        t = ts.time()
        if in_window(t, GREEN_START, GREEN_END):
            return "green"
        if in_window(t, BUSY_START, BUSY_END):
            return "busy"
        return "neutral"

    df["window"] = df["ts"].apply(label_window)
    df["delta_points"] = df.apply(lambda r: score_kwh(r["ts"], r["delta_kwh"]), axis=1)
    df["date"] = df["ts"].dt.date
    return df

def compute_daily_table(data: pd.DataFrame) -> pd.DataFrame:
    daily = (
        data.pivot_table(
            index=["dorm", "members", "date"],
            columns="window",
            values="delta_kwh",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    for col in ["green", "busy", "neutral"]:
        if col not in daily.columns:
            daily[col] = 0.0

    daily.rename(columns={"green": "green_kwh", "busy": "busy_kwh"}, inplace=True)
    return daily

def compute_streak(daily_dorm: pd.DataFrame) -> int:
    # consecutive most recent days where green_kwh > busy_kwh (dorm-level)
    if daily_dorm.empty:
        return 0
    daily_dorm = daily_dorm.sort_values("date")
    streak = 0
    for _, r in daily_dorm[::-1].iterrows():
        if float(r["green_kwh"]) > float(r["busy_kwh"]):
            streak += 1
        else:
            break
    return streak

def compute_metrics(data: pd.DataFrame, daily: pd.DataFrame, replay_idx: int, dorm: str) -> dict:
    replay_idx = int(replay_idx)
    current_ts = data.iloc[replay_idx]["ts"]
    current_date = current_ts.date()

    data_so_far = data[(data["date"] == current_date) & (data["ts"] <= current_ts)]

    # dorm slice
    sel = data_so_far[data_so_far["dorm"] == dorm]
    if sel.empty:
        raise ValueError(f"Dorm '{dorm}' not found in data.")

    members = int(sel["members"].iloc[0])

    # Dorm totals -> normalize per student
    dorm_green_kwh = float(sel.loc[sel["window"] == "green", "delta_kwh"].sum())
    dorm_busy_kwh  = float(sel.loc[sel["window"] == "busy", "delta_kwh"].sum())
    dorm_points    = float(sel["delta_points"].sum())

    green_kwh_per_user = dorm_green_kwh / members
    busy_kwh_per_user  = dorm_busy_kwh / members
    points_per_user    = dorm_points / members

    score_pts = int(round(points_per_user))

    # Streak from daily dorm table (dorm-level condition)
    daily_dorm = daily[daily["dorm"] == dorm][["date", "green_kwh", "busy_kwh", "members"]]
    streak = compute_streak(daily_dorm)

    # Daily challenges (evaluated on per-user normalized numbers)
    # 1) "Solar Champion": active in 3 green hours (use per-user energy threshold)
    sel_green = sel[sel["window"] == "green"].copy()
    sel_green["hour"] = sel_green["ts"].dt.hour
    hours_active = (sel_green.groupby("hour")["delta_kwh"].sum() / members)
    solar_progress = min(int((hours_active > 0.05).sum()), 3)
    solar_completed = solar_progress >= 3

    # 2) Busy cap per user
    busy_limit = 2.0
    busy_completed = (busy_kwh_per_user <= busy_limit)

    # 3) Green > Busy per user
    green_over_busy_completed = (green_kwh_per_user > busy_kwh_per_user)

    # Leaderboard: dorm points normalized per student
    lb_raw = (
        data_so_far.groupby(["dorm", "members"])["delta_points"].sum()
        .reset_index()
        .rename(columns={"delta_points": "dorm_points"})
    )
    lb_raw["points_per_student"] = lb_raw["dorm_points"] / lb_raw["members"]

    leaderboard = (
        lb_raw.sort_values(["points_per_student", "dorm"], ascending=[False, True])
        .reset_index(drop=True)
    )

    dorm_row = leaderboard[leaderboard["dorm"] == dorm]
    rank = int(dorm_row.index[0] + 1) if len(dorm_row) else None

    all_days = sorted(data["date"].unique())
    day_num = all_days.index(current_date) + 1 if current_date in all_days else 1
    total_days = len(all_days)

    normal_kwh = float(sel.loc[sel["window"] == "normal", "delta_kwh"].sum())

    return {
        "current_ts": current_ts,
        "members": members,

        # per-user values (what we show in UI)
        "green_kwh": green_kwh_per_user,
        "busy_kwh": busy_kwh_per_user,
        "score_pts": score_pts,

        "streak": streak,

        "solar_progress": solar_progress,
        "solar_completed": solar_completed,

        "busy_limit": busy_limit,
        "busy_completed": busy_completed,

        "green_over_busy_completed": green_over_busy_completed,

        "leaderboard": leaderboard,
        "rank": rank,
        "dorms_total": int(leaderboard.shape[0]),

        "day_num": day_num,
        "total_days": total_days,

        "normal_kwh": normal_kwh,
    }

from __future__ import annotations
import pandas as pd
from datetime import time

from config import (
    GREEN_START, GREEN_END, BUSY_START, BUSY_END,
    STREAK_GOAL_DAYS, MAX_STREAK_BONUS_PCT
)

# -------------------------
# Scoring (signed points)
# -------------------------
# Green: positive, boosted by streak
# Normal: positive, HALF of Green rate, NO boost
# Busy: negative penalty (subtract)
POINTS_PER_KWH_GREEN = 160
POINTS_PER_KWH_NORMAL = 80      # exactly half of green
PENALTY_PER_KWH_BUSY = 140      # subtract

# -------------------------
# Weekly challenges (fixed rewards)
# -------------------------
WEEKLY_CHALLENGES = [
    {
        "key": "green_3day_streak",
        "title": "3-Day Green Streak",
        "desc": "3 consecutive days where Green > Busy",
        "reward": 400,
    },
    {
        "key": "low_busy_4days",
        "title": "Low Busy Hours",
        "desc": "Busy < 2.0 kWh/student on 4+ days",
        "reward": 300,
    },
    {
        "key": "green_every_day",
        "title": "Consistency",
        "desc": "At least some Green usage every day this week",
        "reward": 250,
    },
    {
        "key": "top3_week",
        "title": "Top Performer",
        "desc": "Reach Top 3 this week (so far)",
        "reward": 500,
    },
]

def in_window(t: time, start: time, end: time) -> bool:
    return start <= t < end

def label_window(ts: pd.Timestamp) -> str:
    t = ts.time()
    if in_window(t, GREEN_START, GREEN_END):
        return "green"
    if in_window(t, BUSY_START, BUSY_END):
        return "busy"
    return "normal"

def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("CSV is empty. Generate it with make_csv.py or provide valid data.")

    required = {"ts", "dorm", "members", "power_w"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df.sort_values(["dorm", "ts"], inplace=True)
    df["date"] = df["ts"].dt.date
    df["window"] = df["ts"].apply(label_window)

    # Delta time per dorm
    df["dt_s"] = df.groupby("dorm")["ts"].diff().dt.total_seconds().fillna(0)

    # Interval energy in kWh
    df["delta_kwh"] = (df["power_w"] * df["dt_s"]) / (3600.0 * 1000.0)
    df["delta_kwh"] = df["delta_kwh"].clip(lower=0)

    return df

def compute_daily_table(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby(["dorm", "members", "date", "window"])["delta_kwh"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["green", "busy", "normal"]:
        if col not in daily.columns:
            daily[col] = 0.0
    return daily

def week_bounds(d: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    d = pd.to_datetime(d).normalize()
    start = d - pd.Timedelta(days=d.weekday())  # Monday
    end = start + pd.Timedelta(days=6)          # Sunday
    return start, end

def streak_bonus_pct(streak_days: int) -> int:
    frac = min(max(streak_days / float(STREAK_GOAL_DAYS), 0.0), 1.0)
    return int(round(frac * MAX_STREAK_BONUS_PCT))

def compute_streak_days(daily: pd.DataFrame, dorm: str) -> int:
    """
    Streak: consecutive days (from most recent backwards) where green_kWh > busy_kWh.
    """
    d = daily[daily["dorm"] == dorm].sort_values("date")
    if d.empty:
        return 0

    streak = 0
    for _, r in d.iloc[::-1].iterrows():
        if float(r.get("green", 0.0)) > float(r.get("busy", 0.0)):
            streak += 1
        else:
            break
    return streak

def signed_points_from_kwh(window: str, kwh: float, bonus_pct: int) -> float:
    """
    Converts kWh to points (signed).
    - Green gets streak boost
    - Normal does NOT get streak boost
    - Busy is a penalty (negative)
    """
    if window == "green":
        boost = 1.0 + (bonus_pct / 100.0)
        return kwh * POINTS_PER_KWH_GREEN * boost

    if window == "busy":
        return -kwh * PENALTY_PER_KWH_BUSY

    # normal
    return kwh * POINTS_PER_KWH_NORMAL

def _weekly_daily_ps(daily: pd.DataFrame, dorm: str, current_date) -> pd.DataFrame:
    """
    Returns per-student daily table for the current week up to current_date (inclusive).
    Columns: date, green_ps, busy_ps, normal_ps
    """
    ws, we = week_bounds(pd.to_datetime(current_date))

    d = daily[daily["dorm"] == dorm].copy()
    if d.empty:
        return d

    d["date_ts"] = pd.to_datetime(d["date"])
    d = d[(d["date_ts"] >= ws) & (d["date_ts"] <= we) & (d["date_ts"].dt.date <= current_date)].copy()
    d.sort_values("date_ts", inplace=True)

    members = int(d["members"].iloc[-1]) if len(d) else 1
    d["green_ps"] = d.get("green", 0.0) / members
    d["busy_ps"] = d.get("busy", 0.0) / members
    d["normal_ps"] = d.get("normal", 0.0) / members

    return d[["date", "date_ts", "green_ps", "busy_ps", "normal_ps"]]

def _max_consecutive_true(flags: list[bool]) -> int:
    best = 0
    run = 0
    for f in flags:
        if f:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best

def compute_weekly_challenges(daily: pd.DataFrame, dorm: str, current_date, rank: int | None) -> tuple[list[dict], int, int]:
    """
    Weekly challenges are reactive and award fixed points when completed.
    Completion is evaluated on "week so far" up to current_date.
    Returns: (challenge_list, completed_count, bonus_points_sum)
    """
    dps = _weekly_daily_ps(daily, dorm, current_date)
    if dps.empty:
        # If no data yet, nothing completed
        ch_list = []
        for ch in WEEKLY_CHALLENGES:
            ch_list.append({**ch, "done": False, "progress_text": "0%"})
        return ch_list, 0, 0

    # 1) 3 consecutive days where Green > Busy
    flags_green_better = list((dps["green_ps"] > dps["busy_ps"]).values)
    max_run = _max_consecutive_true(flags_green_better)
    done_3day = max_run >= 3
    prog_3day = min(max_run, 3)

    # 2) Busy < 2.0 kWh/student on 4+ days
    low_busy_days = int((dps["busy_ps"] < 2.0).sum())
    done_low_busy = low_busy_days >= 4
    prog_low_busy = min(low_busy_days, 4)

    # 3) Some Green usage every day this week so far
    # (week so far means: every day we have data for must have green_ps > threshold)
    done_green_every_day = bool((dps["green_ps"] > 0.02).all())
    prog_green_every_day = int((dps["green_ps"] > 0.02).sum())
    total_days_seen = int(len(dps))

    # 4) Top 3 this week (so far)
    done_top3 = (rank is not None and rank <= 3)

    # Build challenge list with progress_text
    ch_list = [
        {
            **WEEKLY_CHALLENGES[0],
            "done": done_3day,
            "progress_text": f"{prog_3day}/3 days (best run)",
        },
        {
            **WEEKLY_CHALLENGES[1],
            "done": done_low_busy,
            "progress_text": f"{prog_low_busy}/4 days",
        },
        {
            **WEEKLY_CHALLENGES[2],
            "done": done_green_every_day,
            "progress_text": f"{prog_green_every_day}/{total_days_seen} days",
        },
        {
            **WEEKLY_CHALLENGES[3],
            "done": done_top3,
            "progress_text": "Top 3" if done_top3 else "Not Top 3 yet",
        },
    ]

    completed = sum(1 for c in ch_list if c["done"])
    bonus_points = sum(int(c["reward"]) for c in ch_list if c["done"])
    return ch_list, completed, bonus_points

def compute_weekly_leaderboard_so_far(df: pd.DataFrame, daily: pd.DataFrame, current_ts: pd.Timestamp, bonus_pct: int) -> pd.DataFrame:
    """
    Weekly leaderboard for the calendar week (Mon-Sun), up to current replay timestamp.
    Uses signed points (green boosted, normal half-rate, busy penalized).
    Adds reactive weekly challenge bonus points (per dorm) when completed.
    Normalized per student.
    """
    current_date = current_ts.date()
    ws, we = week_bounds(pd.to_datetime(current_date))

    # Week slice up to current timestamp
    dfw = df[
        (pd.to_datetime(df["date"]) >= ws) &
        (pd.to_datetime(df["date"]) <= we) &
        (df["ts"] <= current_ts)
    ].copy()

    # Row-level signed points
    dfw["row_points"] = dfw.apply(lambda r: signed_points_from_kwh(r["window"], r["delta_kwh"], bonus_pct), axis=1)

    base = (
        dfw.groupby(["dorm", "members"])["row_points"].sum()
        .reset_index()
        .rename(columns={"row_points": "weekly_points_total"})
    )

    # Compute rank on base first (before applying Top 3 bonus) for stability
    base["weekly_points_per_student_base"] = base["weekly_points_total"] / base["members"]
    base = base.sort_values(["weekly_points_per_student_base", "dorm"], ascending=[False, True]).reset_index(drop=True)
    base_rank = {row["dorm"]: int(i + 1) for i, row in base.iterrows()}

    # Add weekly challenge bonus points (reactive, week so far)
    bonus_map = {}
    for dorm_name in base["dorm"].tolist():
        rank = base_rank.get(dorm_name)
        _, _, bonus_pts = compute_weekly_challenges(daily, dorm_name, current_date, rank)
        bonus_map[dorm_name] = bonus_pts

    base["weekly_bonus_points"] = base["dorm"].map(bonus_map).fillna(0).astype(int)
    base["weekly_points_total"] = base["weekly_points_total"] + base["weekly_bonus_points"]

    # Final per-student points (used for leaderboard display)
    base["weekly_points_per_student"] = base["weekly_points_total"] / base["members"]
    lb = base.sort_values(["weekly_points_per_student", "dorm"], ascending=[False, True]).reset_index(drop=True)

    # Keep only the columns we need in the UI
    lb = lb[["dorm", "members", "weekly_points_total", "weekly_points_per_student", "weekly_bonus_points"]]
    return lb

def compute_metrics(df: pd.DataFrame, daily: pd.DataFrame, replay_idx: int, dorm: str) -> dict:
    replay_idx = int(replay_idx)
    current_ts = df.iloc[replay_idx]["ts"]
    current_date = current_ts.date()

    # Streak + bonus
    streak_days = compute_streak_days(daily, dorm)
    bonus_pct = streak_bonus_pct(streak_days)
    streak_progress = min(max(streak_days / float(STREAK_GOAL_DAYS), 0.0), 1.0)

    # Today slice (daily resets by date)
    today_df = df[(df["date"] == current_date) & (df["ts"] <= current_ts)].copy()
    dorm_today = today_df[today_df["dorm"] == dorm]
    if dorm_today.empty:
        raise ValueError(f"Dorm '{dorm}' not found in data.")

    members = int(dorm_today["members"].iloc[0])

    # kWh per student by window (today so far)
    def kwh_ps(window: str) -> float:
        return float(dorm_today.loc[dorm_today["window"] == window, "delta_kwh"].sum()) / members

    green_kwh = kwh_ps("green")
    busy_kwh = kwh_ps("busy")
    normal_kwh = kwh_ps("normal")

    total_kwh = max(green_kwh + busy_kwh + normal_kwh, 1e-9)
    pct_green = int(round(100 * green_kwh / total_kwh))
    pct_busy = int(round(100 * busy_kwh / total_kwh))

    # Daily points per student (green boosted, normal no boost, busy penalty)
    daily_points = (
        signed_points_from_kwh("green", green_kwh, bonus_pct) +
        signed_points_from_kwh("normal", normal_kwh, bonus_pct) +
        signed_points_from_kwh("busy", busy_kwh, bonus_pct)
    )
    daily_points = int(round(daily_points))

    # Week info: Day X/7
    ws, we = week_bounds(pd.to_datetime(current_date))
    day_of_week = current_ts.weekday()  # Mon=0..Sun=6
    day_label = f"Day {day_of_week + 1}/7"
    week_text = f"{current_ts.strftime('%A')} • Week: {ws.strftime('%b %d')}–{we.strftime('%b %d')}"

    # Weekly leaderboard (week so far) + reactive weekly challenge bonus
    weekly_lb = compute_weekly_leaderboard_so_far(df, daily, current_ts, bonus_pct)

    dorm_row = weekly_lb[weekly_lb["dorm"] == dorm]
    weekly_points = float(dorm_row["weekly_points_per_student"].iloc[0]) if len(dorm_row) else 0.0
    weekly_points = int(round(weekly_points))

    weekly_bonus_points = int(dorm_row["weekly_bonus_points"].iloc[0]) if len(dorm_row) else 0

    rank = int(dorm_row.index[0] + 1) if len(dorm_row) else None
    dorms_total = int(weekly_lb.shape[0])

    # Weekly challenges for THIS dorm (reactive)
    challenges, completed, _bonus_sum = compute_weekly_challenges(daily, dorm, current_date, rank)

    return {
        "current_ts": current_ts,
        "members": members,

        "day_label": day_label,
        "week_text": week_text,

        "green_kwh": green_kwh,
        "busy_kwh": busy_kwh,
        "pct_green": pct_green,
        "pct_busy": pct_busy,

        "daily_points": daily_points,
        "weekly_points": weekly_points,
        "weekly_bonus_points": weekly_bonus_points,

        "streak_days": streak_days,
        "streak_progress": streak_progress,
        "bonus_pct": bonus_pct,

        "weekly_challenges": challenges,
        "weekly_completed": completed,
        "weekly_total": len(challenges),

        "weekly_leaderboard": weekly_lb,
        "rank": rank,
        "dorms_total": dorms_total,
    }

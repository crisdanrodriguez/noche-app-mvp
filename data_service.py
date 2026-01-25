from __future__ import annotations
import pandas as pd
from datetime import time

from config import (
    GREEN_START, GREEN_END, BUSY_START, BUSY_END,
    STREAK_GOAL_DAYS, MAX_STREAK_BONUS_PCT,
    DEMO_STREAK_BASE_DAYS
)

# -------------------------
# Scoring (signed)
# -------------------------
POINTS_PER_KWH_GREEN = 160
POINTS_PER_KWH_NORMAL = 80
PENALTY_PER_KWH_BUSY = 140

# -------------------------
# Weekly challenges
# IMPORTANT: reward IS PER USER (DO NOT DIVIDE BY MEMBERS)
# -------------------------
WEEKLY_CHALLENGES = [
    {"key": "green_3day_streak", "title": "3-Day Green Streak", "desc": "3 consecutive days where Green > Busy", "reward": 150},
    {"key": "low_busy_4days",    "title": "Low Busy Hours",     "desc": "Busy < 2.0 kWh/student on 4+ days",     "reward": 100},
    {"key": "green_every_day",   "title": "Consistency",        "desc": "At least some Green usage every day",   "reward": 50},
    {"key": "top3_week",         "title": "Top Performer",      "desc": "Reach Top 3 this week (so far)",        "reward": 100},
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
        raise ValueError("CSV is empty. Run make_csv.py or provide valid data.")

    required = {"ts", "dorm", "members", "power_w"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df.sort_values(["dorm", "ts"], inplace=True)

    df["date"] = df["ts"].dt.date
    df["window"] = df["ts"].apply(label_window)

    df["dt_s"] = df.groupby("dorm")["ts"].diff().dt.total_seconds().fillna(0)
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

def signed_points_from_kwh(window: str, kwh: float, bonus_pct: int) -> float:
    if window == "green":
        boost = 1.0 + (bonus_pct / 100.0)
        return kwh * POINTS_PER_KWH_GREEN * boost
    if window == "busy":
        return -kwh * PENALTY_PER_KWH_BUSY
    return kwh * POINTS_PER_KWH_NORMAL

def _weekly_daily_ps(daily: pd.DataFrame, dorm: str, current_date) -> pd.DataFrame:
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

def _consecutive_streak_days(daily: pd.DataFrame, dorm: str, current_date) -> int:
    d = daily[daily["dorm"] == dorm].copy()
    if d.empty:
        return 0

    d = d[pd.to_datetime(d["date"]).dt.date <= current_date].copy()
    d.sort_values("date", inplace=True)

    members = int(d["members"].iloc[-1]) if len(d) else 1
    green_ps = d.get("green", 0.0) / members
    busy_ps  = d.get("busy", 0.0) / members
    flags = list((green_ps > busy_ps).values)

    streak = 0
    for f in reversed(flags):
        if f:
            streak += 1
        else:
            break
    return streak

# -------------------------
# Weekly challenges (rewards per user)
# -------------------------
def _compute_challenges_no_rank(daily: pd.DataFrame, dorm: str, current_date) -> tuple[list[dict], int]:
    dps = _weekly_daily_ps(daily, dorm, current_date)
    if dps.empty:
        ch = [{**c, "done": False, "progress_text": "0%"} for c in WEEKLY_CHALLENGES]
        return ch, 0

    flags = list((dps["green_ps"] > dps["busy_ps"]).values)
    max_run = _max_consecutive_true(flags)
    done_3day = max_run >= 3
    prog_3day = min(max_run, 3)

    low_busy_days = int((dps["busy_ps"] < 2.0).sum())
    done_low_busy = low_busy_days >= 4
    prog_low_busy = min(low_busy_days, 4)

    done_green_every_day = bool((dps["green_ps"] > 0.02).all())
    prog_green_every_day = int((dps["green_ps"] > 0.02).sum())
    total_days_seen = int(len(dps))

    ch_list = [
        {**WEEKLY_CHALLENGES[0], "done": done_3day, "progress_text": f"{prog_3day}/3 days (best run)"},
        {**WEEKLY_CHALLENGES[1], "done": done_low_busy, "progress_text": f"{prog_low_busy}/4 days"},
        {**WEEKLY_CHALLENGES[2], "done": done_green_every_day, "progress_text": f"{prog_green_every_day}/{total_days_seen} days"},
        {**WEEKLY_CHALLENGES[3], "done": False, "progress_text": "Pending rank"},
    ]

    # reward is PER USER -> sum directly
    bonus_per_user = sum(int(c["reward"]) for c in ch_list[:3] if c["done"])
    return ch_list, bonus_per_user

def compute_weekly_leaderboard_so_far(df: pd.DataFrame, daily: pd.DataFrame, current_ts: pd.Timestamp, bonus_pct: int) -> pd.DataFrame:
    """
    2-pass leaderboard:
    - Energy is dorm aggregate -> converted to per-user ONCE by dividing by members
    - Challenge rewards are already per-user -> DO NOT divide by members
    """
    current_date = current_ts.date()
    ws, we = week_bounds(pd.to_datetime(current_date))

    dfw = df[
        (pd.to_datetime(df["date"]) >= ws) &
        (pd.to_datetime(df["date"]) <= we) &
        (df["ts"] <= current_ts)
    ].copy()

    dfw["row_points"] = dfw.apply(
        lambda r: signed_points_from_kwh(r["window"], r["delta_kwh"], bonus_pct),
        axis=1
    )

    base = (
        dfw.groupby(["dorm", "members"])["row_points"].sum()
        .reset_index()
        .rename(columns={"row_points": "weekly_points_total_base"})
    )

    # Convert energy to per-user ONCE
    base["weekly_points_per_student_base"] = base["weekly_points_total_base"] / base["members"]

    # PASS B: add non-rank challenges (per-user, no division)
    nonrank_map = {}
    for dorm_name in base["dorm"].tolist():
        _, nonrank_bonus_per_user = _compute_challenges_no_rank(daily, dorm_name, current_date)
        nonrank_map[dorm_name] = int(nonrank_bonus_per_user)

    base["weekly_bonus_nonrank_per_user"] = base["dorm"].map(nonrank_map).fillna(0).astype(int)
    base["weekly_points_per_student_mid"] = base["weekly_points_per_student_base"] + base["weekly_bonus_nonrank_per_user"]

    # Rank after non-rank bonuses
    mid = base.sort_values(["weekly_points_per_student_mid", "dorm"], ascending=[False, True]).reset_index(drop=True)
    mid_rank = {row["dorm"]: int(i + 1) for i, row in mid.iterrows()}

    # PASS C: top3 (per-user, no division)
    top3_map = {}
    for dorm_name in mid["dorm"].tolist():
        rnk = mid_rank.get(dorm_name)
        done_top3 = (rnk is not None and rnk <= 3)
        top3_map[dorm_name] = int(WEEKLY_CHALLENGES[3]["reward"]) if done_top3 else 0

    mid["weekly_bonus_top3_per_user"] = mid["dorm"].map(top3_map).fillna(0).astype(int)

    # Final per-user totals
    mid["weekly_bonus_points_per_student"] = mid["weekly_bonus_nonrank_per_user"] + mid["weekly_bonus_top3_per_user"]
    mid["weekly_points_per_student"] = mid["weekly_points_per_student_mid"] + mid["weekly_bonus_top3_per_user"]

    # Optional totals (dorm-level) if you want to show them elsewhere
    mid["weekly_points_total"] = mid["weekly_points_per_student"] * mid["members"]
    mid["weekly_bonus_points_total"] = mid["weekly_bonus_points_per_student"] * mid["members"]

    lb = mid.sort_values(["weekly_points_per_student", "dorm"], ascending=[False, True]).reset_index(drop=True)
    return lb[[
        "dorm", "members",
        "weekly_points_total",
        "weekly_points_per_student",
        "weekly_bonus_points_total",
        "weekly_bonus_points_per_student",
    ]]

def compute_weekly_challenges(daily: pd.DataFrame, dorm: str, current_date, rank: int | None) -> tuple[list[dict], int, int]:
    ch_list, nonrank_bonus_per_user = _compute_challenges_no_rank(daily, dorm, current_date)
    done_top3 = (rank is not None and rank <= 3)
    ch_list[3] = {**WEEKLY_CHALLENGES[3], "done": done_top3, "progress_text": "Top 3" if done_top3 else "Not Top 3 yet"}

    completed = sum(1 for c in ch_list if c["done"])
    bonus_per_user = int(nonrank_bonus_per_user) + (int(WEEKLY_CHALLENGES[3]["reward"]) if done_top3 else 0)
    return ch_list, completed, bonus_per_user

def compute_metrics(df: pd.DataFrame, daily: pd.DataFrame, replay_idx: int, dorm: str) -> dict:
    replay_idx = int(replay_idx)
    current_ts = df.iloc[replay_idx]["ts"]
    current_date = current_ts.date()

    consec = _consecutive_streak_days(daily, dorm, current_date)
    streak_days = int(DEMO_STREAK_BASE_DAYS + consec)

    bonus_pct = streak_bonus_pct(streak_days)
    streak_progress = min(max(streak_days / float(STREAK_GOAL_DAYS), 0.0), 1.0)

    today_df = df[(df["date"] == current_date) & (df["ts"] <= current_ts)].copy()
    dorm_today = today_df[today_df["dorm"] == dorm]
    if dorm_today.empty:
        raise ValueError(f"Dorm '{dorm}' not found in data.")

    members = int(dorm_today["members"].iloc[0])

    def kwh_ps(window: str) -> float:
        return float(dorm_today.loc[dorm_today["window"] == window, "delta_kwh"].sum()) / members

    green_kwh = kwh_ps("green")
    busy_kwh = kwh_ps("busy")
    normal_kwh = kwh_ps("normal")

    total_kwh = max(green_kwh + busy_kwh + normal_kwh, 1e-9)
    pct_green = int(round(100 * green_kwh / total_kwh))
    pct_busy = int(round(100 * busy_kwh / total_kwh))

    daily_points = (
        signed_points_from_kwh("green", green_kwh, bonus_pct) +
        signed_points_from_kwh("normal", normal_kwh, bonus_pct) +
        signed_points_from_kwh("busy", busy_kwh, bonus_pct)
    )
    daily_points = int(round(daily_points))

    ws, we = week_bounds(pd.to_datetime(current_date))
    day_label = f"Day {current_ts.weekday() + 1}/7"
    week_text = f"{current_ts.strftime('%A')} • Week: {ws.strftime('%b %d')}–{we.strftime('%b %d')}"

    weekly_lb = compute_weekly_leaderboard_so_far(df, daily, current_ts, bonus_pct)

    dorm_row = weekly_lb[weekly_lb["dorm"] == dorm]
    if len(dorm_row) == 0:
        raise ValueError(f"Dorm '{dorm}' not found in weekly leaderboard.")

    weekly_points = int(round(float(dorm_row["weekly_points_per_student"].iloc[0])))
    weekly_bonus_points = int(round(float(dorm_row["weekly_bonus_points_per_student"].iloc[0])))

    rank = int(dorm_row.index[0] + 1)

    challenges, completed, bonus_per_user = compute_weekly_challenges(daily, dorm, current_date, rank)

    # Keep weekly_bonus_points consistent with challenge evaluation
    weekly_bonus_points = int(bonus_per_user)

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
        "weekly_points": weekly_points,                 # per user, includes challenges
        "weekly_bonus_points": weekly_bonus_points,     # per user, earned from challenges

        "streak_days": streak_days,
        "streak_progress": streak_progress,
        "bonus_pct": bonus_pct,

        "weekly_challenges": challenges,
        "weekly_completed": completed,
        "weekly_total": len(challenges),

        "weekly_leaderboard": weekly_lb,
        "rank": rank,
    }

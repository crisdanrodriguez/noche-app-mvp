"""
Deterministic demo CSV for USC dorm MVP.

Guarantees:
- Trojans Hall - 4B achieves multiple days where Green > Busy (per student),
  so streak increases as replay advances across days.
- Weekly challenge "3-Day Green Streak" becomes completed by day 3 (Mon-Wed),
  so challenge points are added into weekly leaderboard.

Columns:
- ts (ISO timestamp)
- dorm
- members
- power_w (aggregate dorm power in watts)
"""

from datetime import datetime, timedelta
import pandas as pd
import random
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.config import CSV_PATH, DEMO_DORM

random.seed(7)

DORMS = [
    ("Trojans Hall - 4B", 4),
    ("Cardinal House - 2A", 2),
    ("Heritage Hall - 3C", 3),
    ("Sunset Dorm - 1D", 1),
    ("Village East - 6F", 6),
    ("Apt Solo - Studio", 1),
    ("Parkside - 5E", 5),
    ("Florence Apt - 2B", 2),
    ("McCarthy Way - 4A", 4),
    ("Gateway - 3A", 3),
    ("Bunker Hill - 1A", 1),
    ("Expo House - 2C", 2),
]

def base_profile(hour: float) -> float:
    # baseline watt curve
    if 0 <= hour < 6:
        return 240
    if 6 <= hour < 10:
        return 360
    if 10 <= hour < 15:     # green
        return 520
    if 15 <= hour < 17:
        return 420
    if 17 <= hour < 21:     # busy
        return 760
    return 480

def dorm_modifier(dorm: str) -> float:
    if "Solo" in dorm:
        return 0.65
    if "Village" in dorm:
        return 1.25
    if "Parkside" in dorm:
        return 1.10
    return 1.0

def simulate_days(num_days: int = 7, step_minutes: int = 5) -> pd.DataFrame:
    now = datetime.now()
    start = (now - timedelta(days=num_days)).replace(hour=0, minute=0, second=0, microsecond=0)

    rows = []
    for d in range(num_days):
        day0 = start + timedelta(days=d)

        # We’ll “force” Trojans Hall to have a strong Green pattern for first 4 days
        # so 3-day consecutive challenge completes.
        trojans_green_boost = 1.0
        trojans_busy_cut = 1.0
        if d <= 3:
            trojans_green_boost = 1.35   # more midday activity
            trojans_busy_cut = 0.70      # less busy usage (students shift loads)
        elif d == 4:
            trojans_green_boost = 1.15
            trojans_busy_cut = 0.85
        else:
            trojans_green_boost = 1.0
            trojans_busy_cut = 1.0

        for k in range(int(24 * 60 / step_minutes)):
            ts = day0 + timedelta(minutes=k * step_minutes)
            hour = ts.hour + ts.minute / 60.0

            for dorm, members in DORMS:
                b = base_profile(hour) * dorm_modifier(dorm)

                # Deterministic-ish spikes
                spike = 0.0
                noise = random.uniform(-30, 30)

                # Generic spikes for all dorms
                if 11 <= hour <= 14 and random.random() < 0.10:
                    spike += random.uniform(250, 700)
                if 18 <= hour <= 20 and random.random() < 0.20:
                    spike += random.uniform(400, 1200)

                power = b + spike + noise

                # Force Trojans pattern to make streak + challenges visible
                if dorm == DEMO_DORM:
                    if 10 <= hour < 15:
                        power *= trojans_green_boost
                        # add extra midday flexible loads (laundry/dishwasher)
                        if random.random() < 0.18:
                            power += random.uniform(300, 900)
                    if 17 <= hour < 21:
                        power *= trojans_busy_cut
                        # reduce chance of heavy busy spikes
                        if random.random() < 0.08:
                            power += random.uniform(150, 350)

                # Make some other dorms “worse” in busy hours so Trojans can rank up/down
                if dorm != DEMO_DORM and 17 <= hour < 21:
                    if "Village" in dorm or "Parkside" in dorm:
                        power *= 1.10
                        if random.random() < 0.15:
                            power += random.uniform(300, 800)

                power = max(120, power)

                rows.append({
                    "ts": ts.isoformat(),
                    "dorm": dorm,
                    "members": members,
                    "power_w": round(power, 1)
                })

    df = pd.DataFrame(rows)
    df.to_csv(CSV_PATH, index=False)
    return df

if __name__ == "__main__":
    df = simulate_days(num_days=7, step_minutes=5)
    print(f"Wrote {len(df):,} rows to {CSV_PATH}")
    print(df.head())

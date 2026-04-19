"""
Generate deterministic demo data for the Origin App MVP.

The output is intended for local playback inside the Dash dashboard and
keeps the scoring mechanics visible during the replay window.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import random

import pandas as pd

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
    if 0 <= hour < 6:
        return 240
    if 6 <= hour < 10:
        return 360
    if 10 <= hour < 15:
        return 520
    if 15 <= hour < 17:
        return 420
    if 17 <= hour < 21:
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


def simulate_days(
    num_days: int = 7,
    step_minutes: int = 5,
    output_path: Path = CSV_PATH,
) -> pd.DataFrame:
    now = datetime.now()
    start = (now - timedelta(days=num_days)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    rows = []
    for day_idx in range(num_days):
        day_start = start + timedelta(days=day_idx)

        trojans_green_boost = 1.0
        trojans_busy_cut = 1.0
        if day_idx <= 3:
            trojans_green_boost = 1.35
            trojans_busy_cut = 0.70
        elif day_idx == 4:
            trojans_green_boost = 1.15
            trojans_busy_cut = 0.85

        for step_idx in range(int(24 * 60 / step_minutes)):
            ts = day_start + timedelta(minutes=step_idx * step_minutes)
            hour = ts.hour + ts.minute / 60.0

            for dorm, members in DORMS:
                baseline = base_profile(hour) * dorm_modifier(dorm)
                spike = 0.0
                noise = random.uniform(-30, 30)

                if 11 <= hour <= 14 and random.random() < 0.10:
                    spike += random.uniform(250, 700)
                if 18 <= hour <= 20 and random.random() < 0.20:
                    spike += random.uniform(400, 1200)

                power = baseline + spike + noise

                if dorm == DEMO_DORM:
                    if 10 <= hour < 15:
                        power *= trojans_green_boost
                        if random.random() < 0.18:
                            power += random.uniform(300, 900)
                    if 17 <= hour < 21:
                        power *= trojans_busy_cut
                        if random.random() < 0.08:
                            power += random.uniform(150, 350)

                if dorm != DEMO_DORM and 17 <= hour < 21:
                    if "Village" in dorm or "Parkside" in dorm:
                        power *= 1.10
                        if random.random() < 0.15:
                            power += random.uniform(300, 800)

                rows.append(
                    {
                        "ts": ts.isoformat(),
                        "dorm": dorm,
                        "members": members,
                        "power_w": round(max(120, power), 1),
                    }
                )

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def main() -> None:
    df = simulate_days()
    print(f"Wrote {len(df):,} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()

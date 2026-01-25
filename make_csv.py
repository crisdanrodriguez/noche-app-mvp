import random
import pandas as pd
from datetime import datetime, timedelta

CSV_PATH = "smart_plug_stream.csv"

def generate_demo_csv(path: str = CSV_PATH, num_dorms: int = 10):
    """
    Generates demo USC dorm power stream for 7 days.
    Adds per-day variability per dorm so weekly leaderboard can fluctuate during replay.
    Columns:
      - ts (ISO timestamp)
      - dorm
      - members
      - power_w
    """
    random.seed(7)

    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)

    dorms = [("Trojans Hall - 4B", 4)]  # Alex dorm

    dorm_name_pool = [
        "Cardinal Gardens - A2",
        "Pardee Tower - 9F",
        "University Village - 12C",
        "Fluor Tower - 6D",
        "Marks Hall - 3A",
        "McCarthy Way - 2E",
        "Birnkrant - 8C",
        "New North - 5B",
        "Century Apt - 1G",
        "Sunset Apt - 1B",
        "Gateway - 7F",
        "Parkside - 10A",
    ]

    needed = max(0, num_dorms - 1)
    picked = dorm_name_pool[:needed]
    for name in picked:
        dorms.append((name, random.choice([1, 2, 3, 4])))

    profiles = ["green_shifter", "busy_heavy", "balanced", "night_owl"]
    dorm_profile = {}
    for dorm, _ in dorms:
        dorm_profile[dorm] = "green_shifter" if dorm == "Trojans Hall - 4B" else random.choice(profiles)

    # Per-dorm daily multipliers to force weekly rank movement
    # Example: a dorm may have a "bad day" mid-week and drop in ranking.
    dorm_day_factor = {dorm: [] for dorm, _ in dorms}
    for dorm, _ in dorms:
        for _day in range(7):
            dorm_day_factor[dorm].append(random.uniform(0.85, 1.20))

    def power_pattern(profile: str, ts: datetime) -> float:
        h = ts.hour + ts.minute / 60.0
        base = random.uniform(80, 140)

        if profile == "green_shifter":
            if 11 <= h <= 14:
                return base + random.uniform(550, 950)
            if 18 <= h <= 20:
                return base + random.uniform(160, 320)
            return base + random.uniform(60, 140)

        if profile == "busy_heavy":
            if 17 <= h <= 21:
                return base + random.uniform(520, 980)
            if 10 <= h <= 14:
                return base + random.uniform(160, 320)
            return base + random.uniform(70, 160)

        if profile == "night_owl":
            if 20 <= h <= 23:
                return base + random.uniform(450, 850)
            if 10 <= h <= 14:
                return base + random.uniform(220, 420)
            return base + random.uniform(60, 150)

        # balanced
        if 10 <= h <= 14:
            return base + random.uniform(300, 650)
        if 17 <= h <= 20:
            return base + random.uniform(260, 540)
        return base + random.uniform(60, 150)

    rows = []
    for d in range(7):
        day0 = base_date + timedelta(days=d)
        for i in range(24 * 6):  # every 10 minutes
            ts = day0 + timedelta(minutes=10 * i)

            for dorm, members in dorms:
                profile = dorm_profile[dorm]
                p = power_pattern(profile, ts)

                # Apply dorm/day factor + small noise to create rank fluctuations
                p *= dorm_day_factor[dorm][d]
                p *= random.uniform(0.97, 1.03)

                rows.append({
                    "ts": ts.isoformat(),
                    "dorm": dorm,
                    "members": members,
                    "power_w": round(p, 1),
                })

    df = pd.DataFrame(rows).sort_values(["dorm", "ts"])
    df.to_csv(path, index=False)
    print(f"✅ Wrote {len(df)} rows to {path} with {len(dorms)} dorms")

if __name__ == "__main__":
    generate_demo_csv(CSV_PATH, num_dorms=10)

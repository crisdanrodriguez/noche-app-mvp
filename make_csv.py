import pandas as pd
from datetime import datetime, timedelta

CSV_PATH = "data/smart_plug_stream.csv"

def make_demo_csv(path: str):
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)

    # Dorms/groups (leaderboard compares per-student)
    dorms = [
        ("Trojans Hall - 4B", 4),     # Alex dorm
        ("Cardinal Gardens - A2", 1),
        ("University Village - 12C", 3),
        ("Pardee Tower - 9F", 2),
        ("Century - 6D", 4),
        ("Sunset Apt - 1B", 1),
    ]

    def pattern(dorm: str, ts: datetime) -> float:
        h = ts.hour + ts.minute/60
        base = 120

        # Make slightly different behavior per dorm
        if dorm == "Trojans Hall - 4B":        # tries shifting to Green Hours
            if 11 <= h <= 14: return base + 900
            if 18 <= h <= 20: return base + 260
            return base + 90

        if dorm == "Cardinal Gardens - A2":    # solo apartment
            if 12 <= h <= 14: return base + 550
            if 18 <= h <= 20: return base + 230
            return base + 80

        if dorm == "University Village - 12C": # 3 students, a bit heavier at night
            if 19 <= h <= 23: return base + 650
            if 12 <= h <= 13: return base + 350
            return base + 120

        if dorm == "Pardee Tower - 9F":
            if 10 <= h <= 15: return base + 700
            if 18 <= h <= 21: return base + 220
            return base + 100

        if dorm == "Century - 6D":
            if 18 <= h <= 20: return base + 720
            if 11 <= h <= 14: return base + 500
            return base + 110

        if dorm == "Sunset Apt - 1B":
            if 12 <= h <= 14: return base + 480
            if 18 <= h <= 20: return base + 210
            return base + 75

        return base + 100

    rows = []
    for d in range(7):
        day0 = base_date + timedelta(days=d)
        for i in range(24 * 6):  # every 10 minutes
            ts = day0 + timedelta(minutes=10 * i)
            for dorm, members in dorms:
                p = pattern(dorm, ts)
                rows.append({
                    "ts": ts.isoformat(),
                    "dorm": dorm,
                    "members": members,
                    "power_w": round(p, 1),
                })

    df = pd.DataFrame(rows).sort_values("ts")
    df.to_csv(path, index=False)
    print(f"✅ Wrote {len(df)} rows to {path}")

if __name__ == "__main__":
    make_demo_csv(CSV_PATH)

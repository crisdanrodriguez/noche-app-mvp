import pandas as pd
from datetime import datetime, timedelta
import random

OUT = "smart_plug_stream.csv"

# Sampling: every 5 minutes gives smoother motion than 10 min
STEP_MIN = 5
DAYS = 7

# Homes/dorms in the leaderboard (Alex is the "logged-in" user)
HOMES = {
    "Alex": "office_worker",             # <- Logged-in user
    "Dorm A - Floor 3": "students",
    "Dorm B - Floor 1": "students",
    "GreenHouse": "office_worker",
    "VoltRiders": "ev_owner",
    "SunChasers": "ev_owner",
    "PeakBusters": "students",
}

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def pattern(persona: str, ts: datetime) -> float:
    """Return power in Watts for a given persona at time ts."""
    h = ts.hour + ts.minute / 60.0
    base = 120 + random.uniform(-10, 10)

    # Office worker: midday shift + mild evening
    if persona == "office_worker":
        if 11 <= h <= 14:  # dishwasher/laundry midday
            return base + random.uniform(750, 1050)
        if 18 <= h <= 20:  # evening cooking + some HVAC
            return base + random.uniform(300, 550)
        return base + random.uniform(60, 120)

    # EV owner: big flexible EV load midday + sometimes late night
    if persona == "ev_owner":
        if 12 <= h <= 14:
            return base + random.uniform(2200, 3200)
        if 22 <= h <= 23:
            return base + random.uniform(1400, 2200)
        if 18 <= h <= 20:
            return base + random.uniform(250, 500)
        return base + random.uniform(70, 140)

    # Students: late evening spikes + some midday
    if persona == "students":
        if 19 <= h <= 23:
            return base + random.uniform(450, 900)  # gaming + group cooking
        if 12 <= h <= 13:
            return base + random.uniform(250, 550)
        return base + random.uniform(80, 160)

    return base + random.uniform(80, 150)

def device_from_power(p):
    if p > 2000:
        return "ev_charger"
    if p > 800:
        return "dishwasher"
    if p > 500:
        return "gaming_pc"
    if p > 250:
        return "hvac"
    return "idle"

def main():
    random.seed(7)  # deterministic demo
    start = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=DAYS-1))

    rows = []
    total_steps = int((24 * 60 / STEP_MIN) * DAYS)

    for step in range(total_steps):
        ts = start + timedelta(minutes=STEP_MIN * step)

        for home, persona in HOMES.items():
            p = pattern(persona, ts)
            rows.append({
                "ts": ts.isoformat(),
                "home": home,
                "device": device_from_power(p),
                "power_w": round(p, 1),
            })

    df = pd.DataFrame(rows).sort_values(["ts", "home"])
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} with {len(df)} rows, homes={len(HOMES)}")

if __name__ == "__main__":
    main()

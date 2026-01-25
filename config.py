from datetime import time

# =========================
# Data / Replay
# =========================
CSV_PATH = "data/smart_plug_stream.csv"
TICK_MS = 3000
REPLAY_STEP_ROWS = 10

DEMO_DORM = "Trojans Hall - 4B"
DEMO_USER_NAME = "Alex"

# =========================
# Time windows (MVP)
# =========================
GREEN_START = time(10, 0)
GREEN_END   = time(15, 0)

BUSY_START  = time(17, 0)
BUSY_END    = time(21, 0)

# =========================
# Points per kWh
# =========================
POINTS_GREEN   = 50
POINTS_NEUTRAL = 10
POINTS_BUSY    = -5

# =========================
# UI Styling
# =========================
BG = "#f6faf7"
TEXT = "#22302c"
MUTED = "#6b7b76"
BORDER = "#e8ecea"

CARD_RADIUS = "16px"
SHADOW = "0 10px 30px rgba(16, 24, 40, 0.08)"
SHADOW_SOFT = "0 8px 24px rgba(0,0,0,0.05)"

GREEN = "#2e7d32"
GREEN_LIGHT = "#b7e1c1"

RED = "#c62828"
RED_LIGHT = "#f5b5b5"

GREY = "#cfd8d3"  

FONT_FAMILY = "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial"

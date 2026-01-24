from datetime import time

CSV_PATH = "data/smart_plug_stream.csv"

# Replay behavior
TICK_MS = 3000       
REPLAY_STEP_ROWS = 10  

# "Logged-in" user
DEMO_HOME = "Alex"
DEMO_USER_NAME = "Alex"

# Time windows
GREEN_START = time(10, 0)
GREEN_END   = time(15, 0)
PEAK_START  = time(17, 0)
PEAK_END    = time(21, 0)

# Points per kWh
POINTS_GREEN = 150
POINTS_NEUTRAL = 100
POINTS_PEAK = 70

# UI styling
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

FONT_FAMILY = "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial"

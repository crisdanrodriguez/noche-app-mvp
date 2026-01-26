import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from config import (
    BG, BORDER, SHADOW, FONT_FAMILY,
    CSV_PATH, TICK_MS, REPLAY_STEP_ROWS,
    DEMO_DORM, DEMO_USER_NAME, DEMO_LOCATION,
    GREEN_START, GREEN_END, BUSY_START, BUSY_END, TEXT,
)

from data_service import load_data, compute_daily_table, compute_metrics
from ui_components import (
    header_block,
    live_location_card,
    points_card,
    kwh_usage_card,
    streak_card,
    weekly_challenges_card,
    leaderboard_card,
)

# -------------------------
# Load CSV once at startup
# -------------------------
df = load_data(CSV_PATH)
daily = compute_daily_table(df)

external_stylesheets = [
    dbc.themes.FLATLY,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap",
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Noche MVP"

ROW1_H = "200px"
ROW2_H = "140px"
ROW3_H = "360px"

app.layout = html.Div(
    style={"background": BG, "minHeight": "100vh", "padding": "18px", "fontFamily": FONT_FAMILY},
    children=[
        dcc.Interval(id="tick", interval=TICK_MS, n_intervals=0),
        dcc.Store(id="replay_idx", data=0),
        dcc.Store(id="prev_ranks", data={}),

        html.Div(
            style={
                "maxWidth": "1100px",
                "margin": "0 auto",
                "background": "white",
                "borderRadius": "18px",
                "overflow": "hidden",
                "border": f"1px solid {BORDER}",
                "boxShadow": SHADOW,
            },
            children=[
                header_block(company="Noche", user=DEMO_USER_NAME),
                html.Div(f"Welcome, {DEMO_USER_NAME}!", style={"fontSize": "20px", "fontWeight": 800, "color": TEXT, "marginTop": "6px",
                                                               "paddingLeft": "25px"}),
                html.Div(style={"padding": "16px 18px 20px 18px"}, children=[
                    html.Div(id="main_content"),
                ]),
            ],
        ),
    ],
)

@app.callback(
    Output("replay_idx", "data"),
    Input("tick", "n_intervals"),
    State("replay_idx", "data"),
)
def advance_replay(_, idx):
    idx = int(idx) + REPLAY_STEP_ROWS
    if idx >= len(df) - 1:
        idx = 0
    return idx

@app.callback(
    Output("main_content", "children"),
    Output("prev_ranks", "data"),
    Input("replay_idx", "data"),
    State("prev_ranks", "data"),
)
def render(replay_idx, prev_ranks):
    m = compute_metrics(df, daily, replay_idx, DEMO_DORM)

    live_time_text = m["current_ts"].strftime("%I:%M %p").lstrip("0")
    members = m["members"]

    # Full weekly leaderboard for movement arrows
    weekly_lb = m["weekly_leaderboard"].reset_index(drop=True).copy()

    current_ranks = {row["dorm"]: int(i + 1) for i, row in weekly_lb.iterrows()}

    arrows = {}
    for dorm_name, rank_now in current_ranks.items():
        rank_prev = prev_ranks.get(dorm_name)
        if rank_prev is None:
            arrows[dorm_name] = {"symbol": "=", "color": "#94a3b8"}
        else:
            delta = rank_prev - rank_now
            if delta > 0:
                arrows[dorm_name] = {"symbol": "↑", "color": "#16a34a"}
            elif delta < 0:
                arrows[dorm_name] = {"symbol": "↓", "color": "#dc2626"}
            else:
                arrows[dorm_name] = {"symbol": "=", "color": "#94a3b8"}

    next_prev_ranks = current_ranks

    green_window_text = f"{GREEN_START.strftime('%I:%M %p').lstrip('0')} – {GREEN_END.strftime('%I:%M %p').lstrip('0')}"
    busy_window_text = f"{BUSY_START.strftime('%I:%M %p').lstrip('0')} – {BUSY_END.strftime('%I:%M %p').lstrip('0')}"

    row1 = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    live_location_card(live_time_text, DEMO_LOCATION, DEMO_DORM, members),
                    style={"height": "100%", "minHeight": ROW1_H},
                ),
                md=4, xs=12
            ),
            dbc.Col(
                html.Div(
                    points_card(
                        daily_points=m["daily_points"],
                        weekly_points=m["weekly_points"],
                        weekly_bonus_points=m["weekly_bonus_points"],
                        day_label=m["day_label"],
                        week_text=m["week_text"],
                    ),
                    style={"height": "100%", "minHeight": ROW1_H},
                ),
                md=5, xs=12
            ),
            dbc.Col(
                html.Div(
                    streak_card(
                        streak_days=m["streak_days"],
                        progress=m["streak_progress"],
                        bonus_pct=m["bonus_pct"],
                    ),
                    style={"height": "100%", "minHeight": ROW1_H},
                ),
                md=3, xs=12
            ),
        ],
        className="g-3",
        align="stretch",
    )

    row2 = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    kwh_usage_card(
                        title="Green Hours Usage (per student)",
                        window_text=green_window_text,
                        kwh=m["green_kwh"],
                        pct=m["pct_green"],
                        color="#2e7d32",
                        color_light="#b7e1c1"
                    ),
                    style={"height": "100%", "minHeight": ROW2_H},
                ),
                md=6, xs=12
            ),
            dbc.Col(
                html.Div(
                    kwh_usage_card(
                        title="Busy Hours Usage (per student)",
                        window_text=busy_window_text,
                        kwh=m["busy_kwh"],
                        pct=m["pct_busy"],
                        color="#c62828",
                        color_light="#f5b5b5"
                    ),
                    style={"height": "100%", "minHeight": ROW2_H},
                ),
                md=6, xs=12
            ),
        ],
        className="g-3",
        align="stretch",
    )

    row3 = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    weekly_challenges_card(
                        challenges=m["weekly_challenges"],
                        completed=m["weekly_completed"],
                        total=m["weekly_total"],
                    ),
                    style={"height": "100%", "minHeight": ROW3_H},
                ),
                md=6, xs=12
            ),
            dbc.Col(
                html.Div(
                    leaderboard_card(
                        df_lb=weekly_lb,
                        selected_dorm=DEMO_DORM,
                        arrows=arrows,
                        target_rows=8
                    ),
                    style={"height": "100%", "minHeight": ROW3_H},
                ),
                md=6, xs=12
            ),
        ],
        className="g-3",
        align="stretch",
    )

    content = html.Div([
        row1,
        html.Div(style={"height": "10px"}),
        row2,
        html.Div(style={"height": "10px"}),
        row3
    ])

    return content, next_prev_ranks


if __name__ == "__main__":
    app.run(debug=False, port=8040)

import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc

from config import (
    BG, BORDER, SHADOW, FONT_FAMILY,
    CSV_PATH, TICK_MS, REPLAY_STEP_ROWS,
    DEMO_HOME, DEMO_USER_NAME,
    GREEN, GREEN_LIGHT, RED, RED_LIGHT,
    TEXT, MUTED,
    GREEN_START, GREEN_END, PEAK_START, PEAK_END,
)
from data_service import load_data, compute_metrics
from ui_components import (
    card, progress_card, streak_card, leaderboard_card, energy_bar_chart,
    tips_card, live_badge
)

data, daily = load_data(CSV_PATH)

external_stylesheets = [
    dbc.themes.FLATLY,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap",
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "EcoEnergy Challenge (MVP)"


# --- Row height constants (tune as needed) ---
ROW1_H = "170px"
ROW2_H = "120px"
ROW3_H = "300px"
ROW4_H = "200px"


def brand_header():
    return html.Div(
        style={
            "padding": "26px 16px 14px 16px",
            "borderBottom": f"1px solid {BORDER}",
            "background": "linear-gradient(180deg, #eaf6ee 0%, #ffffff 88%)",
            "textAlign": "center",
        },
        children=[
            html.Div("EcoEnergy", style={"fontSize": "34px", "fontWeight": 900, "color": "#1f5c3a", "letterSpacing": "-0.5px"}),
            html.Div(f"Welcome, {DEMO_USER_NAME}!", style={"fontSize": "20px", "fontWeight": 800, "color": TEXT, "marginTop": "6px"}),
        ],
    )


def live_location_card(live_time_text: str, location_text: str):
    # Tip removed from here
    return card(
        [
            html.Div("Time", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(live_badge(live_time_text), style={"marginTop": "8px"}),

            html.Div(style={"height": "14px"}),

            html.Div("Location", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(location_text, style={"fontWeight": 900, "color": TEXT, "marginTop": "4px"}),

            html.Div(style={"height": "10px"}),            
        ],
        padding="16px 16px",
    )


def todays_points_card(points: int, subtitle: str, subline: str):
    return card(
        [
            html.Div("Today's Points", style={"fontWeight": 800, "color": MUTED, "fontSize": "13px"}),
            html.Div(f"{points} pts", style={"fontWeight": 900, "fontSize": "44px", "lineHeight": "1.0", "marginTop": "6px", "color": TEXT}),
            html.Div(subtitle, style={"fontWeight": 900, "color": "#1f5c3a", "marginTop": "10px"}),
            html.Div(subline, style={"color": MUTED, "fontSize": "12px", "marginTop": "6px"}),
        ],
        padding="16px 16px",
    )


def weekly_challenges_panel(completed: int, total: int, items: list[tuple[str, str]]):
    return card(
        [
            html.Div(
                [
                    html.Div("Weekly Challenges", style={"fontWeight": 900, "fontSize": "18px", "color": TEXT}),
                    html.Div(f"{completed} / {total} completed", style={"color": MUTED, "fontWeight": 800}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"},
            ),
            html.Div(style={"height": "10px"}),

            dbc.Button(
                "View Weekly Challenges ▸",
                id="btn_weekly",
                color="primary",
                size="sm",
                style={"borderRadius": "999px", "fontWeight": 800},
            ),

            dbc.Collapse(
                id="collapse_weekly",
                is_open=False,
                children=[
                    html.Div(style={"height": "12px"}),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("✅ " if status == "done" else "⛔ "),
                                    html.Span(text, style={"fontWeight": 800 if status == "done" else 700}),
                                ],
                                style={
                                    "padding": "10px 10px",
                                    "border": f"1px solid {BORDER}",
                                    "borderRadius": "12px",
                                    "marginBottom": "8px",
                                    "background": "#eefaf1" if status == "done" else "white",
                                },
                            )
                            for status, text in items
                        ]
                    ),
                ],
            ),
        ],
        padding="16px 16px",
    )


app.layout = html.Div(
    style={"background": BG, "minHeight": "100vh", "padding": "18px", "fontFamily": FONT_FAMILY},
    children=[
        dcc.Interval(id="tick", interval=TICK_MS, n_intervals=0),
        dcc.Store(id="replay_idx", data=0),
        dcc.Store(id="prev_rank", data=None),
        dcc.Store(id="weekly_open", data=False),


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
                brand_header(),
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
    if idx >= len(data) - 1:
        idx = 0
    return idx


@app.callback(
    Output("main_content", "children"),
    Output("prev_rank", "data"),
    Input("replay_idx", "data"),
    State("prev_rank", "data"),
)
def render(replay_idx, prev_rank):
    m = compute_metrics(data, daily, replay_idx, DEMO_HOME)

    # Rank movement (for row 3)
    rank = m["rank"]
    rank_delta = None
    if prev_rank is not None and rank is not None:
        rank_delta = prev_rank - rank

    if rank is None:
        rank_move = "—"
    elif rank_delta is None or rank_delta == 0:
        rank_move = "—"
    elif rank_delta > 0:
        rank_move = f"↑{rank_delta}"
    else:
        rank_move = f"↓{abs(rank_delta)}"

    # Live time + location
    live_time_text = m["current_ts"].strftime("%I:%M %p").lstrip("0")
    location_text = "Los Angeles, CA"  # MVP static

    # Tip logic + color variant
    t = m["current_ts"].time()
    if GREEN_START <= t < GREEN_END:
        tip_title = "🌿 Green Window Active"
        tip_body = "Best time to run dishwasher, laundry, or EV charging. You earn bonus points now."
        tip_variant = "green"
    elif PEAK_START <= t < PEAK_END:
        tip_title = "⚠️ Dirty Window Active"
        tip_body = "Delay laundry or EV charging until after 9 PM to score higher and reduce grid stress."
        tip_variant = "peak"
    else:
        tip_title = "⏳ Neutral Hours"
        tip_body = "If possible, plan heavy loads for the next Green Window (10 AM–3 PM)."
        tip_variant = "neutral"


    # Weekly challenges (demo list)
    weekly_items = [
        ("done", "Shift 2 heavy loads into the Green Window"),
        ("done", "Keep Peak usage under 2.0 kWh for 2 days"),
        ("todo", "Achieve 5 Green>Peak days this week"),
        ("todo", "Avoid Dirty window for EV charging (2 sessions)"),
        ("todo", "Complete 3 Solar Champion days"),
    ]
    weekly_completed = sum(1 for s, _ in weekly_items if s == "done")
    weekly_total = len(weekly_items)

    # -------------------------
    # ROW 1: Live/Hour/Location | Today's Points | Tip
    # Same height across all 3 cards
    # -------------------------
    row1 = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    live_location_card(live_time_text, location_text),
                    style={"height": "100%", "minHeight": ROW1_H},
                ),
                md=4, xs=12
            ),
            dbc.Col(
                html.Div(
                    todays_points_card(
                        m["score_pts"],
                        subtitle="Daily Challenge",
                        subline=f"Replay: Day {m['day_num']} / {m['total_days']}",
                    ),
                    style={"height": "100%", "minHeight": ROW1_H},
                ),
                md=5, xs=12
            ),
            dbc.Col(
                html.Div(
                    tips_card(tip_title, tip_body, tip_variant),
                    style={"height": "100%", "minHeight": ROW1_H},
                ),
                md=3, xs=12
            ),
        ],
        className="g-3",
        align="stretch",
    )

    # -------------------------
    # ROW 2: Green Usage | Peak Usage (same height)
    # -------------------------
    row2 = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    progress_card("Green Window Usage", m["green_kwh"], "10 AM – 3 PM", GREEN, GREEN_LIGHT, vmax=4.0),
                    style={"height": "100%", "minHeight": ROW2_H},
                ),
                md=6, xs=12
            ),
            dbc.Col(
                html.Div(
                    progress_card("Dirty Window Usage", m["peak_kwh"], "5 PM – 9 PM", RED, RED_LIGHT, vmax=4.0),
                    style={"height": "100%", "minHeight": ROW2_H},
                ),
                md=6, xs=12
            ),
        ],
        className="g-3",
        align="stretch",
    )

    # -------------------------
    # ROW 3: Today Graph | Weekly Leaderboard (same height)
    # Make graph fill available height
    # -------------------------
    graph_card = card(
        [
            html.Div(
                [
                    html.Div("Today: Green vs High Demand Hours", style={"fontWeight": 900, "color": TEXT}),
                    html.Div(f"Rank move: {rank_move}", style={"color": MUTED, "fontSize": "12px", "fontWeight": 800}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline", "marginBottom": "8px"},
            ),
            dcc.Graph(
                figure=energy_bar_chart(m["green_kwh"], m["peak_kwh"]),
                config={"displayModeBar": False},
                style={"flex": "1"},
            ),
        ],
        padding="14px 14px",
    )

    row3 = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    graph_card,
                    style={"height": "100%", "minHeight": ROW3_H, "display": "flex"},
                ),
                md=6, xs=12
            ),
            dbc.Col(
                html.Div(
                    leaderboard_card(m["leaderboard"]),
                    style={"height": "100%", "minHeight": ROW3_H},
                ),
                md=6, xs=12
            ),
        ],
        className="g-3",
        align="stretch",
    )

    # -------------------------
    # ROW 4: Streak | Weekly Challenges (same height)
    # -------------------------
    row4 = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    streak_card(m["streak"], bonus_pct=25),
                    style={"height": "100%", "minHeight": ROW4_H},
                ),
                md=6, xs=12
            ),
            dbc.Col(
                html.Div(
                    weekly_challenges_panel(weekly_completed, weekly_total, weekly_items),
                    style={"height": "100%", "minHeight": ROW4_H},
                ),
                md=6, xs=12
            ),
        ],
        className="g-3",
        align="stretch",
    )

    layout = html.Div(
        [
            row1,
            html.Div(style={"height": "10px"}),
            row2,
            html.Div(style={"height": "10px"}),
            row3,
            html.Div(style={"height": "10px"}),
            row4,
        ]
    )

    return layout, rank


if __name__ == "__main__":
    app.run(debug=True, port=8050)

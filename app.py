import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc

from config import (
    BG, BORDER, SHADOW, FONT_FAMILY,
    CSV_PATH, TICK_MS, REPLAY_STEP_ROWS,
    DEMO_DORM, DEMO_USER_NAME,
    GREEN, GREEN_LIGHT, RED, RED_LIGHT,
    TEXT, MUTED,
)
from data_service import load_data, compute_metrics
from ui_components import (
    card, progress_card, streak_card, leaderboard_card, energy_pct_chart, live_badge
)

data, daily = load_data(CSV_PATH)

external_stylesheets = [
    dbc.themes.FLATLY,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap",
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Noche (MVP)"

ROW1_H = "170px"
ROW2_H = "120px"
ROW3_H = "300px"
ROW4_H = "210px"

def brand_header():
    return html.Div(
        style={
            "padding": "26px 16px 14px 16px",
            "borderBottom": f"1px solid {BORDER}",
            "background": "linear-gradient(180deg, #eaf6ee 0%, #ffffff 88%)",
            "textAlign": "center",
        },
        children=[
            html.Div("Noche", style={"fontSize": "40px", "fontWeight": 900, "color": "#1f5c3a", "letterSpacing": "-0.0px"}),
            html.Div("To a greener future", style={"fontSize": "25px", "fontWeight": 900, "color": "#1f5c3a", "letterSpacing": "-0.0px"}),
        ],
    )

def live_location_card(live_time_text: str, location_text: str, dorm_text: str, members: int):
    return card(
        [
            html.Div("Time", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(live_badge(live_time_text), style={"marginTop": "8px"}),

            html.Div(style={"height": "10px"}),

            html.Div("Location", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(location_text, style={"fontWeight": 900, "color": TEXT, "marginTop": "4px"}),

            html.Div(style={"height": "10px"}),

            html.Div("Dorm / Group", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(dorm_text, style={"fontWeight": 900, "color": TEXT, "marginTop": "4px"}),
            html.Div(f"{members} students", style={"color": MUTED, "fontSize": "12px", "marginTop": "2px"}),
        ],
        padding="16px 16px",
    )

def todays_points_card(points: int, replay_text: str, completed: int, total: int):
    frac = 0 if total == 0 else max(0, min(completed / total, 1))
    return card(
        [
            html.Div(
                [
                    html.Div("Today's Points", style={"fontWeight": 800, "color": MUTED, "fontSize": "13px"}),
                    html.Div(
                        f"Daily Challenges {completed}/{total}",
                        style={"fontWeight": 900, "color": "#1f5c3a", "fontSize": "13px"},
                    ),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"},
            ),
            html.Div(
                f"{points} pts",
                style={"fontWeight": 900, "fontSize": "44px", "lineHeight": "1.0", "marginTop": "10px", "color": TEXT},
            ),
            html.Div(replay_text, style={"color": MUTED, "fontSize": "12px", "marginTop": "8px"}),

            html.Div(style={"height": "10px"}),
            html.Div(
                style={"height": "10px", "background": "#e9efec", "borderRadius": "999px", "overflow": "hidden"},
                children=[
                    html.Div(
                        style={
                            "height": "100%",
                            "width": f"{int(frac * 100)}%",
                            "background": "linear-gradient(90deg, #2e7d32 0%, #b7e1c1 100%)",
                            "transition": "width 0.5s ease",
                        }
                    )
                ],
            ),
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
                html.Div(f"Welcome, {DEMO_USER_NAME}!", style={"fontSize": "20px", "fontWeight": 800, "color": TEXT, "marginTop": "10px", "paddingLeft": "2%"}),
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
    m = compute_metrics(data, daily, replay_idx, DEMO_DORM)

    # rank movement (dorm ranking)
    rank = m["rank"]
    rank_delta = None
    if prev_rank is not None and rank is not None:
        rank_delta = prev_rank - rank
    if rank is None:
        rank_move = "—"
    elif not rank_delta:
        rank_move = "—"
    elif rank_delta > 0:
        rank_move = f"↑{rank_delta}"
    else:
        rank_move = f"↓{abs(rank_delta)}"

    live_time_text = m["current_ts"].strftime("%I:%M %p").lstrip("0")
    location_text = "USC Campus"
    dorm_text = DEMO_DORM
    members = m["members"]

    daily_total = 3
    daily_completed = int(m["solar_completed"]) + int(m["busy_completed"]) + int(m["green_over_busy_completed"])

    todays_points = todays_points_card(
        points=m["score_pts"],
        replay_text=f"Replay: Day {m['day_num']} / {m['total_days']}  •  Dorm rank: #{rank} ({rank_move})",
        completed=daily_completed,
        total=daily_total,
    )

    weekly_items = [
        ("done", "Shift 2 heavy loads into Green Hours (as a dorm)"),
        ("done", "Keep Busy Hours under 2.0 kWh / student for 2 days"),
        ("todo", "Achieve 5 Green>Busy days"),
        ("todo", "Reduce Busy Hours by 10% vs last week"),
        ("todo", "Complete 3 Solar Champion days"),
    ]
    weekly_completed = sum(1 for s, _ in weekly_items if s == "done")
    weekly_total = len(weekly_items)

    row1 = dbc.Row(
        [
            dbc.Col(html.Div(live_location_card(live_time_text, location_text, dorm_text, members),
                             style={"height": "100%", "minHeight": ROW1_H}),
                    md=4, xs=12),
            dbc.Col(html.Div(todays_points, style={"height": "100%", "minHeight": ROW1_H}),
                    md=5, xs=12),
            dbc.Col(html.Div(streak_card(m["streak"], bonus_pct=25),
                             style={"height": "100%", "minHeight": ROW1_H}),
                    md=3, xs=12),
        ],
        className="g-3",
        align="stretch",
    )

    row2 = dbc.Row(
        [
            dbc.Col(html.Div(progress_card("Green Hours Usage", m["green_kwh"], "10 AM – 3 PM", GREEN, GREEN_LIGHT, vmax=4.0),
                             style={"height": "100%", "minHeight": ROW2_H}),
                    md=6, xs=12),
            dbc.Col(html.Div(progress_card("Busy Hours Usage", m["busy_kwh"], "5 PM – 9 PM", RED, RED_LIGHT, vmax=4.0),
                             style={"height": "100%", "minHeight": ROW2_H}),
                    md=6, xs=12),
        ],
        className="g-3",
        align="stretch",
    )

    graph_card = card(
        [
            html.Div(
                [
                    html.Div("Today: Green vs Busy", style={"fontWeight": 900, "color": TEXT}),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "baseline",
                    "marginBottom": "8px",
                    "flex": "0 0 auto",
                    "width": "100%",
                },
            ),

            # Wrapper flex que obliga a ocupar TODO el espacio restante
            html.Div(
                dcc.Graph(
                    id="today_pct",
                    figure=energy_pct_chart(m["green_kwh"], m["busy_kwh"], m["normal_kwh"]),
                    config={"displayModeBar": False, "responsive": True},
                    style={"width": "100%", "height": "100%"},
                ),
                style={
                    "flex": "1 1 auto",
                    "minHeight": 0,   # MUY importante en flex
                    "width": "100%",
                },
            ),
        ],
        padding="14px 14px",
    )

    row3 = dbc.Row(
        [
            dbc.Col(
                html.Div(graph_card, style={"height": "100%", "minHeight": ROW3_H, "width": "100%", "display": "flex"}),
                md=6, xs=12
            ),
            dbc.Col(html.Div(leaderboard_card(m["leaderboard"], DEMO_DORM), style={"height": "100%", "minHeight": ROW3_H}),
                    md=6, xs=12),
        ],
        className="g-3",
        align="stretch",
    )

    row4 = dbc.Row(
        [
            dbc.Col(html.Div(weekly_challenges_panel(weekly_completed, weekly_total, weekly_items),
                             style={"height": "100%", "minHeight": ROW4_H}),
                    md=12, xs=12),
        ],
        className="g-3",
        align="stretch",
    )

    layout = html.Div([row1, html.Div(style={"height": "10px"}), row2,
                       html.Div(style={"height": "10px"}), row3,
                       html.Div(style={"height": "10px"}), row4])

    return layout, rank

@app.callback(
    Output("collapse_weekly", "is_open"),
    Input("btn_weekly", "n_clicks"),
    State("collapse_weekly", "is_open"),
)
def toggle_weekly(n, is_open):
    if n:
        return not is_open
    return is_open

if __name__ == "__main__":
    app.run(debug=True, port=8050)

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html

from .config import (
    ASSETS_DIR,
    BG,
    BORDER,
    BUSY_END,
    BUSY_START,
    CSV_PATH,
    DEMO_DORM,
    DEMO_LOCATION,
    DEMO_USER_NAME,
    FONT_FAMILY,
    GREEN_END,
    GREEN_START,
    REPLAY_STEP_ROWS,
    SHADOW,
    TEXT,
    TICK_MS,
)
from .data_service import compute_daily_table, compute_metrics, load_data
from .ui_components import (
    header_block,
    kwh_usage_card,
    leaderboard_card,
    live_location_card,
    points_card,
    streak_card,
    weekly_challenges_card,
)

ROW1_H = "200px"
ROW2_H = "140px"
ROW3_H = "360px"


def build_layout() -> html.Div:
    return html.Div(
        style={
            "background": BG,
            "minHeight": "100vh",
            "padding": "18px",
            "fontFamily": FONT_FAMILY,
        },
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
                    html.Div(
                        f"Welcome, {DEMO_USER_NAME}!",
                        style={
                            "fontSize": "20px",
                            "fontWeight": 800,
                            "color": TEXT,
                            "marginTop": "6px",
                            "paddingLeft": "25px",
                        },
                    ),
                    html.Div(
                        style={"padding": "16px 18px 20px 18px"},
                        children=[html.Div(id="main_content")],
                    ),
                ],
            ),
        ],
    )


def register_callbacks(app: dash.Dash, df, daily) -> None:
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
        metrics = compute_metrics(df, daily, replay_idx, DEMO_DORM)

        live_time_text = metrics["current_ts"].strftime("%I:%M %p").lstrip("0")
        members = metrics["members"]

        weekly_lb = metrics["weekly_leaderboard"].reset_index(drop=True).copy()
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

        green_window_text = (
            f"{GREEN_START.strftime('%I:%M %p').lstrip('0')} – "
            f"{GREEN_END.strftime('%I:%M %p').lstrip('0')}"
        )
        busy_window_text = (
            f"{BUSY_START.strftime('%I:%M %p').lstrip('0')} – "
            f"{BUSY_END.strftime('%I:%M %p').lstrip('0')}"
        )

        row1 = dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        live_location_card(
                            live_time_text,
                            DEMO_LOCATION,
                            DEMO_DORM,
                            members,
                        ),
                        style={"height": "100%", "minHeight": ROW1_H},
                    ),
                    md=4,
                    xs=12,
                ),
                dbc.Col(
                    html.Div(
                        points_card(
                            daily_points=metrics["daily_points"],
                            weekly_points=metrics["weekly_points"],
                            weekly_bonus_points=metrics["weekly_bonus_points"],
                            day_label=metrics["day_label"],
                            week_text=metrics["week_text"],
                        ),
                        style={"height": "100%", "minHeight": ROW1_H},
                    ),
                    md=5,
                    xs=12,
                ),
                dbc.Col(
                    html.Div(
                        streak_card(
                            streak_days=metrics["streak_days"],
                            progress=metrics["streak_progress"],
                            bonus_pct=metrics["bonus_pct"],
                        ),
                        style={"height": "100%", "minHeight": ROW1_H},
                    ),
                    md=3,
                    xs=12,
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
                            kwh=metrics["green_kwh"],
                            pct=metrics["pct_green"],
                            color="#2e7d32",
                            color_light="#b7e1c1",
                        ),
                        style={"height": "100%", "minHeight": ROW2_H},
                    ),
                    md=6,
                    xs=12,
                ),
                dbc.Col(
                    html.Div(
                        kwh_usage_card(
                            title="Busy Hours Usage (per student)",
                            window_text=busy_window_text,
                            kwh=metrics["busy_kwh"],
                            pct=metrics["pct_busy"],
                            color="#c62828",
                            color_light="#f5b5b5",
                        ),
                        style={"height": "100%", "minHeight": ROW2_H},
                    ),
                    md=6,
                    xs=12,
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
                            challenges=metrics["weekly_challenges"],
                            completed=metrics["weekly_completed"],
                            total=metrics["weekly_total"],
                        ),
                        style={"height": "100%", "minHeight": ROW3_H},
                    ),
                    md=6,
                    xs=12,
                ),
                dbc.Col(
                    html.Div(
                        leaderboard_card(
                            df_lb=weekly_lb,
                            selected_dorm=DEMO_DORM,
                            arrows=arrows,
                            target_rows=8,
                        ),
                        style={"height": "100%", "minHeight": ROW3_H},
                    ),
                    md=6,
                    xs=12,
                ),
            ],
            className="g-3",
            align="stretch",
        )

        content = html.Div(
            [
                row1,
                html.Div(style={"height": "10px"}),
                row2,
                html.Div(style={"height": "10px"}),
                row3,
            ]
        )

        return content, current_ranks


def create_app() -> dash.Dash:
    df = load_data(CSV_PATH)
    daily = compute_daily_table(df)

    external_stylesheets = [
        dbc.themes.FLATLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap",
    ]

    app = dash.Dash(
        __name__,
        external_stylesheets=external_stylesheets,
        assets_folder=str(ASSETS_DIR),
    )
    app.title = "Noche MVP"
    app.layout = build_layout()
    register_callbacks(app, df, daily)
    return app


app = create_app()
server = app.server


def main() -> None:
    app.run(debug=False, port=8040)


if __name__ == "__main__":
    main()

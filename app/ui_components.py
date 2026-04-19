import pandas as pd
from dash import html
from .config import (
    BORDER, CARD_RADIUS, SHADOW_SOFT, TEXT, MUTED,
    YELLOW, ORANGE, GREEN, GREEN_LIGHT,
    STREAK_GOAL_DAYS
)

def card(children, padding="16px"):
    return html.Div(
        children=children,
        style={
            "background": "white",
            "border": f"1px solid {BORDER}",
            "borderRadius": CARD_RADIUS,
            "boxShadow": SHADOW_SOFT,
            "padding": padding,
            "height": "100%",
            "width": "100%",
        },
    )

def header_block(company="Noche", user="Alex"):
    return html.Div(
        style={
            "padding": "26px 16px 14px 16px",
            "borderBottom": f"1px solid {BORDER}",
            "background": "linear-gradient(180deg, #eaf6ee 0%, #ffffff 88%)",
            "textAlign": "center",
        },
        children=[
            html.Div(company, style={"fontSize": "40px", "fontWeight": 900, "color": "#1f5c3a", "letterSpacing": "-0.5px"}),
            html.Div("To a greener future", style={"fontSize": "25px", "fontWeight": 900, "color": "#1f5c3a", "letterSpacing": "-0.5px"}),
        ],
    )

def progress_bar(frac: float, color_left: str, color_right: str | None = None, height_px=10):
    frac = max(0.0, min(frac, 1.0))
    bg = "#e9efec"
    fill = color_left if not color_right else f"linear-gradient(90deg, {color_left} 0%, {color_right} 100%)"
    return html.Div(
        style={"height": f"{height_px}px", "background": bg, "borderRadius": "999px", "overflow": "hidden"},
        children=[
            html.Div(
                style={
                    "height": "100%",
                    "width": f"{int(frac*100)}%",
                    "background": fill,
                    "transition": "width 0.35s ease",
                }
            )
        ],
    )

def live_badge(live_time_text: str):
    return html.Div(
        [
            html.Span("●", className="live-dot", style={"color": "#16a34a"}),
            html.Span("LIVE", style={"fontWeight": 900, "letterSpacing": "0.5px", "color": "#14532d"}),
            html.Span("•", style={"color": "#14532d", "opacity": 0.5}),
            html.Span(live_time_text, style={"fontWeight": 800, "color": "#14532d"}),
        ],
        className="live-chip",
        style={"fontSize": "12px"},
    )

def live_location_card(live_time_text: str, location_text: str, dorm_text: str, members: int):
    return card(
        [
            html.Div("TIME", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(live_badge(live_time_text), style={"marginTop": "8px"}),

            html.Div(style={"height": "12px"}),

            html.Div("LOCATION", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(location_text, style={"fontWeight": 900, "color": TEXT, "marginTop": "4px"}),

            html.Div(style={"height": "12px"}),

            html.Div("DORM / GROUP", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(dorm_text, style={"fontWeight": 900, "color": TEXT, "marginTop": "4px"}),
            html.Div(f"{members} students", style={"color": MUTED, "fontSize": "12px", "marginTop": "2px"}),
        ],
        padding="16px 16px",
    )

def points_card(daily_points: int, weekly_points: int, weekly_bonus_points: int, day_label: str, week_text: str):
    """
    weekly_points already includes challenges.
    weekly_bonus_points is the per-student points earned from completed challenges so far.
    """
    if weekly_points <= 0:
        challenges_line = "Challenges: 0 pts (0%) of weekly"
    else:
        pct = int(round(100 * (weekly_bonus_points / max(weekly_points, 1))))
        challenges_line = f"Challenges: {weekly_bonus_points} pts ({pct}%) of weekly"

    return card(
        [
            html.Div(
                [
                    html.Div("POINTS", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
                    html.Div(day_label, style={"fontWeight": 900, "color": "#1f5c3a", "fontSize": "12px"}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"},
            ),
            html.Div(style={"height": "10px"}),

            html.Div("Daily (resets at midnight)", style={"color": MUTED, "fontSize": "12px", "fontWeight": 800}),
            html.Div(f"{daily_points} pts", style={"fontWeight": 900, "fontSize": "38px", "lineHeight": "1.0", "marginTop": "4px", "color": TEXT}),

            html.Div(style={"height": "10px"}),

            html.Div("Weekly (leaderboard)", style={"color": MUTED, "fontSize": "12px", "fontWeight": 800}),
            html.Div(f"{weekly_points} pts", style={"fontWeight": 900, "fontSize": "32px", "lineHeight": "1.0", "marginTop": "4px", "color": TEXT}),
            html.Div(challenges_line, style={"color": MUTED, "fontSize": "12px", "marginTop": "4px", "fontWeight": 800}),

            html.Div(week_text, style={"color": MUTED, "fontSize": "12px", "marginTop": "10px", "fontWeight": 800}),
        ],
        padding="16px 16px",
    )


def kwh_usage_card(title: str, window_text: str, kwh: float, pct: int, color: str, color_light: str):
    return card(
        [
            html.Div(title, style={"fontWeight": 900, "color": TEXT, "fontSize": "14px"}),
            html.Div(window_text, style={"color": MUTED, "fontSize": "12px", "fontWeight": 800, "marginTop": "2px"}),

            html.Div(
                [
                    html.Div(f"{kwh:.2f} kWh", style={"fontWeight": 900, "color": TEXT, "fontSize": "28px"}),
                    html.Div(f"{pct}%", style={"fontWeight": 900, "color": color, "fontSize": "18px"}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline", "marginTop": "8px"},
            ),

            html.Div(style={"height": "10px"}),
            progress_bar(pct / 100.0, color, color_light, height_px=10),
        ],
        padding="16px 16px",
    )

def streak_card(streak_days: int, progress: float, bonus_pct: int):
    return card(
        [
            html.Div("STREAK", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
            html.Div(f"{streak_days} / {STREAK_GOAL_DAYS} days", style={"fontWeight": 900, "fontSize": "28px", "color": TEXT, "marginTop": "6px"}),

            html.Div(style={"height": "10px"}),
            progress_bar(progress, YELLOW, ORANGE, height_px=10),

            html.Div(style={"height": "10px"}),

            html.Div(
                "Streak grows when you use more energy during Green Hours. "
                "Reach 100 days to maximize your reward bonus.",
                style={"color": MUTED, "fontSize": "12px", "lineHeight": "1.4", "fontWeight": 700},
            ),

            html.Div(style={"height": "10px"}),

            html.Div(
                [
                    html.Div("Current bonus", style={"color": MUTED, "fontSize": "12px", "fontWeight": 800}),
                    html.Div(f"+{bonus_pct}%", style={"color": ORANGE, "fontSize": "12px", "fontWeight": 900}),
                ],
                style={"display": "flex", "justifyContent": "space-between"},
            ),
        ],
        padding="16px 16px",
    )

def weekly_challenges_card(challenges: list[dict], completed: int, total: int):
    frac = 0 if total == 0 else completed / total

    items = []
    for c in challenges:
        done = bool(c["done"])
        items.append(
            html.Div(
                [
                    html.Div("✅" if done else "⬜", style={"width": "28px"}),
                    html.Div(
                        [
                            html.Div(c["title"], style={"fontWeight": 900, "color": TEXT}),
                            html.Div(c["desc"], style={"color": MUTED, "fontSize": "12px", "marginTop": "2px"}),
                            html.Div(c.get("progress_text", ""), style={"color": MUTED, "fontSize": "12px", "marginTop": "2px", "fontWeight": 800}),
                        ],
                        style={"flex": 1},
                    ),
                    html.Div(f"+{c['reward']} pts", style={"fontWeight": 900, "color": GREEN if done else MUTED}),
                ],
                style={
                    "display": "flex",
                    "gap": "8px",
                    "alignItems": "center",
                    "padding": "10px 10px",
                    "border": f"1px solid {BORDER}",
                    "borderRadius": "12px",
                    "background": "#ecfdf3" if done else "white",
                },
            )
        )

    return card(
        [
            html.Div(
                [
                    html.Div("WEEKLY CHALLENGES", style={"fontWeight": 900, "fontSize": "16px", "color": TEXT}),
                    html.Div(f"{completed}/{total} completed", style={"color": MUTED, "fontWeight": 900}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"},
            ),
            html.Div(style={"height": "10px"}),
            progress_bar(frac, GREEN, GREEN_LIGHT, height_px=10),
            html.Div(style={"height": "12px"}),
            html.Div(items, style={"display": "grid", "gap": "10px"}),
        ],
        padding="16px 16px",
    )

def _ellipsis_row():
    return html.Div(
        "⋯",
        style={
            "textAlign": "center",
            "padding": "6px 0",
            "color": MUTED,
            "fontWeight": 900,
            "letterSpacing": "3px",
            "borderBottom": "1px solid #eef2f0",
        },
    )

def leaderboard_card(df_lb, selected_dorm: str, arrows: dict, target_rows: int = 8):
    """
    Top 8 view:
    - If user is outside top 8: show Top 7 + ellipsis + user row (with real rank).
    - Star ⭐ only for #1, left of points.
    - Movement indicator (↑↓=) left of dorm name.
    """
    lb = df_lb.reset_index(drop=True).copy()
    lb["rank"] = lb.index + 1

    user_row = lb[lb["dorm"] == selected_dorm]
    user_rank = int(user_row["rank"].iloc[0]) if len(user_row) else None

    insert_ellipsis = False
    if len(lb) <= target_rows:
        shown = lb.copy()
    else:
        if user_rank is not None and user_rank > target_rows:
            shown = pd.concat([lb.head(target_rows - 1), user_row], ignore_index=True)
            insert_ellipsis = True
        else:
            shown = lb.head(target_rows).copy()

    rows = []
    for i, r in shown.iterrows():
        rank = int(r["rank"])
        is_me = (r["dorm"] == selected_dorm)
        pts = int(round(float(r["weekly_points_per_student"])))
        members = int(r["members"])

        move = arrows.get(r["dorm"], {"symbol": "=", "color": "#94a3b8"})

        row_style = {
            "display": "flex",
            "alignItems": "center",
            "padding": "10px 10px",
            "borderBottom": "1px solid #eef2f0",
            "background": "#ecfdf3" if is_me else "transparent",
            "border": f"1px solid {BORDER}" if is_me else "1px solid transparent",
        }

        badge = html.Span(
            "YOU",
            style={
                "marginLeft": "8px",
                "fontSize": "11px",
                "fontWeight": 900,
                "color": "#14532d",
                "background": "rgba(22, 163, 74, 0.12)",
                "border": "1px solid rgba(22, 163, 74, 0.25)",
                "padding": "2px 8px",
                "borderRadius": "999px",
            },
        ) if is_me else ""

        star_pts = "⭐ " if rank == 1 else ""

        row = html.Div(
            [
                html.Div(f"{rank}.", style={"width": "34px", "color": MUTED, "fontWeight": 900}),
                html.Div(move["symbol"], style={"width": "26px", "textAlign": "center", "fontWeight": 900, "color": move["color"]}),
                html.Div(
                    [html.Span(r["dorm"], style={"fontWeight": 900, "color": TEXT}), badge],
                    style={"flex": 1, "display": "flex", "alignItems": "center"},
                ),
                html.Div(f"{members}👤", style={"width": "70px", "textAlign": "center", "color": MUTED, "fontWeight": 900}),
                html.Div(f"{star_pts}{pts} pts", style={"width": "110px", "textAlign": "right", "fontWeight": 900, "color": TEXT}),
            ],
            style=row_style,
        )
        rows.append(row)

    # Insert the ellipsis row before the last row (which is the pinned user)
    if insert_ellipsis and len(rows) >= 2:
        rows.insert(len(rows) - 1, _ellipsis_row())

    # Remove bottom border for the last item (if last is a real row)
    if rows and isinstance(rows[-1], html.Div):
        try:
            rows[-1].style["borderBottom"] = "none"
        except Exception:
            pass

    return card(
        [
            html.Div(
                [
                    html.Div("🏆 WEEKLY LEADERBOARD", style={"fontWeight": 900, "fontSize": "16px", "color": TEXT}),
                    html.Div("Points per student", style={"color": MUTED, "fontWeight": 900, "fontSize": "12px"}),
                ],
                style={"marginBottom": "10px"},
            ),
            html.Div(rows, style={"display": "flex", "flexDirection": "column"}),
        ],
        padding="16px 16px",
    )

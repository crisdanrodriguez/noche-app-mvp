import dash_bootstrap_components as dbc
from dash import html
import plotly.graph_objects as go
from config import BORDER, TEXT, MUTED

from config import (
    BORDER, CARD_RADIUS, SHADOW_SOFT, TEXT, MUTED, FONT_FAMILY,
    GREEN, RED, GREY,
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
        },
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

def progress_card(title, value_kwh, rng, color, color_light, vmax=4.0):
    frac = 0 if vmax == 0 else max(0, min(value_kwh / vmax, 1))
    return card([
        html.Div(
            [
                html.Div(title, style={"fontWeight": 900, "color": TEXT, "fontSize": "14px"}),
                html.Div(f"{value_kwh:.1f} kWh", style={"fontWeight": 900, "color": color, "fontSize": "16px"}),
            ],
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"}
        ),
        html.Div(rng, style={"color": MUTED, "fontSize": "12px", "marginTop": "2px"}),
        html.Div(style={"height": "10px"}),
        html.Div(
            style={"height": "12px", "background": "#e9efec", "borderRadius": "999px", "overflow": "hidden"},
            children=[
                html.Div(style={
                    "height": "100%",
                    "width": f"{int(frac*100)}%",
                    "background": f"linear-gradient(90deg, {color} 0%, {color_light} 100%)"
                })
            ]
        )
    ], padding="16px 16px")

def streak_card(streak_days: int, bonus_pct=25):
    cap = 7
    filled = max(0, min(streak_days, cap))
    icons = "🔥" * filled + "▫️" * (cap - filled)

    return card([
        html.Div(
            [
                html.Div("Streak", style={"fontWeight": 900, "color": MUTED, "fontSize": "12px"}),
                html.Div(f"{streak_days}-day", style={"fontWeight": 900, "color": TEXT, "fontSize": "12px"}),
            ],
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"}
        ),
        html.Div(style={"height": "10px"}),
        html.Div("10-Day Streak", style={"fontWeight": 900, "fontSize": "18px", "color": TEXT}),
        html.Div(f"Bonus: +{bonus_pct}% points", style={"fontWeight": 900, "color": GREEN, "marginTop": "4px"}),
        html.Div(style={"height": "10px"}),
        html.Div(icons, style={"fontSize": "16px", "letterSpacing": "1px"}),
    ], padding="16px 16px")

def leaderboard_card(df_lb, selected_dorm: str):
    rows = []
    top = df_lb.head(8)  # show a few more if you want

    for i, r in top.iterrows():
        is_me = (r["dorm"] == selected_dorm)

        pts = int(round(float(r["points_per_student"])))
        members = int(r["members"])
        star = "⭐" if i == 0 else ""

        row_style = {
            "display": "flex",
            "alignItems": "center",
            "padding": "10px 10px",
            "borderBottom": "1px solid #eef2f0" if i < len(top) - 1 else "none",
            "borderRadius": "12px" if is_me else "0px",
            "background": "#ecfdf3" if is_me else "transparent",  # subtle green highlight
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

        rows.append(
            html.Div(
                [
                    html.Div(f"{i+1}.", style={"width": "28px", "color": MUTED, "fontWeight": 800}),
                    html.Div(
                        [html.Span(r["dorm"], style={"fontWeight": 900, "color": TEXT}), badge],
                        style={"flex": 1, "display": "flex", "alignItems": "center"},
                    ),
                    html.Div(f"{members}👤", style={"width": "52px", "textAlign": "right", "color": MUTED, "fontWeight": 800}),
                    html.Div(star, style={"width": "28px", "textAlign": "center"}),
                    html.Div(f"{pts} pts", style={"width": "90px", "textAlign": "right", "fontWeight": 900, "color": TEXT}),
                ],
                style=row_style,
            )
        )

    return card(
        [
            html.Div(
                [
                    html.Div("🏆 Weekly Dorm Ranking", style={"fontWeight": 900, "fontSize": "18px", "color": TEXT}),
                    html.Div("Points per student", style={"color": MUTED, "fontWeight": 800, "fontSize": "12px"}),
                ],
                style={"marginBottom": "10px"},
            ),
            html.Div(rows, style={"display": "grid", "gap": "8px"}),  # gap makes highlight look nicer
        ],
        padding="16px 16px",
    )

def energy_pct_chart(green_kwh: float, normal_kwh: float, busy_kwh: float):
    total = max(green_kwh + normal_kwh + busy_kwh, 1e-9)

    green_pct  = 100.0 * green_kwh  / total
    normal_pct = 100.0 * normal_kwh / total
    busy_pct   = 100.0 * busy_kwh   / total

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Green hours", "Normal hours", "Busy hours"],
                values=[green_kwh, normal_kwh, busy_kwh],
                hole=0.62,
                textinfo="percent",
                textposition="inside",
                marker=dict(colors=[GREEN, GREY, RED]),
                sort=False,
                direction="clockwise",
            )
        ]
    )

    # Center annotation (main message)
    fig.update_layout(
        annotations=[
            dict(
                text=f"<b>{green_pct:.0f}%</b><br><span style='font-size:12px;'>Green</span>",
                x=0.5, y=0.56, showarrow=False
            ),
            dict(
                text=f"<span style='font-size:11px;'>{normal_pct:.0f}% Normal</span>",
                x=0.5, y=0.43, showarrow=False
            ),
            dict(
                text=f"<span style='font-size:11px;'>{busy_pct:.0f}% Busy</span>",
                x=0.5, y=0.34, showarrow=False
            ),
        ],
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY),
    )

    return fig

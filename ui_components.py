from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from config import (
    BORDER, CARD_RADIUS, SHADOW_SOFT,
    TEXT, MUTED, GREEN, GREEN_LIGHT, RED, RED_LIGHT, FONT_FAMILY,
    DEMO_HOME
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
        },
    )

def header():
    return html.Div(
        style={
            "background": "linear-gradient(180deg, #eaf6ee 0%, #ffffff 88%)",
            "borderBottom": f"1px solid {BORDER}",
            "padding": "28px 22px 18px 22px",
        },
        children=[
            html.Div(
                style={"maxWidth": "1100px", "margin": "0 auto"},
                children=[
                    html.Div(
                        [html.Span("EcoEnergy", style={"fontWeight": 900}),
                         html.Span(" "),
                         html.Span("Challenge", style={"fontWeight": 500})],
                        style={"fontSize": "34px", "color": "#1f5c3a", "letterSpacing": "-0.5px"},
                    ),
                    html.Div("Use energy at the right time!", style={"marginTop": "6px", "color": "#2f6b47", "fontStyle": "italic"}),
                ],
            )
        ],
    )

def metric(title, value, sub=None):
    return card([
        html.Div(title, style={"color": MUTED, "fontWeight": 600, "fontSize": "13px"}),
        html.Div(value, style={"color": TEXT, "fontWeight": 900, "fontSize": "40px", "lineHeight": "1.05", "marginTop": "4px"}),
        html.Div(sub, style={"color": "#8a9a95", "fontSize": "12px", "marginTop": "6px"}) if sub else None,
    ], padding="16px 18px")

def progress_card(title, value_kwh, rng, color, color_light, vmax=4.0):
    frac = 0 if vmax == 0 else max(0, min(value_kwh / vmax, 1))
    return card([
        html.Div(
            [html.Div(title, style={"fontWeight": 800, "color": TEXT, "fontSize": "14px"}),
             html.Div(f"{value_kwh:.1f} kWh", style={"fontWeight": 900, "color": color, "fontSize": "16px"})],
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"}
        ),
        html.Div(rng, style={"color": MUTED, "fontSize": "12px", "marginTop": "2px"}),
        html.Div(style={"height": "10px"}),
        html.Div(
            style={"height": "12px", "background": "#e9efec", "borderRadius": "999px", "overflow": "hidden"},
            children=[html.Div(style={
                "height": "100%",
                "width": f"{int(frac*100)}%",
                "background": f"linear-gradient(90deg, {color} 0%, {color_light} 100%)"
            })]
        )
    ])

def streak_card(streak_days, bonus_pct=25):
    filled = min(streak_days, 7)
    icons = "🍃"*filled + "🌿"*(7-filled)
    return card([
        html.Div(
            [html.Div("🔥", style={"fontSize": "22px"}),
             html.Div(
                 [html.Div(f"{streak_days}-Day Green Streak!", style={"fontWeight": 900, "fontSize": "18px", "color": TEXT}),
                  html.Div(f"Bonus: +{bonus_pct}% points", style={"fontWeight": 900, "color": GREEN, "marginTop": "2px"})],
                 style={"marginLeft": "10px"}
             )],
            style={"display": "flex", "alignItems": "center"}
        ),
        html.Div(style={"height": "8px"}),
        html.Div(icons, style={"fontSize": "18px"})
    ])

def challenge_card(icon, title, desc, progress_text, frac, accent, completed=False, button=None):
    frac = max(0, min(frac, 1))
    return card([
        html.Div(
            [html.Div(icon, style={"fontSize": "20px", "marginRight": "10px"}),
             html.Div([html.Div(title, style={"fontWeight": 900, "fontSize": "16px", "color": TEXT}),
                       html.Div(desc, style={"color": MUTED, "fontSize": "13px", "marginTop": "2px"})],
                      style={"flex": 1}),
             dbc.Button(button, color="success", size="sm") if button else None],
            style={"display": "flex", "alignItems": "center"}
        ),
        html.Div(style={"height": "10px"}),
        html.Div(
            style={"height": "10px", "background": "#e9efec", "borderRadius": "999px", "overflow": "hidden"},
            children=[html.Div(style={"width": f"{int(frac*100)}%", "height": "100%", "background": accent})]
        ),
        html.Div(
            [html.Div(progress_text, style={"color": "#51615c", "fontSize": "13px", "fontWeight": 700}),
             html.Div("Completed Today!" if completed else "", style={"color": GREEN, "fontSize": "13px", "fontWeight": 900})],
            style={"display": "flex", "justifyContent": "space-between", "marginTop": "8px"}
        )
    ], padding="16px")

def leaderboard_card(df_lb: pd.DataFrame):
    rows = []
    for i, r in df_lb.head(7).iterrows():
        is_me = (r["home"] == DEMO_HOME)
        star = "⭐" if i == 0 else ""
        bg = "#eefaf1" if is_me else "transparent"
        name_weight = 950 if is_me else 850

        rows.append(html.Div(
            [
                html.Div(f"{i+1}.", style={"width": "28px", "color": MUTED, "fontWeight": 800}),
                html.Div(r["home"], style={"flex": 1, "fontWeight": name_weight, "color": TEXT}),
                html.Div(star, style={"width": "28px", "textAlign": "center"}),
                html.Div(f"{int(r['points'])} pts", style={"width": "90px", "textAlign": "right", "fontWeight": 900, "color": TEXT}),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": "10px 10px",
                "background": bg,
                "borderRadius": "10px" if is_me else "0px",
                "borderBottom": "1px solid #eef2f0" if i < 6 else "none"
            }
        ))

    return card([
        html.Div(["🏆 ", html.Span("Weekly Leaderboard", style={"fontWeight": 900, "fontSize": "18px", "color": TEXT})], style={"marginBottom": "10px"}),
        html.Div(rows)
    ])

def energy_bar_chart(green_kwh, peak_kwh):
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Green Window", x=["Energy"], y=[green_kwh]))
    fig.add_trace(go.Bar(name="Peak Window", x=["Energy"], y=[peak_kwh]))
    fig.update_layout(
        barmode="group",
        height=220,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        font=dict(family=FONT_FAMILY),
    )
    fig.update_yaxes(title="kWh", gridcolor="#eef2f0")
    fig.update_xaxes(showticklabels=False)
    return fig

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

def tips_card(title: str, body: str, variant: str):
    styles = {
        "green": {"bg": "#f1faf4", "border": "#a7d7b8"},
        "peak": {"bg": "#fdf3f3", "border": "#f2b4b4"},
        "neutral": {"bg": "#f6f7f8", "border": "#d1d5db"},
    }
    s = styles.get(variant, styles["neutral"])

    return html.Div(
        card(
            [
                html.Div(title, style={"fontWeight": 900, "fontSize": "15px"}),
                html.Div(
                    body,
                    style={
                        "fontSize": "13px",
                        "lineHeight": "1.45",
                        "marginTop": "8px",
                    },
                ),
            ],
            padding="16px 16px",
        ),
        style={
            "background": s["bg"],
            "border": f"1px solid {s['border']}",
            "borderRadius": "16px",
            "height": "100%",
        },
    )






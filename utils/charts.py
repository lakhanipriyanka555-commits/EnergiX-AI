import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from config import CHART_THEME, COLOR_PALETTE


_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)", zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)", zeroline=False),
)


def _apply_defaults(fig):
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


def line_chart(df, x, y, title="", color=None, labels=None):
    color = color or COLOR_PALETTE["primary"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y],
        mode="lines",
        name=y,
        line=dict(color=color, width=2.5),
        fill="tozeroy",
        fillcolor=f"rgba(0,102,255,0.06)",
    ))
    fig.update_layout(title=dict(text=title, font=dict(size=14, color="#0066FF")))
    return _apply_defaults(fig)


def area_chart_multi(df, x, y_cols, title="", colors=None):
    colors = colors or [COLOR_PALETTE["primary"], COLOR_PALETTE["secondary"],
                        COLOR_PALETTE["accent"], COLOR_PALETTE["warning"]]
    fig = go.Figure()
    for i, col in enumerate(y_cols):
        c = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            mode="lines", name=col,
            line=dict(color=c, width=2),
            fill="tonexty" if i > 0 else "tozeroy",
            fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.08)",
        ))
    fig.update_layout(title=dict(text=title, font=dict(size=14, color="#0066FF")))
    return _apply_defaults(fig)


def forecast_chart(hist_df, pred_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_df["timestamp"], y=hist_df["energy_kwh"],
        mode="lines", name="Historical",
        line=dict(color="#0066FF", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=pred_df["timestamp"], y=pred_df["upper"],
        mode="lines", name="Upper Bound",
        line=dict(color="rgba(0,212,255,0.3)", width=0),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=pred_df["timestamp"], y=pred_df["lower"],
        mode="lines", name="Confidence Band",
        fill="tonexty", fillcolor="rgba(0,212,255,0.15)",
        line=dict(color="rgba(0,212,255,0.3)", width=0),
    ))
    fig.add_trace(go.Scatter(
        x=pred_df["timestamp"], y=pred_df["energy_kwh"],
        mode="lines+markers", name="AI Forecast",
        line=dict(color="#00D4FF", width=2.5, dash="dot"),
        marker=dict(size=4),
    ))
    # Peak hour marker
    peak_idx = pred_df["energy_kwh"].idxmax()
    fig.add_annotation(
        x=pred_df.loc[peak_idx, "timestamp"],
        y=pred_df.loc[peak_idx, "energy_kwh"],
        text=f"⚡ Peak: {pred_df.loc[peak_idx,'energy_kwh']:.1f} kWh",
        showarrow=True, arrowhead=2,
        arrowcolor="#FF6B35", font=dict(color="#FF6B35", size=11),
        bgcolor="rgba(255,107,53,0.1)", bordercolor="#FF6B35", borderwidth=1,
    )
    fig.update_layout(title=dict(text="24-Hour AI Demand Forecast", font=dict(size=14, color="#0066FF")))
    return _apply_defaults(fig)


def pie_chart(df, names, values, title=""):
    colors = ["#0066FF", "#00D4FF", "#00FF88", "#FF6B35", "#FF3366", "#A855F7", "#F59E0B", "#10B981"]
    fig = go.Figure(go.Pie(
        labels=df[names], values=df[values],
        hole=0.45,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#0066FF")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="v"),
    )
    return fig


def bar_chart(df, x, y, title="", color=None, orientation="v"):
    color = color or COLOR_PALETTE["primary"]
    fig = go.Figure(go.Bar(
        x=df[x] if orientation == "v" else df[y],
        y=df[y] if orientation == "v" else df[x],
        orientation=orientation,
        marker=dict(
            color=df[y] if orientation == "v" else df[x],
            colorscale=[[0, "#00D4FF"], [0.5, "#0066FF"], [1, "#FF6B35"]],
            showscale=False,
            line=dict(color="rgba(255,255,255,0.3)", width=1),
        ),
    ))
    fig.update_layout(title=dict(text=title, font=dict(size=14, color="#0066FF")))
    return _apply_defaults(fig)


def heatmap_chart(df, x, y, z, title=""):
    pivot = df.pivot_table(index=y, columns=x, values=z, aggfunc="mean")
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#e0f2fe"], [0.5, "#0066FF"], [1, "#FF3366"]],
        showscale=True,
        hovertemplate=f"{y}: %{{y}}<br>{x}: %{{x}}<br>{z}: %{{z:.1f}}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#0066FF")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        margin=dict(l=60, r=20, t=50, b=60),
    )
    return fig


def gauge_chart(value, title="", min_val=0, max_val=100, threshold=75):
    color = "#00C853" if value >= threshold else ("#FF6B35" if value >= threshold * 0.6 else "#FF3366")
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": title, "font": {"size": 14, "color": "#1e293b"}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickcolor": "#94a3b8"},
            "bar": {"color": color},
            "bgcolor": "white",
            "steps": [
                {"range": [min_val, threshold * 0.6], "color": "rgba(255,51,102,0.1)"},
                {"range": [threshold * 0.6, threshold], "color": "rgba(255,107,53,0.1)"},
                {"range": [threshold, max_val], "color": "rgba(0,200,83,0.1)"},
            ],
            "threshold": {
                "line": {"color": "#0066FF", "width": 3},
                "thickness": 0.75,
                "value": threshold,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=60, b=20),
        height=250,
    )
    return fig


def scatter_anomaly_chart(df):
    df = df.copy()
    df["color"] = df["risk_score"].apply(
        lambda x: "#FF3366" if x > 0.75 else ("#FF6B35" if x > 0.5 else "#00C853")
    )
    df["label"] = df["risk_score"].apply(
        lambda x: "High Risk" if x > 0.75 else ("Medium" if x > 0.5 else "Normal")
    )
    fig = px.scatter(
        df, x="usage_deviation_pct", y="risk_score",
        color="label",
        color_discrete_map={"High Risk": "#FF3366", "Medium": "#FF6B35", "Normal": "#00C853"},
        hover_data=["consumer_id", "city", "anomaly_type"],
        size="risk_score",
        title="Anomaly Risk Map",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
    )
    return fig


def optimization_bar(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Before Optimization",
        x=df["category"], y=df["before_kwh"],
        marker_color="#0066FF",
        marker_line=dict(color="white", width=1),
    ))
    fig.add_trace(go.Bar(
        name="After Optimization",
        x=df["category"], y=df["after_kwh"],
        marker_color="#00FF88",
        marker_line=dict(color="white", width=1),
    ))
    fig.update_layout(
        barmode="group",
        title=dict(text="Energy Optimization – Before vs After", font=dict(size=14, color="#0066FF")),
    )
    return _apply_defaults(fig)

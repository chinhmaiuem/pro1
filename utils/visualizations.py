"""Consistent Plotly chart styling."""
import plotly.express as px

PALETTE = ["#127f80", "#4361a8", "#df9343", "#9b6aa0", "#cc6570", "#7e9a49", "#66758b", "#b79e78"]


def polish(fig, title=None, height=350):
    fig.update_layout(
        template="plotly_white", title=title, height=height,
        font=dict(family="Arial, sans-serif", size=13, color="#344454"),
        margin=dict(l=10, r=10, t=48 if title else 20, b=15),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE, legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e7eced", zeroline=False)
    return fig


def monthly_chart(summary):
    fig = px.area(summary, x="month", y="net_value", color_discrete_sequence=PALETTE)
    fig.update_traces(line_width=2, hovertemplate="%{x}<br>Net value: $%{y:,.2f}<extra></extra>")
    fig.update_layout(xaxis_title=None, yaxis_title="Net transaction value · USD")
    return polish(fig)


def segment_chart(summary):
    fig = px.bar(summary.sort_values("customers"), y="Segment", x="customers", orientation="h",
                 color_discrete_sequence=PALETTE, text="customers")
    fig.update_layout(xaxis_title="Customers", yaxis_title=None)
    return polish(fig)


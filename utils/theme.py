def apply_dark_plotly(fig):
    """Apply the TradingView dark palette to any Plotly figure. Returns fig."""
    fig.update_layout(
        paper_bgcolor="#131722",
        plot_bgcolor="#131722",
        font=dict(color="#d1d4dc"),
        xaxis=dict(gridcolor="#2a2e39", linecolor="#2a2e39", color="#d1d4dc"),
        yaxis=dict(gridcolor="#2a2e39", linecolor="#2a2e39", color="#d1d4dc"),
        yaxis2=dict(gridcolor="#2a2e39", linecolor="#2a2e39", color="#d1d4dc"),
        legend=dict(bgcolor="#1e222d", font=dict(color="#d1d4dc")),
    )
    return fig

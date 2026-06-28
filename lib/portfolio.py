"""Load/save the user's portfolio holdings to data/portfolio.json (gitignored)."""

from __future__ import annotations

import json
import os

PORTFOLIO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "portfolio.json")


def load_portfolio() -> list[dict]:
    """Return a list of {ticker, shares, cost_basis} dicts. Empty if no file yet."""
    if not os.path.isfile(PORTFOLIO_PATH):
        return []
    try:
        with open(PORTFOLIO_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_portfolio(holdings: list[dict]) -> None:
    """Persist holdings as a list of {ticker, shares, cost_basis} dicts."""
    os.makedirs(os.path.dirname(PORTFOLIO_PATH), exist_ok=True)
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(holdings, f, indent=2)

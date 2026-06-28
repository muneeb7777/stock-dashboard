"""Curated peer groups of similar ETFs, used for cost (expense ratio) comparisons."""

from __future__ import annotations

# Each group lists ETFs that track substantially the same exposure, so
# expense-ratio differences are a meaningful apples-to-apples comparison.
PEER_GROUPS = [
    ["SPY", "IVV", "VOO", "SPLG"],
    ["QQQ", "QQQM"],
    ["VTI", "ITOT", "SCHB"],
    ["DIA"],
    ["IWM", "VTWO", "SCHA"],
    ["VEA", "IEFA", "SCHF"],
    ["VWO", "IEMG", "SCHE"],
    ["AGG", "BND", "SCHZ"],
    ["TLT", "VGLT", "SPTL"],
    ["GLD", "IAU", "SGOL"],
    ["SLV", "SIVR"],
    ["XLK", "VGT", "FTEC"],
    ["XLF", "VFH", "FNCL"],
    ["XLV", "VHT", "FHLC"],
    ["XLE", "VDE", "FENY"],
    ["XLI", "VIS", "FIDU"],
    ["XLY", "VCR", "FDIS"],
    ["XLP", "VDC", "FSTA"],
    ["XLU", "VPU", "FUTY"],
    ["XLRE", "VNQ", "SCHH"],
    ["XLB", "VAW", "FMAT"],
    ["XLC", "VOX", "FCOM"],
    ["ARKK"],
]


def get_peers(ticker: str) -> list[str]:
    """Return all tickers in the same peer group as `ticker`, including itself."""
    ticker = ticker.upper()
    for group in PEER_GROUPS:
        if ticker in group:
            return group
    return [ticker]

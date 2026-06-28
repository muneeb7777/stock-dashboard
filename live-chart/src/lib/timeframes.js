// Maps UI timeframe labels to Alpaca bar timeframe strings and a sensible
// lookback window (in days) for the initial historical fetch.
export const TIMEFRAMES = {
  '1m': { alpaca: '1Min', lookbackDays: 5 },
  '5m': { alpaca: '5Min', lookbackDays: 20 },
  '15m': { alpaca: '15Min', lookbackDays: 40 },
  '30m': { alpaca: '30Min', lookbackDays: 60 },
  '1H': { alpaca: '1Hour', lookbackDays: 120 },
  '4H': { alpaca: '4Hour', lookbackDays: 365 },
  '1D': { alpaca: '1Day', lookbackDays: 365 * 2 },
  '1W': { alpaca: '1Week', lookbackDays: 365 * 10 },
}

export const TIMEFRAME_LABELS = Object.keys(TIMEFRAMES)

export const DEFAULT_TIMEFRAME = '1m'

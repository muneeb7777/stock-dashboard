import axios from 'axios'
import { TIMEFRAMES } from './timeframes'

const API_KEY = import.meta.env.VITE_ALPACA_KEY
const API_SECRET = import.meta.env.VITE_ALPACA_SECRET

// In dev, the Vite proxy at /api/alpaca avoids CORS. The production build is
// embedded as static HTML with no proxy, so it talks to Alpaca directly.
const BASE_URL = import.meta.env.DEV ? '/api/alpaca' : 'https://data.alpaca.markets'

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'APCA-API-KEY-ID': API_KEY,
    'APCA-API-SECRET-KEY': API_SECRET,
  },
})

/** Convert an Alpaca bar {t,o,h,l,c,v} into a lightweight-charts bar. */
function toChartBar(bar) {
  return {
    time: Math.floor(Date.parse(bar.t) / 1000),
    open: bar.o,
    high: bar.h,
    low: bar.l,
    close: bar.c,
    volume: bar.v,
  }
}

/**
 * Fetch historical bars for `symbol` at the given UI timeframe label
 * (one of TIMEFRAMES keys). Returns an array of chart bars sorted by time.
 */
export async function fetchBars(symbol, timeframeLabel) {
  const cfg = TIMEFRAMES[timeframeLabel] ?? TIMEFRAMES['1D']
  const start = new Date(Date.now() - cfg.lookbackDays * 24 * 60 * 60 * 1000)

  const bars = []
  let pageToken = null

  do {
    const { data } = await client.get(`/v2/stocks/${symbol}/bars`, {
      params: {
        timeframe: cfg.alpaca,
        start: start.toISOString(),
        limit: 10000,
        adjustment: 'raw',
        feed: 'iex',
        page_token: pageToken || undefined,
      },
    })
    bars.push(...(data.bars || []).map(toChartBar))
    pageToken = data.next_page_token
  } while (pageToken)

  // Drop bars with no trading activity (Alpaca forward-fills these as flat
  // zero-volume candles, which render as a flat line across the gap).
  return bars.filter((bar) => bar.volume > 0)
}

/** Fetch the latest trade price for `symbol` (used for the header / price line). */
export async function fetchLatestTrade(symbol) {
  const { data } = await client.get(`/v2/stocks/${symbol}/trades/latest`, {
    params: { feed: 'iex' },
  })
  return data.trade
}

/** Fetch yesterday's daily bar (for change/% change baselines). */
export async function fetchPrevDailyBar(symbol) {
  const end = new Date()
  const start = new Date(end.getTime() - 10 * 24 * 60 * 60 * 1000)
  const { data } = await client.get(`/v2/stocks/${symbol}/bars`, {
    params: {
      timeframe: '1Day',
      start: start.toISOString(),
      end: end.toISOString(),
      limit: 10,
      adjustment: 'raw',
      feed: 'iex',
    },
  })
  const bars = (data.bars || []).map(toChartBar)
  return bars.length ? bars[bars.length - 1] : null
}

/** Fetch a snapshot (latest trade + today's/yesterday's daily bars) for the header. */
export async function fetchSnapshot(symbol) {
  const { data } = await client.get(`/v2/stocks/${symbol}/snapshot`, {
    params: { feed: 'iex' },
  })
  return data
}

const STREAM_URL = 'wss://stream.data.alpaca.markets/v2/iex'

/**
 * Open the Alpaca market-data WebSocket and stream live bar/trade updates.
 *
 * Returns a controller with `setSymbol(symbol)` to switch the active
 * subscription and `close()` to tear the connection down.
 */
export function connectStream({ onBar, onTrade, onStatus }) {
  let ws = null
  let currentSymbol = null
  let authenticated = false
  let closed = false

  const connect = () => {
    ws = new WebSocket(STREAM_URL)

    ws.onopen = () => {
      onStatus?.('connecting')
      ws.send(JSON.stringify({ action: 'auth', key: API_KEY, secret: API_SECRET }))
    }

    ws.onmessage = (event) => {
      let messages
      try {
        messages = JSON.parse(event.data)
      } catch {
        return
      }
      if (!Array.isArray(messages)) messages = [messages]

      for (const msg of messages) {
        switch (msg.T) {
          case 'success':
            if (msg.msg === 'authenticated') {
              authenticated = true
              onStatus?.('live')
              if (currentSymbol) subscribe(currentSymbol)
            }
            break
          case 'subscription':
            break
          case 'error':
            onStatus?.(`error: ${msg.msg || 'unknown'}`)
            break
          case 'b':
            onBar?.(msg)
            break
          case 't':
            onTrade?.(msg)
            break
          default:
            break
        }
      }
    }

    ws.onerror = () => {
      onStatus?.('error')
    }

    ws.onclose = () => {
      authenticated = false
      if (!closed) {
        onStatus?.('reconnecting')
        setTimeout(connect, 3000)
      }
    }
  }

  const send = (payload) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload))
    }
  }

  const subscribe = (symbol) => {
    send({ action: 'subscribe', bars: [symbol], trades: [symbol] })
  }

  const unsubscribe = (symbol) => {
    send({ action: 'unsubscribe', bars: [symbol], trades: [symbol] })
  }

  connect()

  return {
    setSymbol(symbol) {
      if (currentSymbol === symbol) return
      if (authenticated && currentSymbol) unsubscribe(currentSymbol)
      currentSymbol = symbol
      if (authenticated) subscribe(currentSymbol)
    },
    close() {
      closed = true
      ws?.close()
    },
  }
}

export { toChartBar }

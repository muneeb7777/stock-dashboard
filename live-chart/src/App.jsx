import { useEffect, useRef, useState } from 'react'
import Header from './components/Header'
import Toolbar from './components/Toolbar'
import DrawingToolbar from './components/DrawingToolbar'
import ChartPanel from './components/ChartPanel'
import { fetchBars, fetchSnapshot, connectStream, toChartBar } from './lib/alpaca'
import { DEFAULT_TIMEFRAME } from './lib/timeframes'
import './App.css'

const SNAPSHOT_INTERVAL_MS = 30000

const emptyQuote = { price: null, change: null, changePct: null, high: null, low: null, volume: null }

function App() {
  const [symbol, setSymbol] = useState('CELH')
  const [timeframe, setTimeframe] = useState(DEFAULT_TIMEFRAME)
  const [indicators, setIndicators] = useState(() => new Set(['EMA20', 'EMA50', 'Volume']))
  const [bars, setBars] = useState([])
  const [liveBar, setLiveBar] = useState(null)
  const [quote, setQuote] = useState(emptyQuote)
  const [status, setStatus] = useState('connecting')
  const [activeTool, setActiveTool] = useState('cursor')

  const prevCloseRef = useRef(null)
  const streamRef = useRef(null)

  // Historical bars whenever symbol or timeframe changes.
  useEffect(() => {
    let cancelled = false
    setLiveBar(null)

    fetchBars(symbol, timeframe)
      .then((data) => {
        if (!cancelled) setBars(data)
      })
      .catch((err) => {
        console.error('Failed to fetch bars', err)
        if (!cancelled) setBars([])
      })

    return () => {
      cancelled = true
    }
  }, [symbol, timeframe])

  // Header stats: snapshot on symbol change, then refreshed periodically.
  useEffect(() => {
    let cancelled = false

    const loadSnapshot = () => {
      fetchSnapshot(symbol)
        .then((snap) => {
          if (cancelled) return
          const prevClose = snap.prevDailyBar?.c ?? null
          const price = snap.latestTrade?.p ?? snap.dailyBar?.c ?? null
          prevCloseRef.current = prevClose

          setQuote({
            price,
            change: price !== null && prevClose !== null ? price - prevClose : null,
            changePct: price !== null && prevClose ? ((price - prevClose) / prevClose) * 100 : null,
            high: snap.dailyBar?.h ?? null,
            low: snap.dailyBar?.l ?? null,
            volume: snap.dailyBar?.v ?? null,
          })
        })
        .catch((err) => console.error('Failed to fetch snapshot', err))
    }

    loadSnapshot()
    const interval = setInterval(loadSnapshot, SNAPSHOT_INTERVAL_MS)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [symbol])

  // WebSocket connection (created once, symbol switched dynamically).
  useEffect(() => {
    const stream = connectStream({
      onStatus: setStatus,
      onBar: (msg) => {
        if (msg.S !== symbol || timeframe !== '1m') return
        setLiveBar(toChartBar(msg))
      },
      onTrade: (msg) => {
        if (msg.S !== symbol) return
        const price = msg.p
        const prevClose = prevCloseRef.current
        setQuote((q) => ({
          ...q,
          price,
          change: prevClose !== null ? price - prevClose : null,
          changePct: prevClose ? ((price - prevClose) / prevClose) * 100 : null,
          high: q.high !== null ? Math.max(q.high, price) : price,
          low: q.low !== null ? Math.min(q.low, price) : price,
        }))
      },
    })

    streamRef.current = stream
    return () => stream.close()
  }, [])

  // Switch the live subscription whenever the symbol changes.
  useEffect(() => {
    streamRef.current?.setSymbol(symbol)
  }, [symbol])

  const toggleIndicator = (key) => {
    setIndicators((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  return (
    <div className="app">
      <Header symbol={symbol} quote={quote} status={status} />
      <Toolbar
        symbol={symbol}
        onSymbolChange={setSymbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        indicators={indicators}
        onToggleIndicator={toggleIndicator}
      />
      <div className="chart-area">
        <DrawingToolbar activeTool={activeTool} onSelectTool={setActiveTool} />
        <ChartPanel
          bars={bars}
          indicators={indicators}
          livePrice={quote.price}
          liveBar={liveBar}
          activeTool={activeTool}
          onToolChange={setActiveTool}
        />
      </div>
    </div>
  )
}

export default App

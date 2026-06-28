function fmtPrice(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtVolume(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  return value.toFixed(0)
}

export default function Header({ symbol, quote, status }) {
  const { price, change, changePct, high, low, volume } = quote
  const positive = (change ?? 0) >= 0
  const dirClass = positive ? 'positive' : 'negative'

  const statusLabel = {
    live: 'Live',
    connecting: 'Connecting…',
    reconnecting: 'Reconnecting…',
    closed: 'Closed',
  }[status] || status

  return (
    <header className="app-header">
      <div className="header-symbol">
        <span className="symbol-name">{symbol}</span>
        <span className={`status-pill status-${status}`}>{statusLabel}</span>
      </div>

      <div className={`header-price ${dirClass}`}>
        <span className="price-value">{fmtPrice(price)}</span>
        <span className="price-change">
          {change === null ? '—' : `${positive ? '+' : ''}${fmtPrice(change)}`}
          {' '}
          ({changePct === null ? '—' : `${positive ? '+' : ''}${changePct.toFixed(2)}%`})
        </span>
      </div>

      <div className="header-stats">
        <div className="stat">
          <span className="stat-label">High</span>
          <span className="stat-value">{fmtPrice(high)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Low</span>
          <span className="stat-value">{fmtPrice(low)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Volume</span>
          <span className="stat-value">{fmtVolume(volume)}</span>
        </div>
      </div>
    </header>
  )
}

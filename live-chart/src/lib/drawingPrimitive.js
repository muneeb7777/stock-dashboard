// Lightweight canvas primitive that renders user-created drawings (trend
// lines, rectangles, text labels) on top of the candlestick series.
// Horizontal lines are handled separately via `series.createPriceLine()`.

const TREND_COLOR = '#f1c40f'
const RECT_FILL = 'rgba(41,98,255,0.15)'
const RECT_BORDER = '#2962ff'
const TEXT_COLOR = '#e8eaed'

export class DrawingPrimitive {
  constructor(getState) {
    this._getState = getState
    this._chart = null
    this._series = null
    this._requestUpdate = null
  }

  attached({ chart, series, requestUpdate }) {
    this._chart = chart
    this._series = series
    this._requestUpdate = requestUpdate
  }

  detached() {
    this._chart = null
    this._series = null
  }

  updateAllViews() {}

  requestUpdate() {
    this._requestUpdate?.()
  }

  paneViews() {
    return [
      {
        renderer: () => ({
          draw: (target) => {
            const chart = this._chart
            const series = this._series
            if (!chart || !series) return
            const { drawings, pending } = this._getState()

            target.useBitmapCoordinateSpace((scope) => {
              const ctx = scope.context
              ctx.save()
              ctx.scale(scope.horizontalPixelRatio, scope.verticalPixelRatio)
              for (const drawing of drawings) {
                drawShape(ctx, chart, series, drawing, false)
              }
              if (pending) drawShape(ctx, chart, series, pending, true)
              ctx.restore()
            })
          },
        }),
      },
    ]
  }
}

function toXY(chart, series, point) {
  const x = chart.timeScale().timeToCoordinate(point.time)
  const y = series.priceToCoordinate(point.price)
  if (x === null || y === null) return null
  return { x, y }
}

function drawShape(ctx, chart, series, shape, preview) {
  if (shape.type === 'trend') {
    const p1 = toXY(chart, series, shape.p1)
    const p2 = toXY(chart, series, shape.p2)
    if (!p1 || !p2) return
    ctx.strokeStyle = TREND_COLOR
    ctx.lineWidth = 1.5
    ctx.setLineDash(preview ? [4, 4] : [])
    ctx.beginPath()
    ctx.moveTo(p1.x, p1.y)
    ctx.lineTo(p2.x, p2.y)
    ctx.stroke()
    ctx.setLineDash([])
  } else if (shape.type === 'rect') {
    const p1 = toXY(chart, series, shape.p1)
    const p2 = toXY(chart, series, shape.p2)
    if (!p1 || !p2) return
    const x = Math.min(p1.x, p2.x)
    const y = Math.min(p1.y, p2.y)
    const w = Math.abs(p2.x - p1.x)
    const h = Math.abs(p2.y - p1.y)
    ctx.fillStyle = RECT_FILL
    ctx.fillRect(x, y, w, h)
    ctx.strokeStyle = RECT_BORDER
    ctx.lineWidth = 1
    ctx.setLineDash(preview ? [4, 4] : [])
    ctx.strokeRect(x, y, w, h)
    ctx.setLineDash([])
  } else if (shape.type === 'text') {
    const p = toXY(chart, series, shape.p)
    if (!p) return
    ctx.fillStyle = TEXT_COLOR
    ctx.font = '12px -apple-system, BlinkMacSystemFont, sans-serif'
    ctx.textBaseline = 'bottom'
    ctx.fillText(shape.text, p.x + 4, p.y - 4)
  }
}

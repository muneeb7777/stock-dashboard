export const DRAWING_TOOLS = [
  {
    key: 'cursor',
    label: 'Cursor',
    icon: (
      <path d="M4 2.5 L4 17.5 L8.2 13.6 L10.8 19 L13 18 L10.4 12.6 L16 12.6 Z" />
    ),
  },
  {
    key: 'hline',
    label: 'Horizontal Line',
    icon: <path d="M2 10 H18" strokeLinecap="round" />,
  },
  {
    key: 'trend',
    label: 'Trend Line',
    icon: <path d="M3 17 L17 3" strokeLinecap="round" />,
  },
  {
    key: 'rect',
    label: 'Rectangle',
    icon: <rect x="3" y="5" width="14" height="10" rx="1" />,
  },
  {
    key: 'text',
    label: 'Text',
    icon: (
      <path d="M4 4 H16 M10 4 V16" strokeLinecap="round" />
    ),
  },
]

export default function DrawingToolbar({ activeTool, onSelectTool }) {
  return (
    <div className="drawing-toolbar">
      {DRAWING_TOOLS.map((tool) => (
        <button
          key={tool.key}
          className={`draw-btn ${activeTool === tool.key ? 'active' : ''}`}
          title={tool.label}
          onClick={() => onSelectTool(tool.key)}
        >
          <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.6">
            {tool.icon}
          </svg>
        </button>
      ))}
    </div>
  )
}

import { useMemo, useState } from 'react'
import type { IncomeEntry, WealthHistoryMonth, Classification } from '../types/zakat'
import { formatCAD } from '../lib/format'
import { summarizeIncome } from '../lib/income'

const CLASS_COLOR: Record<string, string> = {
  Halal: '#0d4f4a',
  Haram: '#8c2f32',
  Mixed: '#5c4a6e',
  Tentative: '#8f6f3e',
  'Missing Information': '#6b6460',
}

function monthNet(m: WealthHistoryMonth): number {
  return (
    m.maliki_net_wealth ??
    m.cash_and_bank_cad +
      m.business_cash_cad +
      m.business_inventory_halal_cad +
      m.gold_silver_savings_cad +
      m.stock_shares_cad +
      m.other_halal_investments_cad +
      m.crypto_cad +
      m.business_receivables_likely_cad -
      m.debts_due_within_12_months_cad
  )
}

interface ChartsProps {
  incomeRows: IncomeEntry[]
  wealthRows: IncomeEntry[]
  history: WealthHistoryMonth[]
  nisabCad: number
  onPickClass?: (cls: Classification | 'ALL') => void
  onPickWealth?: () => void
  onPickHawl?: () => void
}

export function Charts({
  incomeRows,
  wealthRows,
  history,
  nisabCad,
  onPickClass,
  onPickWealth,
  onPickHawl,
}: ChartsProps) {
  const summary = useMemo(() => summarizeIncome(incomeRows), [incomeRows])
  const [hover, setHover] = useState<string | null>(null)
  const [lockedClass, setLockedClass] = useState<string | null>(null)
  const [hawlHover, setHawlHover] = useState<number | null>(null)
  const [hawlPinned, setHawlPinned] = useState<number | null>(null)
  const [wealthHover, setWealthHover] = useState<string | null>(null)

  const activeClass = lockedClass || hover

  const wealthByCat = useMemo(() => {
    const map = new Map<string, number>()
    for (const row of wealthRows) {
      map.set(row.category, (map.get(row.category) || 0) + (Number(row.gross_amount) || 0))
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1])
  }, [wealthRows])

  const donutSlices = summary.byClass.filter((s) => s.amount > 0)
  const donutSum = donutSlices.reduce((s, x) => s + x.amount, 0)
  const donutTotal = donutSum || 1
  let cursor = 0
  const arcs = donutSlices.map((slice) => {
    const start = cursor
    const frac = slice.amount / donutTotal
    cursor += frac
    return { ...slice, start, end: cursor, color: CLASS_COLOR[slice.label] }
  })

  const hawlPoints = history.map((m, i) => ({
    i,
    label: m.month_end.length >= 10 ? m.month_end.slice(5, 10) : `M${i + 1}`,
    full: m.month_end.slice(0, 10),
    net: monthNet(m),
    note: m.event_note,
  }))
  const hawlMax = Math.max(nisabCad * 1.15, ...hawlPoints.map((p) => p.net), 1)
  const hawlActive = hawlPinned ?? hawlHover

  const pickClass = (label: Classification) => {
    setLockedClass((prev) => (prev === label ? null : label))
    onPickClass?.(label)
  }

  const nearestHawl = (clientX: number, svg: SVGSVGElement) => {
    const rect = svg.getBoundingClientRect()
    const t = (clientX - rect.left) / rect.width
    const idx = Math.round(t * Math.max(0, hawlPoints.length - 1))
    return Math.min(hawlPoints.length - 1, Math.max(0, idx))
  }

  return (
    <div className="chart-grid">
      <section className="card panel">
        <h2>Income by class</h2>
        <p className="sub">Hover to preview. Click a slice or a name to open that list.</p>
        <div className="chart-split">
          <svg viewBox="0 0 120 120" className="donut" role="img" aria-label="Income classification. Click a slice to filter.">
            {arcs.map((arc) => {
              const large = arc.end - arc.start > 0.5 ? 1 : 0
              const a0 = arc.start * 2 * Math.PI - Math.PI / 2
              const a1 = arc.end * 2 * Math.PI - Math.PI / 2
              const selected = activeClass === arc.label
              const r = selected ? 45 : 42
              const cx = 60
              const cy = 60
              const x0 = cx + r * Math.cos(a0)
              const y0 = cy + r * Math.sin(a0)
              const x1 = cx + r * Math.cos(a1)
              const y1 = cy + r * Math.sin(a1)
              const d = `M ${cx} ${cy} L ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1} Z`
              const pct = Math.round((arc.amount / donutTotal) * 100)
              return (
                <path
                  key={arc.label}
                  d={d}
                  fill={arc.color}
                  opacity={activeClass && activeClass !== arc.label ? 0.28 : 1}
                  className="chart-hit"
                  tabIndex={0}
                  role="button"
                  aria-label={`${arc.label}, ${formatCAD(arc.amount)}, ${pct} percent. Activate to filter income.`}
                  onMouseEnter={() => setHover(arc.label)}
                  onMouseLeave={() => setHover(null)}
                  onFocus={() => setHover(arc.label)}
                  onBlur={() => setHover(null)}
                  onClick={() => pickClass(arc.label)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      pickClass(arc.label)
                    }
                  }}
                />
              )
            })}
            <circle cx="60" cy="60" r="24" fill="#fbfbfa" />
            <text x="60" y="56" textAnchor="middle" fontSize="6" fill="#5c615c">
              {activeClass || 'Income'}
            </text>
            <text x="60" y="66" textAnchor="middle" fontSize="6.2" fontWeight="600" fill="#161916">
              {formatCAD(activeClass ? summary.byClass.find((s) => s.label === activeClass)?.amount || 0 : donutSum, 0)}
            </text>
            {activeClass && (
              <text x="60" y="75" textAnchor="middle" fontSize="5.5" fill="#5c615c">
                {Math.round(((summary.byClass.find((s) => s.label === activeClass)?.amount || 0) / donutTotal) * 100)}%
              </text>
            )}
          </svg>
          <ul className="legend">
            {summary.byClass.map((s) => (
              <li key={s.label}>
                <button
                  type="button"
                  className={`legend-btn ${activeClass === s.label ? 'legend-active' : ''}`}
                  title={`Show ${s.label} income`}
                  onMouseEnter={() => setHover(s.label)}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => pickClass(s.label)}
                >
                  <span className="swatch" style={{ background: CLASS_COLOR[s.label] }} />
                  <span>
                    {s.label}
                    <em>
                      {s.count} lines · {formatCAD(s.amount)} · {donutSum ? Math.round((s.amount / donutTotal) * 100) : 0}%
                    </em>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
        <p className="chart-readout" aria-live="polite">
          {activeClass
            ? `${activeClass}: ${formatCAD(summary.byClass.find((s) => s.label === activeClass)?.amount || 0)}. Click again in Income to see every line.`
            : 'Tip: click Haram to jump to those inflows.'}
        </p>
      </section>

      <section className="card panel">
        <h2>Year-end wealth mix</h2>
        <p className="sub">Click a bar to open the Wealth table. Zakat uses this snapshot.</p>
        <div className="bar-list">
          {wealthByCat.map(([cat, amount]) => {
            const max = wealthByCat[0]?.[1] || 1
            const on = wealthHover === cat
            return (
              <button
                key={cat}
                type="button"
                className={`bar-row ${on ? 'bar-on' : ''}`}
                title={`Open wealth — ${cat}`}
                onMouseEnter={() => setWealthHover(cat)}
                onMouseLeave={() => setWealthHover(null)}
                onClick={() => onPickWealth?.()}
              >
                <div className="bar-meta">
                  <span>{cat}</span>
                  <span className="mono">{formatCAD(amount)}</span>
                </div>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${Math.max(4, (amount / max) * 100)}%` }} />
                </div>
              </button>
            )
          })}
          {wealthByCat.length === 0 && <p className="empty">No assets yet.</p>}
        </div>
      </section>

      {hawlPoints.length > 0 && (
        <section className="card panel chart-span">
          <h2>Hawl against nisab</h2>
          <p className="sub">Move across the line. Click a month to pin it. Open Hawl for the full table.</p>
          <svg
            viewBox="0 0 640 180"
            className="hawl-chart"
            role="img"
            aria-label="Monthly net wealth versus nisab. Hover or click a month."
            onMouseMove={(e) => setHawlHover(nearestHawl(e.clientX, e.currentTarget))}
            onMouseLeave={() => {
              if (hawlPinned === null) setHawlHover(null)
            }}
            onClick={(e) => {
              const idx = nearestHawl(e.clientX, e.currentTarget)
              setHawlPinned((prev) => (prev === idx ? null : idx))
              setHawlHover(idx)
            }}
          >
            {(() => {
              const nisabY = 150 - (nisabCad / hawlMax) * 130
              const area = hawlPoints
                .map((p, idx) => {
                  const x = 40 + (idx / Math.max(1, hawlPoints.length - 1)) * 560
                  const y = 150 - (p.net / hawlMax) * 130
                  return `${x},${y}`
                })
                .join(' ')
              const lastX = 40 + 560
              return (
                <>
                  <polygon
                    points={`40,150 ${area} ${lastX},150`}
                    fill="rgba(13, 79, 74, 0.08)"
                  />
                  <line x1="36" y1={nisabY} x2="620" y2={nisabY} stroke="#8f6f3e" strokeDasharray="5 4" />
                  <text x="580" y={nisabY - 6} fontSize="9" fill="#8f6f3e">
                    nisab {formatCAD(nisabCad, 0)}
                  </text>
                </>
              )
            })()}
            <polyline
              fill="none"
              stroke="#0d4f4a"
              strokeWidth="2.2"
              points={hawlPoints
                .map((p, idx) => {
                  const x = 40 + (idx / Math.max(1, hawlPoints.length - 1)) * 560
                  const y = 150 - (p.net / hawlMax) * 130
                  return `${x},${y}`
                })
                .join(' ')}
            />
            {hawlActive !== null && hawlPoints[hawlActive] && (
              <line
                x1={40 + (hawlActive / Math.max(1, hawlPoints.length - 1)) * 560}
                x2={40 + (hawlActive / Math.max(1, hawlPoints.length - 1)) * 560}
                y1="20"
                y2="150"
                stroke="#161916"
                strokeOpacity="0.18"
              />
            )}
            {hawlPoints.map((p, idx) => {
              const x = 40 + (idx / Math.max(1, hawlPoints.length - 1)) * 560
              const y = 150 - (p.net / hawlMax) * 130
              const below = p.net < nisabCad
              const on = hawlActive === idx
              return (
                <g key={p.i}>
                  <circle
                    cx={x}
                    cy={y}
                    r={on ? 7 : 4.5}
                    fill={below ? '#8c2f32' : '#0d4f4a'}
                    stroke={on ? '#fbfbfa' : 'none'}
                    strokeWidth="2"
                    className="chart-hit"
                  />
                  <text x={x} y="172" textAnchor="middle" fontSize="8" fill={on ? '#161916' : '#5c615c'}>
                    {p.label}
                  </text>
                </g>
              )
            })}
          </svg>
          {hawlActive !== null && hawlPoints[hawlActive] && (
            <p className="chart-readout" aria-live="polite">
              {hawlPoints[hawlActive].full}: {formatCAD(hawlPoints[hawlActive].net)}
              {hawlPoints[hawlActive].net < nisabCad ? ' — below nisab, hawl resets' : ' — at or above nisab'}
              {hawlPoints[hawlActive].note ? ` · ${hawlPoints[hawlActive].note}` : ''}
              {hawlPinned !== null ? ' · pinned' : ''}
              {' · '}
              <button type="button" className="linkish" onClick={() => onPickHawl?.()}>
                Open Hawl table
              </button>
            </p>
          )}
        </section>
      )}
    </div>
  )
}

import { useMemo, useState } from 'react'
import type { IncomeEntry, DebtEntry, Classification } from '../types/zakat'
import { formatCAD } from '../lib/format'
import { Pill } from './Header'
import { ConfirmDialog } from './ConfirmDialog'

interface TransactionTableProps {
  title: string
  subtitle: string
  entries: IncomeEntry[]
  debts?: DebtEntry[]
  onRemoveEntry?: (id: string) => void
  onRemoveDebt?: (index: number) => void
  incomeOnly?: boolean
  forcedFilter?: string
}

export function TransactionTable({
  title,
  subtitle,
  entries,
  debts = [],
  onRemoveEntry,
  onRemoveDebt,
  incomeOnly,
  forcedFilter,
}: TransactionTableProps) {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('ALL')
  const [showOutflows, setShowOutflows] = useState(false)
  const [pending, setPending] = useState<{ kind: 'asset' | 'debt'; id: string; label: string; amount: string } | null>(null)
  const activeFilter = forcedFilter && forcedFilter !== 'ALL' ? forcedFilter : filter

  const visible = useMemo(() => {
    return entries.filter((e) => {
      if (incomeOnly && !showOutflows && (e.direction || 'inflow') === 'outflow') return false
      if (incomeOnly && !showOutflows && e.is_income === false) return false
      const hay = `${e.description} ${e.category} ${e.notes} ${e.keyword || ''}`.toLowerCase()
      const matchSearch = hay.includes(search.toLowerCase())
      const matchFilter = activeFilter === 'ALL' || e.classification === activeFilter
      return matchSearch && matchFilter
    })
  }, [entries, search, activeFilter, incomeOnly, showOutflows])

  return (
    <section className="card panel">
      <h2>{title}</h2>
      <p className="sub">{subtitle}</p>
      <div className="filter-row">
        <input
          className="input search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search"
        />
        <select className="select" value={activeFilter} onChange={(e) => setFilter(e.target.value)} style={{ maxWidth: 220 }}>
          <option value="ALL">All classifications</option>
          {(['Halal', 'Haram', 'Mixed', 'Tentative', 'Missing Information'] as Classification[]).map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        {incomeOnly && (
          <button type="button" className="btn" onClick={() => setShowOutflows((v) => !v)}>
            {showOutflows ? 'Hide spending' : 'Show spending'}
          </button>
        )}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Class</th>
              <th>Amount</th>
              <th>Why</th>
              {onRemoveEntry && <th />}
            </tr>
          </thead>
          <tbody>
            {visible.map((e) => (
              <tr key={e.id}>
                <td>
                  <div className="item-title">{e.description}</div>
                  <div className="item-note">
                    {e.category}
                    {e.date ? ` · ${e.date}` : ''}
                    {e.direction === 'outflow' ? ' · outflow' : ''}
                  </div>
                  {e.is_personal_jewelry && <span className="chip">Worn jewelry — exempt</span>}
                  {e.is_personal_loan && <span className="chip">Personal loan — exempt until received</span>}
                  {e.classification === 'Mixed' && !e.is_mixed_separated && (
                    <span className="chip">Retained mixed — still zakatable</span>
                  )}
                </td>
                <td>
                  <Pill kind={e.classification}>{e.classification}</Pill>
                </td>
                <td className="mono">
                  {formatCAD(e.gross_amount)}
                  {e.classification === 'Mixed' && (e.halal_amount > 0 || e.haram_amount > 0) && (
                    <div className="item-note">
                      Halal {formatCAD(e.halal_amount)} · Haram {formatCAD(e.haram_amount)}
                    </div>
                  )}
                </td>
                <td className="item-note">{e.notes || '—'}</td>
                {onRemoveEntry && (
                  <td>
                    <button
                      type="button"
                      className="icon-btn"
                      title="Remove this asset from zakat"
                      aria-label={`Remove ${e.description}`}
                      onClick={() =>
                        setPending({
                          kind: 'asset',
                          id: e.id,
                          label: e.description,
                          amount: formatCAD(e.gross_amount),
                        })
                      }
                    >
                      Remove
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={5} className="empty">
                  Nothing to show yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {debts.length > 0 && (
        <div style={{ marginTop: '1.25rem' }}>
          <h2>Debts</h2>
          <p className="sub">Only the amount due within 12 months is deducted under Maliki rules.</p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Debt</th>
                  <th>Balance</th>
                  <th>Due in 12 months</th>
                  <th>Treatment</th>
                  {onRemoveDebt && <th />}
                </tr>
              </thead>
              <tbody>
                {debts.map((d, idx) => {
                  const due = d.amount_due_within_12_months || (d.is_due_within_12_months ? d.outstanding_balance : 0)
                  const rest = Math.max(0, d.outstanding_balance - due)
                  return (
                    <tr key={d.id || idx}>
                      <td>
                        <div className="item-title">{d.description}</div>
                        <div className="item-note">{d.creditor || ''}</div>
                      </td>
                      <td className="mono">{formatCAD(d.outstanding_balance)}</td>
                      <td className="mono">{formatCAD(due)}</td>
                      <td className="item-note">
                        Deduct {formatCAD(due)}
                        {rest > 0 ? ` · ${formatCAD(rest)} after 12 months is not deducted` : ''}
                      </td>
                      {onRemoveDebt && (
                        <td>
                          <button
                            type="button"
                            className="icon-btn"
                            title="Remove this debt"
                            aria-label={`Remove debt ${d.description}`}
                            onClick={() =>
                              setPending({
                                kind: 'debt',
                                id: String(idx),
                                label: d.description,
                                amount: formatCAD(d.outstanding_balance),
                              })
                            }
                          >
                            Remove
                          </button>
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(pending)}
        title={pending?.kind === 'debt' ? 'Remove this debt?' : 'Remove this from wealth?'}
        body={
          pending
            ? `${pending.label} (${pending.amount}) will leave the snapshot. Zakat will be calculated again.`
            : ''
        }
        confirmLabel="Remove it"
        cancelLabel="Keep it"
        onCancel={() => setPending(null)}
        onConfirm={() => {
          if (!pending) return
          if (pending.kind === 'asset') onRemoveEntry?.(pending.id)
          else onRemoveDebt?.(Number(pending.id))
          setPending(null)
        }}
      />
    </section>
  )
}

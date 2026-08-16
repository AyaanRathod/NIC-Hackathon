import { useState } from 'react'
import type { ZakatCalculationResponse, SheetInventory } from '../types/zakat'
import { formatCAD } from '../lib/format'
import type { IncomeSummary } from '../lib/income'

interface DashboardCardsProps {
  result: ZakatCalculationResponse
  income: IncomeSummary
  inventory: SheetInventory[]
  onGoIncome?: () => void
  onGoWealth?: () => void
}

export function DashboardCards({ result, income, inventory, onGoIncome, onGoWealth }: DashboardCardsProps) {
  const [copied, setCopied] = useState(false)

  const copyZakat = async () => {
    try {
      await navigator.clipboard.writeText(String(result.zakat_due_cad))
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
    }
  }

  return (
    <>
      <section className="card hero">
        <div className="hero-kicker">Estimated zakat · Maliki · 2.5%</div>
        <button type="button" className="hero-copy" onClick={() => void copyZakat()} title="Copy the zakat amount">
          <div className={`hero-amount display ${result.is_eligible_for_zakat ? 'due' : ''}`}>
            {formatCAD(result.zakat_due_cad)}
          </div>
          <span className="copy-hint">{copied ? 'Copied' : 'Click to copy'}</span>
        </button>
        <div className="hero-rule" />
        <p className="hero-meta">
          {result.is_eligible_for_zakat
            ? `${formatCAD(result.net_zakatable_wealth)} net zakatable wealth × 2.5%. Nisab is ${formatCAD(result.nisab_threshold_cad)}. Hawl is complete.`
            : result.is_hawl_maintained
              ? `No zakat this year. Net wealth ${formatCAD(result.net_zakatable_wealth)} is below nisab ${formatCAD(result.nisab_threshold_cad)}.`
              : `No zakat this year. Wealth did not stay at or above nisab for a full lunar year.`}
        </p>
      </section>

      <div className="metric-row metric-row-6">
        <button type="button" className="card metric metric-btn" onClick={onGoIncome} title="Open classified income">
          <label>Total income</label>
          <strong className="mono">{formatCAD(income.totalIncome)}</strong>
          <span className="metric-hint">View income →</span>
        </button>
        <button type="button" className="card metric metric-btn" onClick={onGoWealth} title="Open year-end wealth">
          <label>Zakatable assets</label>
          <strong className="mono">{formatCAD(result.total_zakatable_assets)}</strong>
          <span className="metric-hint">View wealth →</span>
        </button>
        <button type="button" className="card metric metric-btn" onClick={onGoWealth} title="Open debts in wealth">
          <label>Debts deducted</label>
          <strong className="mono">{formatCAD(result.qualifying_debts_deducted)}</strong>
          <span className="metric-hint">View debts →</span>
        </button>
        <div className="card metric">
          <label>Exempt (Maliki)</label>
          <strong className="mono">{formatCAD(result.total_exempt_wealth)}</strong>
        </div>
        <button type="button" className="card metric metric-btn haram" onClick={onGoIncome} title="Open haram income">
          <label>Haram to remove</label>
          <strong className="mono">{formatCAD(result.total_haram_disposed)}</strong>
          <span className="metric-hint">Not zakat →</span>
        </button>
        <button type="button" className="card metric metric-btn" onClick={onGoIncome} title="Open classified income">
          <label>Income inflows</label>
          <strong className="mono">{income.inflowCount}</strong>
          <span className="metric-hint">View inflows →</span>
        </button>
      </div>

      {inventory.length > 0 && (
        <div className="banner file-banner">
          <h3>Full file read — nothing cut</h3>
          <p>{inventory.map((s) => `${s.sheet} ${s.rows_kept}/${s.rows_in_file}`).join(' · ')}</p>
        </div>
      )}
    </>
  )
}

import { useState } from 'react'
import type { ZakatCalculationResponse } from '../types/zakat'
import { formatCAD } from '../lib/format'

export function CalculationBreakdown({ result }: { result: ZakatCalculationResponse }) {
  const [openLog, setOpenLog] = useState(false)

  return (
    <section className="card panel">
      <h2>How this number was reached</h2>
      <p className="sub">Maliki formula, applied only to year-end wealth — not to the sum of income.</p>

      <div className="formula">
        <div>Net zakatable wealth</div>
        <code>
          Cash + halal investments + business inventory + investment gold/silver + expected business invoices
          − worn personal jewelry − unpaid personal loans − haram − tentative / missing
          − debts due within 12 months
        </code>
        <div>
          {formatCAD(result.total_zakatable_assets)} − {formatCAD(result.qualifying_debts_deducted)} ={' '}
          <strong>{formatCAD(result.net_zakatable_wealth)}</strong>
        </div>
        <div style={{ marginTop: '0.45rem' }}>
          {result.is_eligible_for_zakat
            ? `Zakat = ${formatCAD(result.net_zakatable_wealth)} × 2.5% = ${formatCAD(result.zakat_due_cad)}`
            : 'Zakat = $0 because nisab or hawl was not met.'}
        </div>
      </div>

      {result.warnings.length > 0 && (
        <div className="banner warn" style={{ marginTop: '1rem' }}>
          <h3>Needs attention</h3>
          <ul>
            {result.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {result.purification_items.length > 0 && (
        <div className="banner haram" style={{ marginTop: '1rem' }}>
          <h3>Haram to remove · {formatCAD(result.total_haram_disposed)}</h3>
          <p className="sub" style={{ marginBottom: '0.5rem' }}>
            This is not zakat. Separate it from personal wealth and give it away.
          </p>
          <ul>
            {result.purification_items.map((item) => (
              <li key={item.description}>
                {item.description}: {formatCAD(item.amount)} — {item.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button type="button" className="btn" style={{ marginTop: '1rem' }} onClick={() => setOpenLog((v) => !v)}>
        {openLog ? 'Hide line-by-line log' : 'Show line-by-line log'}
      </button>
      {openLog && (
        <pre className="audit">
          {result.audit_breakdown.join('\n')}
        </pre>
      )}
    </section>
  )
}

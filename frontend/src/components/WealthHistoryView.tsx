import type { WealthHistoryMonth } from '../types/zakat'
import { formatCAD } from '../lib/format'

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

export function WealthHistoryView({ history, nisabCad }: { history: WealthHistoryMonth[]; nisabCad: number }) {
  if (!history.length) {
    return (
      <section className="card panel">
        <h2>Hawl</h2>
        <p className="sub">
          Maliki rule: wealth must stay at or above nisab ({formatCAD(nisabCad)}) for one lunar year. If it
          drops below, the year starts again. No monthly history was uploaded.
        </p>
      </section>
    )
  }

  return (
    <section className="card panel">
      <h2>Hawl — twelve lunar months</h2>
      <p className="sub">
        Customary jewelry and unpaid personal loans are left out of this monthly check. If any month falls
        below {formatCAD(nisabCad)}, hawl resets.
      </p>
      <div className="hawl-strip">
        {history.map((m, idx) => {
          const net = monthNet(m)
          const up = net >= nisabCad
          const label = m.month_end.length >= 10 ? m.month_end.slice(5, 10) : `M${idx + 1}`
          return (
            <div key={`${m.month_end}-${idx}`} className={`hawl-cell ${up ? 'up' : 'down'}`} title={m.event_note || ''}>
              <strong>{label}</strong>
              {formatCAD(net, 0)}
            </div>
          )
        })}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Month</th>
              <th>Net wealth</th>
              <th>Status</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {history.map((m, idx) => {
              const net = monthNet(m)
              const up = net >= nisabCad
              return (
                <tr key={`row-${m.month_end}-${idx}`}>
                  <td className="mono">{m.month_end.slice(0, 10)}</td>
                  <td className="mono">{formatCAD(net)}</td>
                  <td>{up ? 'At or above nisab' : 'Below nisab — hawl resets'}</td>
                  <td className="item-note">{m.event_note || '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

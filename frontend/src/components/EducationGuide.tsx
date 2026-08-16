import { useEffect } from 'react'

interface EducationGuideProps {
  isOpen: boolean
  onClose: () => void
}

export function EducationGuide({ isOpen, onClose }: EducationGuideProps) {
  useEffect(() => {
    if (!isOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h2>Maliki rules used here</h2>
            <p className="sub">This tool follows only the Maliki exercise set. It is not a fatwa.</p>
          </div>
          <button type="button" className="btn" onClick={onClose} title="Close rules">
            Close
          </button>
        </div>

        <div className="rule-block">
          <h3>Hawl</h3>
          <p>
            Wealth must stay at or above nisab for one lunar year. If it falls below, the start date resets.
            A new year begins when nisab is reached again.
          </p>
        </div>
        <div className="rule-block">
          <h3>Gold and silver</h3>
          <p>
            Include bullion, coins, jewelry stored as wealth, investment jewelry, and excess jewelry not for
            personal use. Exclude customary jewelry worn for adornment. Diamonds and gemstones are out unless
            they are business inventory.
          </p>
        </div>
        <div className="rule-block">
          <h3>Debts</h3>
          <p>
            Only amounts due now or within 12 months reduce cash, gold and silver, investments, and business
            inventory. Long-term balances are not deducted.
          </p>
        </div>
        <div className="rule-block">
          <h3>Money owed to the user</h3>
          <p>
            Ordinary personal loans are not zakated each year while unpaid. When received, calculate one year
            of zakat on that amount. Unpaid business invoices are included if repayment is reasonably expected.
          </p>
        </div>
        <div className="rule-block">
          <h3>Five classifications</h3>
          <ul>
            <li>Halal — remaining amount is zakatable (subject to Maliki exemptions).</li>
            <li>Haram — separate it. It is not zakatable wealth. Removing it is not paying zakat.</li>
            <li>Mixed — if the haram portion is removed, zakat is on the halal remainder. If kept, the retained amount stays zakatable.</li>
            <li>Tentative — scholar review required. Left out of the zakat figure.</li>
            <li>Missing information — warn, and do not finish the classification.</li>
          </ul>
        </div>
        <div className="rule-block">
          <h3>Formula</h3>
          <p>
            Net zakatable wealth = cash + halal investments + business inventory + investment gold/silver +
            eligible business receivables − qualifying debts. If that total reaches nisab and hawl is complete:
            zakat = 2.5%.
          </p>
        </div>
        <div className="rule-block">
          <h3>Limits</h3>
          <p>
            Nisab is the organizer’s fixed Canadian-dollar figure, not a live gold price. Unusual contracts
            still need a scholar. Future work: bank feeds, better screening of unlisted investments, and a
            clearer path to give away purified funds.
          </p>
        </div>
      </div>
    </div>
  )
}

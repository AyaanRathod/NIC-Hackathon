import { useState, type FormEvent } from 'react'
import type { IncomeEntry, DebtEntry, Category, Classification } from '../types/zakat'
import { classifyTransaction } from '../api/client'

const categories: Category[] = [
  'Cash & Bank Balances',
  'Halal Investments',
  'Business Inventory',
  'Gold & Silver',
  'Receivables / Invoices',
  'Cryptocurrency',
  'Other',
]

interface ManualEntryFormProps {
  onAddEntry: (entry: IncomeEntry) => void
  onAddDebt: (debt: DebtEntry) => void
  nisabCad: number
  onNisabChange: (val: number) => void
  hawlMaintained: boolean
  onHawlChange: (val: boolean) => void
  onRunCalculation: () => void
  isCalculating: boolean
}

export function ManualEntryForm({
  onAddEntry,
  onAddDebt,
  nisabCad,
  onNisabChange,
  hawlMaintained,
  onHawlChange,
  onRunCalculation,
  isCalculating,
}: ManualEntryFormProps) {
  const [tab, setTab] = useState<'asset' | 'debt'>('asset')
  const [desc, setDesc] = useState('')
  const [cat, setCat] = useState<Category>('Cash & Bank Balances')
  const [amount, setAmount] = useState('')
  const [cls, setCls] = useState<Classification>('Halal')
  const [halalPortion, setHalalPortion] = useState('')
  const [haramPortion, setHaramPortion] = useState('')
  const [isMixedSeparated, setIsMixedSeparated] = useState(true)
  const [isJewelry, setIsJewelry] = useState(false)
  const [isPersonalLoan, setIsPersonalLoan] = useState(false)
  const [notes, setNotes] = useState('')
  const [debtDesc, setDebtDesc] = useState('')
  const [debtBalance, setDebtBalance] = useState('')
  const [debt12m, setDebt12m] = useState('')
  const [creditor, setCreditor] = useState('')

  const autoClassify = async () => {
    if (!desc.trim()) return
    const res = await classifyTransaction({ description: desc, category: cat, notes })
    setCls(res.classification)
    if (res.explanation) setNotes(res.explanation)
  }

  const submitAsset = (e: FormEvent) => {
    e.preventDefault()
    const grossVal = parseFloat(amount) || 0
    onAddEntry({
      id: crypto.randomUUID(),
      description: desc.trim(),
      category: cat,
      gross_amount: grossVal,
      classification: cls,
      halal_amount: parseFloat(halalPortion) || (cls === 'Halal' ? grossVal : 0),
      haram_amount: parseFloat(haramPortion) || (cls === 'Haram' ? grossVal : 0),
      is_mixed_separated: isMixedSeparated,
      is_personal_jewelry: isJewelry,
      is_personal_loan: isPersonalLoan,
      is_business_receivable_expected: true,
      notes: notes.trim(),
      is_income: true,
      direction: 'inflow',
    })
    setDesc('')
    setAmount('')
    setHalalPortion('')
    setHaramPortion('')
    setNotes('')
    setIsJewelry(false)
    setIsPersonalLoan(false)
  }

  const submitDebt = (e: FormEvent) => {
    e.preventDefault()
    const total = parseFloat(debtBalance) || 0
    const due12 = debt12m !== '' ? parseFloat(debt12m) : total
    onAddDebt({
      id: crypto.randomUUID(),
      description: debtDesc.trim(),
      outstanding_balance: total,
      amount_due_within_12_months: due12,
      is_due_within_12_months: due12 > 0,
      creditor: creditor.trim() || undefined,
    })
    setDebtDesc('')
    setDebtBalance('')
    setDebt12m('')
    setCreditor('')
  }

  return (
    <section className="card panel">
      <h2>Add by hand</h2>
      <p className="sub">Use this if you do not have a spreadsheet, or to correct a line after upload.</p>
      <div className="tabs" role="tablist">
        <button type="button" className={`tab ${tab === 'asset' ? 'active' : ''}`} onClick={() => setTab('asset')}>
          Income / asset
        </button>
        <button type="button" className={`tab ${tab === 'debt' ? 'active' : ''}`} onClick={() => setTab('debt')}>
          Debt
        </button>
      </div>

      {tab === 'asset' && (
        <form onSubmit={submitAsset} className="form-grid">
          <div className="full">
            <label className="field-label">Description</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} required />
              <button type="button" className="btn" onClick={() => void autoClassify()}>
                Classify
              </button>
            </div>
          </div>
          <div>
            <label className="field-label">Category</label>
            <select className="select" value={cat} onChange={(e) => setCat(e.target.value as Category)}>
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label">Amount (CAD)</label>
            <input className="input mono" type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          </div>
          <div>
            <label className="field-label">Classification</label>
            <select className="select" value={cls} onChange={(e) => setCls(e.target.value as Classification)}>
              <option>Halal</option>
              <option>Haram</option>
              <option>Mixed</option>
              <option>Tentative</option>
              <option>Missing Information</option>
            </select>
          </div>
          {cls === 'Mixed' && (
            <>
              <div>
                <label className="field-label">Halal portion</label>
                <input className="input" type="number" min="0" step="0.01" value={halalPortion} onChange={(e) => setHalalPortion(e.target.value)} />
              </div>
              <div>
                <label className="field-label">Haram portion</label>
                <input className="input" type="number" min="0" step="0.01" value={haramPortion} onChange={(e) => setHaramPortion(e.target.value)} />
              </div>
              <label className="check full">
                <input type="checkbox" checked={isMixedSeparated} onChange={(e) => setIsMixedSeparated(e.target.checked)} />
                Haram portion already removed. If unchecked, the full mixed amount stays zakatable.
              </label>
            </>
          )}
          <label className="check full">
            <input type="checkbox" checked={isJewelry} onChange={(e) => setIsJewelry(e.target.checked)} />
            Customary jewelry worn for personal use (Maliki exempt)
          </label>
          <label className="check full">
            <input type="checkbox" checked={isPersonalLoan} onChange={(e) => setIsPersonalLoan(e.target.checked)} />
            Unpaid personal loan owed to me (exempt until received)
          </label>
          <div className="full">
            <label className="field-label">Explanation</label>
            <input className="input" value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div className="full">
            <button type="submit" className="btn btn-primary">
              Add item
            </button>
          </div>
        </form>
      )}

      {tab === 'debt' && (
        <form onSubmit={submitDebt} className="form-grid">
          <div className="full">
            <label className="field-label">Description</label>
            <input className="input" value={debtDesc} onChange={(e) => setDebtDesc(e.target.value)} required />
          </div>
          <div>
            <label className="field-label">Outstanding balance</label>
            <input className="input" type="number" min="0" step="0.01" value={debtBalance} onChange={(e) => setDebtBalance(e.target.value)} required />
          </div>
          <div>
            <label className="field-label">Due within 12 months</label>
            <input className="input" type="number" min="0" step="0.01" value={debt12m} onChange={(e) => setDebt12m(e.target.value)} />
          </div>
          <div className="full">
            <label className="field-label">Creditor</label>
            <input className="input" value={creditor} onChange={(e) => setCreditor(e.target.value)} />
          </div>
          <div className="full">
            <button type="submit" className="btn btn-primary">
              Add debt
            </button>
          </div>
        </form>
      )}

      <div className="form-grid" style={{ marginTop: '1.2rem', paddingTop: '1rem', borderTop: '1px solid var(--line)' }}>
        <div>
          <label className="field-label">Nisab (CAD)</label>
          <input className="input mono" type="number" min="1" step="0.01" value={nisabCad} onChange={(e) => onNisabChange(parseFloat(e.target.value) || 0)} />
        </div>
        <label className="check" style={{ alignSelf: 'end' }}>
          <input type="checkbox" checked={hawlMaintained} onChange={(e) => onHawlChange(e.target.checked)} />
          Hawl held for one lunar year (used if there is no monthly history)
        </label>
        <div className="full">
          <button type="button" className="btn btn-primary" onClick={onRunCalculation} disabled={isCalculating}>
            {isCalculating ? 'Calculating…' : 'Calculate zakat'}
          </button>
        </div>
      </div>
    </section>
  )
}

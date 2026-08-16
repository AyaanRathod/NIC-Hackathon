import { useMemo, useState } from 'react'
import type { IncomeEntry } from '../types/zakat'
import { formatCAD } from '../lib/format'
import {
  GOLD_SPOT_CAD_PER_GRAM,
  SILVER_SPOT_CAD_PER_GRAM,
  METAL_SPOT_AS_OF,
  metalValueCad,
} from '../lib/metals'

interface KaratToolProps {
  onAddEntry: (entry: IncomeEntry) => void
}

export function KaratTool({ onAddEntry }: KaratToolProps) {
  const [metal, setMetal] = useState<'Gold' | 'Silver'>('Gold')
  const [karat, setKarat] = useState('22K')
  const [weight, setWeight] = useState('10')
  const [unit, setUnit] = useState('grams')
  const [price, setPrice] = useState(String(GOLD_SPOT_CAD_PER_GRAM))
  const [worn, setWorn] = useState(false)
  const [gems, setGems] = useState(false)
  const [desc, setDesc] = useState('22K gold item')

  const result = useMemo(() => {
    return metalValueCad({
      metal,
      karat,
      weight: parseFloat(weight) || 0,
      unit,
      pricePerGram: parseFloat(price) || 0,
    })
  }, [metal, karat, weight, unit, price])

  const switchMetal = (next: 'Gold' | 'Silver') => {
    setMetal(next)
    if (next === 'Gold') {
      setKarat('22K')
      setPrice(String(GOLD_SPOT_CAD_PER_GRAM))
      setDesc('22K gold item')
    } else {
      setKarat('999')
      setPrice(String(SILVER_SPOT_CAD_PER_GRAM))
      setDesc('Fine silver item')
    }
  }

  const add = () => {
    onAddEntry({
      id: crypto.randomUUID(),
      description: desc.trim() || `${karat} ${metal}`,
      category: 'Gold & Silver',
      gross_amount: Math.round(result.cad * 100) / 100,
      classification: 'Halal',
      halal_amount: Math.round(result.cad * 100) / 100,
      haram_amount: 0,
      is_mixed_separated: true,
      is_personal_jewelry: worn,
      is_personal_loan: false,
      is_business_receivable_expected: true,
      notes: worn
        ? `Worn jewelry. ${result.pureGrams.toFixed(2)} g pure × ${formatCAD(parseFloat(price) || 0)}/g. Exempt under Maliki rules.`
        : `Investment / bullion. ${result.pureGrams.toFixed(2)} g pure × ${formatCAD(parseFloat(price) || 0)}/g as of ${METAL_SPOT_AS_OF}.`,
      is_income: false,
      direction: 'inflow',
      source_sheet: 'Gold converter',
    })
  }

  return (
    <section className="card panel">
      <h2>Gold and silver by weight</h2>
      <p className="sub">
        Prototype spot: gold {formatCAD(GOLD_SPOT_CAD_PER_GRAM)}/g and silver {formatCAD(SILVER_SPOT_CAD_PER_GRAM)}/g
        as of {METAL_SPOT_AS_OF} (Kitco CAD snapshot). This is not a live feed. Nisab still uses the organizer CAD
        figure. Spreadsheet gold amounts are not replaced.
      </p>
      <div className="form-grid">
        <div>
          <label className="field-label">Metal</label>
          <select className="select" value={metal} onChange={(e) => switchMetal(e.target.value as 'Gold' | 'Silver')}>
            <option>Gold</option>
            <option>Silver</option>
          </select>
        </div>
        <div>
          <label className="field-label">{metal === 'Gold' ? 'Karat' : 'Purity'}</label>
          <select className="select" value={karat} onChange={(e) => setKarat(e.target.value)}>
            {metal === 'Gold' ? (
              <>
                <option>24K</option>
                <option>22K</option>
                <option>21K</option>
                <option>18K</option>
                <option>14K</option>
                <option>10K</option>
              </>
            ) : (
              <>
                <option value="999">999 fine</option>
                <option value="925">925 sterling</option>
              </>
            )}
          </select>
        </div>
        <div>
          <label className="field-label">Weight</label>
          <input className="input mono" type="number" min="0" step="0.01" value={weight} onChange={(e) => setWeight(e.target.value)} />
        </div>
        <div>
          <label className="field-label">Unit</label>
          <select className="select" value={unit} onChange={(e) => setUnit(e.target.value)}>
            <option value="grams">grams</option>
            <option value="tola">tola</option>
            <option value="oz">troy oz</option>
          </select>
        </div>
        <div>
          <label className="field-label">Price per pure gram (CAD)</label>
          <input className="input mono" type="number" min="0" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} />
        </div>
        <div>
          <label className="field-label">Description</label>
          <input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} />
        </div>
        <label className="check full">
          <input type="checkbox" checked={worn} onChange={(e) => setWorn(e.target.checked)} />
          Worn customary jewelry (Maliki exempt)
        </label>
        <label className="check full">
          <input type="checkbox" checked={gems} onChange={(e) => setGems(e.target.checked)} />
          Item has diamonds or gemstones — value gold/silver only; stones are out unless inventory
        </label>
      </div>
      <div className="formula" style={{ marginTop: '1rem' }}>
        <div>
          {result.grossGrams.toFixed(2)} g gross × {(result.fraction * 100).toFixed(1)}% pure ={' '}
          <strong>{result.pureGrams.toFixed(2)} g pure</strong>
        </div>
        <div>
          × {formatCAD(parseFloat(price) || 0)}/g = <strong className="display">{formatCAD(result.cad)}</strong>
        </div>
        <div style={{ marginTop: '0.4rem' }}>
          {worn
            ? 'This amount is exempt if it is jewelry worn for personal use.'
            : 'This amount is zakatable as investment metal.'}
          {gems ? ' Gemstones are not included in this CAD value.' : ''}
        </div>
      </div>
      <button type="button" className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={add}>
        Add to wealth
      </button>
    </section>
  )
}

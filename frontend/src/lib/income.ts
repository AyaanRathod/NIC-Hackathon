import type { Classification, IncomeEntry } from '../types/zakat'

export interface IncomeSummary {
  totalIncome: number
  halalIncome: number
  haramIncome: number
  mixedIncome: number
  mixedHalal: number
  mixedHaram: number
  tentativeIncome: number
  missingIncome: number
  inflowCount: number
  byClass: { label: Classification; amount: number; count: number }[]
}

export function summarizeIncome(rows: IncomeEntry[]): IncomeSummary {
  const inflows = rows.filter((r) => r.is_income !== false && (r.direction || 'inflow') !== 'outflow')
  const bucket: Record<Classification, { amount: number; count: number }> = {
    Halal: { amount: 0, count: 0 },
    Haram: { amount: 0, count: 0 },
    Mixed: { amount: 0, count: 0 },
    Tentative: { amount: 0, count: 0 },
    'Missing Information': { amount: 0, count: 0 },
  }
  let mixedHalal = 0
  let mixedHaram = 0

  for (const row of inflows) {
    const amount = Number(row.gross_amount) || 0
    bucket[row.classification].amount += amount
    bucket[row.classification].count += 1
    if (row.classification === 'Mixed') {
      mixedHalal += Number(row.halal_amount) || 0
      mixedHaram += Number(row.haram_amount) || 0
    }
  }

  const byClass = (Object.keys(bucket) as Classification[]).map((label) => ({
    label,
    amount: bucket[label].amount,
    count: bucket[label].count,
  }))

  return {
    totalIncome: inflows.reduce((sum, r) => sum + (Number(r.gross_amount) || 0), 0),
    halalIncome: bucket.Halal.amount,
    haramIncome: bucket.Haram.amount,
    mixedIncome: bucket.Mixed.amount,
    mixedHalal,
    mixedHaram,
    tentativeIncome: bucket.Tentative.amount,
    missingIncome: bucket['Missing Information'].amount,
    inflowCount: inflows.length,
    byClass,
  }
}

export const GOLD_SPOT_CAD_PER_GRAM = 195.21
export const SILVER_SPOT_CAD_PER_GRAM = 3.48
export const METAL_SPOT_AS_OF = '2026-08-16'

const GOLD_KARATS: Record<string, number> = {
  '24K': 24 / 24,
  '22K': 22 / 24,
  '21K': 21 / 24,
  '18K': 18 / 24,
  '14K': 14 / 24,
  '10K': 10 / 24,
}

const SILVER_PURITY: Record<string, number> = {
  '999': 0.999,
  '925': 0.925,
}

export function toGrams(weight: number, unit: string): number {
  if (unit === 'tola') return weight * 11.6638
  if (unit === 'oz') return weight * 31.1035
  return weight
}

export function purityFraction(metal: 'Gold' | 'Silver', karat: string): number {
  if (metal === 'Gold') return GOLD_KARATS[karat] ?? 1
  return SILVER_PURITY[karat] ?? 0.999
}

export function metalValueCad(opts: {
  metal: 'Gold' | 'Silver'
  karat: string
  weight: number
  unit: string
  pricePerGram: number
}): { grossGrams: number; pureGrams: number; cad: number; fraction: number } {
  const grossGrams = toGrams(opts.weight, opts.unit)
  const fraction = purityFraction(opts.metal, opts.karat)
  const pureGrams = grossGrams * fraction
  return {
    grossGrams,
    pureGrams,
    fraction,
    cad: pureGrams * opts.pricePerGram,
  }
}

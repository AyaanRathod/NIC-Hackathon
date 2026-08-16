export function formatCAD(val: number, digits = 2): string {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: digits,
  }).format(val || 0)
}

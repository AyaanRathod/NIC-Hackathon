import type {
  IncomeEntry,
  DebtEntry,
  WealthHistoryMonth,
  ZakatCalculationResponse,
  UploadResponse,
  Classification,
  Category,
} from '../types/zakat'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function readError(response: Response, fallback: string): Promise<string> {
  const err = await response.json().catch(() => ({ detail: fallback }))
  return err.detail || fallback
}

export async function calculateZakat(payload: {
  entries: IncomeEntry[]
  debts: DebtEntry[]
  wealth_history: WealthHistoryMonth[]
  nisab_cad: number
  hawl_maintained: boolean
  person_name?: string
}): Promise<ZakatCalculationResponse> {
  const response = await fetch(`${API_BASE}/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, madhhab: 'Maliki' }),
  })
  if (!response.ok) throw new Error(await readError(response, 'Calculation failed'))
  return response.json()
}

export async function classifyTransaction(payload: {
  description: string
  category?: Category
  amount?: number
  notes?: string
}): Promise<{ classification: Classification; explanation: string; matched_keyword?: string }> {
  const response = await fetch(`${API_BASE}/classify-transaction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await readError(response, 'Classification failed'))
  return response.json()
}

export async function uploadFinancialFile(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE}/upload-file`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) throw new Error(await readError(response, 'File upload failed'))
  return response.json()
}

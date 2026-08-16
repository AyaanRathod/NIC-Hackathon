export type Classification =
  | 'Halal'
  | 'Haram'
  | 'Mixed'
  | 'Tentative'
  | 'Missing Information'

export type Category =
  | 'Cash & Bank Balances'
  | 'Halal Investments'
  | 'Business Inventory'
  | 'Gold & Silver'
  | 'Receivables / Invoices'
  | 'Cryptocurrency'
  | 'Other'

export type Madhhab = 'Maliki'

export interface IncomeEntry {
  id: string
  description: string
  category: Category
  gross_amount: number
  classification: Classification
  halal_amount: number
  haram_amount: number
  is_mixed_separated: boolean
  is_personal_jewelry: boolean
  is_personal_loan: boolean
  is_business_receivable_expected: boolean
  notes: string
  date?: string
  keyword?: string
  direction?: string
  is_income?: boolean
  source_sheet?: string
}

export interface DebtEntry {
  id?: string
  description: string
  outstanding_balance: number
  amount_due_within_12_months: number
  is_due_within_12_months: boolean
  creditor?: string
  overdue_amount?: number
  interest_bearing?: boolean
  notes?: string
}

export interface WealthHistoryMonth {
  month_end: string
  cash_and_bank_cad: number
  business_cash_cad: number
  business_inventory_halal_cad: number
  business_inventory_prohibited_cad: number
  gold_silver_savings_cad: number
  customary_gold_jewelry_cad: number
  stock_shares_cad: number
  other_halal_investments_cad: number
  crypto_cad: number
  business_receivables_likely_cad: number
  personal_loans_receivable_cad: number
  receivables_doubtful_cad: number
  total_outstanding_debts_cad: number
  debts_due_within_12_months_cad: number
  event_note?: string
  maliki_zakatable_assets?: number
  maliki_net_wealth?: number
  is_above_nisab?: boolean
}

export interface PurificationItem {
  description: string
  amount: number
  reason: string
}

export interface ZakatCalculationResponse {
  madhhab: string
  person_name: string
  total_gross_wealth: number
  total_zakatable_assets: number
  total_exempt_wealth: number
  total_haram_disposed: number
  total_tentative_review: number
  qualifying_debts_deducted: number
  long_term_debts_excluded: number
  net_zakatable_wealth: number
  nisab_threshold_cad: number
  is_hawl_maintained: boolean
  hawl_notes: string[]
  is_eligible_for_zakat: boolean
  zakat_due_cad: number
  warnings: string[]
  audit_breakdown: string[]
  purification_items: PurificationItem[]
}

export interface SheetInventory {
  sheet: string
  rows_in_file: number
  rows_kept: number
}

export interface UploadResponse {
  filename: string
  person_name?: string
  selected_nisab_cad?: number
  entries: IncomeEntry[]
  transactions: IncomeEntry[]
  debts: DebtEntry[]
  wealth_history: WealthHistoryMonth[]
  user_profile: Record<string, unknown>
  warnings: string[]
  rows_processed: number
  income_inflow_count: number
  income_outflow_count: number
  sheet_inventory: SheetInventory[]
  sheets_in_file: string[]
}

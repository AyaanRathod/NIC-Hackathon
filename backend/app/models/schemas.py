from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.enums import Classification, Category, Madhhab, RepaymentLikelihood

class IncomeEntry(BaseModel):
    id: Optional[str] = None
    description: str
    category: Category = Category.CASH_BANK
    gross_amount: float = Field(default=0.0, ge=0.0)
    classification: Classification = Classification.HALAL
    halal_amount: float = 0.0
    haram_amount: float = 0.0
    is_mixed_separated: bool = True
    is_personal_jewelry: bool = False
    is_personal_loan: bool = False
    is_business_receivable_expected: bool = True
    notes: Optional[str] = ""
    date: Optional[str] = None
    keyword: Optional[str] = None
    direction: Optional[str] = "inflow"
    is_income: bool = True
    source_sheet: Optional[str] = None

class DebtEntry(BaseModel):
    id: Optional[str] = None
    description: str
    outstanding_balance: float = Field(default=0.0, ge=0.0)
    amount_due_within_12_months: float = Field(default=0.0, ge=0.0)
    is_due_within_12_months: bool = True
    creditor: Optional[str] = None
    overdue_amount: float = 0.0
    interest_bearing: bool = False
    notes: Optional[str] = ""

class WealthHistoryMonth(BaseModel):
    month_end: str
    cash_and_bank_cad: float = 0.0
    business_cash_cad: float = 0.0
    business_inventory_halal_cad: float = 0.0
    business_inventory_prohibited_cad: float = 0.0
    gold_silver_savings_cad: float = 0.0
    customary_gold_jewelry_cad: float = 0.0
    stock_shares_cad: float = 0.0
    other_halal_investments_cad: float = 0.0
    crypto_cad: float = 0.0
    business_receivables_likely_cad: float = 0.0
    personal_loans_receivable_cad: float = 0.0
    receivables_doubtful_cad: float = 0.0
    total_outstanding_debts_cad: float = 0.0
    debts_due_within_12_months_cad: float = 0.0
    event_note: Optional[str] = None
    maliki_zakatable_assets: Optional[float] = None
    maliki_net_wealth: Optional[float] = None
    is_above_nisab: Optional[bool] = None

class ClassificationRequest(BaseModel):
    description: str
    category: Optional[Category] = Category.OTHER
    amount: Optional[float] = None
    notes: Optional[str] = ""

class ClassificationResponse(BaseModel):
    classification: Classification
    explanation: str
    matched_keyword: Optional[str] = None

class ZakatCalculationRequest(BaseModel):
    entries: List[IncomeEntry] = []
    debts: List[DebtEntry] = []
    wealth_history: List[WealthHistoryMonth] = []
    nisab_cad: float = 9250.00
    hawl_maintained: bool = True
    person_name: Optional[str] = "Participant"
    madhhab: Madhhab = Madhhab.MALIKI

class PurificationItem(BaseModel):
    description: str
    amount: float
    reason: str

class ZakatCalculationResponse(BaseModel):
    madhhab: str = "Maliki"
    person_name: str = "Participant"
    total_gross_wealth: float
    total_zakatable_assets: float
    total_exempt_wealth: float
    total_haram_disposed: float
    total_tentative_review: float
    qualifying_debts_deducted: float
    long_term_debts_excluded: float
    net_zakatable_wealth: float
    nisab_threshold_cad: float
    is_hawl_maintained: bool
    hawl_notes: List[str]
    is_eligible_for_zakat: bool
    zakat_due_cad: float
    warnings: List[str]
    audit_breakdown: List[str]
    purification_items: List[PurificationItem]

class MetalValuationRequest(BaseModel):
    metal_type: str = "Gold"  # "Gold" or "Silver"
    karat: str = "24K"  # "24K", "22K", "21K", "18K", "14K", "10K", "999", "925"
    weight: float = Field(default=0.0, ge=0.0)
    unit: str = "grams"  # "grams", "tola", "oz"
    manual_price_per_gram_cad: float = Field(default=108.82, ge=0.0)
    is_customary_jewelry: bool = False
    description: Optional[str] = ""

class MetalValuationResponse(BaseModel):
    metal_type: str
    karat: str
    purity_fraction: float
    gross_weight_grams: float
    pure_weight_grams: float
    unit: str
    price_per_gram_cad: float
    total_cad_value: float
    nisab_threshold_grams: float
    is_above_metal_nisab: bool
    is_maliki_exempt: bool
    fiqh_ruling_summary: str

class SheetInventory(BaseModel):
    sheet: str
    rows_in_file: int
    rows_kept: int


class UploadResponse(BaseModel):
    filename: str
    person_name: Optional[str] = None
    selected_nisab_cad: Optional[float] = None
    entries: List[IncomeEntry]
    transactions: List[IncomeEntry] = []
    debts: List[DebtEntry]
    wealth_history: List[WealthHistoryMonth]
    user_profile: Dict[str, Any]
    warnings: List[str]
    rows_processed: int
    income_inflow_count: int = 0
    income_outflow_count: int = 0
    sheet_inventory: List[SheetInventory] = []
    sheets_in_file: List[str] = []

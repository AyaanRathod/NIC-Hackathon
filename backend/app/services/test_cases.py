from typing import List, Dict, Any
from pathlib import Path
from app.models.schemas import ZakatCalculationRequest, IncomeEntry, DebtEntry, WealthHistoryMonth
from app.models.enums import Classification, Category, Madhhab
from app.services.excel_parser import parse_workbook

# Base workspace path for finding files if available
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def load_excel_test_case(filename: str, fallback_title: str) -> ZakatCalculationRequest:
    file_path = BASE_DIR / filename
    if file_path.exists():
        with open(file_path, "rb") as f:
            parsed = parse_workbook(f.read(), filename)
            return ZakatCalculationRequest(
                person_name=parsed.person_name,
                entries=parsed.entries,
                debts=parsed.debts,
                wealth_history=parsed.wealth_history,
                nisab_cad=parsed.selected_nisab_cad or 9250.0,
                hawl_maintained=True,
                madhhab=Madhhab.MALIKI,
            )
    return get_fallback_test_case(fallback_title)

def get_fallback_test_case(title: str) -> ZakatCalculationRequest:
    if "Faris" in title:
        return ZakatCalculationRequest(
            person_name="Faris Mahmood (Practice B)",
            nisab_cad=9250.0,
            hawl_maintained=True,
            madhhab=Madhhab.MALIKI,
            entries=[
                IncomeEntry(id="FM-A01", description="Cash held at home", category=Category.CASH_BANK, gross_amount=850, classification=Classification.HALAL, notes="Cash balance"),
                IncomeEntry(id="FM-A02", description="Personal chequing balance", category=Category.CASH_BANK, gross_amount=10000, classification=Classification.HALAL, notes="Liquid bank funds"),
                IncomeEntry(id="FM-A03", description="Personal savings balance", category=Category.CASH_BANK, gross_amount=7900, classification=Classification.HALAL, notes="Savings funds"),
                IncomeEntry(id="FM-A04", description="Business chequing balance", category=Category.CASH_BANK, gross_amount=5300, classification=Classification.HALAL, notes="Commercial liquid balance"),
                IncomeEntry(id="FM-A05", description="Permissible inventory intended for resale", category=Category.BUSINESS_INVENTORY, gross_amount=5300, classification=Classification.HALAL, notes="Halal business stock"),
                IncomeEntry(id="FM-A06", description="Prohibited-product inventory held for resale", category=Category.BUSINESS_INVENTORY, gross_amount=510, classification=Classification.HARAM, notes="Prohibited goods; excluded from zakat, must be disposed"),
                IncomeEntry(id="FM-A07", description="Customary gold jewelry regularly worn", category=Category.GOLD_SILVER, gross_amount=4500, classification=Classification.HALAL, is_personal_jewelry=True, notes="Customary worn jewelry; exempt under Maliki rules"),
                IncomeEntry(id="FM-A08", description="Gold coins held as savings/investment", category=Category.GOLD_SILVER, gross_amount=2600, classification=Classification.HALAL, notes="Investment gold; zakatable"),
                IncomeEntry(id="FM-A09", description="Silver bars held as savings", category=Category.GOLD_SILVER, gross_amount=1140, classification=Classification.HALAL, notes="Investment silver; zakatable"),
                IncomeEntry(id="FM-A10", description="Screened listed company shares", category=Category.INVESTMENTS, gross_amount=6400, classification=Classification.HALAL, notes="Screened halal equities"),
                IncomeEntry(id="FM-A11", description="Non-stock screened investment holding", category=Category.INVESTMENTS, gross_amount=2800, classification=Classification.HALAL, notes="Halal investment holding"),
                IncomeEntry(id="FM-A12", description="Crypto wallet balance (unscreened)", category=Category.CRYPTO, gross_amount=2500, classification=Classification.TENTATIVE, notes="Missing cost basis & screening; Scholar Review Required"),
                IncomeEntry(id="FM-A13", description="Outstanding client invoice", category=Category.RECEIVABLES, gross_amount=2000, classification=Classification.HALAL, is_business_receivable_expected=True, notes="Business receivable; repayment likely"),
                IncomeEntry(id="FM-A14", description="Money lent personally to a friend", category=Category.RECEIVABLES, gross_amount=2900, classification=Classification.HALAL, is_personal_loan=True, notes="Unpaid personal loan; exempt until received under Maliki"),
                IncomeEntry(id="FM-A15", description="Old amount owed by former customer", category=Category.RECEIVABLES, gross_amount=1050, classification=Classification.TENTATIVE, is_business_receivable_expected=False, notes="Doubtful receivable; Scholar Review Required"),
                IncomeEntry(id="FM-A16", description="Known mixed-income amount still held (retained)", category=Category.CASH_BANK, gross_amount=1500, classification=Classification.MIXED, is_mixed_separated=False, notes="Retained mixed amount; zakatable until purified"),
                IncomeEntry(id="FM-A17", description="Haram income already separated from halal wealth", category=Category.OTHER, gross_amount=700, classification=Classification.HARAM, notes="Separated impermissible funds; for disposal"),
                IncomeEntry(id="FM-A18", description="Money personally lent; repayment doubtful", category=Category.RECEIVABLES, gross_amount=900, classification=Classification.HALAL, is_personal_loan=True, notes="Doubtful personal loan; exempt under Maliki"),
            ],
            debts=[
                DebtEntry(id="FM-D01", description="Credit card balance (Visa)", outstanding_balance=2900, amount_due_within_12_months=2900, is_due_within_12_months=True),
                DebtEntry(id="FM-D02", description="Business supplier invoice (Wholesale)", outstanding_balance=2000, amount_due_within_12_months=2000, is_due_within_12_months=True),
                DebtEntry(id="FM-D03", description="Student loan (Student Centre)", outstanding_balance=16500, amount_due_within_12_months=2100, is_due_within_12_months=True),
                DebtEntry(id="FM-D04", description="Mortgage (Mortgage Lender)", outstanding_balance=180000, amount_due_within_12_months=14200, is_due_within_12_months=True),
                DebtEntry(id="FM-D05", description="Personal loan (Family Lender)", outstanding_balance=5000, amount_due_within_12_months=1600, is_due_within_12_months=True),
            ]
        )
    elif "Nadia" in title:
        return ZakatCalculationRequest(
            person_name="Nadia Rahman (Practice A)",
            nisab_cad=9000.0,
            hawl_maintained=True,
            madhhab=Madhhab.MALIKI,
            entries=[
                IncomeEntry(id="NR-A01", description="Cash held at home", category=Category.CASH_BANK, gross_amount=750, classification=Classification.HALAL, notes="Cash balance"),
                IncomeEntry(id="NR-A02", description="Personal chequing balance", category=Category.CASH_BANK, gross_amount=9100, classification=Classification.HALAL, notes="Liquid bank funds"),
                IncomeEntry(id="NR-A03", description="Personal savings balance", category=Category.CASH_BANK, gross_amount=7050, classification=Classification.HALAL, notes="Savings funds"),
                IncomeEntry(id="NR-A04", description="Business chequing balance", category=Category.CASH_BANK, gross_amount=4600, classification=Classification.HALAL, notes="Commercial liquid balance"),
                IncomeEntry(id="NR-A05", description="Permissible inventory intended for resale", category=Category.BUSINESS_INVENTORY, gross_amount=4800, classification=Classification.HALAL, notes="Halal business stock"),
                IncomeEntry(id="NR-A06", description="Prohibited-product inventory held for resale", category=Category.BUSINESS_INVENTORY, gross_amount=430, classification=Classification.HARAM, notes="Prohibited stock; excluded and marked for purification"),
                IncomeEntry(id="NR-A07", description="Customary gold jewelry regularly worn", category=Category.GOLD_SILVER, gross_amount=4200, classification=Classification.HALAL, is_personal_jewelry=True, notes="Customary worn jewelry; exempt in Maliki fiqh"),
                IncomeEntry(id="NR-A08", description="Gold coins held as savings/investment", category=Category.GOLD_SILVER, gross_amount=2350, classification=Classification.HALAL, notes="Investment gold; zakatable"),
                IncomeEntry(id="NR-A09", description="Silver bars held as savings", category=Category.GOLD_SILVER, gross_amount=1020, classification=Classification.HALAL, notes="Investment silver; zakatable"),
                IncomeEntry(id="NR-A10", description="Screened listed company shares", category=Category.INVESTMENTS, gross_amount=5800, classification=Classification.HALAL, notes="Screened halal equities"),
                IncomeEntry(id="NR-A11", description="Non-stock screened investment holding", category=Category.INVESTMENTS, gross_amount=2500, classification=Classification.HALAL, notes="Halal investment holding"),
                IncomeEntry(id="NR-A12", description="Crypto wallet balance (unscreened)", category=Category.CRYPTO, gross_amount=2150, classification=Classification.TENTATIVE, notes="Token screening missing; Scholar Review Required"),
                IncomeEntry(id="NR-A13", description="Outstanding client invoice", category=Category.RECEIVABLES, gross_amount=1800, classification=Classification.HALAL, is_business_receivable_expected=True, notes="Business receivable; repayment likely"),
                IncomeEntry(id="NR-A14", description="Money lent personally to a friend", category=Category.RECEIVABLES, gross_amount=2650, classification=Classification.HALAL, is_personal_loan=True, notes="Unpaid personal loan; exempt under Maliki until receipt"),
                IncomeEntry(id="NR-A15", description="Old amount owed by former customer", category=Category.RECEIVABLES, gross_amount=950, classification=Classification.TENTATIVE, is_business_receivable_expected=False, notes="Doubtful receivable; Scholar Review Required"),
                IncomeEntry(id="NR-A16", description="Known mixed-income amount still held (retained)", category=Category.CASH_BANK, gross_amount=1500, classification=Classification.MIXED, is_mixed_separated=False, notes="Retained mixed amount; zakatable until purified"),
                IncomeEntry(id="NR-A17", description="Haram income already separated from halal wealth", category=Category.OTHER, gross_amount=700, classification=Classification.HARAM, notes="Separated impermissible funds; for disposal"),
                IncomeEntry(id="NR-A18", description="Money personally lent; repayment doubtful", category=Category.RECEIVABLES, gross_amount=900, classification=Classification.HALAL, is_personal_loan=True, notes="Doubtful personal loan; exempt under Maliki"),
            ],
            debts=[
                DebtEntry(id="NR-D01", description="Credit card balance (Visa)", outstanding_balance=2600, amount_due_within_12_months=2600, is_due_within_12_months=True),
                DebtEntry(id="NR-D02", description="Business supplier invoice (Wholesale)", outstanding_balance=1750, amount_due_within_12_months=1750, is_due_within_12_months=True),
                DebtEntry(id="NR-D03", description="Student loan (Student Centre)", outstanding_balance=15500, amount_due_within_12_months=1950, is_due_within_12_months=True),
                DebtEntry(id="NR-D04", description="Mortgage (Mortgage Lender)", outstanding_balance=174000, amount_due_within_12_months=13700, is_due_within_12_months=True),
                DebtEntry(id="NR-D05", description="Personal loan (Family Lender)", outstanding_balance=4600, amount_due_within_12_months=1400, is_due_within_12_months=True),
            ]
        )
    else:
        # Case C: Mixed-Income Entrepreneur
        return ZakatCalculationRequest(
            person_name="Zayd Al-Ansari (Test Case C: E-Commerce Trader)",
            nisab_cad=9250.0,
            hawl_maintained=True,
            madhhab=Madhhab.MALIKI,
            entries=[
                IncomeEntry(id="TC3-01", description="Business chequing operational account", category=Category.CASH_BANK, gross_amount=14500, classification=Classification.HALAL, notes="Commercial liquid funds"),
                IncomeEntry(id="TC3-02", description="Personal savings reserve", category=Category.CASH_BANK, gross_amount=8200, classification=Classification.HALAL, notes="Personal savings"),
                IncomeEntry(id="TC3-03", description="Halal physical resale inventory", category=Category.BUSINESS_INVENTORY, gross_amount=12000, classification=Classification.HALAL, notes="Resale goods"),
                IncomeEntry(id="TC3-04", description="Mixed advertising revenue (Purified: 85% Halal / 15% Haram)", category=Category.INVESTMENTS, gross_amount=4000, classification=Classification.MIXED, halal_amount=3400, haram_amount=600, is_mixed_separated=True, notes="Mixed payout: $600 haram separated for charity, $3,400 halal added to zakat wealth"),
                IncomeEntry(id="TC3-05", description="Mixed marketplace bundle (Retained without separation)", category=Category.CASH_BANK, gross_amount=2000, classification=Classification.MIXED, halal_amount=0, haram_amount=0, is_mixed_separated=False, notes="Retained mixed funds; full $2,000 remains zakatable under Maliki rules until separated"),
                IncomeEntry(id="TC3-06", description="Direct bank interest received", category=Category.OTHER, gross_amount=450, classification=Classification.HARAM, notes="Interest / Riba; 100% excluded and must be disposed"),
                IncomeEntry(id="TC3-07", description="Worn 22k gold bridal bangles (Regular personal use)", category=Category.GOLD_SILVER, gross_amount=6000, classification=Classification.HALAL, is_personal_jewelry=True, notes="Customary personal jewelry; EXEMPT under Maliki Madhhab"),
                IncomeEntry(id="TC3-08", description="Pure 100g silver bullion investment bar", category=Category.GOLD_SILVER, gross_amount=1800, classification=Classification.HALAL, notes="Investment bullion; zakatable"),
                IncomeEntry(id="TC3-09", description="Unscreened DeFi liquidity pool yield", category=Category.CRYPTO, gross_amount=3200, classification=Classification.TENTATIVE, notes="Unscreened yield tokens; Scholar Review Required"),
                IncomeEntry(id="TC3-10", description="Verified business invoice (Repayment expected next week)", category=Category.RECEIVABLES, gross_amount=3500, classification=Classification.HALAL, is_business_receivable_expected=True, notes="Expected trade invoice; included in zakatable assets"),
                IncomeEntry(id="TC3-11", description="Personal loan to brother (Unpaid)", category=Category.RECEIVABLES, gross_amount=4000, classification=Classification.HALAL, is_personal_loan=True, notes="Unpaid personal loan; exempt under Maliki until repaid"),
            ],
            debts=[
                DebtEntry(id="TC3-D01", description="Supplier commercial credit line", outstanding_balance=5000, amount_due_within_12_months=5000, is_due_within_12_months=True),
                DebtEntry(id="TC3-D02", description="Commercial vehicle lease (Due within 12 months)", outstanding_balance=18000, amount_due_within_12_months=4200, is_due_within_12_months=True),
                DebtEntry(id="TC3-D03", description="Long-term warehouse mortgage", outstanding_balance=240000, amount_due_within_12_months=16800, is_due_within_12_months=True),
            ]
        )

def get_all_test_cases() -> Dict[str, ZakatCalculationRequest]:
    return {
        "case_1": load_excel_test_case("Faris_Mahmood_Participant_Practice_B_.xlsx", "Faris Mahmood (Practice B)"),
        "case_2": load_excel_test_case("Nadia_Rahman_Participant_Practice_A_.xlsx", "Nadia Rahman (Practice A)"),
        "case_3": get_fallback_test_case("Test Case C: E-Commerce Trader"),
    }

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.enums import Classification
from app.services.classifier import classify_entry
from app.services.zakat_calculator import calculate_maliki_zakat
from app.services.test_cases import get_all_test_cases
from app.services.excel_parser import parse_assets_sheet, parse_workbook

def test_classifier():
    print("Testing Classifier...")
    # Test Haram
    cls, exp, _ = classify_entry(description="Bank interest payout", keyword="interest_income")
    assert cls == Classification.HARAM, f"Expected HARAM, got {cls}"

    # Test Mixed Disposed
    cls, exp, _ = classify_entry(description="Mixed income payout", keyword="mixed_income_disposed")
    assert cls == Classification.MIXED, f"Expected MIXED, got {cls}"

    # Test Tentative
    cls, exp, _ = classify_entry(description="Crypto staking yield unscreened", keyword="tentative_crypto_portfolio_unscreened")
    assert cls == Classification.TENTATIVE, f"Expected TENTATIVE, got {cls}"

    # Test Missing info
    cls, exp, _ = classify_entry(description="Marketplace sale missing cost basis", keyword="crypto_sale_missing_cost_basis")
    assert cls == Classification.MISSING_INFO, f"Expected MISSING_INFO, got {cls}"

    # Test Halal
    cls, exp, _ = classify_entry(description="Monthly salary", keyword="salary_income")
    assert cls == Classification.HALAL, f"Expected HALAL, got {cls}"

    # Punctuation and case in keywords
    cls, _, matched = classify_entry(description="Bank interest", keyword="Interest-Income")
    assert cls == Classification.HARAM
    assert matched == "interest_income"

    # A missing-info note must not override a known keyword
    cls, _, matched = classify_entry(
        description="Unscreened crypto",
        keyword="tentative_crypto_portfolio_unscreened",
        missing_info_note="Need token list",
    )
    assert cls == Classification.TENTATIVE
    assert matched == "tentative_crypto_portfolio_unscreened"

    # Explicit classification column when no keyword exists
    cls, _, _ = classify_entry(description="Unknown payout", explicit_classification="Haram")
    assert cls == Classification.HARAM
    print("Classifier tests PASSED!")

def test_faris_calculation():
    print("Testing Faris Mahmood Test Case...")
    cases = get_all_test_cases()
    faris = cases["case_1"]
    res = calculate_maliki_zakat(faris)
    
    print(f"Faris - Zakatable: {res.total_zakatable_assets}, Debts: {res.qualifying_debts_deducted}, Net: {res.net_zakatable_wealth}, Zakat: {res.zakat_due_cad}")
    assert res.total_zakatable_assets == 45790.0, f"Expected 45790.0, got {res.total_zakatable_assets}"
    assert res.qualifying_debts_deducted == 22800.0, f"Expected 22800.0, got {res.qualifying_debts_deducted}"
    assert res.net_zakatable_wealth == 22990.0, f"Expected 22990.0, got {res.net_zakatable_wealth}"
    assert res.zakat_due_cad == 574.75, f"Expected 574.75, got {res.zakat_due_cad}"
    assert res.total_haram_disposed == 1210.0, f"Expected 1210.0, got {res.total_haram_disposed}"
    assert res.is_eligible_for_zakat == True
    print("Faris Mahmood calculation PASSED!")

def test_nadia_calculation():
    print("Testing Nadia Rahman Test Case...")
    cases = get_all_test_cases()
    nadia = cases["case_2"]
    res = calculate_maliki_zakat(nadia)

    print(f"Nadia - Zakatable: {res.total_zakatable_assets}, Debts: {res.qualifying_debts_deducted}, Net: {res.net_zakatable_wealth}, Zakat: {res.zakat_due_cad}")
    assert res.total_zakatable_assets == 41270.0, f"Expected 41270.0, got {res.total_zakatable_assets}"
    assert res.qualifying_debts_deducted == 21400.0, f"Expected 21400.0, got {res.qualifying_debts_deducted}"
    assert res.net_zakatable_wealth == 19870.0, f"Expected 19870.0, got {res.net_zakatable_wealth}"
    assert res.zakat_due_cad == 496.75, f"Expected 496.75, got {res.zakat_due_cad}"
    assert res.total_haram_disposed == 1130.0, f"Expected 1130.0, got {res.total_haram_disposed}"
    assert res.is_eligible_for_zakat == True
    print("Nadia Rahman calculation PASSED!")

def test_case_c_calculation():
    print("Testing Custom Case C...")
    cases = get_all_test_cases()
    case_c = cases["case_3"]
    res = calculate_maliki_zakat(case_c)
    print(f"Case C - Zakatable: {res.total_zakatable_assets}, Debts: {res.qualifying_debts_deducted}, Net: {res.net_zakatable_wealth}, Zakat: {res.zakat_due_cad}")
    assert res.is_eligible_for_zakat == True
    print("Custom Case C calculation PASSED!")

def test_similar_style_workbook():
    """Organizers may rename sheets and headers. The parser must still map them."""
    import io
    import pandas as pd

    assets, _ = parse_assets_sheet(pd.DataFrame({
        "Asset ID": ["A1"],
        "Description": ["Chequing"],
        "Keyword": ["Personal Chequing Account"],
        "Amount (CAD)": [20000],
    }))
    assert len(assets) == 1
    assert assets[0].gross_amount == 20000
    assert assets[0].classification == Classification.HALAL

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame({
            "Field": ["Person Name", "Selected Nisab (CAD)"],
            "Value": ["Test User", 9000],
        }).to_excel(writer, sheet_name="Profile", index=False)
        pd.DataFrame({
            "Asset ID": ["A1"],
            "Description": ["Chequing"],
            "Keyword": ["personal_chequing_account"],
            "Amount (CAD)": [20000],
        }).to_excel(writer, sheet_name="Year_End_Holdings", index=False)
        pd.DataFrame({
            "Debt ID": ["D1"],
            "Description": ["Card"],
            "Outstanding Balance": [1000],
            "Amount Due Within 12 Months": [1000],
        }).to_excel(writer, sheet_name="Liabilities", index=False)
        pd.DataFrame({
            "Transaction ID": ["T1"],
            "Date": ["2025-01-01"],
            "Description": ["Salary"],
            "Keyword": ["Salary Income"],
            "Amount (CAD)": [3000],
            "Direction": ["inflow"],
        }).to_excel(writer, sheet_name="Ledger", index=False)
        pd.DataFrame({
            "Month End": [f"2025-{m:02d}-28" for m in range(1, 13)],
            "Cash and Bank CAD": [20000] * 12,
            "Debts Due Within 12 Months CAD": [1000] * 12,
        }).to_excel(writer, sheet_name="Monthly History", index=False)

    parsed = parse_workbook(buf.getvalue(), "similar.xlsx")
    assert parsed.person_name == "Test User"
    assert parsed.selected_nisab_cad == 9000
    assert len(parsed.entries) == 1
    assert parsed.entries[0].gross_amount == 20000
    assert len(parsed.transactions) == 1
    assert parsed.transactions[0].classification == Classification.HALAL
    assert parsed.transactions[0].keyword == "salary_income"
    assert len(parsed.debts) == 1
    assert parsed.debts[0].amount_due_within_12_months == 1000
    assert len(parsed.wealth_history) == 12
    print("Similar-style workbook parse PASSED!")


if __name__ == "__main__":
    test_classifier()
    test_faris_calculation()
    test_nadia_calculation()
    test_case_c_calculation()
    test_similar_style_workbook()
    print("\nALL BACKEND UNIT TESTS PASSED SUCCESSFULLY!")

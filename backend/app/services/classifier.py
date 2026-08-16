import re
from typing import Tuple, Optional
from app.models.enums import Classification, Category

# Keyword lookup for official participant workbooks + common CSV labels.
# Keyword match always wins over free-text heuristics.
KEYWORD_MAPPING = {
    # --- Halal income ---
    "salary_income": (Classification.HALAL, "Ordinary employment salary from permissible work. Included in income tracking; remaining cash is zakatable."),
    "freelance_income": (Classification.HALAL, "Permissible freelance or contracting income."),
    "rental_income": (Classification.HALAL, "Rental income from permissible property."),
    "tip_income": (Classification.HALAL, "Tips received for permissible work."),
    "content_revenue_income": (Classification.HALAL, "Permissible digital content or advertising revenue."),
    "commission_income": (Classification.HALAL, "Permissible sales or service commission."),
    "gift_income": (Classification.HALAL, "Permissible gift received."),
    "scholarship_income": (Classification.HALAL, "Permissible scholarship or educational stipend."),
    "business_sale_income": (Classification.HALAL, "Revenue from permissible product sales."),
    "gross_business_sale": (Classification.HALAL, "Gross sale before processor settlement. Treated as business income, not a second copy of the later payout."),
    "stock_dividend_income": (Classification.HALAL, "Dividend from screened Shariah-compliant shares."),
    "stock_sale_proceeds": (Classification.HALAL, "Proceeds from selling screened shares. Counted as cash once received."),
    "crypto_sale_with_cost_basis": (Classification.HALAL, "Crypto sale with a recorded cost basis. Proceeds are cash once received."),
    "tax_refund": (Classification.HALAL, "Tax refund — return of the user's own funds, not new earnings."),
    "insurance_proceeds": (Classification.HALAL, "Insurance reimbursement or indemnity payout."),
    "employee_reimbursement": (Classification.HALAL, "Reimbursement of out-of-pocket expenses. Not new income."),
    "crowdfunding_payment": (Classification.HALAL, "Crowdfunding inflow. Included unless a prohibited use is identified."),
    "security_deposit_return": (Classification.HALAL, "Return of a deposit the user already owned."),
    "business_overpayment_return": (Classification.HALAL, "Return of an overpayment. Not new earnings."),

    # --- Not income (still classified so the ledger is complete) ---
    "loan_received": (Classification.HALAL, "Borrowed principal received. This is a liability, not income. Cash goes up and so does debt."),
    "refundable_client_deposit": (Classification.HALAL, "Client security deposit held temporarily. A liability until earned."),
    "internal_transfer": (Classification.HALAL, "Transfer between the user's own accounts. Not income and not a new asset."),
    "processor_payout": (Classification.HALAL, "Payment-processor settlement of an earlier sale. Not counted again as new income."),
    "processor_fee": (Classification.HALAL, "Payment-processor fee. An expense, not income."),
    "customer_refund": (Classification.HALAL, "Refund paid to a customer. Reduces prior sales; not income."),
    "chargeback": (Classification.HALAL, "Chargeback reversing a prior sale. Not income."),
    "loan_repayment": (Classification.HALAL, "Repayment of money the user borrowed. Reduces debt; not income."),

    # --- Ordinary expenses (outflows) ---
    "business_supplies": (Classification.HALAL, "Business supplies expense. Not income."),
    "business_advertising": (Classification.HALAL, "Advertising expense. Not income."),
    "transportation": (Classification.HALAL, "Transportation expense. Not income."),
    "electricity_bill": (Classification.HALAL, "Utility bill. Not income."),
    "phone_bill": (Classification.HALAL, "Phone bill. Not income."),
    "restaurant_meal": (Classification.HALAL, "Meal expense. Not income."),
    "software_subscription": (Classification.HALAL, "Software subscription. Not income."),
    "personal_spending": (Classification.HALAL, "Personal spending. Not income."),
    "groceries": (Classification.HALAL, "Grocery expense. Not income."),
    "inventory_purchase": (Classification.HALAL, "Inventory purchase. Converts cash into business stock."),
    "crypto_purchase": (Classification.HALAL, "Crypto purchase. Converts cash into a crypto holding."),
    "equipment_purchase": (Classification.HALAL, "Equipment purchase. Not zakatable inventory unless held for resale."),

    # --- Haram inflows ---
    "interest_income": (Classification.HARAM, "Bank or loan interest (riba). Excluded from zakat and must be disposed of. Removing it is not paying zakat."),
    "alcohol_sales_income": (Classification.HARAM, "Revenue from alcohol sales. Excluded from zakatable wealth; must be purified."),
    "vape_sales_income": (Classification.HARAM, "Revenue from vape or tobacco products. Excluded from zakatable wealth."),
    "gambling_income": (Classification.HARAM, "Gambling winnings (maisir). Excluded and must be given away."),
    "lottery_winnings": (Classification.HARAM, "Lottery winnings (maisir). Excluded from zakat; must be disposed of."),
    "prohibited_product_commission": (Classification.HARAM, "Commission tied to prohibited products. Entire amount is impermissible."),
    "business_inventory_prohibited": (Classification.HARAM, "Prohibited-product inventory. Not personal zakatable wealth; mark for purification."),
    "haram_income_separated": (Classification.HARAM, "Haram funds already separated from halal wealth. Tracked for disposal, not zakat."),

    # --- Mixed ---
    "mixed_income_disposed": (Classification.MIXED, "Mixed income whose identified haram portion was disposed of. Zakat is due only on the remaining halal amount."),
    "mixed_income_retained": (Classification.MIXED, "Mixed income kept in full. The retained amount stays in zakatable wealth until the haram portion is separated."),
    "mixed_business_cash_retained": (Classification.MIXED, "Known mixed-income cash still held. Included in zakatable wealth until the haram portion is removed."),
    "mixed_income_missing_split": (Classification.MISSING_INFO, "Mixed payment with no halal/haram split. Classification cannot be finished until the percentages are known."),

    # --- Tentative (Scholar Review Required) ---
    "tentative_cashback": (Classification.TENTATIVE, "Cashback or promotional reward with unresolved contract terms. Scholar review required."),
    "tentative_unscreened_investment": (Classification.TENTATIVE, "Distribution from an unscreened investment. Scholar review required."),
    "tentative_crypto_portfolio_unscreened": (Classification.TENTATIVE, "Crypto holding without token screening and complete cost records. Scholar review required."),
    "receivable_tentative": (Classification.TENTATIVE, "Business receivable with doubtful repayment. Scholar review required; not included while recovery is uncertain."),
    "personal_loan_receivable_doubtful": (Classification.HALAL, "Unpaid personal loan with doubtful repayment. Under Maliki rules, unpaid personal loans are exempt until actually received."),

    # --- Missing information ---
    "missing_info_affiliate_income": (Classification.MISSING_INFO, "Affiliate payout missing the underlying product or contract. Cannot classify until the source is known."),
    "missing_info_marketplace_income": (Classification.MISSING_INFO, "Marketplace credit missing product and source details."),
    "crypto_sale_missing_cost_basis": (Classification.MISSING_INFO, "Crypto sale missing cost basis and screening status."),

    # --- Asset snapshot keywords ---
    "cash": (Classification.HALAL, "Cash on hand. Zakatable under Maliki rules."),
    "personal_chequing": (Classification.HALAL, "Personal chequing balance. Zakatable cash."),
    "personal_chequing_account": (Classification.HALAL, "Personal chequing balance. Zakatable cash."),
    "savings_balance": (Classification.HALAL, "Personal savings balance. Zakatable cash."),
    "business_chequing": (Classification.HALAL, "Business chequing balance. Zakatable cash."),
    "business_inventory_halal": (Classification.HALAL, "Permissible inventory held for resale. Zakatable."),
    "worn_gold_jewelry": (Classification.HALAL, "Customary gold jewelry worn for personal use. Exempt from zakat under Maliki rules."),
    "investment_gold_coins": (Classification.HALAL, "Gold coins held as savings or investment. Zakatable."),
    "silver_bars": (Classification.HALAL, "Silver bars held as savings. Zakatable."),
    "stock_shares_screened": (Classification.HALAL, "Screened listed shares. Included as a halal investment under Maliki rules."),
    "other_halal_investment": (Classification.HALAL, "Non-stock screened investment holding. Zakatable."),
    "business_receivable_likely": (Classification.HALAL, "Outstanding business invoice with reasonably expected repayment. Included."),
    "personal_loan_receivable": (Classification.HALAL, "Money personally lent and still unpaid. Exempt under Maliki rules until it is received."),
}

# Keywords that are not "income" even when the row is an inflow.
NON_INCOME_KEYWORDS = {
    "internal_transfer",
    "loan_received",
    "refundable_client_deposit",
    "processor_payout",
    "processor_fee",
    "customer_refund",
    "chargeback",
    "loan_repayment",
    "security_deposit_return",
    "business_overpayment_return",
}

EXPENSE_KEYWORDS = {
    "business_supplies",
    "business_advertising",
    "transportation",
    "electricity_bill",
    "phone_bill",
    "restaurant_meal",
    "software_subscription",
    "personal_spending",
    "groceries",
    "inventory_purchase",
    "crypto_purchase",
    "equipment_purchase",
    "processor_fee",
    "loan_repayment",
    "customer_refund",
    "chargeback",
}

KEYWORD_CATEGORY = {
    "cash": Category.CASH_BANK,
    "personal_chequing": Category.CASH_BANK,
    "savings_balance": Category.CASH_BANK,
    "business_chequing": Category.CASH_BANK,
    "mixed_business_cash_retained": Category.CASH_BANK,
    "salary_income": Category.CASH_BANK,
    "freelance_income": Category.CASH_BANK,
    "rental_income": Category.CASH_BANK,
    "tip_income": Category.CASH_BANK,
    "gift_income": Category.CASH_BANK,
    "scholarship_income": Category.CASH_BANK,
    "tax_refund": Category.CASH_BANK,
    "business_inventory_halal": Category.BUSINESS_INVENTORY,
    "business_inventory_prohibited": Category.BUSINESS_INVENTORY,
    "inventory_purchase": Category.BUSINESS_INVENTORY,
    "business_sale_income": Category.BUSINESS_INVENTORY,
    "gross_business_sale": Category.BUSINESS_INVENTORY,
    "worn_gold_jewelry": Category.GOLD_SILVER,
    "investment_gold_coins": Category.GOLD_SILVER,
    "silver_bars": Category.GOLD_SILVER,
    "stock_shares_screened": Category.INVESTMENTS,
    "other_halal_investment": Category.INVESTMENTS,
    "stock_dividend_income": Category.INVESTMENTS,
    "stock_sale_proceeds": Category.INVESTMENTS,
    "content_revenue_income": Category.INVESTMENTS,
    "commission_income": Category.INVESTMENTS,
    "tentative_unscreened_investment": Category.INVESTMENTS,
    "tentative_crypto_portfolio_unscreened": Category.CRYPTO,
    "crypto_sale_with_cost_basis": Category.CRYPTO,
    "crypto_sale_missing_cost_basis": Category.CRYPTO,
    "crypto_purchase": Category.CRYPTO,
    "business_receivable_likely": Category.RECEIVABLES,
    "receivable_tentative": Category.RECEIVABLES,
    "personal_loan_receivable": Category.RECEIVABLES,
    "personal_loan_receivable_doubtful": Category.RECEIVABLES,
    "haram_income_separated": Category.OTHER,
    "interest_income": Category.OTHER,
    "alcohol_sales_income": Category.OTHER,
    "vape_sales_income": Category.OTHER,
    "gambling_income": Category.OTHER,
    "lottery_winnings": Category.OTHER,
}


def map_category(keyword: str, description: str) -> Category:
    clean_kw = (keyword or "").strip().lower()
    if clean_kw in KEYWORD_CATEGORY:
        return KEYWORD_CATEGORY[clean_kw]
    text = f"{keyword} {description}".lower()
    if any(k in text for k in ["cash", "chequing", "checking", "savings", "balance", "bank", "salary", "freelance", "rental"]):
        return Category.CASH_BANK
    if any(k in text for k in ["gold", "silver", "jewelry", "jewellery", "coins", "bars", "bullion"]):
        return Category.GOLD_SILVER
    if any(k in text for k in ["stock", "share", "investment", "dividend", "equity"]):
        return Category.INVESTMENTS
    if any(k in text for k in ["inventory", "product", "goods", "resale"]):
        return Category.BUSINESS_INVENTORY
    if any(k in text for k in ["crypto", "bitcoin", "ethereum", "wallet", "token"]):
        return Category.CRYPTO
    if any(k in text for k in ["receivable", "invoice", "lent", "loan owed", "loan receivable"]):
        return Category.RECEIVABLES
    return Category.OTHER


KEYWORD_ALIASES = {
    "salary": "salary_income",
    "wages": "salary_income",
    "wage": "salary_income",
    "bank_interest": "interest_income",
    "riba": "interest_income",
    "checking": "personal_chequing",
    "chequing": "personal_chequing",
    "checking_account": "personal_chequing",
    "chequing_account": "personal_chequing",
}

EXPLICIT_CLASS = {
    "halal": Classification.HALAL,
    "permitted": Classification.HALAL,
    "permissible": Classification.HALAL,
    "haram": Classification.HARAM,
    "impermissible": Classification.HARAM,
    "prohibited": Classification.HARAM,
    "mixed": Classification.MIXED,
    "tentative": Classification.TENTATIVE,
    "scholar_review": Classification.TENTATIVE,
    "scholar_review_required": Classification.TENTATIVE,
    "missing": Classification.MISSING_INFO,
    "missing_info": Classification.MISSING_INFO,
    "missing_information": Classification.MISSING_INFO,
}


def normalize_keyword(keyword: Optional[str]) -> str:
    """Turn 'Interest Income', 'interest-income', or 'INTEREST_INCOME' into interest_income."""
    return re.sub(r"[^a-z0-9]+", "_", str(keyword or "").strip().lower()).strip("_")


def match_keyword(keyword: Optional[str]) -> Optional[str]:
    """Return the KEYWORD_MAPPING key for a raw keyword, or None."""
    clean = normalize_keyword(keyword)
    if not clean:
        return None
    if clean in KEYWORD_MAPPING:
        return clean
    if clean in KEYWORD_ALIASES:
        return KEYWORD_ALIASES[clean]
    hits = [key for key in KEYWORD_MAPPING if len(key) >= 10 and key in clean]
    if hits:
        return max(hits, key=len)
    return None


def parse_explicit_classification(value: Optional[str]) -> Optional[Classification]:
    token = normalize_keyword(value)
    if not token:
        return None
    if token in EXPLICIT_CLASS:
        return EXPLICIT_CLASS[token]
    for alias, cls in EXPLICIT_CLASS.items():
        if alias in token and len(alias) >= 5:
            return cls
    return None


def classify_entry(
    description: str,
    keyword: Optional[str] = None,
    notes: Optional[str] = "",
    category: Optional[Category] = Category.OTHER,
    screening_status: Optional[str] = None,
    missing_info_note: Optional[str] = None,
    repayment_likelihood: Optional[str] = None,
    explicit_classification: Optional[str] = None,
) -> Tuple[Classification, str, Optional[str]]:
    """
    Classify a row as Halal, Haram, Mixed, Tentative, or Missing Information.

    Order:
    1. Known keyword (always wins, even if missing-information text is filled).
    2. Explicit classification column on the sheet.
    3. Missing-information note.
    4. Screening status.
    5. Words in the description.
    """
    _ = category  # reserved for future category-specific rules
    matched_kw = match_keyword(keyword)
    extra_missing = str(missing_info_note or "").strip()
    if extra_missing.lower() in {"nan", "none", ""}:
        extra_missing = ""

    if matched_kw:
        cls, exp = KEYWORD_MAPPING[matched_kw]
        if extra_missing:
            exp = f"{exp} Note: {extra_missing}."
        if repayment_likelihood:
            likelihood = str(repayment_likelihood).strip().lower()
            if likelihood == "doubtful" and cls != Classification.TENTATIVE:
                exp = f"{exp} Repayment is marked doubtful."
        return cls, exp, matched_kw

    explicit = parse_explicit_classification(explicit_classification)
    if explicit:
        return (
            explicit,
            f"The sheet set the classification to {explicit.value}.",
            normalize_keyword(keyword) or "explicit_column",
        )

    if extra_missing:
        return (
            Classification.MISSING_INFO,
            f"Missing information: {extra_missing}. Classification cannot be completed until this is filled in.",
            "explicit_missing_info",
        )

    clean_screen = normalize_keyword(screening_status)
    if clean_screen == "prohibited":
        return Classification.HARAM, "Marked prohibited. Excluded from zakat and flagged for purification.", "screening_prohibited"
    if clean_screen in {"not_screened", "unscreened"}:
        return Classification.TENTATIVE, "Not Shariah-screened. Scholar review required.", "screening_unscreened"
    if clean_screen == "mixed_known_retained":
        return Classification.MIXED, "Mixed amount retained by the owner. Stays in zakatable wealth until purified.", "screening_mixed_retained"
    if clean_screen == "haram_separated":
        return Classification.HARAM, "Separated impermissible funds. Excluded from zakatable wealth.", "screening_haram_separated"

    text = f"{description} {notes or ''} {keyword or ''}".lower().strip()
    if not text:
        return Classification.MISSING_INFO, "No description or keyword was provided.", "empty_text"

    haram_words = ["interest", "riba", "usury", "gambling", "casino", "lottery", "alcohol", "liquor", "pork", "vape", "tobacco", "maisir"]
    for hw in haram_words:
        if hw in text:
            if any(mw in text for mw in ["mixed", "split", "portion", "partial"]):
                return Classification.MIXED, f"Contains both a prohibited indicator ('{hw}') and mixed-split language.", "text_mixed_haram"
            return Classification.HARAM, f"Detected impermissible term '{hw}'. Excluded from zakat.", f"text_haram_{hw}"

    for mw in ["mixed", "halal/haram", "partial prohibited"]:
        if mw in text:
            return Classification.MIXED, "Contains mixed halal and haram portions.", "text_mixed"

    for tw in ["unscreened", "unclear", "unsure", "scholar review", "pending review", "provisional"]:
        if tw in text:
            return Classification.TENTATIVE, "Unresolved or provisional. Scholar review required.", "text_tentative"

    for miw in ["missing info", "incomplete", "no record", "missing cost basis", "unknown source"]:
        if miw in text:
            return Classification.MISSING_INFO, "Essential details are missing, so classification cannot be completed.", "text_missing_info"

    return Classification.HALAL, "No prohibited indicators found. Treated as permissible.", "text_halal_default"

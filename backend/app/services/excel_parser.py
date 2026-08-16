import io
import math
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pathlib import Path

from app.models.enums import Classification
from app.models.schemas import IncomeEntry, DebtEntry, WealthHistoryMonth, UploadResponse, SheetInventory
from app.services.classifier import (
    classify_entry,
    map_category,
    NON_INCOME_KEYWORDS,
    EXPENSE_KEYWORDS,
    KEYWORD_MAPPING,
)

SHEET_ALIASES = {
    "user_profile": "User_Profile",
    "profile": "User_Profile",
    "participant": "User_Profile",
    "assets": "Assets",
    "asset": "Assets",
    "wealth": "Assets",
    "year_end": "Assets",
    "holdings": "Assets",
    "portfolio": "Assets",
    "debts": "Debts",
    "debt": "Debts",
    "liabilities": "Debts",
    "liability": "Debts",
    "loans_payable": "Debts",
    "wealth_history": "Wealth_History",
    "hawl": "Wealth_History",
    "monthly": "Wealth_History",
    "history": "Wealth_History",
    "transactions": "Transactions",
    "transaction": "Transactions",
    "income": "Transactions",
    "ledger": "Transactions",
    "inflows": "Transactions",
}

COLUMN_ALIASES = {
    "amount": "amount_cad",
    "value_cad": "amount_cad",
    "gross": "amount_cad",
    "gross_amount": "amount_cad",
    "txn_id": "transaction_id",
    "trans_id": "transaction_id",
    "tx_id": "transaction_id",
    "item": "description",
    "details": "description",
    "memo": "notes",
    "source": "merchant_or_source",
    "merchant": "merchant_or_source",
    "halal_pct": "mixed_halal_pct",
    "halal_percent": "mixed_halal_pct",
    "halal_percentage": "mixed_halal_pct",
    "disposed": "haram_portion_disposed",
    "haram_disposed": "haram_portion_disposed",
    "missing_info": "missing_information",
    "missing": "missing_information",
    "screening": "screening_status",
    "repayment": "repayment_likelihood",
    "likelihood": "repayment_likelihood",
    "use": "intended_use",
    "purpose": "intended_use",
    "balance": "outstanding_balance_cad",
    "outstanding": "outstanding_balance_cad",
    "outstanding_balance": "outstanding_balance_cad",
    "due_12_months": "amount_due_within_12_months_cad",
    "due_within_12_months": "amount_due_within_12_months_cad",
    "due_12m": "amount_due_within_12_months_cad",
    "month": "month_end",
    "month_end_date": "month_end",
    "class": "classification",
    "label": "classification",
    "nisab": "selected_nisab_cad",
    "name": "person_name",
    "participant": "person_name",
    "amount_due_within_12_months": "amount_due_within_12_months_cad",
    "cash_and_bank": "cash_and_bank_cad",
}


def _norm_token(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower()).strip("_")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    new_cols = []
    seen = {}
    for c in out.columns:
        name = _norm_token(c)
        name = COLUMN_ALIASES.get(name, name)
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        new_cols.append(name)
    out.columns = new_cols
    return out


def _is_guide_sheet(name: str) -> bool:
    token = _norm_token(name)
    return any(part in token for part in ("keyword", "guide", "notes", "readme", "instruction", "dictionary", "legend"))


def _resolve_sheets(sheet_names: List[str]) -> Dict[str, str]:
    """Map canonical roles to actual sheet names for similar-style workbooks."""
    mapping: Dict[str, str] = {}
    for official in ("User_Profile", "Assets", "Debts", "Wealth_History", "Transactions"):
        if official in sheet_names:
            mapping[official] = official

    aliases = sorted(SHEET_ALIASES.items(), key=lambda item: len(item[0]), reverse=True)
    for name in sheet_names:
        if name in mapping.values() or _is_guide_sheet(name):
            continue
        token = _norm_token(name)
        if token in SHEET_ALIASES:
            mapping.setdefault(SHEET_ALIASES[token], name)
            continue
        for alias, canonical in aliases:
            if alias in token:
                mapping.setdefault(canonical, name)
                break
    return mapping


def _looks_like_transactions(df: pd.DataFrame) -> bool:
    cols = set(_normalize_columns(df).columns)
    return bool(cols & {"direction", "transaction_id", "merchant_or_source", "transaction_type", "inflow"})


def _looks_like_debts(df: pd.DataFrame) -> bool:
    cols = set(_normalize_columns(df).columns)
    return bool(cols & {"outstanding_balance_cad", "creditor", "debt_id", "amount_due_within_12_months_cad"})


def _looks_like_wealth_history(df: pd.DataFrame) -> bool:
    cols = set(_normalize_columns(df).columns)
    return "month_end" in cols and bool(cols & {"cash_and_bank_cad", "debts_due_within_12_months_cad"})


def _looks_like_profile(df: pd.DataFrame) -> bool:
    cols = set(_normalize_columns(df).columns)
    return "field" in cols and "value" in cols


def _looks_like_assets(df: pd.DataFrame) -> bool:
    cols = set(_normalize_columns(df).columns)
    if _looks_like_transactions(df) or _looks_like_debts(df) or _looks_like_wealth_history(df):
        return False
    return bool(cols & {"asset_id", "screening_status", "intended_use", "amount_cad", "keyword"})


def _clean_str(val: Any) -> str:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return ""
    text = str(val).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def _clean_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        if isinstance(val, float) and math.isnan(val):
            return default
        if isinstance(val, str):
            text = val.strip().replace(",", "").replace("$", "")
            if not text or text.lower() in {"nan", "none", "-"}:
                return default
            return float(text)
        return float(val)
    except (ValueError, TypeError):
        return default


def _optional_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    if isinstance(val, str) and not val.strip():
        return None
    try:
        number = _clean_float(val, default=float("nan"))
        if math.isnan(number):
            return None
        return number
    except (ValueError, TypeError):
        return None


def _clean_bool(val: Any, default: bool = False) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return default
    if isinstance(val, (int, float)) and not (isinstance(val, float) and math.isnan(val)):
        return bool(val)
    text = str(val).strip().lower()
    if text in {"yes", "true", "1", "y"}:
        return True
    if text in {"no", "false", "0", "n"}:
        return False
    return default


def _row_date(val: Any) -> Optional[str]:
    text = _clean_str(val)
    if not text:
        return None
    return text[:10]


def _is_jewelry(keyword: str, description: str, intended_use: str) -> bool:
    blob = f"{keyword} {description} {intended_use}".lower()
    if keyword in {"worn_gold_jewelry", "worn_silver_jewelry"}:
        return True
    if "jewelry" in blob or "jewellery" in blob:
        personal = any(w in blob for w in ["personal", "worn", "adornment", "customary"])
        investment = any(w in blob for w in ["investment", "savings", "bullion", "stored as wealth"])
        return personal and not investment
    return False


def _is_personal_loan(keyword: str, description: str, intended_use: str) -> bool:
    if "personal_loan" in keyword:
        return True
    blob = f"{keyword} {description} {intended_use}".lower()
    return (
        ("personal" in blob and "loan" in blob)
        or "lent personally" in blob
        or "lent to a friend" in blob
        or "lent to another" in blob
    )


def _mixed_split(
    amount: float,
    keyword: str,
    classification: Classification,
    mixed_halal_pct: Any,
    disposed_flag: Any,
) -> Tuple[float, float, bool]:
    """Return (halal_amount, haram_amount, is_mixed_separated)."""
    kw = keyword.lower()
    pct = _optional_float(mixed_halal_pct)

    if "retained" in kw:
        default_separated = False
    elif "disposed" in kw:
        default_separated = True
    else:
        default_separated = True

    is_separated = _clean_bool(disposed_flag, default=default_separated)

    if classification == Classification.HALAL:
        return amount, 0.0, True
    if classification == Classification.HARAM:
        return 0.0, amount, True
    if classification != Classification.MIXED:
        return 0.0, 0.0, is_separated

    if pct is not None:
        pct = min(100.0, max(0.0, pct))
        halal = round(amount * (pct / 100.0), 2)
        haram = round(amount - halal, 2)
        return halal, haram, is_separated

    if is_separated:
        return 0.0, 0.0, True
    return amount, 0.0, False


def _build_entry(
    *,
    entry_id: str,
    description: str,
    keyword: str,
    amount: float,
    classification: Classification,
    explanation: str,
    screening: str = "",
    missing: str = "",
    repayment: str = "",
    intended_use: str = "",
    mixed_halal_pct: Any = None,
    disposed_flag: Any = None,
    direction: str = "inflow",
    date: Optional[str] = None,
    source_sheet: str = "Assets",
    extra_notes: str = "",
) -> IncomeEntry:
    category = map_category(keyword, description)
    jewelry = _is_jewelry(keyword, description, intended_use)
    personal_loan = _is_personal_loan(keyword, description, intended_use)
    expected = repayment != "doubtful" and keyword != "receivable_tentative"
    halal, haram, separated = _mixed_split(
        amount, keyword, classification, mixed_halal_pct, disposed_flag
    )

    kw = keyword.lower()
    is_income = (
        direction == "inflow"
        and kw not in NON_INCOME_KEYWORDS
        and kw not in EXPENSE_KEYWORDS
    )

    notes = explanation
    if extra_notes:
        notes = f"{extra_notes} — {explanation}"

    return IncomeEntry(
        id=entry_id,
        description=description or f"Item {entry_id}",
        category=category,
        gross_amount=amount,
        classification=classification,
        halal_amount=halal,
        haram_amount=haram,
        is_mixed_separated=separated,
        is_personal_jewelry=jewelry,
        is_personal_loan=personal_loan,
        is_business_receivable_expected=expected,
        notes=notes,
        date=date,
        keyword=keyword or None,
        direction=direction,
        is_income=is_income,
        source_sheet=source_sheet,
    )


def parse_assets_sheet(df: pd.DataFrame) -> Tuple[List[IncomeEntry], List[str]]:
    entries: List[IncomeEntry] = []
    warnings: List[str] = []
    data = _normalize_columns(df)

    for idx, row in data.iterrows():
        asset_id = _clean_str(row.get("asset_id", f"A-{idx + 1}"))
        keyword = _clean_str(row.get("keyword", ""))
        desc = _clean_str(row.get("description", ""))
        amount = _clean_float(row.get("amount_cad", row.get("amount", 0.0)))
        if not desc and not keyword and amount == 0:
            continue

        screening = _clean_str(row.get("screening_status", ""))
        missing = _clean_str(row.get("missing_information", ""))
        repayment = _clean_str(row.get("repayment_likelihood", "")).lower()
        intended_use = _clean_str(row.get("intended_use", ""))
        date = _row_date(row.get("as_of_date", row.get("date")))
        explicit = _clean_str(row.get("classification", ""))

        cls, explanation, matched = classify_entry(
            description=desc,
            keyword=keyword,
            screening_status=screening,
            missing_info_note=missing,
            repayment_likelihood=repayment,
            explicit_classification=explicit,
        )
        use_kw = matched if matched in KEYWORD_MAPPING else keyword

        if cls == Classification.MIXED and _optional_float(row.get("mixed_halal_pct")) is None:
            if "disposed" in use_kw.lower():
                warnings.append(
                    f"{asset_id} ('{desc}'): mixed income is marked disposed but has no split percentage."
                )

        entries.append(
            _build_entry(
                entry_id=asset_id or f"A-{idx + 1}",
                description=desc,
                keyword=use_kw,
                amount=amount,
                classification=cls,
                explanation=explanation,
                screening=screening,
                missing=missing,
                repayment=repayment,
                intended_use=intended_use,
                mixed_halal_pct=row.get("mixed_halal_pct") if "mixed_halal_pct" in data.columns else None,
                disposed_flag=row.get("haram_portion_disposed") if "haram_portion_disposed" in data.columns else None,
                direction="inflow",
                date=date,
                source_sheet="Assets",
            )
        )

    return entries, warnings


def parse_transactions_sheet(df: pd.DataFrame) -> Tuple[List[IncomeEntry], List[str]]:
    entries: List[IncomeEntry] = []
    warnings: List[str] = []
    data = _normalize_columns(df)

    for idx, row in data.iterrows():
        tx_id = _clean_str(row.get("transaction_id", row.get("id", f"T-{idx + 1}")))
        keyword = _clean_str(row.get("keyword", ""))
        desc = _clean_str(
            row.get(
                "description",
                row.get("merchant_or_source", row.get("item", "")),
            )
        )
        amount = abs(_clean_float(row.get("amount_cad", row.get("amount", row.get("gross_amount", 0.0)))))
        if not desc and not keyword and amount == 0:
            continue

        direction = _clean_str(row.get("direction", "")).lower()
        if direction not in {"inflow", "outflow"}:
            tx_type = _clean_str(row.get("transaction_type", "")).lower()
            if tx_type in {"expense", "loan_repayment", "refund"} or keyword in EXPENSE_KEYWORDS:
                direction = "outflow"
            else:
                direction = "inflow"

        missing = _clean_str(row.get("missing_information", ""))
        notes = _clean_str(row.get("notes", row.get("memo", "")))
        date = _row_date(row.get("date"))
        merchant = _clean_str(row.get("merchant_or_source", ""))
        extra = " | ".join(part for part in [merchant, notes] if part)
        explicit = _clean_str(row.get("classification", ""))

        cls, explanation, matched = classify_entry(
            description=desc,
            keyword=keyword,
            notes=notes,
            missing_info_note=missing,
            explicit_classification=explicit,
        )
        use_kw = matched if matched in KEYWORD_MAPPING else keyword

        mixed_pct = row.get("mixed_halal_pct") if "mixed_halal_pct" in data.columns else None
        disposed = row.get("haram_portion_disposed") if "haram_portion_disposed" in data.columns else None

        if cls == Classification.MIXED and _optional_float(mixed_pct) is None:
            warnings.append(
                f"{tx_id} ('{desc}'): mixed income has no halal/haram split. Flagged for review."
            )
            if "missing" not in keyword:
                cls = Classification.MISSING_INFO
                explanation = "Mixed income is missing the halal/haram split, so it cannot be classified yet."

        entry = _build_entry(
            entry_id=tx_id or f"T-{idx + 1}",
            description=desc,
            keyword=use_kw,
            amount=amount,
            classification=cls,
            explanation=explanation,
            mixed_halal_pct=mixed_pct,
            disposed_flag=disposed,
            direction=direction,
            date=date,
            source_sheet="Transactions",
            extra_notes=extra,
        )
        entries.append(entry)

    return entries, warnings


def parse_debts_sheet(df: pd.DataFrame) -> Tuple[List[DebtEntry], List[str]]:
    debts: List[DebtEntry] = []
    warnings: List[str] = []
    data = _normalize_columns(df)

    for idx, row in data.iterrows():
        debt_id = _clean_str(row.get("debt_id", row.get("id", f"D-{idx + 1}")))
        desc = _clean_str(row.get("description", f"Debt {idx + 1}"))
        creditor = _clean_str(row.get("creditor", ""))
        keyword = _clean_str(row.get("keyword", ""))
        total_bal = _clean_float(row.get("outstanding_balance_cad", row.get("outstanding_balance", row.get("amount", 0.0))))
        if not desc and not keyword and total_bal == 0:
            continue

        due_raw = row.get("amount_due_within_12_months_cad", row.get("amount_due_within_12_months"))
        due_12m = _clean_float(due_raw, default=total_bal) if due_raw is not None and _clean_str(due_raw) != "" else total_bal
        if due_12m > total_bal > 0:
            warnings.append(
                f"{debt_id}: amount due within 12 months (${due_12m:,.2f}) exceeds the outstanding balance (${total_bal:,.2f}). Capped."
            )
            due_12m = total_bal

        debts.append(
            DebtEntry(
                id=debt_id,
                description=f"{desc} ({creditor})" if creditor and creditor.lower() not in desc.lower() else desc,
                outstanding_balance=total_bal,
                amount_due_within_12_months=due_12m,
                is_due_within_12_months=due_12m > 0,
                creditor=creditor or None,
                overdue_amount=_clean_float(row.get("overdue_amount_cad", 0.0)),
                interest_bearing=_clean_bool(row.get("interest_bearing", False)),
                notes=_clean_str(row.get("notes", keyword)),
            )
        )

    return debts, warnings


def parse_wealth_history_sheet(df: pd.DataFrame) -> Tuple[List[WealthHistoryMonth], List[str]]:
    history: List[WealthHistoryMonth] = []
    warnings: List[str] = []
    data = _normalize_columns(df)

    for idx, row in data.iterrows():
        month_end = _row_date(row.get("month_end", f"Month-{idx + 1}")) or f"Month-{idx + 1}"
        history.append(
            WealthHistoryMonth(
                month_end=month_end,
                cash_and_bank_cad=_clean_float(row.get("cash_and_bank_cad")),
                business_cash_cad=_clean_float(row.get("business_cash_cad")),
                business_inventory_halal_cad=_clean_float(row.get("business_inventory_halal_cad")),
                business_inventory_prohibited_cad=_clean_float(row.get("business_inventory_prohibited_cad")),
                gold_silver_savings_cad=_clean_float(row.get("gold_silver_savings_cad")),
                customary_gold_jewelry_cad=_clean_float(row.get("customary_gold_jewelry_cad")),
                stock_shares_cad=_clean_float(row.get("stock_shares_cad")),
                other_halal_investments_cad=_clean_float(row.get("other_halal_investments_cad")),
                crypto_cad=_clean_float(row.get("crypto_cad")),
                business_receivables_likely_cad=_clean_float(row.get("business_receivables_likely_cad")),
                personal_loans_receivable_cad=_clean_float(row.get("personal_loans_receivable_cad")),
                receivables_doubtful_cad=_clean_float(row.get("receivables_doubtful_cad")),
                total_outstanding_debts_cad=_clean_float(row.get("total_outstanding_debts_cad")),
                debts_due_within_12_months_cad=_clean_float(row.get("debts_due_within_12_months_cad")),
                event_note=_clean_str(row.get("event_note")) or None,
            )
        )

    if history and len(history) < 12:
        warnings.append(
            f"Wealth history has {len(history)} month(s). Maliki hawl needs 12 lunar months above nisab."
        )

    return history, warnings


def parse_user_profile(df: pd.DataFrame) -> Tuple[Dict[str, Any], str, float]:
    data = _normalize_columns(df)
    profile: Dict[str, Any] = {}
    value_col = next((c for c in ("value", "amount_cad", "content") if c in data.columns), None)
    if "field" in data.columns and value_col:
        for _, row in data.iterrows():
            field = _norm_token(_clean_str(row.get("field")))
            if field in {"nisab", "selected_nisab"}:
                field = "selected_nisab_cad"
            if field in {"name", "participant"}:
                field = "person_name"
            if field:
                profile[field] = row.get(value_col)
    elif len(data):
        first = data.iloc[0]
        for col in data.columns:
            profile[col] = first.get(col)

    person_name = _clean_str(profile.get("person_name")) or "Participant"
    nisab = _clean_float(profile.get("selected_nisab_cad", 9250.0), default=9250.0)
    if nisab <= 0:
        nisab = 9250.0
    return profile, person_name, nisab


def _fill_sheets_by_columns(xl, sheet_names: List[str], resolved: Dict[str, str]) -> Dict[str, str]:
    used = set(resolved.values())
    for name in sheet_names:
        if name in used or _is_guide_sheet(name):
            continue
        try:
            sample = pd.read_excel(xl, name)
        except Exception:
            continue
        if "User_Profile" not in resolved and _looks_like_profile(sample):
            resolved["User_Profile"] = name
        elif "Transactions" not in resolved and _looks_like_transactions(sample):
            resolved["Transactions"] = name
        elif "Debts" not in resolved and _looks_like_debts(sample):
            resolved["Debts"] = name
        elif "Wealth_History" not in resolved and _looks_like_wealth_history(sample):
            resolved["Wealth_History"] = name
        elif "Assets" not in resolved and _looks_like_assets(sample):
            resolved["Assets"] = name
        used.add(name)
    return resolved


def parse_workbook(contents: bytes, filename: str) -> UploadResponse:
    """Parse an official multi-sheet workbook, a generic Excel file, or a CSV."""
    ext = Path(filename).suffix.lower()
    warnings: List[str] = []
    entries: List[IncomeEntry] = []
    transactions: List[IncomeEntry] = []
    debts: List[DebtEntry] = []
    wealth_history: List[WealthHistoryMonth] = []
    user_profile: Dict[str, Any] = {}
    person_name = "Participant"
    selected_nisab_cad = 9250.0
    sheet_inventory: List[SheetInventory] = []
    sheets_in_file: List[str] = []

    if ext == ".csv":
        try:
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(contents), encoding="latin1")

        if _looks_like_transactions(df):
            transactions, csv_warnings = parse_transactions_sheet(df)
            warnings.extend(csv_warnings)
            warnings.append(
                "CSV looks like a transaction ledger. Income was classified, but zakat still needs a year-end wealth snapshot (Assets)."
            )
            sheet_inventory.append(SheetInventory(sheet="CSV", rows_in_file=len(df), rows_kept=len(transactions)))
        else:
            entries, csv_warnings = parse_single_sheet_as_assets(df)
            warnings.extend(csv_warnings)
            person_name = "CSV upload"
            sheet_inventory.append(SheetInventory(sheet="CSV", rows_in_file=len(df), rows_kept=len(entries)))

        sheets_in_file = ["CSV"]
        inflow_count = sum(1 for t in (transactions or entries) if t.is_income)
        outflow_count = sum(1 for t in (transactions or entries) if (t.direction or "") == "outflow")
        return UploadResponse(
            filename=filename,
            person_name=person_name,
            selected_nisab_cad=selected_nisab_cad,
            entries=entries,
            transactions=transactions,
            debts=debts,
            wealth_history=wealth_history,
            user_profile=user_profile,
            warnings=warnings,
            rows_processed=len(entries) + len(transactions) + len(debts) + len(wealth_history),
            income_inflow_count=inflow_count,
            income_outflow_count=outflow_count,
            sheet_inventory=sheet_inventory,
            sheets_in_file=sheets_in_file,
        )

    xl = pd.ExcelFile(io.BytesIO(contents))
    sheet_names = xl.sheet_names
    sheets_in_file = list(sheet_names)
    resolved = _fill_sheets_by_columns(xl, sheet_names, _resolve_sheets(sheet_names))

    def _load(canonical: str):
        return pd.read_excel(xl, resolved[canonical]) if canonical in resolved else None

    profile_df = _load("User_Profile")
    if profile_df is not None:
        try:
            user_profile, person_name, selected_nisab_cad = parse_user_profile(profile_df)
            sheet_inventory.append(
                SheetInventory(sheet=resolved["User_Profile"], rows_in_file=len(profile_df), rows_kept=len(profile_df))
            )
        except Exception as exc:
            warnings.append(f"Could not parse profile sheet '{resolved['User_Profile']}': {exc}")

    assets_df = _load("Assets")
    if assets_df is not None:
        try:
            entries, asset_warnings = parse_assets_sheet(assets_df)
            warnings.extend(asset_warnings)
            sheet_inventory.append(
                SheetInventory(sheet=resolved["Assets"], rows_in_file=len(assets_df), rows_kept=len(entries))
            )
        except Exception as exc:
            warnings.append(f"Could not parse assets sheet '{resolved['Assets']}': {exc}")

    debts_df = _load("Debts")
    if debts_df is not None:
        try:
            debts, debt_warnings = parse_debts_sheet(debts_df)
            warnings.extend(debt_warnings)
            sheet_inventory.append(
                SheetInventory(sheet=resolved["Debts"], rows_in_file=len(debts_df), rows_kept=len(debts))
            )
        except Exception as exc:
            warnings.append(f"Could not parse debts sheet '{resolved['Debts']}': {exc}")

    hist_df = _load("Wealth_History")
    if hist_df is not None:
        try:
            wealth_history, hist_warnings = parse_wealth_history_sheet(hist_df)
            warnings.extend(hist_warnings)
            sheet_inventory.append(
                SheetInventory(sheet=resolved["Wealth_History"], rows_in_file=len(hist_df), rows_kept=len(wealth_history))
            )
        except Exception as exc:
            warnings.append(f"Could not parse wealth-history sheet '{resolved['Wealth_History']}': {exc}")

    tx_df = _load("Transactions")
    if tx_df is not None:
        try:
            transactions, tx_warnings = parse_transactions_sheet(tx_df)
            warnings.extend(tx_warnings)
            sheet_inventory.append(
                SheetInventory(sheet=resolved["Transactions"], rows_in_file=len(tx_df), rows_kept=len(transactions))
            )
        except Exception as exc:
            warnings.append(f"Could not parse transactions sheet '{resolved['Transactions']}': {exc}")

    if not entries and not transactions:
        for sheet in sheet_names:
            if _is_guide_sheet(sheet) or sheet in resolved.values():
                continue
            try:
                first_df = pd.read_excel(xl, sheet)
                if _looks_like_transactions(first_df):
                    transactions, fb_warnings = parse_transactions_sheet(first_df)
                else:
                    entries, fb_warnings = parse_single_sheet_as_assets(first_df)
                warnings.extend(fb_warnings)
                if entries or transactions:
                    sheet_inventory.append(
                        SheetInventory(sheet=sheet, rows_in_file=len(first_df), rows_kept=len(entries or transactions))
                    )
                    break
            except Exception as exc:
                warnings.append(f"Could not parse sheet '{sheet}': {exc}")

    if transactions and not entries:
        warnings.append(
            "Income rows were classified, but this file has no Assets sheet. Zakat is calculated on year-end wealth, not on the sum of income."
        )
    if entries and transactions:
        warnings.append(
            f"Classified {sum(1 for t in transactions if t.is_income)} income inflows. Zakat uses the {len(entries)} year-end assets, not the transaction total."
        )

    inflow_count = sum(1 for t in transactions if t.is_income)
    outflow_count = sum(1 for t in transactions if (t.direction or "") == "outflow")

    return UploadResponse(
        filename=filename,
        person_name=person_name,
        selected_nisab_cad=selected_nisab_cad,
        entries=entries,
        transactions=transactions,
        debts=debts,
        wealth_history=wealth_history,
        user_profile=user_profile,
        warnings=warnings,
        rows_processed=len(entries) + len(transactions) + len(debts) + len(wealth_history),
        income_inflow_count=inflow_count,
        income_outflow_count=outflow_count,
        sheet_inventory=sheet_inventory,
        sheets_in_file=sheets_in_file,
    )


def parse_single_sheet_as_assets(df: pd.DataFrame) -> Tuple[List[IncomeEntry], List[str]]:
    """Generic table → wealth items (CSV / unknown sheet)."""
    entries: List[IncomeEntry] = []
    warnings: List[str] = []
    data = _normalize_columns(df)

    for idx, row in data.iterrows():
        desc = _clean_str(row.get("description", row.get("item", row.get("details", ""))))
        amount = _clean_float(
            row.get("amount_cad", row.get("amount", row.get("gross_amount", row.get("value", 0.0))))
        )
        keyword = _clean_str(row.get("keyword", ""))
        notes = _clean_str(row.get("notes", row.get("memo", row.get("reason", ""))))
        missing = _clean_str(row.get("missing_information", ""))
        if not desc and not keyword and amount == 0:
            continue

        cls, explanation, matched = classify_entry(
            description=desc or f"Row {idx + 1}",
            keyword=keyword,
            notes=notes,
            missing_info_note=missing,
            explicit_classification=_clean_str(row.get("classification", "")),
        )
        keyword = matched if matched in KEYWORD_MAPPING else keyword

        mixed_pct = row.get("mixed_halal_pct") if "mixed_halal_pct" in data.columns else None
        disposed = row.get("haram_portion_disposed") if "haram_portion_disposed" in data.columns else None
        if "is_mixed_separated" in data.columns:
            disposed = row.get("is_mixed_separated")

        if cls == Classification.MIXED and _optional_float(mixed_pct) is None:
            explicit_halal = _optional_float(row.get("halal_amount"))
            explicit_haram = _optional_float(row.get("haram_amount"))
            if explicit_halal is None and explicit_haram is None:
                warnings.append(f"Row {idx + 1} ('{desc}'): mixed income needs a halal/haram split.")

        entry = _build_entry(
            entry_id=_clean_str(row.get("transaction_id", row.get("id", f"row-{idx + 1}"))) or f"row-{idx + 1}",
            description=desc or f"Row {idx + 1}",
            keyword=keyword,
            amount=amount,
            classification=cls,
            explanation=explanation,
            mixed_halal_pct=mixed_pct,
            disposed_flag=disposed,
            direction=_clean_str(row.get("direction", "inflow")).lower() or "inflow",
            date=_row_date(row.get("date")),
            source_sheet="Upload",
            extra_notes=notes,
        )

        if "halal_amount" in data.columns:
            explicit_halal = _optional_float(row.get("halal_amount"))
            if explicit_halal is not None:
                entry.halal_amount = explicit_halal
        if "haram_amount" in data.columns:
            explicit_haram = _optional_float(row.get("haram_amount"))
            if explicit_haram is not None:
                entry.haram_amount = explicit_haram
        if "is_personal_jewelry" in data.columns:
            entry.is_personal_jewelry = _clean_bool(row.get("is_personal_jewelry"), entry.is_personal_jewelry)
        if "is_personal_loan" in data.columns:
            entry.is_personal_loan = _clean_bool(row.get("is_personal_loan"), entry.is_personal_loan)

        entries.append(entry)

    return entries, warnings


# Back-compat alias used by older tests
def parse_single_sheet(df: pd.DataFrame) -> Tuple[List[IncomeEntry], List[str]]:
    return parse_single_sheet_as_assets(df)

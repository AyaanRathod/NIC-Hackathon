from typing import List, Dict, Any, Tuple
from app.models.schemas import (
    IncomeEntry,
    DebtEntry,
    WealthHistoryMonth,
    ZakatCalculationRequest,
    ZakatCalculationResponse,
    PurificationItem,
)
from app.models.enums import Classification, Category
from app.core.config import settings

def evaluate_monthly_hawl(
    wealth_history: List[WealthHistoryMonth],
    nisab_cad: float
) -> Tuple[bool, List[str]]:
    """
    Evaluates Hawl continuity under Maliki Madhhab:
    The user's net zakatable wealth must remain at or above nisab continuously for 12 lunar months.
    If wealth drops below nisab, hawl resets.
    """
    if not wealth_history:
        return True, ["No monthly wealth history was uploaded. Hawl is taken from the user's confirmation."]

    notes = []
    hawl_intact = True
    reset_month = None

    for idx, month in enumerate(wealth_history):
        # Maliki Zakatable assets snapshot:
        # Cash & bank + business cash + halal inventory + investment gold/silver + stocks + other investments + crypto + likely receivables
        # Customary jewelry is EXEMPT; Prohibited inventory is EXCLUDED; Personal loans are EXEMPT
        assets = (
            month.cash_and_bank_cad +
            month.business_cash_cad +
            month.business_inventory_halal_cad +
            month.gold_silver_savings_cad +
            month.stock_shares_cad +
            month.other_halal_investments_cad +
            month.crypto_cad +
            month.business_receivables_likely_cad
        )
        debts_12m = month.debts_due_within_12_months_cad
        net_wealth = assets - debts_12m
        is_above = net_wealth >= nisab_cad

        month.maliki_zakatable_assets = round(assets, 2)
        month.maliki_net_wealth = round(net_wealth, 2)
        month.is_above_nisab = is_above

        date_label = month.month_end[:10] if len(month.month_end) >= 10 else month.month_end

        if not is_above:
            hawl_intact = False
            reset_month = date_label
            notes.append(
                f"Month {idx + 1} ({date_label}): net ${net_wealth:,.2f} fell below nisab (${nisab_cad:,.2f}). Hawl resets here."
            )
        else:
            event_text = f" — {month.event_note}" if month.event_note else ""
            notes.append(
                f"Month {idx + 1} ({date_label}): net ${net_wealth:,.2f} is at or above nisab (${nisab_cad:,.2f}).{event_text}"
            )

    if not hawl_intact:
        notes.append(
            f"Hawl reset: net wealth dropped below nisab on {reset_month}. "
            "Under Maliki rules a new lunar year starts only after nisab is reached again."
        )
    elif len(wealth_history) < 12:
        notes.append(
            f"Only {len(wealth_history)} month(s) of history were provided. "
            "Maliki hawl needs 12 continuous lunar months at or above nisab."
        )
        hawl_intact = False
    else:
        notes.append(
            f"Hawl complete: net wealth stayed at or above nisab (${nisab_cad:,.2f}) "
            f"across all {len(wealth_history)} recorded months."
        )

    return hawl_intact, notes

def calculate_maliki_zakat(payload: ZakatCalculationRequest) -> ZakatCalculationResponse:
    """
    Executes the definitive Maliki Madhhab Halal Income and Zakat Calculation.
    """
    total_gross = 0.0
    zakatable_wealth = 0.0
    exempt_wealth = 0.0
    haram_disposal = 0.0
    tentative_wealth = 0.0
    
    warnings: List[str] = []
    audit_breakdown: List[str] = []
    purification_items: List[PurificationItem] = []

    audit_breakdown.append(f"Maliki zakat breakdown — {payload.person_name}")
    audit_breakdown.append(f"Nisab: ${payload.nisab_cad:,.2f} CAD")
    audit_breakdown.append("1. Classification of each asset")

    for entry in payload.entries:
        total_gross += entry.gross_amount

        # 1. Missing Information
        if entry.classification == Classification.MISSING_INFO:
            warnings.append(
                f"Missing information: '{entry.description}' (${entry.gross_amount:,.2f}). Excluded until the record is complete."
            )
            audit_breakdown.append(
                f"Missing information — {entry.description} (${entry.gross_amount:,.2f}): cannot classify; excluded from zakat."
            )
            continue

        # 2. Tentative / Scholar Review Required
        if entry.classification == Classification.TENTATIVE:
            tentative_wealth += entry.gross_amount
            warnings.append(
                f"Scholar review required: '{entry.description}' (${entry.gross_amount:,.2f}) is tentative."
            )
            audit_breakdown.append(
                f"Tentative — {entry.description} (${entry.gross_amount:,.2f}): scholar review required; excluded from zakat."
            )
            continue

        # 3. Haram Wealth
        if entry.classification == Classification.HARAM:
            haram_disposal += entry.gross_amount
            purification_items.append(
                PurificationItem(
                    description=entry.description,
                    amount=entry.gross_amount,
                    reason=entry.notes or "Impermissible income / asset (e.g. interest, alcohol, gambling, prohibited inventory)."
                )
            )
            audit_breakdown.append(
                f"Haram — {entry.description} (${entry.gross_amount:,.2f}): excluded from zakat; separate and dispose of this amount. Removing it is not paying zakat."
            )
            continue

        # 4. Mixed Wealth
        if entry.classification == Classification.MIXED:
            if entry.is_mixed_separated:
                haram_portion = entry.haram_amount
                halal_portion = entry.halal_amount if entry.halal_amount > 0 else max(0.0, entry.gross_amount - haram_portion)

                if haram_portion <= 0 and halal_portion <= 0:
                    warnings.append(
                        f"Mixed income '{entry.description}' (${entry.gross_amount:,.2f}) has no halal/haram split. Excluded until the split is known."
                    )
                    audit_breakdown.append(
                        f"Mixed (missing split) — {entry.description} (${entry.gross_amount:,.2f}): excluded until percentages are provided."
                    )
                    continue

                if haram_portion > 0:
                    haram_disposal += haram_portion
                    purification_items.append(
                        PurificationItem(
                            description=f"{entry.description} (haram portion)",
                            amount=haram_portion,
                            reason="Identified impermissible portion of mixed income.",
                        )
                    )
                zakatable_wealth += halal_portion
                audit_breakdown.append(
                    f"Mixed (haram disposed) — {entry.description} (${entry.gross_amount:,.2f}): "
                    f"removed ${haram_portion:,.2f} haram; added ${halal_portion:,.2f} halal remainder."
                )
            else:
                zakatable_wealth += entry.gross_amount
                audit_breakdown.append(
                    f"Mixed (retained) — {entry.description} (${entry.gross_amount:,.2f}): "
                    f"haram portion not yet removed, so the full retained amount stays zakatable."
                )
            continue

        # 5. Halal Wealth - Apply Maliki Specific Exemptions
        if entry.classification == Classification.HALAL:
            # Customary personal jewelry exemption
            if entry.is_personal_jewelry or (entry.keyword == "worn_gold_jewelry"):
                exempt_wealth += entry.gross_amount
                audit_breakdown.append(
                    f"Exempt jewelry — {entry.description} (${entry.gross_amount:,.2f}): "
                    "customary jewelry worn for personal use is exempt under Maliki rules."
                )
            elif entry.is_personal_loan or (entry.keyword in {"personal_loan_receivable", "personal_loan_receivable_doubtful"}):
                exempt_wealth += entry.gross_amount
                audit_breakdown.append(
                    f"Exempt personal loan — {entry.description} (${entry.gross_amount:,.2f}): "
                    "unpaid ordinary personal loans are exempt until received. One year of zakat is due on the amount when it arrives."
                )
            elif entry.category == Category.RECEIVABLES and not entry.is_business_receivable_expected:
                exempt_wealth += entry.gross_amount
                audit_breakdown.append(
                    f"Excluded receivable — {entry.description} (${entry.gross_amount:,.2f}): "
                    "repayment is not reasonably expected."
                )
            else:
                zakatable_wealth += entry.gross_amount
                audit_breakdown.append(
                    f"Zakatable — {entry.description} (${entry.gross_amount:,.2f}): {entry.category.value}."
                )

    # 6. Section 2: Deducting Qualifying Debts
    audit_breakdown.append("2. Qualifying debts (due now or within 12 months)")

    qualifying_debts = 0.0
    long_term_excluded_debts = 0.0

    for debt in payload.debts:
        # Determine 12-month deductible portion
        due_12m = debt.amount_due_within_12_months if debt.amount_due_within_12_months > 0 else (debt.outstanding_balance if debt.is_due_within_12_months else 0.0)
        long_term_portion = max(0.0, debt.outstanding_balance - due_12m)

        if due_12m > 0:
            qualifying_debts += due_12m
            audit_breakdown.append(
                f"Deducted — {debt.description}: ${due_12m:,.2f} due within 12 months."
            )
        if long_term_portion > 0:
            long_term_excluded_debts += long_term_portion
            audit_breakdown.append(
                f"Not deducted — {debt.description}: ${long_term_portion:,.2f} falls after 12 months."
            )

    net_zakatable = max(0.0, zakatable_wealth - qualifying_debts)

    # 7. Section 3: Hawl Evaluation
    audit_breakdown.append("3. Hawl (one lunar year at or above nisab)")

    if payload.wealth_history:
        hawl_intact, hawl_notes = evaluate_monthly_hawl(payload.wealth_history, payload.nisab_cad)
        for h_note in hawl_notes:
            audit_breakdown.append(f"• {h_note}")
    else:
        hawl_intact = payload.hawl_maintained
        hawl_notes = ["Hawl taken from the user's confirmation because no monthly history was uploaded."]
        if hawl_intact:
            audit_breakdown.append("User confirmed wealth stayed at or above nisab for one lunar year.")
        else:
            audit_breakdown.append("User indicated wealth fell below nisab; hawl was reset.")

    # 8. Section 4: Final Calculation
    is_eligible = hawl_intact and (net_zakatable >= payload.nisab_cad)
    zakat_due = round(net_zakatable * settings.ZAKAT_RATE, 2) if is_eligible else 0.0

    audit_breakdown.append("4. Final figure")
    audit_breakdown.append(f"Zakatable assets: ${zakatable_wealth:,.2f}")
    audit_breakdown.append(f"Minus debts due within 12 months: -${qualifying_debts:,.2f}")
    audit_breakdown.append(f"Net zakatable wealth: ${net_zakatable:,.2f}")
    audit_breakdown.append(f"Nisab: ${payload.nisab_cad:,.2f} — {'met' if net_zakatable >= payload.nisab_cad else 'not met'}")
    audit_breakdown.append(f"Hawl: {'complete' if hawl_intact else 'not complete'}")
    audit_breakdown.append(f"Zakat due (2.5%): ${zakat_due:,.2f}")
    audit_breakdown.append(f"Haram to dispose of (not zakat): ${haram_disposal:,.2f}")

    return ZakatCalculationResponse(
        madhhab="Maliki",
        person_name=payload.person_name or "Participant",
        total_gross_wealth=round(total_gross, 2),
        total_zakatable_assets=round(zakatable_wealth, 2),
        total_exempt_wealth=round(exempt_wealth, 2),
        total_haram_disposed=round(haram_disposal, 2),
        total_tentative_review=round(tentative_wealth, 2),
        qualifying_debts_deducted=round(qualifying_debts, 2),
        long_term_debts_excluded=round(long_term_excluded_debts, 2),
        net_zakatable_wealth=round(net_zakatable, 2),
        nisab_threshold_cad=payload.nisab_cad,
        is_hawl_maintained=hawl_intact,
        hawl_notes=hawl_notes,
        is_eligible_for_zakat=is_eligible,
        zakat_due_cad=zakat_due,
        warnings=warnings,
        audit_breakdown=audit_breakdown,
        purification_items=purification_items,
    )

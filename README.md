# Halal Income and Zakat Calculator
# SECOND PLACE WINNERS  🥳
**Classification in depth:** [CLASSIFICATION.md](CLASSIFICATION.md). Use that file when a judge asks how the five labels are assigned.

---

## 1. What this tool does

This tool helps a user do four tasks:

1. Record income.
2. Classify each income line.
3. Separate haram money from halal wealth.
4. Calculate estimated zakat with **Maliki** rules only.

The team selected **one madhhab**: Maliki. The calculator does not mix rules from other schools.

A **madhhab** is a school of Islamic law.

---

## 2. Words you must know

Use these words in the presentation. Do not replace them with synonyms.

### Zakat

Zakat is an obligatory annual payment on qualifying wealth. The rate in this exercise is **2.5%**.

Zakat is not a tax on every dollar of income. Zakat is a charge on **net zakatable wealth** after one lunar year.

Haram money is not zakat. If you give haram money away, that act is not payment of zakat.

### Nisab

**Nisab** is the minimum wealth that makes zakat due.

If net zakatable wealth is below nisab, zakat is **0**.

The organizers give nisab in Canadian dollars. The team **must not** use a live internet gold price for nisab.

This prototype uses the nisab in the uploaded file:

| File | Nisab (CAD) |
| --- | --- |
| Faris Mahmood Practice B | 9250 |
| Nadia Rahman Practice A | 9000 |
| Default if the file has no nisab | 9250 |

The file also lists a silver nisab for reference (875 CAD in the Faris file). This calculator uses the **selected nisab** from `User_Profile`.

### Hawl

**Hawl** is one full lunar year.

Maliki rule:

- The user must stay at or above nisab for one lunar year.
- If wealth falls below nisab, the start date **resets**.
- A new year starts when the user reaches nisab again.

The `Wealth_History` sheet has monthly snapshots. The tool checks each month.

### Halal and haram

**Halal** means permitted.

**Haram** means not permitted. Examples: interest (riba), alcohol sales, gambling, lottery.

---

## 3. How you classify income

The full procedure is in [CLASSIFICATION.md](CLASSIFICATION.md). This section is the short version.

Every line gets **one** label:

| Label | Meaning | Zakat effect |
| --- | --- | --- |
| Halal | Permitted money | Include the remaining amount in zakatable wealth (Maliki exemptions still apply). |
| Haram | Not permitted | Exclude it. Show it as money to return or give away. |
| Mixed | Halal part and haram part together | See the mixed rule below. |
| Tentative | The case is not resolved | Mark **Scholar Review Required**. Exclude it from the zakat figure. |
| Missing Information | Data is not enough | Warn the user. Do not finish the classification. |

### Mixed income

Two results are possible:

1. **The haram part is removed.** Zakat is only on the halal remainder.
2. **The owner keeps the mixed amount.** The retained amount stays in zakatable wealth. Mixed status does not make it exempt.

### Classifier order

The tool uses this order. A later step cannot override an earlier step.

1. Normalize the `keyword` (`Salary Income` → `salary_income`) and look it up.
2. Read an explicit `classification` column if the sheet has one.
3. Read a missing-information note.
4. Read `screening_status`.
5. Search the description text.

A known keyword **wins**. A note on a Tentative row does not change the label to Missing Information.

### Similar Excel files

The organizers may give a new workbook. Sheet names and headers may differ. The style should stay similar.

The parser still maps sheets by alias (`Ledger` → Transactions, `Liabilities` → Debts, `Holdings` → Assets, `Monthly History` → Wealth_History).

If the name does not match, the parser looks at the columns.

Headers such as `Amount (CAD)` become `amount_cad`. The tool reads every row. There is no row limit.

Details and examples: [CLASSIFICATION.md](CLASSIFICATION.md).

---

## 4. How the tool calculates zakat (Maliki)

### Step A — Read the file

An official workbook has more than one sheet. The tool reads **all** of these sheets:

| Sheet | Use |
| --- | --- |
| `Transactions` | Classify income for the year |
| `Assets` | Year-end wealth for zakat |
| `Debts` | Liabilities |
| `Wealth_History` | Monthly hawl check |
| `User_Profile` | Name and selected nisab |

The tool also reads `Keyword_Guide` and `Manual_Notes` only as reference. It does not use them in the math.

**The file is not cut.** Pandas reads the full sheet. There is no row limit. A practice file has hundreds of transaction rows. The tool keeps all of them. After upload, the screen shows row counts for each sheet (rows in file / rows kept).

Blank rows are the only rows that the tool skips.

### Step B — Do not add income to get zakat

This is an important point for the presentation.

- **Income** = money that arrived during the year (`Transactions`).
- **Zakat** = 2.5% of **year-end wealth** (`Assets`), after debts and after hawl.

If you add all salaries, you do **not** get zakat. Cash that remains at year end is already in `Assets`.

### Step C — Build net zakatable wealth

From `Assets`, the tool:

1. **Includes** cash, bank balances, halal investments, business inventory for sale, investment gold and silver, and business invoices if repayment is likely.
2. **Excludes** haram amounts.
3. **Excludes** tentative and missing-information amounts from the zakat figure.
4. **Exempts** customary jewelry that the user wears.
5. **Exempts** unpaid ordinary personal loans until the user receives the money.
6. **Subtracts** debts that are due now or in the next 12 months.

Maliki formula used in this prototype:

```
Net zakatable wealth
  = cash
  + halal investments
  + business inventory
  + investment gold and silver
  + eligible business receivables
  − qualifying debts (due in 12 months)
```

The tool does **not** subtract the long-term part of a mortgage or a student loan.

### Step D — Apply nisab and hawl

If **both** are true:

- net zakatable wealth ≥ nisab
- hawl is complete

then:

```
Zakat = net zakatable wealth × 2.5%
```

If either test fails, zakat is 0.

---

## 5. Maliki rules in this prototype

The team uses **only** these Maliki exercise rules.

### Gold and silver

**Include:**

- gold and silver bullion
- coins
- jewelry stored as wealth
- jewelry bought as an investment
- excess jewelry that is not for personal use

**Exclude:**

- customary jewelry that the user wears
- diamonds and gemstones, unless they are business inventory

### Debts

Debts may reduce cash, gold and silver, investments, and business inventory.

Subtract only the amount due now or in the next 12 months.

### Money owed to the user

**Ordinary personal loan:**

- Do not calculate zakat on it each year while it is unpaid.
- When the user receives it, calculate one year of zakat on that amount.

**Unpaid business sale or invoice:**

- Include it if repayment is reasonably expected.

---

## 6. Gold karats and metal prices

Two different prices exist. Do not mix them.

### A. Nisab (required by the organizers)

Nisab is the **fixed CAD value in the file**. The tool does not call the internet for nisab.

### B. Karat converter (manual gold and silver)

If a user adds gold **by weight**, the tool converts weight to CAD.

Prototype spot prices, dated **16 August 2026** (Kitco CAD, not a live feed):

| Metal | Prototype price |
| --- | --- |
| Gold (24K / pure) | 195.21 CAD per gram |
| Silver (fine) | 3.48 CAD per gram |

The user can change the price in the Gold tab.

**Karat** is purity:

| Karat | Pure gold fraction |
| --- | --- |
| 24K | 24/24 = 1.00 |
| 22K | 22/24 |
| 21K | 21/24 |
| 18K | 18/24 |
| 14K | 14/24 |
| 10K | 10/24 |

Formula:

```
pure grams = weight in grams × (karat / 24)
CAD value  = pure grams × price per gram
```

Example: 10 g of 18K gold.

- pure grams = 10 × 18/24 = 7.5 g
- CAD value = 7.5 × 195.21 = 1464.08 CAD

If that item is worn jewelry, Maliki exempts it. If it is bullion or investment jewelry, the tool includes it.

Silver uses 999 or 925 (sterling) instead of karats.

**Do not** replace the CAD amounts that are already in the Excel `Assets` sheet. Those amounts are part of the official test data.

---

## 7. How to run the prototype

1. Start the backend and the frontend (or use `run.bat` / Docker).
2. Open the website.
3. Upload the Excel file. Do not use a hidden test-case button. The start screen is empty on purpose.
4. Open **Results** for zakat, haram to remove, and charts.
5. Open **Income** for every classified inflow.
6. Open **Wealth** for the year-end snapshot.
7. Open **Hawl** for the monthly nisab check.
8. Open **Gold** to convert karat weight to CAD.
9. Open **Rules** if a judge asks for the Maliki list.

---

## 8. How you explain this in 3 to 5 minutes

Say the sentences below. Keep them in this order.

1. "This calculator follows **Maliki** rules only."
2. "Zakat is 2.5% of net zakatable wealth, not a tax on all income."
3. "**Nisab** is the minimum. The organizers set it in CAD. We do not use a live gold feed for nisab."
4. "**Hawl** is one lunar year above nisab. If wealth falls below nisab, the year starts again."
5. "We classify each income line as Halal, Haram, Mixed, Tentative, or Missing Information."
6. "Haram money is set aside. That act is not zakat."
7. "Mixed money: if we remove the haram part, we calculate zakat on the halal remainder. If we keep the mixed amount, it stays zakatable."
8. "We read the full workbook: Transactions, Assets, Debts, Wealth History, and User Profile."
9. "Zakat uses the Assets snapshot. Income classification uses the Transactions sheet."
10. "Worn jewelry is exempt. Unpaid personal loans are exempt until received. Only debts due in 12 months are deducted."

---

## 9. Worked numbers (Faris Mahmood Practice B)

After a full-file upload:

- Transactions read: 656
- Income inflows classified: 227
- Assets used for zakat: 18
- Debts: 5
- Months of hawl: 13
- Zakatable assets: 45,790.00 CAD
- Debts deducted (12 months): 22,800.00 CAD
- Net zakatable wealth: 22,990.00 CAD
- Nisab: 9,250.00 CAD
- Hawl: complete
- **Zakat due: 574.75 CAD**
- Haram to remove: 1,210.00 CAD

Nadia Rahman Practice A uses nisab 9,000.00 CAD. Her month with a large withdrawal stays **above** nisab. Hawl does not reset. Zakat due is 496.75 CAD.

---

## 10. Limits

- The tool uses the organizer rule set. Specialists in the Maliki school may add more detail.
- Nisab is a fixed CAD test value.
- The karat price is a dated prototype price. It is not a live ticker.
- Unscreened crypto and incomplete records stay in Tentative or Missing Information.
- Future work: bank feeds, better investment screening, and a clear path to give haram money away.

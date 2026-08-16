import { useMemo, useState } from 'react'
import './App.css'
import type { IncomeEntry, DebtEntry, WealthHistoryMonth, ZakatCalculationResponse, UploadResponse, Classification } from './types/zakat'
import { calculateZakat } from './api/client'
import { Header } from './components/Header'
import { DashboardCards } from './components/DashboardCards'
import { FileUploadSection } from './components/FileUploadSection'
import { WealthHistoryView } from './components/WealthHistoryView'
import { ManualEntryForm } from './components/ManualEntryForm'
import { TransactionTable } from './components/TransactionTable'
import { CalculationBreakdown } from './components/CalculationBreakdown'
import { EducationGuide } from './components/EducationGuide'
import { Charts } from './components/Charts'
import { KaratTool } from './components/KaratTool'
import { LatticeBackground } from './components/LatticeBackground'
import { ConfirmDialog } from './components/ConfirmDialog'
import { summarizeIncome } from './lib/income'

type Tab = 'results' | 'income' | 'wealth' | 'hawl' | 'gold' | 'add'

function App() {
  const [started, setStarted] = useState(false)
  const [personName, setPersonName] = useState('')
  const [entries, setEntries] = useState<IncomeEntry[]>([])
  const [transactions, setTransactions] = useState<IncomeEntry[]>([])
  const [debts, setDebts] = useState<DebtEntry[]>([])
  const [wealthHistory, setWealthHistory] = useState<WealthHistoryMonth[]>([])
  const [nisabCad, setNisabCad] = useState(9250)
  const [hawlMaintained, setHawlMaintained] = useState(true)
  const [parseWarnings, setParseWarnings] = useState<string[]>([])
  const [isCalculating, setIsCalculating] = useState(false)
  const [result, setResult] = useState<ZakatCalculationResponse | null>(null)
  const [guideOpen, setGuideOpen] = useState(false)
  const [tab, setTab] = useState<Tab>('results')
  const [error, setError] = useState<string | null>(null)
  const [sheetInventory, setSheetInventory] = useState<UploadResponse['sheet_inventory']>([])
  const [incomeFilter, setIncomeFilter] = useState<Classification | 'ALL'>('ALL')
  const [resetOpen, setResetOpen] = useState(false)

  const executeCalculation = async (
    currentEntries = entries,
    currentDebts = debts,
    currentHistory = wealthHistory,
    currentNisab = nisabCad,
    currentHawl = hawlMaintained,
    name = personName,
  ) => {
    if (currentEntries.length === 0 && currentDebts.length === 0) {
      setResult(null)
      return
    }
    setIsCalculating(true)
    setError(null)
    try {
      const res = await calculateZakat({
        entries: currentEntries,
        debts: currentDebts,
        wealth_history: currentHistory,
        nisab_cad: currentNisab,
        hawl_maintained: currentHawl,
        person_name: name || 'Participant',
      })
      setResult(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Calculation failed')
    } finally {
      setIsCalculating(false)
    }
  }

  const handleUploadSuccess = (uploadRes: UploadResponse) => {
    setStarted(true)
    setTab('results')
    if (uploadRes.person_name) setPersonName(uploadRes.person_name)
    if (uploadRes.selected_nisab_cad) setNisabCad(uploadRes.selected_nisab_cad)
    setEntries(uploadRes.entries)
    setTransactions(uploadRes.transactions || [])
    setDebts(uploadRes.debts)
    setWealthHistory(uploadRes.wealth_history)
    setParseWarnings(uploadRes.warnings || [])
    setSheetInventory(uploadRes.sheet_inventory || [])
    setIncomeFilter('ALL')
    void executeCalculation(
      uploadRes.entries,
      uploadRes.debts,
      uploadRes.wealth_history,
      uploadRes.selected_nisab_cad || nisabCad,
      true,
      uploadRes.person_name || 'Participant',
    )
  }

  const handleReset = () => {
    setStarted(false)
    setPersonName('')
    setEntries([])
    setTransactions([])
    setDebts([])
    setWealthHistory([])
    setResult(null)
    setParseWarnings([])
    setNisabCad(9250)
    setHawlMaintained(true)
    setTab('results')
    setError(null)
    setSheetInventory([])
    setIncomeFilter('ALL')
  }

  const handleAddManualEntry = (entry: IncomeEntry) => {
    const updated = [entry, ...entries]
    setEntries(updated)
    setStarted(true)
    void executeCalculation(updated, debts, wealthHistory, nisabCad, hawlMaintained, personName)
  }

  const handleAddManualDebt = (debt: DebtEntry) => {
    const updated = [debt, ...debts]
    setDebts(updated)
    setStarted(true)
    void executeCalculation(entries, updated, wealthHistory, nisabCad, hawlMaintained, personName)
  }

  const incomeRows = useMemo(
    () => (transactions.length > 0 ? transactions : entries.filter((e) => e.source_sheet !== 'Assets')),
    [transactions, entries],
  )
  const incomeSummary = useMemo(() => summarizeIncome(incomeRows.length ? incomeRows : entries), [incomeRows, entries])

  return (
    <main className="app">
      <LatticeBackground />
      <Header
        personName={started ? personName : undefined}
        onOpenRules={() => setGuideOpen(true)}
        onReset={() => setResetOpen(true)}
        showReset={started}
      />

      {!started && (
        <section className="welcome">
          <div className="welcome-copy">
            <h2 className="display">Upload a ledger. Get a Maliki zakat figure.</h2>
            <p className="lede">
              Classify income, set haram amounts aside, and estimate zakat from year-end wealth.
              One school of law only: Maliki.
            </p>
            <div className="steps">
              <div className="step">
                <span>01</span>
                <p>Upload the Excel workbook or a CSV. Nothing is preloaded.</p>
              </div>
              <div className="step">
                <span>02</span>
                <p>Every income line is labelled Halal, Haram, Mixed, Tentative, or Missing information.</p>
              </div>
              <div className="step">
                <span>03</span>
                <p>Zakat is 2.5% of net zakatable wealth if nisab and hawl are both met.</p>
              </div>
            </div>
          </div>
          <FileUploadSection onUploadSuccess={handleUploadSuccess} onUploadError={setError} />
          {error && <div className="status-err">{error}</div>}
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              setStarted(true)
              setTab('add')
              setPersonName('Manual entry')
            }}
          >
            Or enter income by hand
          </button>
        </section>
      )}

      {started && (
        <>
          <div className="tabs" role="tablist">
            {(
              [
                ['results', 'Results', null],
                ['income', 'Income', incomeSummary.inflowCount || null],
                ['wealth', 'Wealth', entries.length || null],
                ['hawl', 'Hawl', wealthHistory.length || null],
                ['gold', 'Gold', null],
                ['add', 'Add / upload', null],
              ] as [Tab, string, number | null][]
            ).map(([id, label, count]) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={tab === id}
                title={count ? `${label} (${count})` : label}
                className={`tab ${tab === id ? 'active' : ''}`}
                onClick={() => setTab(id)}
              >
                {label}
                {count ? <span className="tab-count">{count}</span> : null}
              </button>
            ))}
          </div>

          {error && <div className="status-err" style={{ marginBottom: '1rem' }}>{error}</div>}

          {tab === 'results' && (
            <>
              {result ? (
                <>
                  <DashboardCards
                    result={result}
                    income={incomeSummary}
                    inventory={sheetInventory}
                    onGoIncome={() => setTab('income')}
                    onGoWealth={() => setTab('wealth')}
                  />
                  <Charts
                    incomeRows={incomeRows.length ? incomeRows : entries}
                    wealthRows={entries}
                    history={wealthHistory}
                    nisabCad={nisabCad}
                    onPickClass={(cls) => {
                      setIncomeFilter(cls)
                      setTab('income')
                    }}
                    onPickWealth={() => setTab('wealth')}
                    onPickHawl={() => setTab('hawl')}
                  />
                  {parseWarnings.length > 0 && (
                    <div className="banner warn">
                      <h3>From the file</h3>
                      <ul>
                        {parseWarnings.map((w) => (
                          <li key={w}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <CalculationBreakdown result={result} />
                </>
              ) : (
                <section className="card panel">
                  <h2>No zakat figure yet</h2>
                  <p className="sub">
                    {entries.length === 0
                      ? 'Upload a workbook with an Assets sheet, or add wealth by hand.'
                      : 'Calculating…'}
                  </p>
                </section>
              )}
            </>
          )}

          {tab === 'income' && (
            <>
                  {incomeFilter !== 'ALL' && (
                    <button type="button" className="btn" style={{ marginBottom: '0.75rem' }} onClick={() => setIncomeFilter('ALL')} title="Clear the class filter">
                      Show all classes
                    </button>
                  )}
              <TransactionTable
                title="Classified income"
                subtitle={
                  transactions.length
                    ? `${incomeSummary.inflowCount} inflows · total income ${new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(incomeSummary.totalIncome)}. Outflows stay hidden unless you show spending.`
                    : 'Income and items you added by hand. Each row has a classification and a reason.'
                }
                entries={incomeRows.length ? incomeRows : entries}
                incomeOnly={transactions.length > 0}
                forcedFilter={incomeFilter}
              />
            </>
          )}

          {tab === 'wealth' && (
            <TransactionTable
              title="Year-end wealth"
              subtitle="Zakat is calculated from this snapshot, not from adding up income for the year."
              entries={entries}
              debts={debts}
              onRemoveEntry={(id) => {
                const updated = entries.filter((e) => e.id !== id)
                setEntries(updated)
                void executeCalculation(updated, debts, wealthHistory, nisabCad, hawlMaintained, personName)
              }}
              onRemoveDebt={(idx) => {
                const updated = debts.filter((_, i) => i !== idx)
                setDebts(updated)
                void executeCalculation(entries, updated, wealthHistory, nisabCad, hawlMaintained, personName)
              }}
            />
          )}

          {tab === 'hawl' && <WealthHistoryView history={wealthHistory} nisabCad={nisabCad} />}

          {tab === 'gold' && <KaratTool onAddEntry={handleAddManualEntry} />}

          {tab === 'add' && (
            <>
              <FileUploadSection
                compact
                needsConfirm
                onUploadSuccess={handleUploadSuccess}
                onUploadError={setError}
              />
              <div style={{ height: '1rem' }} />
              <ManualEntryForm
                onAddEntry={handleAddManualEntry}
                onAddDebt={handleAddManualDebt}
                nisabCad={nisabCad}
                onNisabChange={setNisabCad}
                hawlMaintained={hawlMaintained}
                onHawlChange={setHawlMaintained}
                onRunCalculation={() => void executeCalculation()}
                isCalculating={isCalculating}
              />
            </>
          )}
        </>
      )}

      <p className="footer-note">
        Educational exercise using the organizer’s Maliki rule set and fixed nisab values. Not a fatwa.
        Unresolved cases belong with a qualified scholar.
      </p>
      <EducationGuide isOpen={guideOpen} onClose={() => setGuideOpen(false)} />
      <ConfirmDialog
        open={resetOpen}
        title="Start over?"
        body="This clears the uploaded file, wealth, debts, and the zakat figure. You will need to upload again."
        confirmLabel="Clear everything"
        cancelLabel="Stay here"
        onCancel={() => setResetOpen(false)}
        onConfirm={() => {
          setResetOpen(false)
          handleReset()
        }}
      />
    </main>
  )
}

export default App

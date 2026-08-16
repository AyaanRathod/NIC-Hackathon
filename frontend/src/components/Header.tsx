import type { ReactNode } from 'react'

interface HeaderProps {
  personName?: string
  onOpenRules: () => void
  onReset: () => void
  showReset: boolean
}

export function Header({ personName, onOpenRules, onReset, showReset }: HeaderProps) {
  return (
    <header className="topbar">
      <div className="brand">
        <h1>Halal Income &amp; Zakat</h1>
        <p>{personName ? personName : 'Maliki calculator'}</p>
      </div>
      <div className="topbar-actions">
        <span className="madhhab-mark">Maliki</span>
        <button type="button" className="btn btn-ghost" onClick={onOpenRules} title="Maliki rules used in this calculator">
          Rules
        </button>
        {showReset && (
          <button type="button" className="btn" onClick={onReset} title="Clear the current file and start again">
            Start over
          </button>
        )}
      </div>
    </header>
  )
}

export function Pill({ children, kind }: { children: ReactNode; kind: string }) {
  const cls =
    kind === 'Halal'
      ? 'pill-halal'
      : kind === 'Haram'
        ? 'pill-haram'
        : kind === 'Mixed'
          ? 'pill-mixed'
          : kind === 'Tentative'
            ? 'pill-tentative'
            : kind === 'Missing Information'
              ? 'pill-missing'
              : 'pill-muted'
  return <span className={`pill ${cls}`}>{children}</span>
}

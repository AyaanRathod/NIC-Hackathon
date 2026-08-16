/** Decorative 8-point lattice. Subject: mosque geometry, not a chart. */
export function LatticeBackground() {
  return (
    <svg className="lattice" aria-hidden="true" focusable="false">
      <defs>
        <pattern id="zakat-lattice" width="84" height="84" patternUnits="userSpaceOnUse">
          <path
            d="M42 6 L48 28 L70 22 L54 40 L76 48 L54 56 L70 74 L48 68 L42 90 L36 68 L14 74 L30 56 L8 48 L30 40 L14 22 L36 28 Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.7"
          />
          <circle cx="42" cy="42" r="3.2" fill="none" stroke="currentColor" strokeWidth="0.6" />
          <path d="M42 0 V18 M42 66 V84 M0 42 H18 M66 42 H84" stroke="currentColor" strokeWidth="0.45" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#zakat-lattice)" />
    </svg>
  )
}

import { useState } from 'react'
import { uploadFinancialFile } from '../api/client'
import type { UploadResponse } from '../types/zakat'
import { ConfirmDialog } from './ConfirmDialog'

interface FileUploadSectionProps {
  compact?: boolean
  needsConfirm?: boolean
  onUploadSuccess: (data: UploadResponse) => void
  onUploadError: (err: string) => void
}

export function FileUploadSection({ compact, needsConfirm, onUploadSuccess, onUploadError }: FileUploadSectionProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [heldFile, setHeldFile] = useState<File | null>(null)

  const processFile = async (file: File) => {
    setIsUploading(true)
    setStatus(null)
    setError(null)
    try {
      const res = await uploadFinancialFile(file)
      setStatus(
        `Read ${res.rows_processed} rows` +
          (res.sheet_inventory?.length
            ? `: ${res.sheet_inventory.map((s) => `${s.sheet} ${s.rows_kept}/${s.rows_in_file}`).join(', ')}.`
            : ` from ${res.filename}.`),
      )
      onUploadSuccess(res)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
      onUploadError(msg)
    } finally {
      setIsUploading(false)
    }
  }

  const takeFile = (file: File | undefined) => {
    if (!file) return
    if (needsConfirm) {
      setHeldFile(file)
      return
    }
    void processFile(file)
  }

  return (
    <div
      className={`dropzone ${dragOver ? 'over' : ''}`}
      role="group"
      aria-label="Upload spreadsheet"
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        takeFile(e.dataTransfer.files?.[0])
      }}
    >
      <div className="drop-glyph" aria-hidden="true">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect x="5" y="3" width="14" height="18" rx="1.5" stroke="currentColor" strokeWidth="1.4" />
          <path d="M19 9h4v16H9v-4" stroke="currentColor" strokeWidth="1.4" />
          <path d="M12 11v7M12 11l-3 3M12 11l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      </div>
      <h3>{compact ? 'Replace spreadsheet' : 'Drop an Excel or CSV file'}</h3>
      <p>
        {dragOver
          ? 'Release to read the whole workbook.'
          : 'Official participant workbooks work as-is. The tool reads every sheet in full. Zakat uses Assets. Income uses Transactions.'}
      </p>
      <div className="file-chips" aria-hidden="true">
        <span>.xlsx</span>
        <span>.xls</span>
        <span>.csv</span>
      </div>
      <label className="btn btn-primary">
        <input
          type="file"
          accept=".xlsx,.xls,.csv"
          hidden
          disabled={isUploading}
          onChange={(e) => {
            takeFile(e.target.files?.[0])
            e.target.value = ''
          }}
        />
        {isUploading ? 'Reading file…' : compact ? 'Choose a replacement' : 'Choose file'}
      </label>
      {status && <div className="status-ok">{status}</div>}
      {error && <div className="status-err">{error}</div>}
      <ConfirmDialog
        open={Boolean(heldFile)}
        title="Replace the current ledger?"
        body={`${heldFile?.name || 'This file'} will replace income, wealth, debts, and the zakat figure.`}
        confirmLabel="Replace"
        cancelLabel="Cancel"
        onCancel={() => setHeldFile(null)}
        onConfirm={() => {
          if (heldFile) void processFile(heldFile)
          setHeldFile(null)
        }}
      />
    </div>
  )
}

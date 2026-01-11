import { useEffect, useMemo, useRef, useState } from 'react'

type Evidence = {
  title: string
  file_path: string
  line_range: string
}

type VariantParams = {
  confidence_range: string
  evidence_source: string
  risk_tolerance: string
  expression_style: string
}

type VariantState = {
  id: string
  label: string
  params: VariantParams
  reply: string
  evidence: Evidence[]
  draft_snapshot?: Record<string, unknown>
  notes: string
  checks: Record<string, boolean>
}

type Preset = {
  name: string
  params: VariantParams
}

type LabProps = {
  open: boolean
  onClose: () => void
  sessionId: string | null
  lastUserMessage: string | null
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8001'
const PRESET_KEY = 'bp_lab_presets'

const DEFAULT_VARIANTS: VariantState[] = [
  {
    id: 'A',
    label: 'Variant A',
    params: {
      confidence_range: 'Balanced',
      evidence_source: 'Product artifacts',
      risk_tolerance: 'Pragmatic',
      expression_style: 'Concrete',
    },
    reply: '',
    evidence: [],
    notes: '',
    checks: {},
  },
  {
    id: 'B',
    label: 'Variant B',
    params: {
      confidence_range: 'Focused',
      evidence_source: 'Product artifacts',
      risk_tolerance: 'Cautious',
      expression_style: 'Concrete',
    },
    reply: '',
    evidence: [],
    notes: '',
    checks: {},
  },
]

const VARIANT_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

const CHECKS = [
  'Clear',
  'Trustworthy',
  'Overconfident',
  'Too cautious',
  'Distracting evidence',
]

const PARAM_OPTIONS: Record<keyof VariantParams, string[]> = {
  confidence_range: ['Focused', 'Balanced', 'Broad'],
  evidence_source: ['Product artifacts', 'Public knowledge', 'Both'],
  risk_tolerance: ['Cautious', 'Pragmatic', 'Adventurous'],
  expression_style: ['Concrete', 'Conversational'],
}

const PARAM_LABELS: Record<keyof VariantParams, { label: string; info: string }> = {
  confidence_range: {
    label: 'Confidence Range',
    info: 'How decisive vs contextual the assistant sounds.',
  },
  evidence_source: {
    label: 'Evidence Source',
    info: 'What the assistant is allowed to base answers on.',
  },
  risk_tolerance: {
    label: 'Risk Tolerance',
    info: 'How easily the assistant refuses vs proceeds.',
  },
  expression_style: {
    label: 'Expression Style',
    info: 'Proof-forward vs smooth readability.',
  },
}

const readPresets = (): Preset[] => {
  try {
    const stored = localStorage.getItem(PRESET_KEY)
    if (!stored) return []
    return JSON.parse(stored) as Preset[]
  } catch {
    return []
  }
}

const writePresets = (presets: Preset[]) => {
  localStorage.setItem(PRESET_KEY, JSON.stringify(presets))
}

export default function ResponseQualityLab({ open, onClose, sessionId, lastUserMessage }: LabProps) {
  const [variants, setVariants] = useState<VariantState[]>(DEFAULT_VARIANTS)
  const [presets, setPresets] = useState<Preset[]>([])
  const variantCountRef = useRef(variants.length)

  useEffect(() => {
    setPresets(readPresets())
  }, [])

  const canRun = useMemo(() => !!sessionId && !!lastUserMessage, [sessionId, lastUserMessage])

  const runVariant = async (variant: VariantState) => {
    if (!sessionId || !lastUserMessage) return
    const response = await fetch(`${API_BASE}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message: lastUserMessage,
        variant: variant.params,
      }),
    })
    const payload = await response.json()
    setVariants((prev) =>
      prev.map((item) =>
        item.id === variant.id
          ? {
              ...item,
              reply: payload.reply || '',
              evidence: payload.evidence || [],
              draft_snapshot: payload.draft_snapshot || undefined,
            }
          : item,
      ),
    )
  }

  const runAll = async () => {
    await Promise.all(variants.map((variant) => runVariant(variant)))
  }

  useEffect(() => {
    if (open && canRun) {
      runAll()
    }
  }, [open, canRun])

  useEffect(() => {
    if (!open || !canRun) {
      variantCountRef.current = variants.length
      return
    }
    if (variants.length > variantCountRef.current) {
      const newVariant = variants[variants.length - 1]
      runVariant(newVariant)
    }
    variantCountRef.current = variants.length
  }, [variants, open, canRun])

  const updateParam = (variantId: string, key: keyof VariantParams, value: string) => {
    setVariants((prev) =>
      prev.map((variant) =>
        variant.id === variantId
          ? { ...variant, params: { ...variant.params, [key]: value } }
          : variant,
      ),
    )
  }

  const applyPreset = (variantId: string, presetName: string) => {
    const preset = presets.find((item) => item.name === presetName)
    if (!preset) return
    setVariants((prev) =>
      prev.map((variant) =>
        variant.id === variantId ? { ...variant, params: preset.params } : variant,
      ),
    )
    const target = variants.find((item) => item.id === variantId)
    if (target) {
      runVariant({ ...target, params: preset.params })
    }
  }

  const savePreset = (variant: VariantState) => {
    const name = window.prompt('Preset name')
    if (!name) return
    const next = [...presets, { name, params: variant.params }]
    setPresets(next)
    writePresets(next)
  }

  const updateChecks = (variantId: string, label: string) => {
    setVariants((prev) =>
      prev.map((variant) =>
        variant.id === variantId
          ? {
              ...variant,
              checks: { ...variant.checks, [label]: !variant.checks[label] },
            }
          : variant,
      ),
    )
  }

  const updateNotes = (variantId: string, value: string) => {
    setVariants((prev) =>
      prev.map((variant) =>
        variant.id === variantId ? { ...variant, notes: value } : variant,
      ),
    )
  }

  const handleParamChange = (variantId: string, key: keyof VariantParams, value: string) => {
    updateParam(variantId, key, value)
    const target = variants.find((item) => item.id === variantId)
    if (target) {
      runVariant({ ...target, params: { ...target.params, [key]: value } })
    }
  }

  const addVariant = () => {
    setVariants((prev) => {
      const nextIndex = prev.length
      const letter = VARIANT_LETTERS[nextIndex] || `V${nextIndex + 1}`
      const newVariant: VariantState = {
        id: `V${nextIndex + 1}`,
        label: `Variant ${letter}`,
        params: {
          confidence_range: 'Balanced',
          evidence_source: 'Product artifacts',
          risk_tolerance: 'Pragmatic',
          expression_style: 'Concrete',
        },
        reply: '',
        evidence: [],
        notes: '',
        checks: {},
      }
      return [...prev, newVariant]
    })
  }

  return (
    <aside className={`lab-drawer ${open ? 'open' : ''}`} aria-hidden={!open}>
      <div className="lab-header">
        <div>
          <p className="lab-title">Response Quality Lab</p>
          <span className="lab-subtitle">Designer view</span>
        </div>
        <div className="lab-header-actions">
          <button className="lab-add" onClick={addVariant} type="button">
            Add variant
          </button>
          <button className="lab-close" onClick={onClose} type="button" aria-label="Close lab">
            ✕
          </button>
        </div>
      </div>

      {!canRun && <p className="lab-empty">Send a message to compare responses.</p>}

      {canRun && (
        <div className="lab-grid">
          {variants.map((variant) => (
            <div key={variant.id} className="lab-panel">
              <div className="lab-panel-header">
                <span>{variant.label}</span>
                <select
                  className="preset-select"
                  onChange={(event) => applyPreset(variant.id, event.target.value)}
                  value=""
                >
                  <option value="">Apply preset</option>
                  {presets.map((preset) => (
                    <option key={preset.name} value={preset.name}>
                      {preset.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="lab-controls">
                {(Object.keys(PARAM_OPTIONS) as Array<keyof VariantParams>).map((key) => (
                  <div key={key} className="control-group">
                    <label>
                      {PARAM_LABELS[key].label}
                      <span>{PARAM_LABELS[key].info}</span>
                    </label>
                    <select
                      value={variant.params[key]}
                      onChange={(event) => handleParamChange(variant.id, key, event.target.value)}
                    >
                      {PARAM_OPTIONS[key].map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              <div className="lab-reply">
                <p>Answer</p>
                <div className="lab-reply-text">{variant.reply || 'Awaiting response...'}</div>
                <details className="evidence-details">
                  <summary className="evidence-summary">
                    ▸ Supporting evidence ({variant.evidence.length})
                  </summary>
                  <div className="evidence-list" role="list">
                    {variant.evidence.map((item, index) => (
                      <div key={`${item.file_path}-${index}`} className="evidence-item" role="listitem">
                        <span className="evidence-title">{item.title}</span>
                        <span className="evidence-path">
                          {item.file_path}:{item.line_range}
                        </span>
                      </div>
                    ))}
                  </div>
                </details>
                {variant.draft_snapshot && (
                  <div className="lab-draft">
                    <p>Draft snapshot</p>
                    <pre>{JSON.stringify(variant.draft_snapshot, null, 2)}</pre>
                  </div>
                )}
              </div>

              <div className="lab-judgment">
                <p>Designer Judgment</p>
                <div className="checklist">
                  {CHECKS.map((label) => (
                    <label key={label} className="check-item">
                      <input
                        type="checkbox"
                        checked={!!variant.checks[label]}
                        onChange={() => updateChecks(variant.id, label)}
                      />
                      {label}
                    </label>
                  ))}
                </div>
                <textarea
                  placeholder="Notes"
                  value={variant.notes}
                  onChange={(event) => updateNotes(variant.id, event.target.value)}
                />
                <button type="button" className="save-preset" onClick={() => savePreset(variant)}>
                  Save as preset
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </aside>
  )
}

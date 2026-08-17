import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

const POINT_FIELDS = [
  { key: 'ecossistema_mapeado', label: 'Ecossistema mapeado', tone: 'orange' },
  { key: 'concorrente_citado', label: 'Concorrente citado', tone: 'red' },
  { key: 'oportunidade', label: 'Oportunidade', tone: 'green' },
  { key: 'retencao_churn', label: 'Retenção / churn', tone: 'red' },
  { key: 'budget', label: 'Budget', tone: 'green' },
  { key: 'persona_detectada', label: 'Persona detectada', tone: 'teal' },
  { key: 'sentimento', label: 'Sentimento', tone: 'teal' },
] as const

const TONE_CLASS: Record<(typeof POINT_FIELDS)[number]['tone'] | 'grey', string> = {
  orange: 'bg-chart-1',
  red: 'bg-chart-2',
  green: 'bg-chart-3',
  teal: 'bg-chart-4',
  grey: 'bg-chart-5',
}

const DEFAULT_VALUE = 'Não identificado'
const DEFAULT_ANALISE = 'Sem análise aprofundada disponível.'

type Point = {
  valor: string
  analise: string
  evidencias: string[]
}

type CardShape = {
  conta?: string
  status?: string
  [key: string]: unknown
}

function normalizeCard(card: unknown): CardShape | null {
  if (!card) return null
  if (typeof card === 'object' && !Array.isArray(card)) {
    return card as CardShape
  }
  if (typeof card === 'string') {
    try {
      const parsed = JSON.parse(card)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed as CardShape
      }
    } catch {
      return null
    }
  }
  return null
}

function normalizePoint(raw: unknown): Point {
  if (typeof raw === 'string') {
    return {
      valor: raw.trim() || DEFAULT_VALUE,
      analise: DEFAULT_ANALISE,
      evidencias: [],
    }
  }
  if (!raw || typeof raw !== 'object') {
    return {
      valor: DEFAULT_VALUE,
      analise: DEFAULT_ANALISE,
      evidencias: [],
    }
  }

  const record = raw as Record<string, unknown>
  const valor =
    String(record.valor || record.value || '').trim() || DEFAULT_VALUE
  const analise = String(record.analise || '').trim() || DEFAULT_ANALISE
  const evidencias = Array.isArray(record.evidencias)
    ? record.evidencias.map((item) => String(item).trim()).filter(Boolean)
    : []

  return { valor, analise, evidencias }
}

export function IntelligenceCard({
  card,
  className,
}: {
  card: unknown
  className?: string
}) {
  const data = normalizeCard(card)
  const [expandedKey, setExpandedKey] = useState<string | null>(null)

  if (!data) return null

  const toggle = (key: string) => {
    setExpandedKey((current) => (current === key ? null : key))
  }

  return (
    <article
      className={cn(
        'mt-2 overflow-hidden rounded-xl border border-border bg-card text-card-foreground shadow-sm',
        className
      )}
    >
      <header className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">Card de Inteligência</h2>
        <p className="text-xs text-muted-foreground">{data.conta || DEFAULT_VALUE}</p>
      </header>

      <ul className="m-0 list-none p-0">
        {POINT_FIELDS.map(({ key, label, tone }) => {
          const point = normalizePoint(data[key])
          const isExpanded = expandedKey === key

          return (
            <li key={key} className="flex items-start gap-3 border-b border-border px-4 py-3.5">
              <span
                className={cn('mt-1.5 size-2.5 shrink-0 rounded-full', TONE_CLASS[tone])}
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1">
                <button
                  type="button"
                  className="flex w-full items-start justify-between gap-3 text-left"
                  aria-expanded={isExpanded}
                  onClick={() => toggle(key)}
                >
                  <span className="flex min-w-0 flex-col gap-0.5">
                    <span className="text-xs text-muted-foreground">{label}</span>
                    <span className="text-sm font-semibold break-words text-foreground">
                      {point.valor}
                    </span>
                  </span>
                  <ChevronDown
                    className={cn(
                      'mt-1 size-4 shrink-0 text-muted-foreground transition-transform',
                      isExpanded && 'rotate-180'
                    )}
                    aria-hidden="true"
                  />
                </button>

                {isExpanded && (
                  <div className="mt-2.5 rounded-lg bg-muted px-3 py-2.5">
                    <p className="text-[13px] leading-relaxed text-foreground">
                      {point.analise}
                    </p>
                    {point.evidencias.length > 0 && (
                      <div className="mt-2.5">
                        <span className="mb-1.5 block text-[11px] tracking-wide text-muted-foreground uppercase">
                          Evidências
                        </span>
                        <ul className="m-0 list-disc space-y-1 pl-4">
                          {point.evidencias.map((item, index) => (
                            <li
                              key={`${key}-ev-${index}`}
                              className="text-xs leading-snug text-muted-foreground"
                            >
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </li>
          )
        })}

        <li className="flex items-start gap-3 px-4 py-3.5">
          <span
            className={cn('mt-1.5 size-2.5 shrink-0 rounded-full', TONE_CLASS.grey)}
            aria-hidden="true"
          />
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="text-xs text-muted-foreground">Status</span>
            <span className="text-sm font-semibold text-foreground">
              {data.status || 'Pendente revisão humana'}
            </span>
          </div>
        </li>
      </ul>
    </article>
  )
}

export default IntelligenceCard

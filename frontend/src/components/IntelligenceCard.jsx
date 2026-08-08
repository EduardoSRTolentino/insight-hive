import { useState } from 'react'

const POINT_FIELDS = [
  { key: 'ecossistema_mapeado', label: 'Ecossistema mapeado', tone: 'orange' },
  { key: 'concorrente_citado', label: 'Concorrente citado', tone: 'red' },
  { key: 'oportunidade', label: 'Oportunidade', tone: 'green' },
  { key: 'persona_detectada', label: 'Persona detectada', tone: 'teal' },
  { key: 'sentimento', label: 'Sentimento', tone: 'teal' },
]

const DEFAULT_VALUE = 'Não identificado'
const DEFAULT_ANALISE = 'Sem análise aprofundada disponível.'

function normalizeCard(card) {
  if (!card) return null
  if (typeof card === 'object' && !Array.isArray(card)) return card
  if (typeof card === 'string') {
    try {
      const parsed = JSON.parse(card)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed
      }
    } catch {
      return null
    }
  }
  return null
}

function normalizePoint(raw) {
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
  const valor = (raw.valor || raw.value || '').trim() || DEFAULT_VALUE
  const analise = (raw.analise || '').trim() || DEFAULT_ANALISE
  const evidencias = Array.isArray(raw.evidencias)
    ? raw.evidencias.map((item) => String(item).trim()).filter(Boolean)
    : []
  return { valor, analise, evidencias }
}

export default function IntelligenceCard({ card }) {
  const data = normalizeCard(card)
  const [expandedKey, setExpandedKey] = useState(null)

  if (!data) return null

  const toggle = (key) => {
    setExpandedKey((current) => (current === key ? null : key))
  }

  return (
    <article className="intelligence-card">
      <header className="intelligence-card-header">
        <h2>Card de Inteligência</h2>
        <p className="intelligence-card-conta">{data.conta || DEFAULT_VALUE}</p>
      </header>

      <ul className="intelligence-card-list">
        {POINT_FIELDS.map(({ key, label, tone }) => {
          const point = normalizePoint(data[key])
          const isExpanded = expandedKey === key

          return (
            <li key={key} className={`intelligence-card-item${isExpanded ? ' is-expanded' : ''}`}>
              <span className={`intelligence-card-dot tone-${tone}`} aria-hidden="true" />
              <div className="intelligence-card-body">
                <button
                  type="button"
                  className="intelligence-card-trigger"
                  aria-expanded={isExpanded}
                  onClick={() => toggle(key)}
                >
                  <span className="intelligence-card-trigger-text">
                    <span className="intelligence-card-label">{label}</span>
                    <span className="intelligence-card-value">{point.valor}</span>
                  </span>
                  <span className="intelligence-card-chevron" aria-hidden="true" />
                </button>

                {isExpanded && (
                  <div className="intelligence-card-detail">
                    <p className="intelligence-card-analise">{point.analise}</p>
                    {point.evidencias.length > 0 && (
                      <div className="intelligence-card-evidencias">
                        <span className="intelligence-card-evidencias-label">Evidências</span>
                        <ul>
                          {point.evidencias.map((item, index) => (
                            <li key={`${key}-ev-${index}`}>{item}</li>
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

        <li className="intelligence-card-item intelligence-card-item-static">
          <span className="intelligence-card-dot tone-grey" aria-hidden="true" />
          <div className="intelligence-card-body">
            <span className="intelligence-card-label">Status</span>
            <span className="intelligence-card-value">
              {data.status || 'Pendente revisão humana'}
            </span>
          </div>
        </li>
      </ul>
    </article>
  )
}

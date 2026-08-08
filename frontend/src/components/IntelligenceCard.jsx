const CARD_FIELDS = [
  { key: 'ecossistema_mapeado', label: 'Ecossistema mapeado', tone: 'orange' },
  { key: 'concorrente_citado', label: 'Concorrente citado', tone: 'red' },
  { key: 'oportunidade', label: 'Oportunidade', tone: 'green' },
  { key: 'persona_detectada', label: 'Persona detectada', tone: 'teal' },
  { key: 'sentimento', label: 'Sentimento', tone: 'teal' },
  { key: 'status', label: 'Status', tone: 'grey' },
]

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

export default function IntelligenceCard({ card }) {
  const data = normalizeCard(card)
  if (!data) return null

  return (
    <article className="intelligence-card">
      <header className="intelligence-card-header">
        <h2>Card de Inteligência</h2>
        <p className="intelligence-card-conta">{data.conta || 'Não identificado'}</p>
      </header>

      <ul className="intelligence-card-list">
        {CARD_FIELDS.map(({ key, label, tone }) => (
          <li key={key} className="intelligence-card-item">
            <span className={`intelligence-card-dot tone-${tone}`} aria-hidden="true" />
            <div className="intelligence-card-body">
              <span className="intelligence-card-label">{label}</span>
              <span className="intelligence-card-value">
                {data[key] || 'Não identificado'}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </article>
  )
}

import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { IntelligenceCard } from '@/components/intelligence-card'

describe('IntelligenceCard', () => {
  it('renders retention and budget axes', () => {
    render(
      <IntelligenceCard
        card={{
          conta: 'Acme',
          retencao_churn: { valor: 'Baixo risco', analise: 'Sem sinal de saída.', evidencias: [] },
          budget: { valor: 'R$ 50 mil', analise: 'Citou teto anual.', evidencias: [] },
        }}
      />,
    )
    expect(screen.getByText('Retenção / churn')).toBeInTheDocument()
    expect(screen.getByText('Baixo risco')).toBeInTheDocument()
    expect(screen.getByText('Budget')).toBeInTheDocument()
    expect(screen.getByText('R$ 50 mil')).toBeInTheDocument()
  })
})

import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MeetingResult } from '@/components/meeting-result'

describe('MeetingResult', () => {
  it('renders triage, agents and the intelligence card', () => {
    render(
      <MeetingResult
        triage="Cliente em avaliação."
        selected_agents={['ecossistema_totvs']}
        final_report={{ conta: 'Acme' }}
        description="meeting.json · agora"
      />,
    )
    expect(screen.getByText('Cliente em avaliação.')).toBeInTheDocument()
    expect(screen.getByText('ecossistema_totvs')).toBeInTheDocument()
    expect(screen.getByText('meeting.json · agora')).toBeInTheDocument()
    expect(screen.getByText('Card de Inteligência')).toBeInTheDocument()
    expect(screen.getByText('Acme')).toBeInTheDocument()
  })
})

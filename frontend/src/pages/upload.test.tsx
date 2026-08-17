import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import MockAdapter from 'axios-mock-adapter'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { analysisJobOptions } from '@/lib/analysis-job'
import client from '@/lib/api'
import UploadPage from '@/pages/upload'
import type { ClientListItem, MeetingDetail } from '@/lib/types'

vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    token: 'test-token',
    user: null,
    ready: true,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  }),
}))

const acme: ClientListItem = {
  id: 1,
  name: 'Acme',
  created_at: '2026-08-16T00:00:00Z',
  meetings_count: 0,
  last_meeting_at: null,
  segment: null,
  company_size: null,
  website: null,
  city: null,
  state: null,
  contact_name: null,
  contact_role: null,
  contact_email: null,
  contact_phone: null,
  owner: null,
  status: 'prospect',
  notes: null,
}

const meeting: MeetingDetail = {
  id: 9,
  client_id: 1,
  client_name: 'Acme',
  source_filename: 'meeting.json',
  created_at: '2026-08-16T00:00:00Z',
  triage: 'Cliente em avaliação.',
  selected_agents: ['ecossistema_totvs'],
  final_report: { conta: 'Acme' },
}

describe('UploadPage', () => {
  const mock = new MockAdapter(client)

  beforeEach(() => {
    analysisJobOptions.pollIntervalMs = 10
    mock.reset()
    mock.onGet('/clients').reply(200, [acme])
  })

  afterEach(() => {
    analysisJobOptions.pollIntervalMs = 1500
    mock.reset()
  })

  it('uploads a file, polls the job and shows the meeting result', async () => {
    mock.onPost('/analysis/upload').reply(202, {
      id: 3,
      status: 'queued',
      source_filename: 'meeting.json',
      created_at: '2026-08-16T00:00:00Z',
      error_detail: null,
      meeting: null,
    })
    mock.onGet('/analysis/jobs/3').reply(200, {
      id: 3,
      status: 'done',
      source_filename: 'meeting.json',
      created_at: '2026-08-16T00:00:00Z',
      error_detail: null,
      meeting,
    })

    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    )

    const select = await screen.findByLabelText('Cliente')
    fireEvent.change(select, { target: { value: '1' } })

    const file = new File(['[{"speaker":"A","text":"oi"}]'], 'meeting.json', {
      type: 'application/json',
    })
    fireEvent.change(screen.getByLabelText('Arquivo'), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Analisar' }))

    await waitFor(() => {
      expect(screen.getByText('Cliente em avaliação.')).toBeInTheDocument()
    })
    expect(screen.getByText('Card de Inteligência')).toBeInTheDocument()
  })
})

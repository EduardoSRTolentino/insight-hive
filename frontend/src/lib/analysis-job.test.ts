import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { analysisJobOptions, runAnalysisUpload } from '@/lib/analysis-job'
import client from '@/lib/api'
import type { AnalysisJob, MeetingDetail } from '@/lib/types'

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

function job(partial: Partial<AnalysisJob>): AnalysisJob {
  return {
    id: 3,
    status: 'queued',
    source_filename: 'meeting.json',
    created_at: '2026-08-16T00:00:00Z',
    error_detail: null,
    meeting: null,
    ...partial,
  }
}

describe('runAnalysisUpload', () => {
  const mock = new MockAdapter(client)

  beforeEach(() => {
    analysisJobOptions.pollIntervalMs = 10
    mock.reset()
  })

  afterEach(() => {
    analysisJobOptions.pollIntervalMs = 1500
    mock.reset()
  })

  it('polls until the job is done and returns the meeting', async () => {
    mock.onPost('/analysis/upload').reply(202, job({ status: 'queued' }))
    mock.onGet('/analysis/jobs/3').replyOnce(200, job({ status: 'running' }))
    mock.onGet('/analysis/jobs/3').replyOnce(200, job({ status: 'done', meeting }))

    const form = new FormData()
    form.append('client_id', '1')
    const onStatusChange = vi.fn()
    const result = await runAnalysisUpload(form, { onStatusChange })
    expect(result.triage).toBe('Cliente em avaliação.')
    expect(result.id).toBe(9)
    expect(onStatusChange.mock.calls.map((call) => call[0])).toEqual([
      'queued',
      'running',
      'done',
    ])
  })

  it('throws the job error_detail when the analysis fails', async () => {
    mock.onPost('/analysis/upload').reply(
      202,
      job({ status: 'failed', error_detail: 'Ollama fora do ar.' }),
    )
    await expect(runAnalysisUpload(new FormData())).rejects.toThrow('Ollama fora do ar.')
  })

  it('tolerates a couple of transient poll failures', async () => {
    mock.onPost('/analysis/upload').reply(202, job({ status: 'queued' }))
    mock.onGet('/analysis/jobs/3').networkErrorOnce()
    mock.onGet('/analysis/jobs/3').replyOnce(502)
    mock.onGet('/analysis/jobs/3').replyOnce(200, job({ status: 'done', meeting }))

    const result = await runAnalysisUpload(new FormData())
    expect(result.id).toBe(9)
  })

  it('gives up after too many consecutive poll failures', async () => {
    mock.onPost('/analysis/upload').reply(202, job({ status: 'queued' }))
    mock.onGet('/analysis/jobs/3').networkError()

    await expect(runAnalysisUpload(new FormData())).rejects.toThrow(
      'Não foi possível acompanhar a análise. Confira o histórico do cliente — ela pode ter concluído mesmo assim.',
    )
  })
})

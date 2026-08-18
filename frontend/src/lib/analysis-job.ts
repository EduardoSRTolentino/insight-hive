import axios from 'axios'
import client, { ANALYSIS_UPLOAD_TIMEOUT_MS } from '@/lib/api'
import type { AnalysisJob, MeetingDetail } from '@/lib/types'

export const analysisJobOptions = {
  pollIntervalMs: 1500,
}

const MAX_CONSECUTIVE_POLL_FAILURES = 3
const MAX_POLL_INTERVAL_MS = 10_000
const POLL_BACKOFF = 1.3

function sleep(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(signal.reason ?? new DOMException('Aborted', 'AbortError'))
      return
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      clearTimeout(timer)
      reject(signal?.reason ?? new DOMException('Aborted', 'AbortError'))
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

function pollDelay(attempt: number) {
  return Math.min(
    analysisJobOptions.pollIntervalMs * POLL_BACKOFF ** attempt,
    MAX_POLL_INTERVAL_MS,
  )
}

export type RunAnalysisUploadOptions = {
  signal?: AbortSignal
  onStatusChange?: (status: AnalysisJob['status']) => void
}

export async function runAnalysisUpload(
  formData: FormData,
  options: RunAnalysisUploadOptions = {},
): Promise<MeetingDetail> {
  const { signal, onStatusChange } = options
  const deadline = Date.now() + ANALYSIS_UPLOAD_TIMEOUT_MS
  const created = await client.post<AnalysisJob>('/analysis/upload', formData, {
    timeout: 60_000,
    signal,
  })
  let job = created.data
  onStatusChange?.(job.status)

  let consecutiveFailures = 0
  let attempt = 0

  while (job.status === 'queued' || job.status === 'running') {
    if (Date.now() > deadline) {
      throw new Error('A análise demorou demais. Tente novamente.')
    }
    await sleep(pollDelay(attempt), signal)
    attempt += 1
    try {
      const polled = await client.get<AnalysisJob>(`/analysis/jobs/${job.id}`, { signal })
      job = polled.data
      consecutiveFailures = 0
      onStatusChange?.(job.status)
    } catch (err) {
      if (axios.isCancel(err) || signal?.aborted) {
        throw err
      }
      consecutiveFailures += 1
      if (consecutiveFailures >= MAX_CONSECUTIVE_POLL_FAILURES) {
        throw new Error(
          'Não foi possível acompanhar a análise. Confira o histórico do cliente — ela pode ter concluído mesmo assim.',
        )
      }
    }
  }

  if (job.status === 'failed') {
    throw new Error(job.error_detail || 'Falha na análise.')
  }
  if (!job.meeting) {
    throw new Error('A análise terminou sem resultado.')
  }
  return job.meeting
}

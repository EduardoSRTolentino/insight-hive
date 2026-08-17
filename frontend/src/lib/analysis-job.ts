import client, { ANALYSIS_UPLOAD_TIMEOUT_MS } from '@/lib/api'
import type { AnalysisJob, MeetingDetail } from '@/lib/types'

export const analysisJobOptions = {
  pollIntervalMs: 1500,
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function runAnalysisUpload(formData: FormData): Promise<MeetingDetail> {
  const deadline = Date.now() + ANALYSIS_UPLOAD_TIMEOUT_MS
  const created = await client.post<AnalysisJob>('/analysis/upload', formData, {
    timeout: 60_000,
  })
  let job = created.data

  while (job.status === 'queued' || job.status === 'running') {
    if (Date.now() > deadline) {
      throw new Error('A análise demorou demais. Tente novamente.')
    }
    await sleep(analysisJobOptions.pollIntervalMs)
    const polled = await client.get<AnalysisJob>(`/analysis/jobs/${job.id}`)
    job = polled.data
  }

  if (job.status === 'failed') {
    throw new Error(job.error_detail || 'Falha na análise.')
  }
  if (!job.meeting) {
    throw new Error('A análise terminou sem resultado.')
  }
  return job.meeting
}

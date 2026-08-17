export type ClientStatus = 'prospect' | 'ativo' | 'inativo'
export type CompanySize = 'pme' | 'media' | 'enterprise'

export type ClientProfile = {
  segment: string | null
  company_size: CompanySize | null
  website: string | null
  city: string | null
  state: string | null
  contact_name: string | null
  contact_role: string | null
  contact_email: string | null
  contact_phone: string | null
  owner: string | null
  status: ClientStatus
  notes: string | null
}

export type ClientListItem = ClientProfile & {
  id: number
  name: string
  created_at: string
  meetings_count: number
  last_meeting_at: string | null
}

export type MeetingSummary = {
  id: number
  source_filename: string
  created_at: string
  conta: string
  status: string
}

export type ClientDetail = ClientProfile & {
  id: number
  name: string
  created_at: string
  meetings: MeetingSummary[]
}

export type MeetingDetail = {
  id: number
  client_id: number
  client_name: string
  source_filename: string
  created_at: string
  triage: string
  selected_agents: string[]
  final_report: unknown
}

export type AnalysisJobStatus = 'queued' | 'running' | 'done' | 'failed'

export type AnalysisJob = {
  id: number
  status: AnalysisJobStatus
  source_filename: string
  created_at: string
  error_detail: string | null
  meeting: MeetingDetail | null
}

export type ClientPayload = {
  name: string
  segment?: string | null
  company_size?: CompanySize | null
  website?: string | null
  city?: string | null
  state?: string | null
  contact_name?: string | null
  contact_role?: string | null
  contact_email?: string | null
  contact_phone?: string | null
  owner?: string | null
  status?: ClientStatus
  notes?: string | null
}

export const CLIENT_STATUSES: { value: ClientStatus; label: string }[] = [
  { value: 'prospect', label: 'Prospect' },
  { value: 'ativo', label: 'Ativo' },
  { value: 'inativo', label: 'Inativo' },
]

export const COMPANY_SIZES: { value: CompanySize; label: string }[] = [
  { value: 'pme', label: 'PME' },
  { value: 'media', label: 'Média' },
  { value: 'enterprise', label: 'Enterprise' },
]

export function statusLabel(status: string | null | undefined) {
  return CLIENT_STATUSES.find((item) => item.value === status)?.label ?? 'Prospect'
}

export function companySizeLabel(size: string | null | undefined) {
  return COMPANY_SIZES.find((item) => item.value === size)?.label ?? null
}

export type UserProfile = {
  id: number
  email: string
  full_name: string
  company: string | null
  job_title: string | null
  department: string | null
  phone: string | null
  city: string | null
  state: string | null
  linkedin_url: string | null
  bio: string | null
  created_at: string
}

export type UserRegisterPayload = {
  full_name: string
  email: string
  password: string
  company?: string | null
  job_title?: string | null
  department?: string | null
  phone?: string | null
  city?: string | null
  state?: string | null
  linkedin_url?: string | null
  bio?: string | null
}

export type UserUpdatePayload = Omit<UserRegisterPayload, 'password'>

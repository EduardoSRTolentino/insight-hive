import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Trash2 } from 'lucide-react'
import { ClientForm } from '@/components/client-form'
import IntelligenceCard from '@/components/intelligence-card'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import client, { apiErrorMessage, isUnauthorized } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import {
  companySizeLabel,
  statusLabel,
  type ClientDetail,
  type ClientPayload,
  type MeetingDetail,
} from '@/lib/types'
import { cn, formatDateTime } from '@/lib/utils'

function display(value: string | null | undefined) {
  return value?.trim() || '—'
}

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { token, logout } = useAuth()
  const clientId = Number(id)
  const meetingFromUrl = searchParams.get('meeting')

  const [detail, setDetail] = useState<ClientDetail | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(
    meetingFromUrl ? Number(meetingFromUrl) : null
  )
  const [meeting, setMeeting] = useState<MeetingDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [meetingLoading, setMeetingLoading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (meetingFromUrl) {
      const parsed = Number(meetingFromUrl)
      if (!Number.isNaN(parsed)) {
        setSelectedId(parsed)
      }
    }
  }, [meetingFromUrl])

  useEffect(() => {
    if (!token || Number.isNaN(clientId)) return
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await client.get<ClientDetail>(`/clients/${clientId}`)
        if (!cancelled) {
          setDetail(response.data)
        }
      } catch (err: unknown) {
        if (cancelled) return
        if (isUnauthorized(err)) {
          logout()
          navigate('/login')
          return
        }
        setError(apiErrorMessage(err, 'Não foi possível carregar o cliente.'))
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [token, clientId, logout, navigate])

  useEffect(() => {
    if (!token || !selectedId) {
      setMeeting(null)
      return
    }
    let cancelled = false

    const loadMeeting = async () => {
      setMeetingLoading(true)
      try {
        const response = await client.get<MeetingDetail>(`/meetings/${selectedId}`)
        if (!cancelled) {
          if (response.data.client_id !== clientId) {
            setError('Reunião não pertence a este cliente.')
            setMeeting(null)
            return
          }
          setMeeting(response.data)
        }
      } catch (err: unknown) {
        if (cancelled) return
        if (isUnauthorized(err)) {
          logout()
          navigate('/login')
          return
        }
        setError(apiErrorMessage(err, 'Não foi possível carregar a reunião.'))
        setMeeting(null)
      } finally {
        if (!cancelled) {
          setMeetingLoading(false)
        }
      }
    }

    void loadMeeting()
    return () => {
      cancelled = true
    }
  }, [token, selectedId, clientId, logout, navigate])

  const selectMeeting = (meetingId: number) => {
    setSelectedId(meetingId)
    navigate(`/clients/${clientId}?meeting=${meetingId}`, { replace: true })
  }

  const handleDelete = async (meetingId: number) => {
    if (!window.confirm('Remover esta reunião do histórico?')) return
    try {
      await client.delete(`/meetings/${meetingId}`)
      setDetail((current) =>
        current
          ? { ...current, meetings: current.meetings.filter((item) => item.id !== meetingId) }
          : current
      )
      if (selectedId === meetingId) {
        setSelectedId(null)
        setMeeting(null)
        navigate(`/clients/${clientId}`, { replace: true })
      }
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        logout()
        navigate('/login')
        return
      }
      setError(apiErrorMessage(err, 'Não foi possível remover a reunião.'))
    }
  }

  const handleUpdate = async (payload: ClientPayload) => {
    try {
      const response = await client.patch<ClientDetail>(`/clients/${clientId}`, payload)
      setDetail(response.data)
      setEditing(false)
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        logout()
        navigate('/login')
        return
      }
      throw new Error(apiErrorMessage(err, 'Não foi possível atualizar o cliente.'))
    }
  }

  const location = [detail?.city, detail?.state].filter(Boolean).join(' / ')

  return (
    <>
      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-20 w-full rounded-xl" />
          <Skeleton className="h-20 w-full rounded-xl" />
        </div>
      )}

      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

      {detail && (
        <>
          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">{detail.name}</h1>
              <p className="mt-1 text-sm text-gray-500">
                {statusLabel(detail.status)}
                {detail.segment ? ` · ${detail.segment}` : ''}
                {' · '}
                {detail.meetings.length === 1
                  ? '1 reunião'
                  : `${detail.meetings.length} reuniões`}
              </p>
            </div>
            <Button
              asChild
              className="rounded-full bg-orange-600 text-white hover:bg-orange-700"
            >
              <Link to={`/upload?client=${detail.id}`}>Nova análise</Link>
            </Button>
          </div>

          <Card className="mb-8">
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle>Ficha da conta</CardTitle>
                <CardDescription>Contexto usado para acompanhar o cliente.</CardDescription>
              </div>
              {!editing && (
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-full"
                  onClick={() => setEditing(true)}
                >
                  Editar
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {editing ? (
                <ClientForm
                  initial={detail}
                  submitLabel="Salvar"
                  pendingLabel="Salvando..."
                  onSubmit={handleUpdate}
                  onCancel={() => setEditing(false)}
                />
              ) : (
                <dl className="grid gap-3 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-gray-500">Porte</dt>
                    <dd className="font-medium text-gray-900">
                      {companySizeLabel(detail.company_size) ?? '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Dono interno</dt>
                    <dd className="font-medium text-gray-900">{display(detail.owner)}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Website</dt>
                    <dd className="font-medium text-gray-900">
                      {detail.website ? (
                        <a
                          href={
                            detail.website.startsWith('http')
                              ? detail.website
                              : `https://${detail.website}`
                          }
                          target="_blank"
                          rel="noreferrer"
                          className="text-orange-600 hover:text-orange-700"
                        >
                          {detail.website}
                        </a>
                      ) : (
                        '—'
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Cidade / UF</dt>
                    <dd className="font-medium text-gray-900">{location || '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Contato</dt>
                    <dd className="font-medium text-gray-900">
                      {detail.contact_name
                        ? `${detail.contact_name}${detail.contact_role ? ` · ${detail.contact_role}` : ''}`
                        : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">E-mail / telefone</dt>
                    <dd className="font-medium text-gray-900">
                      {[detail.contact_email, detail.contact_phone].filter(Boolean).join(' · ') || '—'}
                    </dd>
                  </div>
                  {detail.notes && (
                    <div className="sm:col-span-2">
                      <dt className="text-gray-500">Observações</dt>
                      <dd className="whitespace-pre-wrap font-medium text-gray-900">{detail.notes}</dd>
                    </div>
                  )}
                </dl>
              )}
            </CardContent>
          </Card>

          {detail.meetings.length === 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Nenhuma reunião ainda</CardTitle>
                <CardDescription>
                  Importe um arquivo para começar o histórico deste cliente.
                </CardDescription>
              </CardHeader>
            </Card>
          )}

          <ol className="relative space-y-3 border-l border-gray-200 pl-6">
            {detail.meetings.map((item) => {
              const active = selectedId === item.id
              return (
                <li key={item.id} className="relative">
                  <span
                    className={cn(
                      'absolute top-5 -left-[1.9rem] size-2.5 rounded-full',
                      active ? 'bg-orange-500' : 'bg-gray-300'
                    )}
                    aria-hidden="true"
                  />
                  <div
                    className={cn(
                      'flex items-start justify-between gap-3 rounded-xl border px-4 py-3',
                      active ? 'border-orange-200 bg-orange-50/50' : 'border-gray-200 bg-white'
                    )}
                  >
                    <button
                      type="button"
                      className="min-w-0 flex-1 text-left"
                      onClick={() => selectMeeting(item.id)}
                    >
                      <p className="text-sm font-medium text-gray-900">
                        {formatDateTime(item.created_at)}
                      </p>
                      <p className="mt-0.5 truncate text-xs text-gray-500">
                        {item.source_filename || 'Arquivo sem nome'}
                        {' · '}
                        {item.status}
                      </p>
                    </button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="shrink-0 text-gray-400 hover:text-red-600"
                      onClick={() => void handleDelete(item.id)}
                      aria-label="Remover reunião"
                    >
                      <Trash2 />
                    </Button>
                  </div>
                </li>
              )
            })}
          </ol>

          {meetingLoading && (
            <div className="mt-8 space-y-3">
              <Skeleton className="h-24 w-full rounded-xl" />
              <Skeleton className="h-40 w-full rounded-xl" />
            </div>
          )}

          {meeting && !meetingLoading && (
            <div className="mt-8 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Triagem</CardTitle>
                  <CardDescription>
                    {meeting.source_filename} · {formatDateTime(meeting.created_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed text-gray-700">
                    {meeting.triage}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Agentes selecionados</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-700">
                    {meeting.selected_agents?.join(', ') || '—'}
                  </p>
                </CardContent>
              </Card>

              <IntelligenceCard card={meeting.final_report} />
            </div>
          )}
        </>
      )}
    </>
  )
}

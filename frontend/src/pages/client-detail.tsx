import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Trash2 } from 'lucide-react'
import { ClientForm } from '@/components/client-form'
import { MeetingResult } from '@/components/meeting-result'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import client, { apiErrorMessage } from '@/lib/api'
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
  const { token } = useAuth()
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
    if (Number.isNaN(clientId)) {
      setError('Cliente inválido.')
      setLoading(false)
      return
    }
    if (!token) return
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
  }, [token, clientId])

  useEffect(() => {
    if (!token || !selectedId || Number.isNaN(clientId)) {
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
  }, [token, selectedId, clientId])

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
      setError(apiErrorMessage(err, 'Não foi possível remover a reunião.'))
    }
  }

  const handleUpdate = async (payload: ClientPayload) => {
    try {
      const response = await client.patch<ClientDetail>(`/clients/${clientId}`, payload)
      setDetail(response.data)
      setEditing(false)
    } catch (err: unknown) {
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

      {error && (
        <p role="alert" className="mb-4 text-sm text-destructive">
          {error}
        </p>
      )}

      {detail && (
        <>
          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">{detail.name}</h1>
              <p className="mt-1 text-sm text-muted-foreground">
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
              className="rounded-full"
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
                    <dt className="text-muted-foreground">Porte</dt>
                    <dd className="font-medium text-foreground">
                      {companySizeLabel(detail.company_size) ?? '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Dono interno</dt>
                    <dd className="font-medium text-foreground">{display(detail.owner)}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Website</dt>
                    <dd className="font-medium text-foreground">
                      {detail.website ? (
                        <a
                          href={
                            detail.website.startsWith('http')
                              ? detail.website
                              : `https://${detail.website}`
                          }
                          target="_blank"
                          rel="noreferrer"
                          className="text-primary hover:text-primary/90"
                        >
                          {detail.website}
                        </a>
                      ) : (
                        '—'
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Cidade / UF</dt>
                    <dd className="font-medium text-foreground">{location || '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Contato</dt>
                    <dd className="font-medium text-foreground">
                      {detail.contact_name
                        ? `${detail.contact_name}${detail.contact_role ? ` · ${detail.contact_role}` : ''}`
                        : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">E-mail / telefone</dt>
                    <dd className="font-medium text-foreground">
                      {[detail.contact_email, detail.contact_phone].filter(Boolean).join(' · ') || '—'}
                    </dd>
                  </div>
                  {detail.notes && (
                    <div className="sm:col-span-2">
                      <dt className="text-muted-foreground">Observações</dt>
                      <dd className="whitespace-pre-wrap font-medium text-foreground">{detail.notes}</dd>
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

          <ol className="relative space-y-3 border-l border-border pl-6">
            {detail.meetings.map((item) => {
              const active = selectedId === item.id
              return (
                <li key={item.id} className="relative">
                  <span
                    className={cn(
                      'absolute top-5 -left-[1.9rem] size-2.5 rounded-full',
                      active ? 'bg-primary' : 'bg-border'
                    )}
                    aria-hidden="true"
                  />
                  <div
                    className={cn(
                      'flex items-start justify-between gap-3 rounded-xl border px-4 py-3',
                      active ? 'border-primary/30 bg-accent' : 'border-border bg-card'
                    )}
                  >
                    <button
                      type="button"
                      className="min-w-0 flex-1 text-left"
                      onClick={() => selectMeeting(item.id)}
                    >
                      <p className="text-sm font-medium text-foreground">
                        {formatDateTime(item.created_at)}
                      </p>
                      <p className="mt-0.5 truncate text-xs text-muted-foreground">
                        {item.source_filename || 'Arquivo sem nome'}
                        {' · '}
                        {item.status}
                      </p>
                    </button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="shrink-0 text-muted-foreground hover:text-destructive"
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
            <MeetingResult
              triage={meeting.triage}
              selected_agents={meeting.selected_agents}
              final_report={meeting.final_report}
              description={`${meeting.source_filename} · ${formatDateTime(meeting.created_at)}`}
            />
          )}
        </>
      )}
    </>
  )
}

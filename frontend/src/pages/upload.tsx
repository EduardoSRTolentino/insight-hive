import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import IntelligenceCard from '@/components/intelligence-card'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import client, { apiErrorMessage, isUnauthorized } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import type { ClientListItem, MeetingDetail } from '@/lib/types'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [clients, setClients] = useState<ClientListItem[]>([])
  const [clientsLoading, setClientsLoading] = useState(true)
  const [clientId, setClientId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<MeetingDetail | null>(null)
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselected = searchParams.get('client')

  useEffect(() => {
    if (!token) return
    let cancelled = false

    const loadClients = async () => {
      setClientsLoading(true)
      try {
        const response = await client.get<ClientListItem[]>('/clients')
        if (cancelled) return
        setClients(response.data)
        const validPreselect =
          preselected && response.data.some((item) => String(item.id) === preselected)
        if (validPreselect) {
          setClientId(preselected)
        }
      } catch (err: unknown) {
        if (cancelled) return
        if (isUnauthorized(err)) {
          logout()
          navigate('/login')
          return
        }
        setError(apiErrorMessage(err, 'Não foi possível carregar os clientes.'))
      } finally {
        if (!cancelled) {
          setClientsLoading(false)
        }
      }
    }

    void loadClients()
    return () => {
      cancelled = true
    }
  }, [token, preselected, logout, navigate])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!file) {
      setError('Selecione um arquivo .csv ou .json.')
      return
    }
    if (!clientId) {
      setError('Selecione um cliente antes de analisar.')
      return
    }

    setError('')
    setResult(null)
    setLoading(true)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('client_id', clientId)

    try {
      const response = await client.post<MeetingDetail>('/analysis/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(response.data)
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        logout()
        navigate('/login')
        return
      }
      setError(apiErrorMessage(err, 'Erro ao processar o arquivo.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Nova análise</CardTitle>
          <CardDescription>
            Escolha um cliente já cadastrado e um arquivo .csv ou .json. O
            resultado fica salvo no histórico da conta.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {clientsLoading ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-9 w-full rounded-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-10 w-full rounded-full" />
              </div>
              <Skeleton className="h-9 w-28 rounded-full" />
            </div>
          ) : clients.length === 0 ? (
            <p className="text-sm text-gray-600">
              Nenhum cliente cadastrado.{' '}
              <Link to="/clients/new" className="font-medium text-orange-600 hover:text-orange-700">
                Criar cliente
              </Link>
            </p>
          ) : (
            <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="client">Cliente</Label>
                <select
                  id="client"
                  value={clientId}
                  onChange={(event) => setClientId(event.target.value)}
                  className="border-input h-9 w-full rounded-full border bg-transparent px-3 text-sm text-gray-900 outline-none focus-visible:border-orange-500 focus-visible:ring-[3px] focus-visible:ring-orange-500/50"
                >
                  <option value="">Selecione um cliente</option>
                  {clients.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="file">Arquivo</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".csv,.json"
                  onChange={(event) => {
                    setFile(event.target.files?.[0] || null)
                    setResult(null)
                    setError('')
                  }}
                  className="h-auto cursor-pointer rounded-full py-2 file:mr-4 file:rounded-full file:border-0 file:bg-orange-50 file:px-4 file:py-1 file:text-sm file:font-medium file:text-orange-700"
                />
              </div>

              <Button
                type="submit"
                disabled={loading || !file || !clientId}
                className="rounded-full bg-orange-600 text-white hover:bg-orange-700"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" />
                    Analisando...
                  </>
                ) : (
                  'Analisar'
                )}
              </Button>
            </form>
          )}

          {loading && (
            <div className="mt-6 space-y-3">
              <p className="text-sm text-gray-500">
                A análise pode levar algum tempo, pois roda o modelo de
                linguagem localmente. Aguarde...
              </p>
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-40 w-full rounded-xl" />
            </div>
          )}

          {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="mt-8 space-y-6">
          <p className="text-sm text-gray-600">
            Análise salva em{' '}
            <span className="font-medium text-gray-900">{result.client_name}</span>
            .{' '}
            <Link
              to={`/clients/${result.client_id}?meeting=${result.id}`}
              className="font-medium text-orange-600 hover:text-orange-700"
            >
              Ver no histórico do cliente
            </Link>
          </p>

          <Card>
            <CardHeader>
              <CardTitle>Triagem</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-gray-700">
                {result.triage}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Agentes selecionados</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-700">
                {result.selected_agents?.join(', ') || '—'}
              </p>
            </CardContent>
          </Card>

          <IntelligenceCard card={result.final_report} />
        </div>
      )}
    </>
  )
}

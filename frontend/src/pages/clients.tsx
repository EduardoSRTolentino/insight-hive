import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import client, { apiErrorMessage, isUnauthorized } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { type ClientListItem, statusLabel } from '@/lib/types'
import { formatDateTime } from '@/lib/utils'

export default function ClientsPage() {
  const [clients, setClients] = useState<ClientListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { token, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!token) return
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await client.get<ClientListItem[]>('/clients')
        if (!cancelled) {
          setClients(response.data)
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
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [token, logout, navigate])

  return (
    <>
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Clientes</h1>
          <p className="mt-1 text-sm text-gray-500">
            Acompanhe a evolução das reuniões por conta.
          </p>
        </div>
        <Button
          asChild
          className="rounded-full bg-orange-600 text-white hover:bg-orange-700"
        >
          <Link to="/clients/new">Novo cliente</Link>
        </Button>
      </div>

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-24 w-full rounded-xl" />
        </div>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}

      {!loading && !error && clients.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Nenhum cliente ainda</CardTitle>
            <CardDescription>
              Cadastre uma conta para começar a importar análises.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <div className="space-y-3">
        {clients.map((item) => (
          <Link key={item.id} to={`/clients/${item.id}`} className="block">
            <Card className="transition-colors hover:border-orange-200 hover:bg-orange-50/40">
              <CardHeader>
                <CardTitle className="text-lg">{item.name}</CardTitle>
                <CardDescription>
                  {statusLabel(item.status)}
                  {item.segment ? ` · ${item.segment}` : ''}
                  {item.owner ? ` · ${item.owner}` : ''}
                  {' · '}
                  {item.meetings_count === 1
                    ? '1 reunião'
                    : `${item.meetings_count} reuniões`}
                  {' · última: '}
                  {formatDateTime(item.last_meeting_at)}
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </>
  )
}

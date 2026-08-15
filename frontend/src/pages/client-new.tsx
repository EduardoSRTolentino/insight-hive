import { useNavigate } from 'react-router-dom'
import { ClientForm } from '@/components/client-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import client, { apiErrorMessage, isUnauthorized } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import type { ClientListItem, ClientPayload } from '@/lib/types'

export default function ClientNewPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleSubmit = async (payload: ClientPayload) => {
    try {
      const response = await client.post<ClientListItem>('/clients', payload)
      navigate(`/clients/${response.data.id}`)
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        logout()
        navigate('/login')
        return
      }
      throw new Error(apiErrorMessage(err, 'Não foi possível criar o cliente.'))
    }
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Novo cliente</CardTitle>
          <CardDescription>
            Cadastre a conta antes de importar reuniões. Só o nome é obrigatório.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ClientForm
            submitLabel="Criar cliente"
            pendingLabel="Criando..."
            onSubmit={handleSubmit}
          />
        </CardContent>
      </Card>
    </>
  )
}

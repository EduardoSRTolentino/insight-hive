import { AccountForm } from '@/components/account-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import client, { apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import type { UserProfile, UserUpdatePayload } from '@/lib/types'

export default function AccountPage() {
  const { user, refreshUser } = useAuth()

  if (!user) {
    return <p className="text-sm text-muted-foreground">Carregando perfil...</p>
  }

  const handleSubmit = async (payload: UserUpdatePayload) => {
    try {
      await client.patch<UserProfile>('/auth/me', payload)
      await refreshUser()
    } catch (err: unknown) {
      throw new Error(apiErrorMessage(err, 'Não foi possível salvar o perfil.'))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Minha conta</CardTitle>
        <CardDescription>
          Atualize seus dados. Só nome e e-mail são obrigatórios.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <AccountForm
          mode="edit"
          initial={user}
          submitLabel="Salvar"
          pendingLabel="Salvando..."
          onSubmit={handleSubmit}
        />
      </CardContent>
    </Card>
  )
}

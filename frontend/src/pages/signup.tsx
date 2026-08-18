import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, CircleIcon } from 'lucide-react'
import { AccountForm } from '@/components/account-form'
import { ThemeToggle } from '@/components/theme-toggle'
import { apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import type { UserRegisterPayload } from '@/lib/types'

export default function SignupPage() {
  const { register, token, ready } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (ready && token) {
      navigate('/clients', { replace: true })
    }
  }, [ready, token, navigate])

  const handleSubmit = async (payload: UserRegisterPayload) => {
    try {
      await register(payload)
      navigate('/clients')
    } catch (err: unknown) {
      throw new Error(apiErrorMessage(err, 'Não foi possível criar a conta. Tente novamente.'))
    }
  }

  return (
    <div className="relative flex min-h-[100dvh] flex-col justify-center bg-background px-4 py-12 sm:px-6 lg:px-8">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="sm:mx-auto sm:w-full sm:max-w-xl">
        <Link
          to="/"
          className="mb-8 flex items-center justify-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Voltar ao início
        </Link>
        <div className="flex justify-center">
          <CircleIcon className="h-12 w-12 text-primary" />
        </div>
        <h1 className="mt-6 text-center text-3xl font-extrabold text-foreground">
          Crie sua conta
        </h1>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          Só nome, e-mail e senha são obrigatórios. O restante você pode completar depois.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
          <AccountForm
            mode="signup"
            submitLabel="Criar conta"
            pendingLabel="Criando..."
            onSubmit={handleSubmit}
          />
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Já tem conta?{' '}
            <Link to="/login" className="font-medium text-primary hover:text-primary/90">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

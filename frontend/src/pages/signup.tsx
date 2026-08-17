import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, CircleIcon } from 'lucide-react'
import { AccountForm } from '@/components/account-form'
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
    <div className="flex min-h-[100dvh] flex-col justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl">
        <Link
          to="/"
          className="mb-8 flex items-center justify-center gap-1.5 text-sm text-gray-500 hover:text-gray-900"
        >
          <ArrowLeft className="size-4" />
          Voltar ao início
        </Link>
        <div className="flex justify-center">
          <CircleIcon className="h-12 w-12 text-orange-500" />
        </div>
        <h1 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Crie sua conta
        </h1>
        <p className="mt-2 text-center text-sm text-gray-500">
          Só nome, e-mail e senha são obrigatórios. O restante você pode completar depois.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
          <AccountForm
            mode="signup"
            submitLabel="Criar conta"
            pendingLabel="Criando..."
            onSubmit={handleSubmit}
          />
          <p className="mt-6 text-center text-sm text-gray-500">
            Já tem conta?{' '}
            <Link to="/login" className="font-medium text-orange-600 hover:text-orange-700">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

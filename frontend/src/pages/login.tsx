import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, CircleIcon, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, token, ready } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (ready && token) {
      navigate('/clients', { replace: true })
    }
  }, [ready, token, navigate])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/clients')
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Não foi possível entrar. Tente novamente.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[100dvh] flex-col justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
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
          Entre na sua conta
        </h1>
        <p className="mt-2 text-center text-sm text-gray-500">
          Insight Hive — análise multiagente
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Usuário
            </Label>
            <div className="mt-1">
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="admin"
                className="relative block w-full rounded-full border-gray-300 px-3 py-2 text-gray-900 placeholder:text-gray-500 focus-visible:border-orange-500 focus-visible:ring-orange-500/50"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Senha
            </Label>
            <div className="mt-1">
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                className="relative block w-full rounded-full border-gray-300 px-3 py-2 text-gray-900 placeholder:text-gray-500 focus-visible:border-orange-500 focus-visible:ring-orange-500/50"
              />
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center rounded-full bg-orange-600 text-white shadow-sm hover:bg-orange-700 focus-visible:ring-orange-500"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" />
                Entrando...
              </>
            ) : (
              'Entrar'
            )}
          </Button>
        </form>
      </div>
    </div>
  )
}

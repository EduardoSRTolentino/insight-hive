import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/upload')
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Não foi possível entrar. Tente novamente.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-center">
      <form className="card" onSubmit={handleSubmit}>
        <h1>Sistema Multiagente</h1>
        <p className="subtitle">Entre com suas credenciais para continuar</p>

        <label htmlFor="username">Usuário</label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />

        <label htmlFor="password">Senha</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

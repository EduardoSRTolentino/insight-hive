import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function UploadPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleFileChange = (event) => {
    setFile(event.target.files[0] || null)
    setResult(null)
    setError('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!file) {
      setError('Selecione um arquivo .csv ou .json.')
      return
    }

    setError('')
    setResult(null)
    setLoading(true)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await client.post('/analysis/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(response.data)
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout()
        return
      }
      setError(err.response?.data?.detail || 'Erro ao processar o arquivo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-center">
      <div className="card wide">
        <div className="card-header">
          <h1>Importar arquivo</h1>
          <button type="button" className="secondary" onClick={handleLogout}>
            Sair
          </button>
        </div>
        <p className="subtitle">
          Selecione um arquivo .csv ou .json para acionar a análise do sistema
          multiagente.
        </p>

        <form onSubmit={handleSubmit}>
          <input type="file" accept=".csv,.json" onChange={handleFileChange} />
          <button type="submit" disabled={loading}>
            {loading ? 'Analisando...' : 'Analisar'}
          </button>
        </form>

        {loading && (
          <p className="hint">
            A análise pode levar algum tempo, pois roda o modelo de linguagem
            localmente. Aguarde...
          </p>
        )}

        {error && <p className="error">{error}</p>}

        {result && (
          <div className="result">
            <h2>Triagem</h2>
            <p>{result.triage}</p>

            <h2>Agentes selecionados</h2>
            <p>{result.selected_agents?.join(', ') || '—'}</p>

            <h2>Relatório final</h2>
            <pre>{result.final_report}</pre>
          </div>
        )}
      </div>
    </div>
  )
}

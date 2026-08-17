import { AxiosError } from 'axios'
import MockAdapter from 'axios-mock-adapter'
import { afterEach, describe, expect, it, vi } from 'vitest'
import client, {
  ANALYSIS_UPLOAD_TIMEOUT_MS,
  apiErrorMessage,
  DEFAULT_TIMEOUT_MS,
  isUnauthorized,
  setOnUnauthorized,
} from '@/lib/api'

function axiosError(status: number, detail?: string) {
  const error = new AxiosError('request failed')
  error.response = {
    data: detail ? { detail } : {},
    status,
    statusText: 'Error',
    headers: {},
    config: {} as never,
  }
  return error
}

describe('timeouts', () => {
  it('keeps a short default and a long analysis upload timeout', () => {
    expect(DEFAULT_TIMEOUT_MS).toBe(20_000)
    expect(client.defaults.timeout).toBe(DEFAULT_TIMEOUT_MS)
    expect(ANALYSIS_UPLOAD_TIMEOUT_MS).toBe(600_000)
  })
})

describe('apiErrorMessage', () => {
  it('returns the detail string from an axios error', () => {
    expect(apiErrorMessage(axiosError(404, 'Cliente não encontrado.'), 'fallback')).toBe(
      'Cliente não encontrado.',
    )
  })

  it('returns the error message for a plain Error', () => {
    expect(apiErrorMessage(new Error('boom'), 'Não deu.')).toBe('boom')
  })

  it('joins FastAPI 422 validation messages', () => {
    const error = axiosError(422)
    error.response = {
      ...error.response!,
      data: { detail: [{ loc: ['body', 'email'], msg: 'Informe um e-mail válido.' }] },
    }
    expect(apiErrorMessage(error, 'fallback')).toBe('Informe um e-mail válido.')
  })

  it('explains a network failure', () => {
    const error = new AxiosError('network')
    expect(apiErrorMessage(error, 'fallback')).toBe(
      'Não foi possível conectar ao servidor. Confira se o backend está no ar.',
    )
  })
})

describe('isUnauthorized', () => {
  it('detects HTTP 401', () => {
    expect(isUnauthorized(axiosError(401))).toBe(true)
    expect(isUnauthorized(axiosError(403))).toBe(false)
  })
})

describe('401 interceptor', () => {
  afterEach(() => {
    setOnUnauthorized(null)
  })

  it('calls the handler on 401 except for login and register', async () => {
    const mock = new MockAdapter(client)
    const handler = vi.fn()
    setOnUnauthorized(handler)

    mock.onGet('/clients').reply(401)
    await expect(client.get('/clients')).rejects.toBeDefined()
    expect(handler).toHaveBeenCalledTimes(1)

    handler.mockClear()
    mock.onPost('/auth/login').reply(401, { detail: 'E-mail ou senha inválidos.' })
    await expect(client.post('/auth/login')).rejects.toBeDefined()
    expect(handler).not.toHaveBeenCalled()

    handler.mockClear()
    mock.onPost('/auth/register').reply(401, { detail: 'Não autorizado.' })
    await expect(client.post('/auth/register')).rejects.toBeDefined()
    expect(handler).not.toHaveBeenCalled()

    mock.restore()
  })
})

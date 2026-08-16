import { AxiosError } from 'axios'
import MockAdapter from 'axios-mock-adapter'
import { afterEach, describe, expect, it, vi } from 'vitest'
import client, {
  apiErrorMessage,
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

describe('apiErrorMessage', () => {
  it('returns the detail string from an axios error', () => {
    expect(apiErrorMessage(axiosError(404, 'Cliente não encontrado.'), 'fallback')).toBe(
      'Cliente não encontrado.',
    )
  })

  it('returns the fallback when detail is missing', () => {
    expect(apiErrorMessage(new Error('boom'), 'Não deu.')).toBe('Não deu.')
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

  it('calls the handler on 401 except for login', async () => {
    const mock = new MockAdapter(client)
    const handler = vi.fn()
    setOnUnauthorized(handler)

    mock.onGet('/clients').reply(401)
    await expect(client.get('/clients')).rejects.toBeDefined()
    expect(handler).toHaveBeenCalledTimes(1)

    handler.mockClear()
    mock.onPost('/auth/login').reply(401, { detail: 'Usuário ou senha inválidos.' })
    await expect(client.post('/auth/login')).rejects.toBeDefined()
    expect(handler).not.toHaveBeenCalled()

    mock.restore()
  })
})

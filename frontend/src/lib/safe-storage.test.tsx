import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/lib/auth-context'
import { getItem, removeItem, setItem } from '@/lib/safe-storage'
import { ThemeProvider } from '@/lib/theme'

function mockMatchMedia() {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }),
  })
}

describe('safe-storage', () => {
  beforeEach(() => {
    mockMatchMedia()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('returns null and no-ops when storage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('blocked')
    })

    expect(getItem('token')).toBeNull()
    expect(() => setItem('token', 'abc')).not.toThrow()
    expect(() => removeItem('token')).not.toThrow()
  })

  it('lets ThemeProvider and AuthProvider render when storage is blocked', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })

    render(
      <ThemeProvider>
        <AuthProvider>
          <p>app ok</p>
        </AuthProvider>
      </ThemeProvider>,
    )

    expect(screen.getByText('app ok')).toBeInTheDocument()
  })
})

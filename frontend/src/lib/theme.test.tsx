import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ThemeToggle } from '@/components/theme-toggle'
import { THEME_STORAGE_KEY, ThemeProvider, useTheme } from '@/lib/theme'

type MediaQueryListener = (event: { matches: boolean }) => void

function mockMatchMedia(matches: boolean) {
  let current = matches
  const listeners = new Set<MediaQueryListener>()

  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      get matches() {
        return current
      },
      media: query,
      onchange: null,
      addEventListener: (_event: string, listener: MediaQueryListener) => {
        listeners.add(listener)
      },
      removeEventListener: (_event: string, listener: MediaQueryListener) => {
        listeners.delete(listener)
      },
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }),
  })

  return {
    setMatches(next: boolean) {
      current = next
      listeners.forEach((listener) => listener({ matches: next }))
    },
  }
}

function ThemeProbe() {
  const { theme, resolvedTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
    </div>
  )
}

describe('theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
    mockMatchMedia(false)
  })

  afterEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('defaults to system and stays light when the OS is light', () => {
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('system')
    expect(screen.getByTestId('resolved')).toHaveTextContent('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('applies dark when the stored preference is dark', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(screen.getByTestId('resolved')).toHaveTextContent('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('follows prefers-color-scheme when theme is system', () => {
    mockMatchMedia(true)
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    )
    expect(screen.getByTestId('resolved')).toHaveTextContent('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('updates resolvedTheme when the OS preference changes', () => {
    const media = mockMatchMedia(false)
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('system')
    expect(screen.getByTestId('resolved')).toHaveTextContent('light')

    act(() => {
      media.setMatches(true)
    })

    expect(screen.getByTestId('resolved')).toHaveTextContent('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('toggle switches to light and persists the choice', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
        <ThemeProbe />
      </ThemeProvider>
    )
    fireEvent.click(screen.getByRole('button', { name: 'Ativar modo claro' }))
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
    expect(screen.getByRole('button', { name: 'Ativar modo escuro' })).toBeInTheDocument()
  })

  it('cycles system → light → dark → system', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
        <ThemeProbe />
      </ThemeProvider>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Ativar modo claro' }))
    expect(screen.getByTestId('theme')).toHaveTextContent('light')

    fireEvent.click(screen.getByRole('button', { name: 'Ativar modo escuro' }))
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')

    fireEvent.click(screen.getByRole('button', { name: 'Usar tema do sistema' }))
    expect(screen.getByTestId('theme')).toHaveTextContent('system')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('system')
  })
})

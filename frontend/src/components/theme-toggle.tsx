import { Moon, Monitor, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme, type Theme } from '@/lib/theme'

const CYCLE: Record<Theme, Theme> = {
  system: 'light',
  light: 'dark',
  dark: 'system',
}

const NEXT_LABEL: Record<Theme, string> = {
  system: 'Ativar modo claro',
  light: 'Ativar modo escuro',
  dark: 'Usar tema do sistema',
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className="rounded-full"
      aria-label={NEXT_LABEL[theme]}
      onClick={() => setTheme(CYCLE[theme])}
    >
      {theme === 'dark' ? <Moon /> : theme === 'light' ? <Sun /> : <Monitor />}
    </Button>
  )
}

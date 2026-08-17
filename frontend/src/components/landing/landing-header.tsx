import { Link } from 'react-router-dom'
import { CircleIcon } from 'lucide-react'
import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'

export function LandingHeader() {
  return (
    <header className="fixed top-0 z-30 w-full">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mt-4 flex h-14 items-center justify-between rounded-2xl border border-border/80 bg-card/80 px-3 shadow-sm backdrop-blur-md sm:px-4">
          <Link to="/" className="flex items-center gap-2 rounded-full px-1 py-1">
            <CircleIcon className="size-6 text-primary" />
            <span className="text-sm font-semibold text-foreground">Insight Hive</span>
          </Link>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button asChild variant="ghost" className="rounded-full">
              <Link to="/login">Entrar</Link>
            </Button>
            <Button asChild className="rounded-full px-4">
              <Link to="/signup">Criar conta</Link>
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

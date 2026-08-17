import { Link } from 'react-router-dom'
import { CircleIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function LandingHeader() {
  return (
    <header className="fixed top-0 z-30 w-full">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mt-4 flex h-14 items-center justify-between rounded-2xl border border-gray-200/80 bg-white/80 px-3 shadow-sm backdrop-blur-md sm:px-4">
          <Link to="/" className="flex items-center gap-2 rounded-full px-1 py-1">
            <CircleIcon className="size-6 text-orange-500" />
            <span className="text-sm font-semibold text-gray-900">Insight Hive</span>
          </Link>
          <div className="flex items-center gap-2">
            <Button
              asChild
              variant="ghost"
              className="rounded-full text-gray-700 hover:bg-gray-50"
            >
              <Link to="/login">Entrar</Link>
            </Button>
            <Button
              asChild
              className="rounded-full bg-orange-600 px-4 text-white shadow-sm hover:bg-orange-700 focus-visible:ring-orange-500"
            >
              <Link to="/signup">Criar conta</Link>
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

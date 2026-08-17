import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  CircleIcon,
  FileUp,
  LogOut,
  Menu,
  UserRound,
  UserPlus,
  Users,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth-context'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/clients', label: 'Clientes', icon: Users, match: 'clients' },
  { href: '/clients/new', label: 'Novo cliente', icon: UserPlus, match: 'new' },
  { href: '/upload', label: 'Nova análise', icon: FileUp, match: 'upload' },
  { href: '/account', label: 'Minha conta', icon: UserRound, match: 'account' },
] as const

function isActive(pathname: string, item: (typeof NAV)[number]) {
  if (item.match === 'new') return pathname === '/clients/new'
  if (item.match === 'upload') return pathname === '/upload'
  if (item.match === 'account') return pathname === '/account'
  return pathname === '/clients' || (pathname.startsWith('/clients/') && pathname !== '/clients/new')
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const { pathname } = useLocation()

  return (
    <nav className="flex flex-col gap-1">
      {NAV.map((item) => {
        const Icon = item.icon
        const active = isActive(pathname, item)
        return (
          <Link
            key={item.href}
            to={item.href}
            onClick={onNavigate}
            className={cn(
              'flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium',
              active
                ? 'bg-orange-50 text-orange-600'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            )}
          >
            <Icon className="size-4" />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

export function AppShell() {
  const { token, user, ready, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    if (ready && !token) {
      navigate('/login', { replace: true })
    }
  }, [ready, token, navigate])

  useEffect(() => {
    if (!menuOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [menuOpen])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!ready || !token) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-gray-50 text-sm text-gray-600">
        Carregando...
      </div>
    )
  }

  return (
    <div className="flex min-h-[100dvh] bg-white">
      <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col self-start border-r border-gray-200 lg:flex">
        <div className="flex h-16 items-center px-4">
          <Link to="/clients" className="flex items-center">
            <CircleIcon className="h-6 w-6 text-orange-500" />
            <span className="ml-2 text-lg font-semibold text-gray-900">Insight Hive</span>
          </Link>
        </div>
        <div className="flex flex-1 flex-col px-3 pb-4">
          <NavLinks />
          <div className="mt-auto pt-4">
            {user && (
              <p className="mb-3 truncate px-3 text-xs text-gray-500" title={user.email}>
                {user.full_name}
              </p>
            )}
            <Button
              type="button"
              variant="outline"
              className="w-full rounded-full"
              onClick={handleLogout}
            >
              <LogOut className="size-4" />
              Sair
            </Button>
          </div>
        </div>
      </aside>

      {menuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/30"
            aria-label="Fechar menu"
            onClick={() => setMenuOpen(false)}
          />
          <aside
            className="relative z-50 flex h-full w-64 flex-col bg-white shadow-lg"
            role="dialog"
            aria-modal="true"
            aria-label="Menu"
          >
            <div className="flex h-16 items-center justify-between px-4">
              <Link to="/clients" className="flex items-center" onClick={() => setMenuOpen(false)}>
                <CircleIcon className="h-6 w-6 text-orange-500" />
                <span className="ml-2 text-lg font-semibold text-gray-900">Insight Hive</span>
              </Link>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setMenuOpen(false)}
                aria-label="Fechar menu"
              >
                <X />
              </Button>
            </div>
            <div className="flex flex-1 flex-col px-3 pb-4">
              <NavLinks onNavigate={() => setMenuOpen(false)} />
              <div className="mt-auto pt-4">
                {user && (
                  <p className="mb-3 truncate px-3 text-xs text-gray-500" title={user.email}>
                    {user.full_name}
                  </p>
                )}
                <Button
                  type="button"
                  variant="outline"
                  className="w-full rounded-full"
                  onClick={handleLogout}
                >
                  <LogOut className="size-4" />
                  Sair
                </Button>
              </div>
            </div>
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center gap-3 border-b border-gray-200 px-4 lg:hidden">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => setMenuOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu />
          </Button>
          <Link to="/clients" className="flex items-center">
            <CircleIcon className="h-5 w-5 text-orange-500" />
            <span className="ml-2 font-semibold text-gray-900">Insight Hive</span>
          </Link>
        </header>
        <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

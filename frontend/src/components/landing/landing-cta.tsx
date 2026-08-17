import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export function LandingCta() {
  return (
    <section className="py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-white px-6 py-14 text-center shadow-sm sm:px-12">
          <div
            className="pointer-events-none absolute -top-16 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-orange-100/80 blur-3xl"
            aria-hidden="true"
          />
          <h2 className="relative text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Crie sua conta e analise a próxima reunião
          </h2>
          <p className="relative mx-auto mt-3 max-w-xl text-gray-600">
            Cadastre-se, registre a conta do cliente, envie o arquivo e receba o card de
            inteligência com evidências para o time comercial.
          </p>
          <div className="relative mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button
              asChild
              className="h-11 rounded-full bg-orange-600 px-6 text-white shadow-sm hover:bg-orange-700 focus-visible:ring-orange-500"
            >
              <Link to="/signup">Criar conta</Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="h-11 rounded-full border-gray-300 bg-white px-6 text-gray-700 hover:bg-gray-50"
            >
              <Link to="/login">Entrar</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}

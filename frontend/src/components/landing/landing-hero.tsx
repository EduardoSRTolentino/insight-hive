import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const MOCK_ROWS = [
  { tone: 'bg-orange-400', label: 'Ecossistema mapeado', value: 'Protheus + Fluig' },
  { tone: 'bg-red-400', label: 'Concorrente citado', value: 'SAP S/4HANA' },
  { tone: 'bg-emerald-400', label: 'Oportunidade', value: 'Cross-sell RMS' },
  { tone: 'bg-teal-400', label: 'Persona detectada', value: 'CFO — decisor' },
  { tone: 'bg-teal-400', label: 'Sentimento', value: 'Misto, renovação em pauta' },
] as const

export function LandingHero() {
  return (
    <section className="relative overflow-hidden pt-32 pb-16 md:pt-40 md:pb-24">
      <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <div className="absolute -top-16 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-orange-200/50 blur-3xl" />
        <div className="absolute top-48 right-[12%] h-64 w-64 rounded-full bg-gray-200/70 blur-3xl" />
        <div className="absolute top-72 left-[8%] h-56 w-56 rounded-full bg-orange-100/60 blur-3xl" />
      </div>

      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-5 flex items-center justify-center gap-3">
            <span className="h-px w-8 bg-linear-to-r from-transparent to-orange-300" />
            <p className="text-sm font-medium tracking-wide text-orange-600 uppercase">
              Análise multiagente
            </p>
            <span className="h-px w-8 bg-linear-to-l from-transparent to-orange-300" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
            Transforme reuniões em{' '}
            <span className="text-orange-600">inteligência comercial</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-gray-600 sm:text-lg">
            Especialistas analisam transcrições B2B no contexto TOTVS: oportunidade,
            retenção, ecossistema, persona e budget — em um card único por reunião.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
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

        <div className="mx-auto mt-14 max-w-lg">
          <article className="overflow-hidden rounded-xl bg-gray-900 text-gray-100 shadow-xl ring-1 ring-black/5">
            <header className="flex items-start gap-3 border-b border-white/10 px-4 py-3">
              <div className="mt-1.5 flex gap-1.5" aria-hidden="true">
                <span className="size-2.5 rounded-full bg-red-500" />
                <span className="size-2.5 rounded-full bg-yellow-400" />
                <span className="size-2.5 rounded-full bg-green-500" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white">Card de Inteligência</h2>
                <p className="text-xs text-gray-400">Indústria Aurora Ltda.</p>
              </div>
            </header>
            <ul className="m-0 list-none p-0">
              {MOCK_ROWS.map((row) => (
                <li
                  key={row.label}
                  className="flex items-start gap-3 border-b border-white/10 px-4 py-3.5 last:border-b-0"
                >
                  <span className={`mt-1.5 size-2.5 shrink-0 rounded-full ${row.tone}`} />
                  <div className="flex min-w-0 flex-col gap-0.5">
                    <span className="text-xs text-gray-400">{row.label}</span>
                    <span className="text-sm font-semibold text-gray-100">{row.value}</span>
                  </div>
                </li>
              ))}
            </ul>
          </article>
        </div>
      </div>
    </section>
  )
}

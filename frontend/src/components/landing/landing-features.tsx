import {
  History,
  Layers,
  Lock,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from 'lucide-react'

const FEATURES = [
  {
    icon: TrendingUp,
    title: 'Oportunidade',
    body: 'Upsell, cross-sell e timing de expansão de contrato, com evidência no transcript.',
  },
  {
    icon: ShieldAlert,
    title: 'Retenção e churn',
    body: 'Sinais de insatisfação, ameaça de troca e renovação em risco — com ações sugeridas.',
  },
  {
    icon: Layers,
    title: 'Ecossistema TOTVS',
    body: 'Produtos, gaps e integrações alinhados ao catálogo público de produtos.totvs.com.',
  },
  {
    icon: History,
    title: 'Histórico por cliente',
    body: 'Cada análise fica na ficha da conta. Reuniões anteriores continuam acessíveis.',
  },
  {
    icon: Sparkles,
    title: 'Limpeza de transcrição',
    body: 'Ruído, timestamps e falas irrelevantes saem antes dos especialistas rodarem.',
  },
  {
    icon: Lock,
    title: 'Acesso autenticado',
    body: 'Login JWT para o time interno. Sem cadastro público — só quem já tem credencial entra.',
  },
] as const

export function LandingFeatures() {
  return (
    <section className="py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <div className="mb-4 flex items-center justify-center gap-3">
            <span className="h-px w-8 bg-linear-to-r from-transparent to-orange-300" />
            <p className="text-sm font-medium tracking-wide text-orange-600 uppercase">
              Capacidades
            </p>
            <span className="h-px w-8 bg-linear-to-l from-transparent to-orange-300" />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Especialistas no contexto TOTVS
          </h2>
          <p className="mt-3 text-gray-600">
            Cada agente olha um recorte. O manager consolida o card para revisão humana.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => {
            const Icon = feature.icon
            return (
              <article
                key={feature.title}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition hover:shadow-md hover:ring-1 hover:ring-orange-500/20"
              >
                <span className="flex size-10 items-center justify-center rounded-full bg-orange-50 text-orange-600">
                  <Icon className="size-5" />
                </span>
                <h3 className="mt-4 text-lg font-semibold text-gray-900">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">{feature.body}</p>
              </article>
            )
          })}
        </div>
      </div>
    </section>
  )
}

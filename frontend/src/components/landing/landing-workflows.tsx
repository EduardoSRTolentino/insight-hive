import { ClipboardCheck, FileUp, UserPlus } from 'lucide-react'

const STEPS = [
  {
    icon: UserPlus,
    title: 'Cadastre a conta',
    body: 'Registre segmento, porte, contato e dono interno. O contexto da conta fica pronto para a próxima análise.',
  },
  {
    icon: FileUp,
    title: 'Envie a transcrição',
    body: 'Faça upload de CSV ou JSON da reunião. A transcrição é limpa antes de entrar no grafo de agentes.',
  },
  {
    icon: ClipboardCheck,
    title: 'Receba o relatório',
    body: 'Especialistas devolvem um card de inteligência com evidências, sinais e próximos passos comerciais.',
  },
] as const

export function LandingWorkflows() {
  return (
    <section id="como-funciona" className="scroll-mt-24 py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <div className="mb-4 flex items-center justify-center gap-3">
            <span className="h-px w-8 bg-linear-to-r from-transparent to-orange-300" />
            <p className="text-sm font-medium tracking-wide text-orange-600 uppercase">
              Fluxo
            </p>
            <span className="h-px w-8 bg-linear-to-l from-transparent to-orange-300" />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Da reunião ao card em três passos
          </h2>
          <p className="mt-3 text-gray-600">
            Sem montar briefing à mão: o pipeline lê a conversa e devolve o que importa para CS e vendas.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {STEPS.map((step, index) => {
            const Icon = step.icon
            return (
              <article
                key={step.title}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition hover:shadow-md hover:ring-1 hover:ring-orange-500/20"
              >
                <div className="mb-4 flex items-center justify-between">
                  <span className="flex size-10 items-center justify-center rounded-full bg-orange-50 text-orange-600">
                    <Icon className="size-5" />
                  </span>
                  <span className="text-sm font-semibold text-gray-400">0{index + 1}</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">{step.body}</p>
              </article>
            )
          })}
        </div>
      </div>
    </section>
  )
}

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
            <span className="h-px w-8 bg-linear-to-r from-transparent to-primary/40" />
            <p className="text-sm font-medium tracking-wide text-primary uppercase">
              Fluxo
            </p>
            <span className="h-px w-8 bg-linear-to-l from-transparent to-primary/40" />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            Da reunião ao card em três passos
          </h2>
          <p className="mt-3 text-muted-foreground">
            Sem montar briefing à mão: o pipeline lê a conversa e devolve o que importa para CS e vendas.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {STEPS.map((step) => {
            const Icon = step.icon
            return (
              <article
                key={step.title}
                className="rounded-2xl border border-border bg-card p-6 shadow-sm transition hover:shadow-md hover:ring-1 hover:ring-primary/20"
              >
                <div className="mb-4">
                  <span className="flex size-10 items-center justify-center rounded-full bg-accent text-accent-foreground">
                    <Icon className="size-5" />
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-foreground">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </article>
            )
          })}
        </div>
      </div>
    </section>
  )
}

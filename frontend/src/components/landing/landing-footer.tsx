import { CircleIcon } from 'lucide-react'

export function LandingFooter() {
  return (
    <footer className="border-t border-border py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-4 text-center sm:px-6">
        <div className="flex items-center gap-2">
          <CircleIcon className="size-5 text-primary" />
          <span className="text-sm font-semibold text-foreground">Insight Hive</span>
        </div>
        <p className="text-sm text-muted-foreground">
          Análise multiagente de reuniões B2B no contexto TOTVS.
        </p>
      </div>
    </footer>
  )
}

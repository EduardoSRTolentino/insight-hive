import { CircleIcon } from 'lucide-react'

export function LandingFooter() {
  return (
    <footer className="border-t border-gray-200 py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-4 text-center sm:px-6">
        <div className="flex items-center gap-2">
          <CircleIcon className="size-5 text-orange-500" />
          <span className="text-sm font-semibold text-gray-900">Insight Hive</span>
        </div>
        <p className="text-sm text-gray-500">
          Análise multiagente de reuniões B2B no contexto TOTVS.
        </p>
      </div>
    </footer>
  )
}

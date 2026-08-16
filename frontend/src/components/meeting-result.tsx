import type { ReactNode } from 'react'
import { IntelligenceCard } from '@/components/intelligence-card'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type MeetingResultProps = {
  triage: string
  selected_agents: string[]
  final_report: unknown
  description?: string
  header?: ReactNode
}

export function MeetingResult({
  triage,
  selected_agents,
  final_report,
  description,
  header,
}: MeetingResultProps) {
  return (
    <div className="mt-8 space-y-6">
      {header}
      <Card>
        <CardHeader>
          <CardTitle>Triagem</CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-gray-700">{triage}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Agentes selecionados</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-700">
            {selected_agents?.join(', ') || '—'}
          </p>
        </CardContent>
      </Card>
      <IntelligenceCard card={final_report} />
    </div>
  )
}

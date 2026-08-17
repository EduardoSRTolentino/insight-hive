import { Link } from 'react-router-dom'
import { IntelligenceCard } from '@/components/intelligence-card'
import { Button } from '@/components/ui/button'

const MOCK_CARD = {
  conta: 'Indústria Aurora Ltda.',
  ecossistema_mapeado: 'Protheus + Fluig',
  concorrente_citado: 'SAP S/4HANA',
  oportunidade: 'Cross-sell RMS',
  persona_detectada: 'CFO — decisor',
  sentimento: 'Misto, renovação em pauta',
}

export function LandingHero() {
  return (
    <section className="relative overflow-hidden pt-32 pb-16 md:pt-40 md:pb-24">
      <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <div className="absolute -top-16 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-primary/20 blur-3xl" />
        <div className="absolute top-48 right-[12%] h-64 w-64 rounded-full bg-muted/70 blur-3xl" />
        <div className="absolute top-72 left-[8%] h-56 w-56 rounded-full bg-primary/10 blur-3xl" />
      </div>

      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-5 flex items-center justify-center gap-3">
            <span className="h-px w-8 bg-linear-to-r from-transparent to-primary/40" />
            <p className="text-sm font-medium tracking-wide text-primary uppercase">
              Análise multiagente
            </p>
            <span className="h-px w-8 bg-linear-to-l from-transparent to-primary/40" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl md:text-6xl">
            Transforme reuniões em{' '}
            <span className="text-primary">inteligência comercial</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            Especialistas analisam transcrições B2B no contexto TOTVS: oportunidade,
            retenção, ecossistema, persona e budget — em um card único por reunião.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button asChild className="h-11 rounded-full px-6">
              <Link to="/signup">Criar conta</Link>
            </Button>
            <Button asChild variant="outline" className="h-11 rounded-full px-6">
              <Link to="/login">Entrar</Link>
            </Button>
          </div>
        </div>

        <div className="mx-auto mt-14 max-w-lg">
          <IntelligenceCard className="mt-0 shadow-xl" card={MOCK_CARD} />
        </div>
      </div>
    </section>
  )
}

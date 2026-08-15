import { Navigate } from 'react-router-dom'
import { LandingCta } from '@/components/landing/landing-cta'
import { LandingFeatures } from '@/components/landing/landing-features'
import { LandingFooter } from '@/components/landing/landing-footer'
import { LandingHeader } from '@/components/landing/landing-header'
import { LandingHero } from '@/components/landing/landing-hero'
import { LandingWorkflows } from '@/components/landing/landing-workflows'
import { useAuth } from '@/lib/auth-context'

export default function HomePage() {
  const { token, ready } = useAuth()

  if (!ready) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-gray-50 text-sm text-gray-600">
        Carregando...
      </div>
    )
  }

  if (token) {
    return <Navigate to="/clients" replace />
  }

  return (
    <div className="min-h-[100dvh] bg-gray-50">
      <LandingHeader />
      <main>
        <LandingHero />
        <LandingWorkflows />
        <LandingFeatures />
        <LandingCta />
      </main>
      <LandingFooter />
    </div>
  )
}

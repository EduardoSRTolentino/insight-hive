import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[100dvh] flex-col items-center justify-center bg-background px-4 text-center">
      <h1 className="text-3xl font-extrabold text-foreground">Página não encontrada</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        O endereço que você acessou não existe ou foi movido.
      </p>
      <Button asChild className="mt-6 rounded-full">
        <Link to="/">Voltar ao início</Link>
      </Button>
    </div>
  )
}

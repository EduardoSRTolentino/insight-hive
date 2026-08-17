import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Erro no frontend:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-[100dvh] flex-col items-center justify-center bg-background px-4 text-center">
          <p className="text-lg font-semibold text-foreground">Algo deu errado na interface</p>
          <p className="mt-2 max-w-md text-sm text-destructive">{this.state.error.message}</p>
          <button
            type="button"
            className="mt-6 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            onClick={() => window.location.assign('/')}
          >
            Recarregar
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

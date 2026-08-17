import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/app-shell'
import { ErrorBoundary } from '@/components/error-boundary'
import { AuthProvider } from '@/lib/auth-context'
import { ThemeProvider } from '@/lib/theme'
import AccountPage from '@/pages/account'
import ClientDetailPage from '@/pages/client-detail'
import ClientNewPage from '@/pages/client-new'
import ClientsPage from '@/pages/clients'
import HomePage from '@/pages/home'
import LoginPage from '@/pages/login'
import SignupPage from '@/pages/signup'
import UploadPage from '@/pages/upload'

export default function App() {
  return (
    <ErrorBoundary>
    <ThemeProvider>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route element={<AppShell />}>
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/clients/new" element={<ClientNewPage />} />
            <Route path="/clients/:id" element={<ClientDetailPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/account" element={<AccountPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </ThemeProvider>
    </ErrorBoundary>
  )
}

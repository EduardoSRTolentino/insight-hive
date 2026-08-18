import { type ChangeEvent, type FormEvent, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import type { UserProfile, UserRegisterPayload, UserUpdatePayload } from '@/lib/types'

const inputClassName =
  'relative block w-full rounded-full px-3 py-2'

type FormState = {
  full_name: string
  email: string
  password: string
  password_confirm: string
  company: string
  job_title: string
  department: string
  phone: string
  city: string
  state: string
  linkedin_url: string
  bio: string
}

function emptyForm(): FormState {
  return {
    full_name: '',
    email: '',
    password: '',
    password_confirm: '',
    company: '',
    job_title: '',
    department: '',
    phone: '',
    city: '',
    state: '',
    linkedin_url: '',
    bio: '',
  }
}

function fromProfile(profile?: Partial<UserProfile> | null): FormState {
  return {
    ...emptyForm(),
    full_name: profile?.full_name ?? '',
    email: profile?.email ?? '',
    company: profile?.company ?? '',
    job_title: profile?.job_title ?? '',
    department: profile?.department ?? '',
    phone: profile?.phone ?? '',
    city: profile?.city ?? '',
    state: profile?.state ?? '',
    linkedin_url: profile?.linkedin_url ?? '',
    bio: profile?.bio ?? '',
  }
}

function blank(value: string) {
  return value.trim() || null
}

function toProfilePayload(values: FormState) {
  return {
    full_name: values.full_name.trim(),
    email: values.email.trim(),
    company: blank(values.company),
    job_title: blank(values.job_title),
    department: blank(values.department),
    phone: blank(values.phone),
    city: blank(values.city),
    state: blank(values.state),
    linkedin_url: blank(values.linkedin_url),
    bio: blank(values.bio),
  }
}

type AccountFormProps =
  | {
      mode: 'signup'
      submitLabel: string
      pendingLabel: string
      onSubmit: (payload: UserRegisterPayload) => Promise<void>
    }
  | {
      mode: 'edit'
      initial: UserProfile
      submitLabel: string
      pendingLabel: string
      onSubmit: (payload: UserUpdatePayload) => Promise<void>
    }

export function AccountForm(props: AccountFormProps) {
  const [values, setValues] = useState<FormState>(() =>
    props.mode === 'edit' ? fromProfile(props.initial) : emptyForm(),
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const update =
    (field: keyof FormState) =>
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setValues((current) => ({ ...current, [field]: event.target.value }))
    }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!values.full_name.trim()) {
      setError('Informe o nome completo.')
      return
    }
    if (!values.email.trim()) {
      setError('Informe o e-mail.')
      return
    }
    if (props.mode === 'signup') {
      if (values.password.length < 8) {
        setError('A senha precisa ter pelo menos 8 caracteres.')
        return
      }
      if (values.password !== values.password_confirm) {
        setError('As senhas não coincidem.')
        return
      }
    }
    setError('')
    setSaving(true)
    try {
      const profile = toProfilePayload(values)
      if (props.mode === 'signup') {
        await props.onSubmit({ ...profile, password: values.password })
      } else {
        await props.onSubmit(profile)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível salvar a conta.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-foreground">Conta</h2>
        <div className="space-y-2">
          <Label htmlFor="full_name">Nome completo</Label>
          <Input
            id="full_name"
            required
            autoComplete="name"
            value={values.full_name}
            onChange={update('full_name')}
            placeholder="Seu nome"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? 'account-form-error' : undefined}
            className={inputClassName}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={values.email}
            onChange={update('email')}
            placeholder="voce@empresa.com"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? 'account-form-error' : undefined}
            className={inputClassName}
          />
        </div>
        {props.mode === 'signup' && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input
                id="password"
                type="password"
                required
                minLength={8}
                maxLength={72}
                autoComplete="new-password"
                value={values.password}
                onChange={update('password')}
                placeholder="Mínimo 8 caracteres"
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'account-form-error' : undefined}
                className={inputClassName}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password_confirm">Confirmar senha</Label>
              <Input
                id="password_confirm"
                type="password"
                required
                minLength={8}
                maxLength={72}
                autoComplete="new-password"
                value={values.password_confirm}
                onChange={update('password_confirm')}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'account-form-error' : undefined}
                className={inputClassName}
              />
            </div>
          </div>
        )}
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Trabalho</h2>
          <p className="text-xs text-muted-foreground">Opcional — ajuda a contextualizar suas análises.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="company">Empresa</Label>
            <Input
              id="company"
              autoComplete="organization"
              value={values.company}
              onChange={update('company')}
              placeholder="Onde você trabalha"
              className={inputClassName}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="job_title">Cargo</Label>
            <Input
              id="job_title"
              autoComplete="organization-title"
              value={values.job_title}
              onChange={update('job_title')}
              placeholder="CS, AE, gerente..."
              className={inputClassName}
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="department">Área / departamento</Label>
            <Input
              id="department"
              value={values.department}
              onChange={update('department')}
              placeholder="Customer Success, Vendas..."
              className={inputClassName}
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Contato</h2>
          <p className="text-xs text-muted-foreground">Opcional.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="phone">Telefone</Label>
            <Input
              id="phone"
              type="tel"
              autoComplete="tel"
              value={values.phone}
              onChange={update('phone')}
              className={inputClassName}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="linkedin_url">LinkedIn</Label>
            <Input
              id="linkedin_url"
              type="text"
              value={values.linkedin_url}
              onChange={update('linkedin_url')}
              placeholder="https://linkedin.com/in/..."
              className={inputClassName}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="city">Cidade</Label>
            <Input
              id="city"
              autoComplete="address-level2"
              value={values.city}
              onChange={update('city')}
              className={inputClassName}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="state">UF</Label>
            <Input
              id="state"
              autoComplete="address-level1"
              value={values.state}
              onChange={update('state')}
              maxLength={2}
              placeholder="SP"
              className={`${inputClassName} uppercase`}
            />
          </div>
        </div>
      </section>

      <section className="space-y-2">
        <Label htmlFor="bio">Sobre você</Label>
        <Textarea
          id="bio"
          value={values.bio}
          onChange={update('bio')}
          placeholder="Como você usa o Insight Hive, carteira, foco comercial..."
          rows={4}
        />
      </section>

      {error && (
        <p id="account-form-error" role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <Button
        type="submit"
        disabled={saving}
        className="rounded-full"
      >
        {saving ? (
          <>
            <Loader2 className="animate-spin" />
            {props.pendingLabel}
          </>
        ) : (
          props.submitLabel
        )}
      </Button>
    </form>
  )
}

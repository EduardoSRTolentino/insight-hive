import { type ChangeEvent, FormEvent, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  CLIENT_STATUSES,
  COMPANY_SIZES,
  type ClientPayload,
  type ClientProfile,
  type ClientStatus,
  type CompanySize,
} from '@/lib/types'

const selectClassName =
  'border-input h-9 w-full rounded-full border bg-transparent px-3 text-sm text-gray-900 outline-none focus-visible:border-orange-500 focus-visible:ring-[3px] focus-visible:ring-orange-500/50'

type FormState = {
  name: string
  segment: string
  company_size: string
  website: string
  city: string
  state: string
  contact_name: string
  contact_role: string
  contact_email: string
  contact_phone: string
  owner: string
  status: ClientStatus
  notes: string
}

function emptyForm(): FormState {
  return {
    name: '',
    segment: '',
    company_size: '',
    website: '',
    city: '',
    state: '',
    contact_name: '',
    contact_role: '',
    contact_email: '',
    contact_phone: '',
    owner: '',
    status: 'prospect',
    notes: '',
  }
}

function fromProfile(name: string, profile?: Partial<ClientProfile> | null): FormState {
  return {
    ...emptyForm(),
    name,
    segment: profile?.segment ?? '',
    company_size: profile?.company_size ?? '',
    website: profile?.website ?? '',
    city: profile?.city ?? '',
    state: profile?.state ?? '',
    contact_name: profile?.contact_name ?? '',
    contact_role: profile?.contact_role ?? '',
    contact_email: profile?.contact_email ?? '',
    contact_phone: profile?.contact_phone ?? '',
    owner: profile?.owner ?? '',
    status: profile?.status ?? 'prospect',
    notes: profile?.notes ?? '',
  }
}

function toPayload(values: FormState): ClientPayload {
  const blank = (value: string) => value.trim() || null
  return {
    name: values.name.trim(),
    segment: blank(values.segment),
    company_size: (blank(values.company_size) as CompanySize | null),
    website: blank(values.website),
    city: blank(values.city),
    state: blank(values.state),
    contact_name: blank(values.contact_name),
    contact_role: blank(values.contact_role),
    contact_email: blank(values.contact_email),
    contact_phone: blank(values.contact_phone),
    owner: blank(values.owner),
    status: values.status,
    notes: blank(values.notes),
  }
}

type ClientFormProps = {
  initial?: (Partial<ClientProfile> & { name?: string }) | null
  submitLabel: string
  pendingLabel: string
  onSubmit: (payload: ClientPayload) => Promise<void>
  onCancel?: () => void
}

export function ClientForm({
  initial,
  submitLabel,
  pendingLabel,
  onSubmit,
  onCancel,
}: ClientFormProps) {
  const [values, setValues] = useState<FormState>(() =>
    fromProfile(initial?.name ?? '', initial)
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const update = (field: keyof FormState) => (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setValues((current) => ({ ...current, [field]: event.target.value }))
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!values.name.trim()) {
      setError('Informe o nome do cliente.')
      return
    }
    setError('')
    setSaving(true)
    try {
      await onSubmit(toPayload(values))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível salvar o cliente.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-gray-900">Conta</h2>
        <div className="space-y-2">
          <Label htmlFor="name">Nome da conta</Label>
          <Input
            id="name"
            required
            value={values.name}
            onChange={update('name')}
            placeholder="Nome da empresa"
            className="rounded-full"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="segment">Segmento</Label>
            <Input
              id="segment"
              value={values.segment}
              onChange={update('segment')}
              placeholder="SaaS, varejo, saúde..."
              className="rounded-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company_size">Porte</Label>
            <select
              id="company_size"
              value={values.company_size}
              onChange={update('company_size')}
              className={selectClassName}
            >
              <option value="">Não informado</option>
              {COMPANY_SIZES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <select
              id="status"
              value={values.status}
              onChange={update('status')}
              className={selectClassName}
            >
              {CLIENT_STATUSES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="owner">Dono interno</Label>
            <Input
              id="owner"
              value={values.owner}
              onChange={update('owner')}
              placeholder="CS ou AE responsável"
              className="rounded-full"
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              value={values.website}
              onChange={update('website')}
              placeholder="https://"
              className="rounded-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="city">Cidade</Label>
            <Input
              id="city"
              value={values.city}
              onChange={update('city')}
              className="rounded-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="state">UF</Label>
            <Input
              id="state"
              value={values.state}
              onChange={update('state')}
              maxLength={2}
              placeholder="SP"
              className="rounded-full uppercase"
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-gray-900">Contato principal</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="contact_name">Nome</Label>
            <Input
              id="contact_name"
              value={values.contact_name}
              onChange={update('contact_name')}
              className="rounded-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="contact_role">Cargo</Label>
            <Input
              id="contact_role"
              value={values.contact_role}
              onChange={update('contact_role')}
              className="rounded-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="contact_email">E-mail</Label>
            <Input
              id="contact_email"
              type="email"
              value={values.contact_email}
              onChange={update('contact_email')}
              className="rounded-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="contact_phone">Telefone</Label>
            <Input
              id="contact_phone"
              value={values.contact_phone}
              onChange={update('contact_phone')}
              className="rounded-full"
            />
          </div>
        </div>
      </section>

      <section className="space-y-2">
        <Label htmlFor="notes">Observações</Label>
        <Textarea
          id="notes"
          value={values.notes}
          onChange={update('notes')}
          placeholder="Contexto da conta, produto, alertas..."
          rows={4}
        />
      </section>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex flex-wrap gap-2">
        <Button
          type="submit"
          disabled={saving}
          className="rounded-full bg-orange-600 text-white hover:bg-orange-700"
        >
          {saving ? (
            <>
              <Loader2 className="animate-spin" />
              {pendingLabel}
            </>
          ) : (
            submitLabel
          )}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" className="rounded-full" onClick={onCancel}>
            Cancelar
          </Button>
        )}
      </div>
    </form>
  )
}

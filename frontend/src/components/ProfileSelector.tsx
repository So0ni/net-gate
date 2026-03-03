import type { Profile } from '../api/types'

interface ProfileSelectorProps {
  profiles: Profile[]
  value?: number
  onChange: (profileId: number) => void
  disabled?: boolean
}

export function ProfileSelector({ profiles, value, onChange, disabled }: ProfileSelectorProps) {
  return (
    <select
      value={value ?? ''}
      onChange={(e) => onChange(Number(e.target.value))}
      disabled={disabled}
      className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white
                 focus:outline-none focus:ring-2 focus:ring-brand-500
                 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <option value="" disabled>选择预设</option>
      {profiles.map((p) => (
        <option key={p.id} value={p.id}>
          {p.name}
        </option>
      ))}
    </select>
  )
}

// Shared TypeScript types mirroring backend Pydantic schemas

export interface Profile {
  id: number
  name: string
  latency_ms: number
  jitter_ms: number
  loss_percent: number
  bandwidth_kbps: number
  is_builtin: boolean
  created_at?: string
}

export interface Device {
  mac_address: string
  alias: string
  ip_address?: string
  profile_id?: number
  mark_id: number
  created_at?: string
  profile?: Profile
}

export interface DeviceCreate {
  mac_address: string
  alias?: string
  ip_address?: string
}

export interface DeviceUpdate {
  alias?: string
  ip_address?: string
  profile_id?: number
}

export interface ProfileCreate {
  name: string
  latency_ms?: number
  jitter_ms?: number
  loss_percent?: number
  bandwidth_kbps?: number
}

export interface ProfileUpdate extends Partial<ProfileCreate> {}

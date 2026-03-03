import { useState, useEffect } from 'react'
import type { Profile, ProfileCreate, ProfileUpdate } from '../api/types'
import client from '../api/client'

const FIELD_DEFAULTS: ProfileCreate = {
  name: '',
  latency_ms: 0,
  jitter_ms: 0,
  loss_percent: 0,
  bandwidth_kbps: 0,
}

function ProfileModal({
  initial,
  onClose,
  onSuccess,
}: {
  initial?: Profile
  onClose: () => void
  onSuccess: () => void
}) {
  const [form, setForm] = useState<ProfileCreate>(
    initial
      ? {
          name: initial.name,
          latency_ms: initial.latency_ms,
          jitter_ms: initial.jitter_ms,
          loss_percent: initial.loss_percent,
          bandwidth_kbps: initial.bandwidth_kbps,
        }
      : { ...FIELD_DEFAULTS }
  )
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function set<K extends keyof ProfileCreate>(key: K, val: ProfileCreate[K]) {
    setForm((prev) => ({ ...prev, [key]: val }))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError('')
    if (!form.name.trim()) {
      setError('预设名称不能为空')
      return
    }
    setLoading(true)
    try {
      if (initial) {
        const patch: ProfileUpdate = { ...form }
        await client.patch(`/profiles/${initial.id}`, patch)
      } else {
        await client.post('/profiles', form)
      }
      onSuccess()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail ?? '操作失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const isEdit = !!initial

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-5">
          {isEdit ? '编辑预设' : '新建预设'}
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">
              预设名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              placeholder="如：弱网 2G"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">延迟 (ms)</label>
              <input
                type="number"
                min={0}
                value={form.latency_ms}
                onChange={(e) => set('latency_ms', Number(e.target.value))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">抖动 (ms)</label>
              <input
                type="number"
                min={0}
                value={form.jitter_ms}
                onChange={(e) => set('jitter_ms', Number(e.target.value))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">丢包 (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                step={0.1}
                value={form.loss_percent}
                onChange={(e) => set('loss_percent', Number(e.target.value))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                带宽 (Kbps)
                <span className="text-gray-400 text-xs ml-1">0=不限</span>
              </label>
              <input
                type="number"
                min={0}
                value={form.bandwidth_kbps}
                onChange={(e) => set('bandwidth_kbps', Number(e.target.value))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-200 rounded-lg py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '保存中…' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ProfileBadge({ label }: { label: string }) {
  return (
    <span className="inline-block bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full">
      {label}
    </span>
  )
}

function ProfileCard({
  profile,
  onEdit,
  onDelete,
}: {
  profile: Profile
  onEdit: (p: Profile) => void
  onDelete: (id: number) => void
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-gray-900 text-sm">{profile.name}</p>
          {profile.is_builtin && (
            <span className="text-xs text-blue-500 font-medium">内置</span>
          )}
        </div>
        {!profile.is_builtin && (
          <div className="flex gap-2">
            <button
              onClick={() => onEdit(profile)}
              className="text-xs text-gray-400 hover:text-blue-500 transition-colors"
            >
              编辑
            </button>
            <button
              onClick={() => onDelete(profile.id)}
              className="text-xs text-gray-400 hover:text-red-400 transition-colors"
            >
              删除
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 pt-1 border-t border-gray-50">
        <ProfileBadge label={`延迟 ${profile.latency_ms}ms`} />
        <ProfileBadge label={`抖动 ${profile.jitter_ms}ms`} />
        <ProfileBadge label={`丢包 ${profile.loss_percent}%`} />
        <ProfileBadge
          label={
            profile.bandwidth_kbps === 0
              ? '带宽不限'
              : `带宽 ${profile.bandwidth_kbps >= 1024
                  ? (profile.bandwidth_kbps / 1024).toFixed(0) + 'Mbps'
                  : profile.bandwidth_kbps + 'Kbps'}`
          }
        />
      </div>
    </div>
  )
}

export default function Profiles() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<Profile | null>(null)

  async function fetchProfiles() {
    try {
      const res = await client.get<Profile[]>('/profiles')
      setProfiles(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfiles()
  }, [])

  async function handleDelete(id: number) {
    const target = profiles.find((p) => p.id === id)
    if (!confirm(`确认删除预设「${target?.name}」？`)) return
    try {
      await client.delete(`/profiles/${id}`)
      setProfiles((prev) => prev.filter((p) => p.id !== id))
    } catch {
      // error handled by interceptor
    }
  }

  const builtins = profiles.filter((p) => p.is_builtin)
  const customs = profiles.filter((p) => !p.is_builtin)

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">网络预设</h1>
          <p className="text-sm text-gray-500 mt-0.5">管理自定义网络限速方案</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          + 新建预设
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400 text-sm">加载中…</div>
      ) : (
        <>
          {builtins.length > 0 && (
            <section className="mb-8">
              <h2 className="text-sm font-medium text-gray-500 mb-3">内置预设</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {builtins.map((p) => (
                  <ProfileCard
                    key={p.id}
                    profile={p}
                    onEdit={setEditTarget}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            </section>
          )}

          <section>
            <h2 className="text-sm font-medium text-gray-500 mb-3">自定义预设</h2>
            {customs.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-gray-100 rounded-xl">
                <p className="text-gray-400 text-sm">暂无自定义预设</p>
                <p className="text-gray-300 text-xs mt-1">点击「新建预设」创建</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {customs.map((p) => (
                  <ProfileCard
                    key={p.id}
                    profile={p}
                    onEdit={setEditTarget}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {showCreate && (
        <ProfileModal
          onClose={() => setShowCreate(false)}
          onSuccess={fetchProfiles}
        />
      )}

      {editTarget && (
        <ProfileModal
          initial={editTarget}
          onClose={() => setEditTarget(null)}
          onSuccess={fetchProfiles}
        />
      )}
    </div>
  )
}

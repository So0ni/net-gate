import { useState, useEffect, useCallback } from 'react'
import type { Device, Profile, DeviceCreate } from '../api/types'
import client from '../api/client'
import { DeviceCard } from '../components/DeviceCard'
import { useWebSocket } from '../hooks/useWebSocket'

function RegisterModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void
  onSuccess: () => void
}) {
  const [mac, setMac] = useState('')
  const [alias, setAlias] = useState('')
  const [ip, setIp] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const macRegex = /^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$/

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError('')

    if (!macRegex.test(mac)) {
      setError('MAC 地址格式不正确，应为 xx:xx:xx:xx:xx:xx')
      return
    }

    setLoading(true)
    try {
      const body: DeviceCreate = { mac_address: mac.toLowerCase() }
      if (alias.trim()) body.alias = alias.trim()
      if (ip.trim()) body.ip_address = ip.trim()
      await client.post('/devices', body)
      onSuccess()
      onClose()
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(detail === 'Device already registered' ? '该设备已注册' : (detail ?? '注册失败，请重试'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-5">注册设备</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">
              MAC 地址 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={mac}
              onChange={(e) => setMac(e.target.value)}
              placeholder="aa:bb:cc:dd:ee:ff"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">设备别名</label>
            <input
              type="text"
              value={alias}
              onChange={(e) => setAlias(e.target.value)}
              placeholder="可选"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">IP 地址</label>
            <input
              type="text"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              placeholder="可选，如 192.168.1.100"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
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
              {loading ? '注册中…' : '注册'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [devices, setDevices] = useState<Device[]>([])
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  const fetchAll = useCallback(async () => {
    try {
      const [devRes, proRes] = await Promise.all([
        client.get<Device[]>('/devices'),
        client.get<Profile[]>('/profiles'),
      ])
      setDevices(devRes.data)
      setProfiles(proRes.data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  useWebSocket((msg) => {
    if (msg.event === 'device_updated') {
      const updated = msg.data as Device
      setDevices((prev) => {
        const exists = prev.find((d) => d.mac_address === updated.mac_address)
        return exists
          ? prev.map((d) => (d.mac_address === updated.mac_address ? updated : d))
          : [...prev, updated]
      })
    } else if (msg.event === 'device_deleted') {
      const { mac_address } = msg.data as { mac_address: string }
      setDevices((prev) => prev.filter((d) => d.mac_address !== mac_address))
    }
  })

  async function handleProfileChange(mac: string, profileId: number) {
    try {
      const res = await client.patch<Device>(`/devices/${mac}`, { profile_id: profileId })
      setDevices((prev) => prev.map((d) => (d.mac_address === mac ? res.data : d)))
    } catch {
      // error handled by interceptor
    }
  }

  async function handleDelete(mac: string) {
    if (!confirm(`确认移除设备 ${mac}？该操作将清除其所有流量规则。`)) return
    try {
      await client.delete(`/devices/${mac}`)
      setDevices((prev) => prev.filter((d) => d.mac_address !== mac))
    } catch {
      // error handled by interceptor
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">设备列表</h1>
          <p className="text-sm text-gray-500 mt-0.5">共 {devices.length} 台设备</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          + 注册设备
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400 text-sm">加载中…</div>
      ) : devices.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-4xl mb-3">📡</div>
          <p className="text-gray-500 text-sm">暂无设备</p>
          <p className="text-gray-400 text-xs mt-1">
            点击「注册设备」添加需要限速的设备
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices.map((device) => (
            <DeviceCard
              key={device.mac_address}
              device={device}
              profiles={profiles}
              onProfileChange={handleProfileChange}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showModal && (
        <RegisterModal
          onClose={() => setShowModal(false)}
          onSuccess={fetchAll}
        />
      )}
    </div>
  )
}

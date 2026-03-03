import { Device, Profile } from '../api/types'
import { ProfileSelector } from './ProfileSelector'
import { StatusDot } from './StatusDot'

interface DeviceCardProps {
  device: Device
  profiles: Profile[]
  onProfileChange: (mac: string, profileId: number) => void
  onDelete: (mac: string) => void
}

export function DeviceCard({ device, profiles, onProfileChange, onDelete }: DeviceCardProps) {
  const currentProfile = profiles.find((p) => p.id === device.profile_id)

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <StatusDot online={true} />
          <div>
            <p className="font-semibold text-gray-900 text-sm leading-tight">
              {device.alias || '未命名设备'}
            </p>
            <p className="text-xs text-gray-400 font-mono mt-0.5">{device.mac_address}</p>
          </div>
        </div>
        <button
          onClick={() => onDelete(device.mac_address)}
          className="text-gray-300 hover:text-red-400 transition-colors text-xs"
        >
          移除
        </button>
      </div>

      {/* IP */}
      {device.ip_address && (
        <p className="text-xs text-gray-500 font-mono">{device.ip_address}</p>
      )}

      {/* Profile */}
      <div className="flex items-center justify-between pt-1 border-t border-gray-50">
        <span className="text-xs text-gray-400">当前策略</span>
        <ProfileSelector
          profiles={profiles}
          value={device.profile_id}
          onChange={(id) => onProfileChange(device.mac_address, id)}
        />
      </div>
    </div>
  )
}

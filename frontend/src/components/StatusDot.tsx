// Status indicator dot for device online state
interface StatusDotProps {
  online?: boolean
}

export function StatusDot({ online }: StatusDotProps) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${
        online ? 'bg-emerald-400' : 'bg-gray-300'
      }`}
    />
  )
}

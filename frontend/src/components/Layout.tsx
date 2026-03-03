import { Link, Outlet, useLocation } from 'react-router-dom'

export default function Layout() {
  const { pathname } = useLocation()

  const navItems = [
    { to: '/', label: '设备管理' },
    { to: '/profiles', label: '网络预设' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top Nav */}
      <header className="bg-white border-b border-gray-100 px-6 h-14 flex items-center justify-between">
        <span className="font-bold text-gray-900 tracking-tight">Network Gate</span>
        <nav className="flex gap-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pathname === item.to
                  ? 'bg-brand-50 text-brand-600'
                  : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>

      {/* Main */}
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}

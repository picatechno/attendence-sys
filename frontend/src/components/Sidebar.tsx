type Page = 'login' | 'dashboard' | 'employees' | 'attendance' | 'shifts'

const navItems: { page: Page; label: string; icon: string }[] = [
  { page: 'dashboard', label: 'Dashboard', icon: '📊' },
  { page: 'employees', label: 'Employees', icon: '👥' },
  { page: 'attendance', label: 'Attendance', icon: '📋' },
  { page: 'shifts', label: 'Shifts', icon: '🕐' },
]

export default function Sidebar({
  current,
  onNavigate,
  onLogout,
}: {
  current: Page
  onNavigate: (p: Page) => void
  onLogout: () => void
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>⏱ Attendance</h2>
      </div>
      <nav className="sidebar-nav">
        {navItems.map(item => (
          <button
            key={item.page}
            className={`nav-item ${current === item.page ? 'active' : ''}`}
            onClick={() => onNavigate(item.page)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <button className="nav-item logout" onClick={onLogout}>
          <span className="nav-icon">🚪</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}

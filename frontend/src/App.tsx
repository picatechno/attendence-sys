import { useState, useEffect } from 'react'
import { api, setToken, getToken } from './api/client'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Employees from './pages/Employees'
import Attendance from './pages/Attendance'
import Shifts from './pages/Shifts'

type Page = 'login' | 'dashboard' | 'employees' | 'attendance' | 'shifts'

export default function App() {
  const [page, setPage] = useState<Page>(
    getToken() ? 'dashboard' : 'login'
  )

  useEffect(() => {
    const onHash = () => {
      const hash = window.location.hash.replace('#/', '') as Page
      if (hash && hash !== 'login') setPage(hash)
      else if (!getToken()) setPage('login')
    }
    window.addEventListener('hashchange', onHash)
    onHash()
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const navigate = (p: Page) => {
    setPage(p)
    window.location.hash = p === 'login' ? '#/login' : `#/${p}`
  }

  const handleLogin = async (email: string, password: string) => {
    const res = await api.login(email, password)
    setToken(res.access_token)
    navigate('dashboard')
  }

  const handleLogout = () => {
    setToken(null)
    navigate('login')
  }

  if (page === 'login') return <Login onLogin={handleLogin} />

  return (
    <div className="app-layout">
      <Sidebar current={page} onNavigate={navigate} onLogout={handleLogout} />
      <main className="main-content">
        {page === 'dashboard' && <Dashboard />}
        {page === 'employees' && <Employees />}
        {page === 'attendance' && <Attendance />}
        {page === 'shifts' && <Shifts />}
      </main>
    </div>
  )
}

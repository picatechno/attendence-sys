import { useState, useEffect } from 'react'
import { api } from '../api/client'

interface Stats {
  total_employees: number
  today_attendance: {
    total: number
    by_status: Record<string, number>
  }
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.dashboard()
      .then(setStats)
      .catch(e => setError(e.message))
  }, [])

  if (error) return <div className="error-card">{error}</div>
  if (!stats) return <div className="loading">Loading dashboard...</div>

  const statusColors: Record<string, string> = {
    present: '#22c55e',
    late: '#f59e0b',
    absent: '#ef4444',
    holiday: '#3b82f6',
    week_off: '#8b5cf6',
  }

  const statusLabels: Record<string, string> = {
    present: 'Present',
    late: 'Late',
    absent: 'Absent',
    holiday: 'Holiday',
    week_off: 'Week Off',
  }

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-value">{stats.total_employees}</div>
          <div className="kpi-label">Total Employees</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{stats.today_attendance.total}</div>
          <div className="kpi-label">Today's Attendance</div>
        </div>
      </div>

      <h3>Today's Status</h3>
      <div className="status-grid">
        {Object.entries(stats.today_attendance.by_status).map(([key, count]) => (
          <div key={key} className="status-card" style={{ borderLeftColor: statusColors[key] || '#888' }}>
            <div className="status-count">{count as number}</div>
            <div className="status-label">{statusLabels[key] || key}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

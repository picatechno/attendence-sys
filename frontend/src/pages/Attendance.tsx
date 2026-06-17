import { useState, useEffect } from 'react'
import { api } from '../api/client'

export default function Attendance() {
  const [records, setRecords] = useState<any[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.listAttendances()
      .then(r => setRecords(r.items || []))
      .catch(e => setError(e.message))
  }, [])

  const statusLabels: Record<string, string> = {
    present: 'Present',
    late: 'Late',
    absent: 'Absent',
    holiday: 'Holiday',
    week_off: 'Week Off',
  }

  const statusColors: Record<string, string> = {
    present: '#22c55e',
    late: '#f59e0b',
    absent: '#ef4444',
    holiday: '#3b82f6',
    week_off: '#8b5cf6',
  }

  return (
    <div>
      <div className="page-header">
        <h2>Attendance Records</h2>
      </div>
      {error && <div className="error">{error}</div>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Date</th>
            <th>Status</th>
            <th>Clock In</th>
            <th>Clock Out</th>
            <th>Work Hours</th>
            <th>Late (min)</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r: any) => (
            <tr key={r.id}>
              <td>{r.employee?.first_name || r.employee_id?.slice(0, 8)} {r.employee?.last_name || ''}</td>
              <td>{r.date}</td>
              <td>
                <span className="status-badge" style={{ backgroundColor: statusColors[r.status] || '#888' }}>
                  {statusLabels[r.status] || r.status}
                </span>
              </td>
              <td>{r.clock_in ? new Date(r.clock_in).toLocaleTimeString() : '-'}</td>
              <td>{r.clock_out ? new Date(r.clock_out).toLocaleTimeString() : '-'}</td>
              <td>{r.work_hours ? Math.floor(r.work_hours / 3600) + 'h ' + Math.floor((r.work_hours % 3600) / 60) + 'm' : '-'}</td>
              <td>{r.late_minutes || 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

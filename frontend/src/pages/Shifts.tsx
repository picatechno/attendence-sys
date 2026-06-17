import { useState, useEffect } from 'react'
import { api } from '../api/client'

export default function Shifts() {
  const [shifts, setShifts] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('18:00')
  const [graceLate, setGraceLate] = useState('15')
  const [error, setError] = useState('')

  const load = () => {
    api.listShifts().then(setShifts).catch(e => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.createShift({
        name, code,
        start_time: start,
        end_time: end,
        grace_late_minutes: parseInt(graceLate) || 0,
        grace_early_minutes: 0,
      })
      setShowForm(false)
      setName(''); setCode(''); setStart('09:00'); setEnd('18:00'); setGraceLate('15')
      load()
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Shifts</h2>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Shift'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="inline-form">
          <input placeholder="Name *" value={name} onChange={e => setName(e.target.value)} required />
          <input placeholder="Code *" value={code} onChange={e => setCode(e.target.value)} required />
          <input type="time" value={start} onChange={e => setStart(e.target.value)} required />
          <input type="time" value={end} onChange={e => setEnd(e.target.value)} required />
          <input type="number" placeholder="Grace Late (min)" value={graceLate} onChange={e => setGraceLate(e.target.value)} />
          <button type="submit" className="btn-primary">Save</button>
        </form>
      )}

      {error && <div className="error">{error}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Code</th>
            <th>Start</th>
            <th>End</th>
            <th>Grace Late</th>
          </tr>
        </thead>
        <tbody>
          {shifts.map((s: any) => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.code}</td>
              <td>{s.start_time}</td>
              <td>{s.end_time}</td>
              <td>{s.grace_late_minutes} min</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

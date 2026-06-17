import { useState, useEffect } from 'react'
import { api } from '../api/client'

export default function Employees() {
  const [employees, setEmployees] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [code, setCode] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const load = () => {
    api.listEmployees().then(r => setEmployees(r.items || [])).catch(e => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.createEmployee({ employee_code: code, first_name: firstName, last_name: lastName, email: email || undefined })
      setShowForm(false)
      setCode(''); setFirstName(''); setLastName(''); setEmail('')
      load()
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Employees</h2>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Employee'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="inline-form">
          <input placeholder="Code *" value={code} onChange={e => setCode(e.target.value)} required />
          <input placeholder="First Name *" value={firstName} onChange={e => setFirstName(e.target.value)} required />
          <input placeholder="Last Name *" value={lastName} onChange={e => setLastName(e.target.value)} required />
          <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <button type="submit" className="btn-primary">Save</button>
        </form>
      )}

      {error && <div className="error">{error}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Email</th>
            <th>Designation</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((emp: any) => (
            <tr key={emp.id}>
              <td>{emp.employee_code}</td>
              <td>{emp.first_name} {emp.last_name}</td>
              <td>{emp.email || '-'}</td>
              <td>{emp.designation || '-'}</td>
              <td><span className={emp.is_active ? 'badge-active' : 'badge-inactive'}>{emp.is_active ? 'Active' : 'Inactive'}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

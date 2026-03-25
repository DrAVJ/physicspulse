import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export default function Login() {
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { loginStudent } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await loginStudent(pin)
      navigate('/home')
    } catch (err: any) {
      setError(err.message || 'Invalid PIN')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', background:'#f0f4f8'}}>
      <div className="card" style={{padding:'2rem', minWidth:'320px'}}>
        <h1 style={{textAlign:'center', marginBottom:'0.5rem'}}>PhysicsPulse</h1>
        <p style={{textAlign:'center', color:'#666', marginBottom:'1.5rem'}}>Enter your student PIN to continue</p>
        <form onSubmit={handleSubmit}>
          <div style={{marginBottom:'1rem'}}>
            <label style={{display:'block', marginBottom:'0.25rem', fontWeight:500}}>Student PIN</label>
            <input
              type="text"
              value={pin}
              onChange={e => setPin(e.target.value)}
              placeholder="Enter PIN"
              className="form-control"
              style={{width:'100%', padding:'0.5rem', fontSize:'1.2rem', letterSpacing:'0.2rem', textAlign:'center'}}
              maxLength={8}
              required
            />
          </div>
          {error && <p style={{color:'red', marginBottom:'1rem'}}>{error}</p>}
          <button type="submit" className="btn btn-primary" style={{width:'100%'}} disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

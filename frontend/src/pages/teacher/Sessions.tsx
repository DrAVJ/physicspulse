import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { sessionsApi, videosApi } from '../../services/api'

export default function Sessions() {
  const [sessions, setSessions] = useState<any[]>([])
  const [videos, setVideos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ video_id: '', class_name: '' })

  useEffect(() => {
    Promise.all([sessionsApi.list(), videosApi.list()])
      .then(([sRes, vRes]) => { setSessions(sRes.data); setVideos(vRes.data) })
      .finally(() => setLoading(false))
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    await sessionsApi.create({ video_id: +form.video_id, class_name: form.class_name })
    setSessions((await sessionsApi.list()).data)
    setShowForm(false)
  }

  if (loading) return <div>Loading...</div>

  return (
    <div className="page">
      <div className="page-header">
        <h2>Sessions</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">+ New Session</button>
      </div>
      {showForm && (
        <form onSubmit={handleCreate} className="card">
          <select value={form.video_id} onChange={e => setForm({...form, video_id: e.target.value})} required>
            <option value="">Select Video</option>
            {videos.map((v: any) => <option key={v.id} value={v.id}>{v.title}</option>)}
          </select>
          <input placeholder="Class name" value={form.class_name} onChange={e => setForm({...form, class_name: e.target.value})} />
          <button type="submit" className="btn btn-primary">Create</button>
        </form>
      )}
      {sessions.map((s: any) => (
        <div key={s.id} className="card">
          <h3>Session #{s.id} - {s.class_name} <span className="badge">{s.status}</span></h3>
          <p>Join code: <strong>{s.join_code}</strong></p>
          <Link to={`/sessions/${s.id}/player`} className="btn btn-primary">Open Player</Link>
          <Link to={`/sessions/${s.id}/results`} className="btn btn-secondary">Results</Link>
          <Link to={`/sessions/${s.id}/recommendations`} className="btn btn-secondary">Recommendations</Link>
        </div>
      ))}
    </div>
  )
}

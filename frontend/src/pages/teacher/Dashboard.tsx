import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { videosApi, sessionsApi } from '../../services/api'

export default function Dashboard() {
  const [videos, setVideos] = useState<any[]>([])
  const [sessions, setSessions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([videosApi.list(), sessionsApi.list()])
      .then(([vRes, sRes]) => { setVideos(vRes.data); setSessions(sRes.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="page">
      <h2>Dashboard</h2>
      <div className="stats-grid">
        <div className="stat-card"><h3>{videos.length}</h3><p>Videos</p></div>
        <div className="stat-card"><h3>{sessions.length}</h3><p>Sessions</p></div>
        <div className="stat-card">
          <h3>{sessions.filter((s: any) => s.status === 'active').length}</h3>
          <p>Active Sessions</p>
        </div>
      </div>
      <div className="dashboard-actions">
        <Link to="/videos" className="btn btn-primary">Manage Videos</Link>
        <Link to="/sessions" className="btn btn-secondary">View Sessions</Link>
      </div>
      <h3>Recent Videos</h3>
      {videos.slice(0, 5).map((v: any) => (
        <div key={v.id} className="list-item">
          <span>{v.title}</span>
          <span className="badge">{v.status}</span>
          <Link to={`/videos/${v.id}`}>Edit</Link>
        </div>
      ))}
    </div>
  )
}

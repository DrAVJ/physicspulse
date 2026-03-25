import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'

interface Video {
  id: number
  title: string
  description: string
  youtube_url: string
  topic: string
}

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const { student, logout } = useAuth()

  useEffect(() => {
    api.get('/videos').then(r => {
      setVideos(r.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  return (
    <div style={{maxWidth:'900px', margin:'0 auto', padding:'1rem'}}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1.5rem'}}>
        <h1>PhysicsPulse</h1>
        <div>
          <span style={{marginRight:'1rem', color:'#555'}}>Hi, {student?.name || 'Student'}</span>
          <button className="btn btn-secondary" onClick={logout}>Logout</button>
        </div>
      </div>
      <h2 style={{marginBottom:'1rem'}}>Videos</h2>
      {loading ? (
        <p>Loading videos...</p>
      ) : (
        <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(280px,1fr))', gap:'1rem'}}>
          {videos.map(v => (
            <Link key={v.id} to={`/video/${v.id}`} style={{textDecoration:'none', color:'inherit'}}>
              <div className="card" style={{padding:'1rem', cursor:'pointer'}}>
                <div style={{background:'#e2e8f0', height:'160px', borderRadius:'4px', marginBottom:'0.75rem', display:'flex', alignItems:'center', justifyContent:'center'}}>
                  <span style={{fontSize:'2rem'}}>▶</span>
                </div>
                <h3 style={{marginBottom:'0.25rem', fontSize:'1rem'}}>{v.title}</h3>
                <p style={{color:'#666', fontSize:'0.85rem', margin:0}}>{v.topic}</p>
              </div>
            </Link>
          ))}
          {videos.length === 0 && <p style={{color:'#888'}}>No videos available yet.</p>}
        </div>
      )}
    </div>
  )
}

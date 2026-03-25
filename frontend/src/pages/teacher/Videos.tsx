import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { videosApi } from '../../services/api'

export default function Videos() {
  const [videos, setVideos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', youtube_url: '' })
  const navigate = useNavigate()

  useEffect(() => { videosApi.list().then(r => setVideos(r.data)).finally(() => setLoading(false)) }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    const res = await videosApi.create(form)
    navigate(`/videos/${res.data.id}`)
  }

  if (loading) return <div>Loading...</div>

  return (
    <div className="page">
      <div className="page-header">
        <h2>Videos</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">+ Add Video</button>
      </div>
      {showForm && (
        <form onSubmit={handleCreate} className="card">
          <h3>Add Video</h3>
          <input placeholder="Title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} required />
          <input placeholder="YouTube URL" value={form.youtube_url} onChange={e => setForm({...form, youtube_url: e.target.value})} />
          <textarea placeholder="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
          <button type="submit" className="btn btn-primary">Create</button>
        </form>
      )}
      {videos.map((v: any) => (
        <div key={v.id} className="card">
          <h3>{v.title}</h3>
          <span className="badge">{v.status}</span>
          <Link to={`/videos/${v.id}`} className="btn btn-secondary">Edit</Link>
        </div>
      ))}
    </div>
  )
}

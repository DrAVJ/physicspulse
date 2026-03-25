import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { videosApi, sessionsApi } from '../../services/api'

export default function VideoDetail() {
  const { videoId } = useParams()
  const [video, setVideo] = useState<any>(null)
  const [questions, setQuestions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('')

  useEffect(() => {
    if (!videoId) return
    Promise.all([videosApi.get(+videoId), videosApi.getQuestions(+videoId)])
      .then(([vRes, qRes]) => { setVideo(vRes.data); setQuestions(qRes.data) })
      .finally(() => setLoading(false))
  }, [videoId])

  const handleTranscribe = async () => {
    setStatus('Transcribing...')
    await videosApi.transcribe(+videoId!)
    const res = await videosApi.get(+videoId!)
    setVideo(res.data)
    setStatus('Transcribed!')
  }

  const handleDetect = async () => {
    setStatus('Detecting concepts...')
    await videosApi.detectConcepts(+videoId!)
    setStatus('Concepts detected!')
  }

  const handleGenerate = async () => {
    setStatus('Generating questions...')
    await videosApi.generateQuestions(+videoId!, 0)
    const qRes = await videosApi.getQuestions(+videoId!)
    setQuestions(qRes.data)
    setStatus('Questions generated!')
  }

  const handleStartSession = async () => {
    const res = await sessionsApi.create({ video_id: +videoId!, class_name: 'Physics Class' })
    window.location.href = `/sessions/${res.data.id}/player`
  }

  if (loading) return <div>Loading...</div>
  if (!video) return <div>Not found</div>

  return (
    <div className="page">
      <h2>{video.title}</h2>
      {status && <div className="status-msg">{status}</div>}
      {video.youtube_url && <div className="video-embed">
        <iframe src={video.youtube_url.replace('watch?v=', 'embed/')} title="Video" allowFullScreen />
      </div>}
      <div className="action-bar">
        <button onClick={handleTranscribe} className="btn btn-secondary">Transcribe</button>
        <button onClick={handleDetect} className="btn btn-secondary">Detect Concepts</button>
        <button onClick={handleGenerate} className="btn btn-secondary">Generate Questions</button>
        <button onClick={handleStartSession} className="btn btn-primary">Start Session</button>
      </div>
      <h3>Questions ({questions.length})</h3>
      {questions.map((q: any) => (
        <div key={q.id} className="card">
          <p><strong>{q.question_text}</strong></p>
          <ul>{(q.options || []).map((o: string, i: number) => (
            <li key={i} style={{ color: i === q.correct_index ? 'green' : 'inherit' }}>{o}</li>
          ))}</ul>
          <small>{q.concept_tag}</small>
        </div>
      ))}
    </div>
  )
}

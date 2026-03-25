import React, { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { sessionsApi, answersApi } from '../../services/api'

export default function TeacherPlayer() {
  const { sessionId } = useParams()
  const [session, setSession] = useState<any>(null)
  const [questions, setQuestions] = useState<any[]>([])
  const [activeQ, setActiveQ] = useState<any>(null)
  const [distribution, setDistribution] = useState<any>(null)
  const [studentCount, setStudentCount] = useState(0)
  const [answerCount, setAnswerCount] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!sessionId) return
    sessionsApi.get(+sessionId).then(r => { setSession(r.data); setQuestions(r.data.questions || []) })
    const ws = new WebSocket(`ws://${window.location.host}/ws/teacher/${sessionId}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'student_joined') setStudentCount(msg.student_count)
      if (msg.type === 'answer_count_update') setAnswerCount(msg.count)
      if (msg.type === 'question_closed') setDistribution(msg.distribution)
    }
    return () => ws.close()
  }, [sessionId])

  const activate = (q: any) => {
    setActiveQ(q); setAnswerCount(0); setDistribution(null)
    wsRef.current?.send(JSON.stringify({ type: 'activate_question', question_id: q.id }))
  }

  const closeQ = () => {
    wsRef.current?.send(JSON.stringify({ type: 'close_question', question_id: activeQ.id }))
    answersApi.getDistribution(+sessionId!, activeQ.id).then(r => setDistribution(r.data))
  }

  if (!session) return <div>Loading...</div>

  return (
    <div className="page">
      <h2>Teacher Player #{sessionId}</h2>
      <p>Join code: <strong style={{fontSize:'2em', color:'#2563eb'}}>{session.join_code}</strong></p>
      <p>Students: {studentCount} | Status: {session.status}</p>
      {session.status === 'waiting' && <button onClick={() => sessionsApi.start(+sessionId!).then(r=>setSession(r.data))} className="btn btn-primary">Start</button>}
      {session.status === 'active' && <button onClick={() => sessionsApi.close(+sessionId!).then(r=>setSession(r.data))} className="btn btn-danger">End Session</button>}
      <div style={{display:'flex', gap:'1rem', marginTop:'1rem'}}>
        <div style={{flex:1}}>
          <h3>Questions</h3>
          {questions.map((q: any) => (
            <div key={q.id} className={`card ${activeQ?.id === q.id ? 'active' : ''}`}>
              <p>{q.question_text}</p>
              <button onClick={() => activate(q)} className="btn btn-secondary" disabled={session.status !== 'active'}>Activate</button>
            </div>
          ))}
        </div>
        {activeQ && (
          <div style={{flex:1}}>
            <h3>Active: {activeQ.question_text}</h3>
            <p>Answers received: {answerCount}</p>
            <button onClick={closeQ} className="btn btn-warning">Close & Show Results</button>
            {distribution && (
              <div>
                {(activeQ.options||[]).map((opt:string,i:number)=>(
                  <div key={i} style={{display:'flex', alignItems:'center', gap:'0.5rem', margin:'0.5rem 0', color: i===activeQ.correct_index?'green':'inherit'}}>
                    <span style={{minWidth:'200px'}}>{opt}</span>
                    <div style={{height:'24px', background: i===activeQ.correct_index?'#22c55e':'#3b82f6', width:`${(distribution[i]||0)*20}px`, minWidth:'4px'}} />
                    <span>{distribution[i]||0}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      <Link to={`/sessions/${sessionId}/results`} className="btn btn-secondary" style={{marginTop:'1rem', display:'inline-block'}}>Full Results</Link>
    </div>
  )
}

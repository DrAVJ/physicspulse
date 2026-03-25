import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';

interface Question {
  id: number;
  text: string;
  options: { text: string; is_correct: boolean }[];
  concept_tag?: string;
}

type Phase = 'waiting' | 'question' | 'answered' | 'closed';

export default function StudentLive() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const wsRef = useRef<WebSocket | null>(null);
  const [phase, setPhase] = useState<Phase>('waiting');
  const [question, setQuestion] = useState<Question | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [studentCount, setStudentCount] = useState(0);
  const studentId = sessionStorage.getItem('student_id');
  const studentName = sessionStorage.getItem('student_name') || 'Elev';

  useEffect(() => {
    if (!studentId || !sessionId) {
      navigate('/student/join');
      return;
    }

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${
      window.location.host
    }/ws/student/${sessionId}?student_id=${studentId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === 'question_activated') {
          setQuestion(msg.question);
          setSelectedIndex(null);
          setIsCorrect(null);
          setPhase('question');
        } else if (msg.type === 'question_closed') {
          setPhase('answered');
        } else if (msg.type === 'session_closed') {
          setPhase('closed');
        } else if (msg.type === 'student_count') {
          setStudentCount(msg.count);
        }
      } catch {}
    };

    ws.onclose = () => {
      console.log('WS closed');
    };

    return () => ws.close();
  }, [sessionId, studentId, navigate]);

  const submitAnswer = async (idx: number) => {
    if (selectedIndex !== null || !question) return;
    setSelectedIndex(idx);
    try {
      const result = await api.submitAnswer({
        session_id: Number(sessionId),
        question_id: question.id,
        student_id: Number(studentId),
        chosen_index: idx,
      });
      setIsCorrect(result.is_correct);
    } catch (err) {
      console.error('Failed to submit answer', err);
    }
  };

  if (phase === 'waiting') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 to-indigo-800 flex items-center justify-center p-4">
        <div className="text-center text-white">
          <div className="text-6xl mb-6 animate-pulse">⏳</div>
          <h2 className="text-2xl font-bold mb-2">Hej, {studentName}!</h2>
          <p className="text-blue-200 text-lg">Väntar på att läraren startar lektionen...</p>
          {studentCount > 0 && (
            <p className="text-blue-300 mt-4">{studentCount} elever anslutna</p>
          )}
        </div>
      </div>
    );
  }

  if (phase === 'closed') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center p-4">
        <div className="text-center text-white">
          <div className="text-6xl mb-6">✅</div>
          <h2 className="text-2xl font-bold mb-2">Lektionen är slut!</h2>
          <p className="text-green-200">Tack för att du deltog, {studentName}!</p>
          <button
            onClick={() => navigate('/student/join')}
            className="mt-6 bg-white text-green-600 font-bold py-3 px-8 rounded-xl hover:bg-green-50"
          >
            Gå med i ny lektion
          </button>
        </div>
      </div>
    );
  }

  if (phase === 'question' && question) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <div className="bg-blue-600 text-white p-4 text-center">
          <p className="text-sm opacity-75">PhysicsPulse</p>
        </div>
        <div className="flex-1 p-4 max-w-lg mx-auto w-full">
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-4">
            {question.concept_tag && (
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full mb-3 inline-block">
                {question.concept_tag}
              </span>
            )}
            <p className="text-lg font-semibold text-gray-900 leading-relaxed">{question.text}</p>
          </div>

          <div className="space-y-3">
            {question.options.map((opt, idx) => {
              let cls = 'w-full text-left p-4 rounded-xl border-2 font-medium transition-all ';
              if (selectedIndex === null) {
                cls += 'border-gray-200 bg-white hover:border-blue-400 hover:bg-blue-50 active:bg-blue-100';
              } else if (idx === selectedIndex) {
                cls += isCorrect ? 'border-green-500 bg-green-50 text-green-700' : 'border-red-500 bg-red-50 text-red-700';
              } else {
                cls += 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed';
              }
              return (
                <button
                  key={idx}
                  className={cls}
                  onClick={() => submitAnswer(idx)}
                  disabled={selectedIndex !== null}
                >
                  <span className="inline-block w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-sm font-bold mr-3 text-center leading-7">
                    {String.fromCharCode(65 + idx)}
                  </span>
                  {opt.text}
                </button>
              );
            })}
          </div>

          {selectedIndex !== null && (
            <div className={`mt-6 p-4 rounded-xl text-center font-bold text-lg ${
              isCorrect ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {isCorrect ? '✅ Rätt svar!' : '❌ Fel svar. Väntar på nästa fråga...'}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="text-4xl mb-4">⏳</div>
        <p className="text-gray-600">Väntar på nästa fråga...</p>
      </div>
    </div>
  );
}

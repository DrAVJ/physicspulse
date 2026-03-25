import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../services/api';

interface QuestionResult {
  question_id: number;
  question_text: string;
  concept_tag: string;
  total_answers: number;
  correct_count: number;
  correct_pct: number;
  option_distribution: number[];
  correct_index: number;
}

interface SessionResults {
  session_id: number;
  join_code: string;
  class_name: string;
  student_count: number;
  question_results: QuestionResult[];
}

export default function Results() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [results, setResults] = useState<SessionResults | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;
    api.getSessionResults(Number(sessionId))
      .then(setResults)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleExportCSV = async () => {
    if (!sessionId) return;
    try {
      const blob = await api.exportSessionCSV(Number(sessionId));
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `session_${sessionId}_results.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="p-8 text-center">Laddar resultat...</div>;
  if (!results) return <div className="p-8 text-center text-red-600">Kunde inte hämta resultat.</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to="/teacher/sessions" className="text-blue-600 hover:underline text-sm">← Sessioner</Link>
          <h1 className="text-2xl font-bold mt-1">Resultat: {results.class_name || results.join_code}</h1>
          <p className="text-gray-500">{results.student_count} elever deltog</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportCSV}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium"
          >
            Exportera CSV
          </button>
          <Link
            to={`/teacher/sessions/${sessionId}/recommendations`}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 text-sm font-medium"
          >
            AI-rekommendationer
          </Link>
        </div>
      </div>

      <div className="space-y-6">
        {results.question_results.map((qr, idx) => (
          <div key={qr.question_id} className="bg-white rounded-xl shadow p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full mr-2">
                  Fråga {idx + 1}
                </span>
                {qr.concept_tag && (
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                    {qr.concept_tag}
                  </span>
                )}
                <p className="mt-2 font-semibold text-gray-900">{qr.question_text}</p>
              </div>
              <div className="ml-4 text-right">
                <div className={`text-2xl font-bold ${
                  qr.correct_pct >= 70 ? 'text-green-600' : qr.correct_pct >= 40 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {qr.correct_pct.toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">{qr.correct_count}/{qr.total_answers} rätt</div>
              </div>
            </div>

            <div className="space-y-2">
              {qr.option_distribution.map((count, optIdx) => {
                const pct = qr.total_answers > 0 ? (count / qr.total_answers) * 100 : 0;
                const isCorrect = optIdx === qr.correct_index;
                return (
                  <div key={optIdx} className="flex items-center gap-3">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      isCorrect ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {String.fromCharCode(65 + optIdx)}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded-full h-6 relative overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isCorrect ? 'bg-green-400' : 'bg-blue-300'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                      <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-gray-700">
                        {count} svar ({pct.toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../services/api';

interface Recommendation {
  concept: string;
  misconception: string;
  intervention: string;
  priority: 'high' | 'medium' | 'low';
  evidence: string;
}

interface RecommendationsData {
  session_id: number;
  generated_at: string;
  summary: string;
  recommendations: Recommendation[];
  strengths: string[];
  areas_for_improvement: string[];
}

export default function Recommendations() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [data, setData] = useState<RecommendationsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const load = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const result = await api.getRecommendations(Number(sessionId));
      setData(result);
    } catch (err: any) {
      if (err?.response?.status === 404) {
        setData(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [sessionId]);

  const handleGenerate = async () => {
    if (!sessionId) return;
    setGenerating(true);
    try {
      const result = await api.generateRecommendations(Number(sessionId));
      setData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const priorityColor = (p: string) => {
    if (p === 'high') return 'bg-red-100 text-red-700 border-red-200';
    if (p === 'medium') return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    return 'bg-green-100 text-green-700 border-green-200';
  };

  if (loading) return <div className="p-8 text-center">Laddar rekommendationer...</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to={`/teacher/sessions/${sessionId}/results`} className="text-blue-600 hover:underline text-sm">
            ← Resultat
          </Link>
          <h1 className="text-2xl font-bold mt-1">AI-pedagogiska rekommendationer</h1>
          <p className="text-gray-500 text-sm">Baserat på forskning inom Physics Education Research (PER)</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium"
        >
          {generating ? 'Genererar...' : data ? 'Regenerera' : 'Generera rekommendationer'}
        </button>
      </div>

      {!data && !generating && (
        <div className="text-center py-16 text-gray-500">
          <div className="text-5xl mb-4">🤖</div>
          <p>Inga rekommendationer ännu.</p>
          <p className="text-sm mt-1">Klicka på knappen ovan för att generera AI-analys av lektionsresultaten.</p>
        </div>
      )}

      {generating && (
        <div className="text-center py-16">
          <div className="text-5xl mb-4 animate-spin">⚙️</div>
          <p className="text-gray-600">AI analyserar resultat och genererar pedagogiska rekommendationer...</p>
          <p className="text-sm text-gray-400 mt-2">Detta kan ta 10-30 sekunder</p>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-5">
            <h2 className="font-bold text-purple-900 mb-2">📊 Sammanfattning</h2>
            <p className="text-purple-800">{data.summary}</p>
          </div>

          {/* Strengths */}
          {data.strengths?.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-5">
              <h2 className="font-bold text-green-900 mb-3">✅ Styrkor</h2>
              <ul className="space-y-1">
                {data.strengths.map((s, i) => (
                  <li key={i} className="text-green-800 text-sm flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">•</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Areas for improvement */}
          {data.areas_for_improvement?.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-xl p-5">
              <h2 className="font-bold text-orange-900 mb-3">🎯 Områden att förbättra</h2>
              <ul className="space-y-1">
                {data.areas_for_improvement.map((a, i) => (
                  <li key={i} className="text-orange-800 text-sm flex items-start gap-2">
                    <span className="text-orange-500 mt-0.5">•</span>{a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          <h2 className="font-bold text-gray-900 text-lg">📚 Specifika interventioner</h2>
          {data.recommendations.map((rec, i) => (
            <div key={i} className={`border rounded-xl p-5 ${priorityColor(rec.priority)}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="font-bold">{rec.concept}</span>
                  {rec.misconception && (
                    <span className="ml-2 text-sm opacity-75">Missuppfattning: {rec.misconception}</span>
                  )}
                </div>
                <span className={`text-xs font-bold px-2 py-1 rounded-full border ${priorityColor(rec.priority)}`}>
                  {rec.priority === 'high' ? 'HÖG PRIORITET' : rec.priority === 'medium' ? 'MEDEL' : 'LÅG'}
                </span>
              </div>
              <p className="font-medium mb-2">{rec.intervention}</p>
              {rec.evidence && (
                <p className="text-sm opacity-75 italic">📚 {rec.evidence}</p>
              )}
            </div>
          ))}

          <p className="text-xs text-gray-400 text-center">
            Genererat: {new Date(data.generated_at).toLocaleString('sv-SE')}
          </p>
        </div>
      )}
    </div>
  );
}

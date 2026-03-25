import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';

export default function StudentJoin() {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !name.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.joinSession(code.trim().toUpperCase(), name.trim());
      // Store student info in sessionStorage
      sessionStorage.setItem('student_id', String(data.student_id));
      sessionStorage.setItem('student_name', name.trim());
      sessionStorage.setItem('session_id', String(data.session_id));
      sessionStorage.setItem('join_code', code.trim().toUpperCase());
      navigate(`/student/live/${data.session_id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Kunde inte gå med i sessionen. Kontrollera koden.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-indigo-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">⚡</div>
          <h1 className="text-3xl font-bold text-gray-900">PhysicsPulse</h1>
          <p className="text-gray-500 mt-2">Gå med i en lektion</p>
        </div>

        <form onSubmit={handleJoin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lektionskod</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="t.ex. ABCD1234"
              maxLength={8}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-xl text-center font-mono tracking-widest focus:border-blue-500 focus:outline-none uppercase"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ditt namn</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Förnamn Efternamn"
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-lg focus:border-blue-500 focus:outline-none"
            />
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 rounded-lg p-3 text-sm">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading || !code.trim() || !name.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-bold py-4 px-6 rounded-xl text-lg transition-colors"
          >
            {loading ? 'Ansluter...' : 'Gå med i lektionen'}
          </button>
        </form>
      </div>
    </div>
  );
}

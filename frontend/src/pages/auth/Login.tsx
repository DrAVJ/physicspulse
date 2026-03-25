import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      navigate('/teacher/dashboard');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Inloggning misslyckades.');
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
          <p className="text-gray-500 mt-2">Logga in som lärare</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">E-post</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 focus:border-blue-500 focus:outline-none"
              placeholder="din@email.se" autoFocus />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lösenord</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 focus:border-blue-500 focus:outline-none"
              placeholder="••••••••" />
          </div>
          {error && <div className="bg-red-50 text-red-600 rounded-lg p-3 text-sm">{error}</div>}
          <button type="submit" disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-bold py-4 px-6 rounded-xl text-lg transition-colors">
            {loading ? 'Loggar in...' : 'Logga in'}
          </button>
        </form>
        <p className="mt-6 text-center text-gray-500 text-sm">
          Inget konto?{' '}
          <Link to="/register" className="text-blue-600 hover:underline font-medium">Registrera dig</Link>
        </p>
        <div className="mt-4 pt-4 border-t text-center">
          <Link to="/student/join" className="text-gray-500 hover:text-gray-700 text-sm">
            → Gå med som elev istället
          </Link>
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { HardHat } from 'lucide-react';
import api from '../lib/api';

const DEMO_USERS = [
  { email: 'director@demo.com', role: 'Project Director' },
  { email: 'pm@demo.com', role: 'Project Manager' },
  { email: 'se@demo.com', role: 'Site Engineer' },
  { email: 'qi@demo.com', role: 'Quality Inspector' },
  { email: 'contractor@demo.com', role: 'Contractor' },
  { email: 'store@demo.com', role: 'Store Keeper' },
  { email: 'finance@demo.com', role: 'Finance Officer' },
  { email: 'auditor@demo.com', role: 'Auditor' }
];

export default function Login() {
  const [email, setEmail] = useState('pm@demo.com');
  const [password, setPassword] = useState('demo1234');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const response = await api.post('/api/auth/login', {
        email: email,
        password: password
      });
      
      localStorage.setItem('token', response.data.access_token);
      navigate('/projects');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoUserClick = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('demo1234');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <HardHat className="h-12 w-12 text-amber-500" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900">
          ConstructFlow
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Sign in to your account
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full max-w-4xl flex flex-col md:flex-row gap-6 items-start justify-center">
        
        {/* Login Form */}
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 border border-slate-200 w-full md:w-[400px]">
          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-slate-700">Email</label>
              <div className="mt-1">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Password</label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm"
                />
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>
        </div>

        {/* Demo Users Panel */}
        <div className="bg-white py-6 px-6 shadow sm:rounded-lg border border-slate-200 w-full md:w-[350px]">
          <h3 className="text-lg font-medium text-slate-900 mb-4 border-b pb-2">Quick Login (Testing)</h3>
          <p className="text-sm text-slate-500 mb-4">Click any persona below to autofill credentials.</p>
          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-2">
            {DEMO_USERS.map((user) => (
              <button
                key={user.email}
                type="button"
                onClick={() => handleDemoUserClick(user.email)}
                className="w-full text-left p-3 border border-slate-200 rounded-md hover:bg-slate-50 hover:border-amber-300 transition-colors group flex flex-col"
              >
                <span className="text-sm font-semibold text-slate-700 group-hover:text-amber-700">{user.role}</span>
                <span className="text-xs text-slate-500 mt-1">{user.email}</span>
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

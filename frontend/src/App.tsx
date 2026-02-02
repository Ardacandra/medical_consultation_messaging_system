import { useState, useEffect } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import ClinicianDashboard from './components/ClinicianDashboard';
import Login from './components/Login';

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [role, setRole] = useState<string | null>(localStorage.getItem('user_role'));
  const [view, setView] = useState<'patient' | 'clinician'>('patient');

  useEffect(() => {
    if (token) {
      // Optionally validate token expiry here or rely on API 401s
    }
  }, [token]);

  const handleLogin = (newToken: string, newRole: string) => {
    localStorage.setItem('access_token', newToken);
    localStorage.setItem('user_role', newRole);
    setToken(newToken);
    setRole(newRole);
    // Auto-switch view based on role
    if (newRole === 'clinician') setView('clinician');
    else setView('patient');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    setToken(null);
    setRole(null);
    setView('patient');
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8 font-sans">
      <header className="mb-8 flex justify-between items-center bg-white p-4 rounded shadow">
        <h1 className="text-2xl font-bold text-gray-800">Nightingale AI</h1>
        <div className="flex items-center gap-4">
          <div className="space-x-4">
            {role !== 'clinician' && (
              <button
                onClick={() => setView('patient')}
                className={`px-4 py-2 rounded ${view === 'patient' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
              >
                Patient View
              </button>
            )}
            {role === 'clinician' && (
              <span className="px-4 py-2 rounded bg-amber-100 text-amber-800 font-bold border border-amber-200">
                Clinician Workspace
              </span>
            )}
          </div>
          <button onClick={handleLogout} className="text-red-500 hover:text-red-700 text-sm underline">
            Logout
          </button>
        </div>
      </header>

      <main className="flex justify-center">
        {view === 'patient' ? <ChatInterface token={token} /> : <ClinicianDashboard token={token} />}
      </main>
    </div>
  );
}

export default App;

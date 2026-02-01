import { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import ClinicianDashboard from './components/ClinicianDashboard';

function App() {
  const [view, setView] = useState<'patient' | 'clinician'>('patient');

  return (
    <div className="min-h-screen bg-gray-100 p-8 font-sans">
      <header className="mb-8 flex justify-between items-center bg-white p-4 rounded shadow">
        <h1 className="text-2xl font-bold text-gray-800">Nightingale Prototype</h1>
        <div className="space-x-4">
          <button
            onClick={() => setView('patient')}
            className={`px-4 py-2 rounded ${view === 'patient' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Patient View
          </button>
          <button
            onClick={() => setView('clinician')}
            className={`px-4 py-2 rounded ${view === 'clinician' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Clinician View
          </button>
        </div>
      </header>

      <main className="flex justify-center">
        {view === 'patient' ? <ChatInterface /> : <ClinicianDashboard />}
      </main>
    </div>
  );
}

export default App;

import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
import Agents from './pages/Agents';
import Debate from './pages/Debate';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
  { id: 'predict', label: 'Predict', icon: '🎯' },
  { id: 'debate', label: 'Debate', icon: '⚔️' },
  { id: 'agents', label: 'Agents', icon: '🤖' },
];

export default function App() {
  const [tab, setTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <header className="border-b border-gray-800 bg-[#0d0d14]">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🪙</span>
            <h1 className="text-2xl font-bold text-white tracking-tight">CoinToss</h1>
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full font-medium">v0.1</span>
          </div>
          <nav className="flex gap-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  tab === t.id
                    ? 'bg-yellow-500/20 text-yellow-400'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="mr-1.5">{t.icon}</span>
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'predict' && <Predict />}
        {tab === 'debate' && <Debate />}
        {tab === 'agents' && <Agents />}
      </main>
    </div>
  );
}

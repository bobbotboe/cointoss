import { useState, useEffect } from 'react';
import { api } from '../api';
import Card from '../components/Card';

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    api.agents().then(setAgents);
  }, []);

  const loadDetail = async (id) => {
    setSelected(id);
    const d = await api.agentDetail(id);
    setDetail(d);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Agents</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map(a => (
          <button
            key={a.id}
            onClick={() => loadDetail(a.id)}
            className={`text-left bg-[#12121a] border rounded-xl p-5 transition-all hover:border-yellow-500/50 ${
              selected === a.id ? 'border-yellow-500/50 ring-1 ring-yellow-500/20' : 'border-gray-800'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">{a.emoji}</span>
              <div>
                <h3 className="text-white font-semibold">{a.name}</h3>
                <p className="text-xs text-gray-500">{a.id}</p>
              </div>
            </div>
            <p className="text-sm text-gray-400">{a.perspective}</p>
          </button>
        ))}
      </div>

      {/* Detail panel */}
      {detail && (
        <Card title={`${detail.emoji} ${detail.name} — Track Record`}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat label="Predictions" value={detail.stats.total_predictions} />
            <Stat label="Scored" value={detail.stats.scored_predictions} />
            <Stat label="Avg Hits" value={detail.stats.avg_main_hits.toFixed(2)} highlight />
            <Stat label="Best Hits" value={detail.stats.best_main_hits} highlight />
            <Stat label="Total Hits" value={detail.stats.total_main_hits} />
            <Stat label="Bonus Hits" value={detail.stats.total_bonus_hits} />
            <Stat label="Perfect Bonus" value={detail.stats.perfect_bonus} />
          </div>
        </Card>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }) {
  return (
    <div className="text-center">
      <p className={`text-2xl font-bold ${highlight ? 'text-yellow-400' : 'text-white'}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  );
}

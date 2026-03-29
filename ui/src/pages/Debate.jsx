import { useState, useEffect } from 'react';
import { api } from '../api';
import Card from '../components/Card';
import LotteryBalls from '../components/LotteryBalls';

const ROUND_LABELS = {
  analysis: '📝 Opening Analyses',
  challenge: '⚔️ Challenges',
  defense: '🛡️ Defenses',
};

export default function Debate() {
  const [lotteries, setLotteries] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedLottery, setSelectedLottery] = useState('');
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [rounds, setRounds] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [currentRound, setCurrentRound] = useState(0);

  useEffect(() => {
    Promise.all([api.lotteries(), api.agents()]).then(([l, a]) => {
      setLotteries(l);
      setAgents(a);
      const withData = l.find(x => x.id === 'powerball_us');
      if (withData) setSelectedLottery(withData.id);
      else if (l.length) setSelectedLottery(l[0].id);
    });
  }, []);

  const toggleAgent = (id) => {
    setSelectedAgents(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const runDebate = async () => {
    setLoading(true);
    setResult(null);
    setCurrentRound(0);
    try {
      const agentIds = selectedAgents.length > 0 ? selectedAgents : null;
      const data = await api.debate(selectedLottery, agentIds, rounds);
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Debate Arena</h2>

      {/* Controls */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center gap-4 flex-wrap">
            <select
              value={selectedLottery}
              onChange={e => setSelectedLottery(e.target.value)}
              className="bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-yellow-500"
            >
              {lotteries.map(l => (
                <option key={l.id} value={l.id}>{l.name} ({l.country})</option>
              ))}
            </select>
            <select
              value={rounds}
              onChange={e => setRounds(Number(e.target.value))}
              className="bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-yellow-500"
            >
              <option value={1}>1 round</option>
              <option value={2}>2 rounds</option>
              <option value={3}>3 rounds</option>
            </select>
            <button
              onClick={runDebate}
              disabled={loading}
              className="bg-red-500 hover:bg-red-400 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold px-6 py-2 rounded-lg text-sm transition-all"
            >
              {loading ? 'Debating...' : '⚔️ Start Debate'}
            </button>
          </div>

          <div>
            <p className="text-xs text-gray-500 mb-2">Select agents (empty = all)</p>
            <div className="flex flex-wrap gap-2">
              {agents.map(a => (
                <button
                  key={a.id}
                  onClick={() => toggleAgent(a.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                    selectedAgents.includes(a.id)
                      ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40'
                      : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
                  }`}
                >
                  {a.emoji} {a.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-400 text-sm">Agents are debating...</p>
          <p className="text-gray-600 text-xs mt-1">Full debates take 2-5 minutes</p>
        </div>
      )}

      {/* Debate transcript */}
      {result && (
        <>
          {/* Round navigation */}
          <div className="flex gap-2 flex-wrap">
            {result.rounds.map((r, i) => (
              <button
                key={i}
                onClick={() => setCurrentRound(i)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  currentRound === i
                    ? 'bg-white/10 text-white'
                    : 'text-gray-500 hover:text-white hover:bg-white/5'
                }`}
              >
                {ROUND_LABELS[r.round_type] || `Round ${r.round_number}`}
              </button>
            ))}
            <button
              onClick={() => setCurrentRound(-1)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentRound === -1
                  ? 'bg-yellow-500/20 text-yellow-400'
                  : 'text-gray-500 hover:text-yellow-400 hover:bg-yellow-500/10'
              }`}
            >
              🏆 Consensus
            </button>
          </div>

          {/* Round content */}
          {currentRound >= 0 && result.rounds[currentRound] && (
            <div className="space-y-4">
              {result.rounds[currentRound].entries.map((entry, i) => (
                <Card key={i}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">{entry.emoji}</span>
                    <span className="text-white font-semibold">{entry.agent_name}</span>
                    {entry.target_agent_id && (
                      <span className="text-xs text-gray-500">→ {entry.target_agent_id}</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {entry.text}
                  </div>
                  {entry.picks && (
                    <div className="mt-3 pt-3 border-t border-gray-800">
                      <LotteryBalls numbers={entry.picks} bonus={entry.bonus} />
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}

          {/* Consensus view */}
          {currentRound === -1 && (
            <div className="space-y-4">
              <Card className="border-yellow-500/30 bg-yellow-500/5">
                <h3 className="text-white font-bold text-lg mb-3">🏆 Consensus Picks</h3>
                <LotteryBalls numbers={result.consensus.numbers} bonus={result.consensus.bonus} size="lg" />
                {result.consensus.convergence?.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-yellow-500/20">
                    <p className="text-xs text-yellow-400/70 mb-2">Convergence</p>
                    {result.consensus.convergence.map(c => (
                      <p key={c.number} className="text-sm text-gray-300">
                        <span className="text-yellow-400 font-bold">#{c.number}</span>
                        {' — '}{c.agents.join(', ')}
                      </p>
                    ))}
                  </div>
                )}
              </Card>

              <Card title="All Agent Picks">
                <div className="space-y-3">
                  {Object.entries(result.agent_picks).map(([id, p]) => (
                    <div key={id} className="flex items-center gap-3">
                      <span className="text-lg">{p.emoji}</span>
                      <span className="text-sm text-gray-400 w-32">{p.name}</span>
                      <LotteryBalls numbers={p.numbers} bonus={p.bonus} />
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}

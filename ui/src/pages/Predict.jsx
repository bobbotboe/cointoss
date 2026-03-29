import { useState, useEffect } from 'react';
import { api } from '../api';
import Card from '../components/Card';
import AgentCard from '../components/AgentCard';
import LotteryBalls from '../components/LotteryBalls';

export default function Predict() {
  const [lotteries, setLotteries] = useState([]);
  const [selectedLottery, setSelectedLottery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.lotteries().then(l => {
      setLotteries(l);
      const withData = l.filter(x => x.id === 'powerball_us' || x.id === 'mega_millions');
      if (withData.length) setSelectedLottery(withData[0].id);
      else if (l.length) setSelectedLottery(l[0].id);
    });
  }, []);

  const runPrediction = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await api.predict(selectedLottery);
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Predict</h2>

      {/* Controls */}
      <Card>
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
          <button
            onClick={runPrediction}
            disabled={loading || !selectedLottery}
            className="bg-yellow-500 hover:bg-yellow-400 disabled:bg-gray-700 disabled:text-gray-500 text-black font-semibold px-6 py-2 rounded-lg text-sm transition-all"
          >
            {loading ? 'Agents analysing...' : '🎯 Run All Agents'}
          </button>
        </div>
      </Card>

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-yellow-500/30 border-t-yellow-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-400 text-sm">6 agents are analysing {selectedLottery}...</p>
          <p className="text-gray-600 text-xs mt-1">This takes 30-60 seconds</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Consensus */}
          <Card className="border-yellow-500/30 bg-yellow-500/5">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">🏆</span>
              <h3 className="text-white font-bold text-lg">Consensus Picks</h3>
            </div>
            <LotteryBalls numbers={result.consensus.numbers} bonus={result.consensus.bonus} size="lg" />

            {result.consensus.convergence?.length > 0 && (
              <div className="mt-4 pt-3 border-t border-yellow-500/20">
                <p className="text-xs text-yellow-400/70 mb-2">Convergence (multiple agents agree)</p>
                {result.consensus.convergence.map(c => (
                  <p key={c.number} className="text-sm text-gray-300">
                    <span className="text-yellow-400 font-bold">#{c.number}</span>
                    {' — picked by '}
                    {c.agents.join(', ')}
                  </p>
                ))}
              </div>
            )}
          </Card>

          {/* Agent results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.agents.map(a => (
              <AgentCard
                key={a.agent_id}
                emoji={a.emoji}
                name={a.agent_name}
                perspective=""
                analysis={a.analysis}
                picks={a.picks}
                bonus={a.bonus}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

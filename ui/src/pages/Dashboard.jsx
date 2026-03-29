import { useState, useEffect } from 'react';
import { api } from '../api';
import Card from '../components/Card';
import LotteryBalls from '../components/LotteryBalls';

export default function Dashboard() {
  const [lotteries, setLotteries] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.lotteries(), api.leaderboard()])
      .then(([lots, lb]) => {
        // Fetch stats for each lottery that has draws
        return Promise.all(
          lots.map(l => api.lotteryStats(l.id).then(s => ({ ...l, ...s })))
        ).then(enriched => {
          setLotteries(enriched);
          setLeaderboard(lb);
        });
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-gray-500 py-12 text-center">Loading dashboard...</div>;
  }

  const withData = lotteries.filter(l => l.total_draws > 0);
  const noData = lotteries.filter(l => l.total_draws === 0);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Dashboard</h2>

      {/* Lotteries with data */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {withData.map(l => (
          <Card key={l.id}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-white font-semibold">{l.name}</h3>
              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{l.country}</span>
            </div>
            <div className="text-sm text-gray-400 space-y-1 mb-3">
              <p>{l.total_draws.toLocaleString()} draws ({l.earliest_date} → {l.latest_date})</p>
              <p className="text-xs text-gray-600">Pick {l.main_pick_count} from 1-{l.main_pool_size}
                {l.bonus_pool_size ? ` + bonus 1-${l.bonus_pool_size}` : ''}</p>
            </div>
            {l.latest_numbers && (
              <div>
                <p className="text-xs text-gray-600 mb-1">Latest draw</p>
                <LotteryBalls numbers={l.latest_numbers} />
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Awaiting data */}
      {noData.length > 0 && (
        <Card title="Awaiting Data">
          <div className="flex flex-wrap gap-2">
            {noData.map(l => (
              <span key={l.id} className="text-xs bg-gray-800 text-gray-500 px-3 py-1 rounded-full">
                {l.name} ({l.country})
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* Leaderboard */}
      {leaderboard.length > 0 && (
        <Card title="Agent Leaderboard">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase">
                <th className="text-left pb-2">#</th>
                <th className="text-left pb-2">Agent</th>
                <th className="text-right pb-2">Predictions</th>
                <th className="text-right pb-2">Avg Hits</th>
                <th className="text-right pb-2">Best</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map(e => (
                <tr key={e.agent_id} className="border-t border-gray-800/50">
                  <td className="py-2 text-yellow-400 font-bold">{e.rank}</td>
                  <td className="py-2 text-white">{e.agent_id}</td>
                  <td className="py-2 text-right text-gray-400">{e.predictions}</td>
                  <td className="py-2 text-right text-yellow-400 font-medium">{e.avg_hits.toFixed(2)}</td>
                  <td className="py-2 text-right text-green-400">{e.best_hits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

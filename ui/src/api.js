const BASE = '/api';

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  health: () => get('/health'),
  lotteries: (country) => get(`/lotteries${country ? `?country=${country}` : ''}`),
  lotteryStats: (id) => get(`/lotteries/${id}/stats`),
  draws: (id, limit = 20) => get(`/draws/${id}?limit=${limit}`),
  latestDraw: (id) => get(`/draws/${id}/latest`),
  frequency: (id, lastN) => get(`/draws/${id}/frequency${lastN ? `?last_n=${lastN}` : ''}`),
  agents: () => get('/agents'),
  agentDetail: (id) => get(`/agents/${id}`),
  leaderboard: (lotteryId) => get(`/leaderboard${lotteryId ? `?lottery_id=${lotteryId}` : ''}`),
  toldYouSo: (lotteryId) => get(`/told-you-so${lotteryId ? `?lottery_id=${lotteryId}` : ''}`),
  predict: (lotteryId, agentIds, targetDate) => post('/predict', {
    lottery_id: lotteryId,
    agent_ids: agentIds || null,
    target_date: targetDate || null,
  }),
  debate: (lotteryId, agentIds, rounds, targetDate) => post('/debate', {
    lottery_id: lotteryId,
    agent_ids: agentIds || null,
    rounds: rounds || 1,
    target_date: targetDate || null,
  }),
};

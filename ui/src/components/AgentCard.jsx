import LotteryBalls from './LotteryBalls';

export default function AgentCard({ emoji, name, perspective, analysis, picks, bonus, loading }) {
  return (
    <div className="bg-[#12121a] border border-gray-800 rounded-xl p-5 transition-all hover:border-gray-700">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">{emoji}</span>
        <div>
          <h3 className="text-white font-semibold">{name}</h3>
          <p className="text-xs text-gray-500">{perspective}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-500 py-4">
          <div className="w-4 h-4 border-2 border-yellow-500/30 border-t-yellow-500 rounded-full animate-spin" />
          <span className="text-sm">Analysing...</span>
        </div>
      ) : (
        <>
          {analysis && (
            <div className="text-sm text-gray-300 leading-relaxed max-h-64 overflow-y-auto mb-3 whitespace-pre-wrap">
              {analysis}
            </div>
          )}
          {picks && (
            <div className="pt-3 border-t border-gray-800">
              <p className="text-xs text-gray-500 mb-1.5">Picks</p>
              <LotteryBalls numbers={picks} bonus={bonus} size="lg" />
            </div>
          )}
        </>
      )}
    </div>
  );
}

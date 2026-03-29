export default function LotteryBalls({ numbers, bonus, size = 'md' }) {
  const sz = size === 'lg' ? 'w-12 h-12 text-lg' : 'w-9 h-9 text-sm';
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {numbers?.map((n, i) => (
        <span key={i} className={`${sz} rounded-full bg-yellow-500/20 text-yellow-400 font-bold flex items-center justify-center`}>
          {n}
        </span>
      ))}
      {bonus?.map((n, i) => (
        <span key={`b${i}`} className={`${sz} rounded-full bg-blue-500/20 text-blue-400 font-bold flex items-center justify-center`}>
          {n}
        </span>
      ))}
    </div>
  );
}

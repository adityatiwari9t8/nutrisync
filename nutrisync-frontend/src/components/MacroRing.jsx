export default function MacroRing({ label, value, goal, color = "#1a7a4a" }) {
  const safeGoal = goal > 0 ? goal : value || 1;
  const percentage = Math.min(value / safeGoal, 1);
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeOffset = circumference - circumference * percentage;

  return (
    <div className="surface-card flex flex-col items-center gap-3 p-5">
      <svg viewBox="0 0 120 120" className="h-28 w-28">
        <circle cx="60" cy="60" r={radius} stroke="#d7e7db" strokeWidth="10" fill="none" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          stroke={color}
          strokeWidth="10"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeOffset}
          transform="rotate(-90 60 60)"
        />
        <text x="60" y="56" textAnchor="middle" className="fill-ink text-[18px] font-bold">
          {Math.round(value)}
        </text>
        <text x="60" y="74" textAnchor="middle" className="fill-mist text-[10px]">
          / {Math.round(goal || 0)}
        </text>
      </svg>
      <div className="text-center">
        <p className="text-sm font-semibold text-ink">{label}</p>
        <p className="text-xs text-mist">{Math.round(percentage * 100)}% of target</p>
      </div>
    </div>
  );
}

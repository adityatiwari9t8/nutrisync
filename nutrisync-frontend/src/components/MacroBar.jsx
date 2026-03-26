export default function MacroBar({ label, value, goal, accent = "bg-brand" }) {
  const percentage = goal > 0 ? Math.min((value / goal) * 100, 100) : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-ink">{label}</span>
        <span className="text-mist">
          {Math.round(value)} / {Math.round(goal || 0)}
        </span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-sand">
        <div className={`h-full rounded-full ${accent}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

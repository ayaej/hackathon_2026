import SpotlightCard from './ui/SpotlightCard';

function StatCard({ label, value, color, spotlightColor }) {
  return (
    <SpotlightCard spotlightColor={spotlightColor} className="px-5 py-4">
      <p className="text-xs font-medium text-white/40 uppercase tracking-widest">{label}</p>
      <p className={`text-3xl font-bold mt-2 ${color}`}>{value ?? '—'}</p>
    </SpotlightCard>
  );
}

export default function StatsBar({ stats, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 rounded-xl bg-white/5 animate-pulse" />
        ))}
      </div>
    );
  }

  const { total = 0, anomalies = 0, byStatus = {} } = stats ?? {};
  const validated = byStatus.validated ?? 0;
  const processing = (byStatus.uploaded ?? 0) + (byStatus.processing ?? 0);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <StatCard label="Total" value={total} color="text-white" spotlightColor="rgba(255,255,255,0.08)" />
      <StatCard label="Validés" value={validated} color="text-emerald-400" spotlightColor="rgba(52,211,153,0.15)" />
      <StatCard label="En traitement" value={processing} color="text-amber-400" spotlightColor="rgba(251,191,36,0.15)" />
      <StatCard label="Anomalies" value={anomalies} color="text-orange-400" spotlightColor="rgba(251,146,60,0.15)" />
    </div>
  );
}

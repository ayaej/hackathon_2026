function StatCard({ label, value, color }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-4 flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</span>
      <span className={`text-2xl font-bold ${color}`}>{value ?? '—'}</span>
    </div>
  );
}

export default function StatsBar({ stats, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  const { total = 0, anomalies = 0, byStatus = {} } = stats ?? {};
  const validated = byStatus.validated ?? 0;
  const processing = (byStatus.uploaded ?? 0) + (byStatus.processing ?? 0);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <StatCard label="Total documents" value={total} color="text-gray-800" />
      <StatCard label="Validés" value={validated} color="text-green-600" />
      <StatCard label="En traitement" value={processing} color="text-yellow-600" />
      <StatCard label="Anomalies" value={anomalies} color="text-orange-600" />
    </div>
  );
}

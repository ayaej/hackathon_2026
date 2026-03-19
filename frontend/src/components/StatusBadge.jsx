const config = {
  uploaded:   { label: 'Uploadé',       color: 'bg-white/10 text-white/60 border border-white/10' },
  processing: { label: 'En traitement', color: 'bg-amber-500/20 text-amber-300 border border-amber-500/20' },
  processed:  { label: 'Traité',        color: 'bg-blue-500/20 text-blue-300 border border-blue-500/20' },
  validated:  { label: 'Validé',        color: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/20' },
  rejected:   { label: 'Rejeté',        color: 'bg-red-500/20 text-red-400 border border-red-500/20' },
  anomaly:    { label: 'Anomalie',       color: 'bg-orange-500/20 text-orange-300 border border-orange-500/20' },
};

export default function StatusBadge({ status }) {
  const { label, color } = config[status] ?? { label: status, color: 'bg-white/10 text-white/50' };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium backdrop-blur-sm ${color}`}>
      {label}
    </span>
  );
}

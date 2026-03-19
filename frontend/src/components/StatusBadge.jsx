const config = {
  uploaded:   { label: 'Uploadé',       color: 'bg-gray-100 text-gray-600' },
  processing: { label: 'En traitement', color: 'bg-yellow-100 text-yellow-700' },
  processed:  { label: 'Traité',        color: 'bg-blue-100 text-blue-700' },
  validated:  { label: 'Validé',        color: 'bg-green-100 text-green-700' },
  rejected:   { label: 'Rejeté',        color: 'bg-red-100 text-red-600' },
  anomaly:    { label: 'Anomalie',       color: 'bg-orange-100 text-orange-700' },
};

export default function StatusBadge({ status }) {
  const { label, color } = config[status] ?? { label: status, color: 'bg-gray-100 text-gray-500' };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

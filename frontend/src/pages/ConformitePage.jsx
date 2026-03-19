import { useEffect, useState } from 'react';
import { getAnomalies, getConformiteStats } from '../api/conformite';
import StatusBadge from '../components/StatusBadge';
import BlurText from '../components/ui/BlurText';
import SpotlightCard from '../components/ui/SpotlightCard';

const SEVERITY_BADGE = {
  critical: 'bg-red-500/20 text-red-400 border border-red-500/30',
  high:     'bg-orange-500/20 text-orange-300 border border-orange-500/30',
  medium:   'bg-amber-500/20 text-amber-300 border border-amber-500/30',
  low:      'bg-white/8 text-white/40 border border-white/10',
};
const SEVERITY_LABEL = { critical: 'Critique', high: 'Haute', medium: 'Moyenne', low: 'Basse' };

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('fr-FR');
}

export default function ConformitePage() {
  const [anomalies, setAnomalies] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');

  useEffect(() => { getConformiteStats().then(({ data }) => setStats(data.data)).catch(() => {}); }, []);

  useEffect(() => {
    setLoading(true);
    getAnomalies({ severity: severityFilter || undefined })
      .then(({ data }) => setAnomalies(data.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [severityFilter]);

  const { total = 0, validated = 0, anomalies: anomalyCount = 0, pending = 0, tauxConformite = 0 } = stats ?? {};
  const taux = tauxConformite;
  const tauxColor = taux >= 80 ? 'text-emerald-400' : taux >= 50 ? 'text-amber-400' : 'text-red-400';

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">
          <BlurText text="Outil Conformité" direction="top" delay={80} />
        </h1>
        <p className="text-sm text-white/35 mt-1">Surveillance et détection des anomalies documentaires</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SpotlightCard spotlightColor={`rgba(${taux >= 80 ? '52,211,153' : taux >= 50 ? '251,191,36' : '248,113,113'},0.15)`} className="px-5 py-4">
          <p className="text-xs font-medium text-white/40 uppercase tracking-widest">Taux conformité</p>
          <p className={`text-3xl font-bold mt-2 ${tauxColor}`}>{taux}%</p>
        </SpotlightCard>
        <SpotlightCard spotlightColor="rgba(52,211,153,0.12)" className="px-5 py-4">
          <p className="text-xs font-medium text-white/40 uppercase tracking-widest">Validés</p>
          <p className="text-3xl font-bold mt-2 text-emerald-400">{validated}</p>
        </SpotlightCard>
        <SpotlightCard spotlightColor="rgba(251,146,60,0.15)" className="px-5 py-4">
          <p className="text-xs font-medium text-white/40 uppercase tracking-widest">Anomalies</p>
          <p className="text-3xl font-bold mt-2 text-orange-400">{anomalyCount}</p>
        </SpotlightCard>
        <SpotlightCard spotlightColor="rgba(251,191,36,0.12)" className="px-5 py-4">
          <p className="text-xs font-medium text-white/40 uppercase tracking-widest">En attente</p>
          <p className="text-3xl font-bold mt-2 text-amber-400">{pending}</p>
        </SpotlightCard>
      </div>

      <div className="spotlight-card overflow-hidden">
        <div className="px-5 py-4 border-b border-white/8 flex items-center justify-between flex-wrap gap-3">
          <h2 className="text-sm font-semibold text-white/70">Documents en anomalie</h2>
          <div className="flex gap-1.5 flex-wrap">
            {['', 'critical', 'high', 'medium', 'low'].map((s) => (
              <button
                key={s}
                onClick={() => setSeverityFilter(s)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all border
                  ${severityFilter === s
                    ? 'bg-indigo-500/30 text-indigo-200 border-indigo-500/40'
                    : 'bg-white/5 text-white/40 border-white/10 hover:bg-white/10 hover:text-white/70'
                  }`}
              >
                {s ? SEVERITY_LABEL[s] : 'Tous'}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div>{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-white/5 animate-pulse border-b border-white/5" />)}</div>
        ) : anomalies.length === 0 ? (
          <div className="py-16 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-white/30">Aucune anomalie détectée</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {anomalies.map((doc) => (
              <div key={doc._id} className="px-5 py-4 hover:bg-white/3 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-white/85 truncate">{doc.originalName}</p>
                      <StatusBadge status={doc.status} />
                    </div>
                    <p className="text-xs text-white/30 mt-0.5">
                      {doc.extractedData?.siret && <span>SIRET : {doc.extractedData.siret} · </span>}
                      Vérifié le {formatDate(doc.validationResult?.validatedAt)}
                      {doc.validationResult?.score != null && ` · Score : ${doc.validationResult.score}`}
                    </p>
                  </div>
                </div>
                {doc.validationResult?.anomalies?.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {doc.validationResult.anomalies.map((a, i) => (
                      <span key={i} title={a.description} className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_BADGE[a.severity] ?? 'bg-white/8 text-white/40'}`}>
                        {SEVERITY_LABEL[a.severity] ?? a.severity} — {a.type}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getClient } from '../api/crm';
import StatusBadge from '../components/StatusBadge';
import BlurText from '../components/ui/BlurText';
import SpotlightCard from '../components/ui/SpotlightCard';

const STATUT_BADGE = {
  actif:           'bg-emerald-500/20 text-emerald-300 border-emerald-500/20',
  inactif:         'bg-white/10 text-white/40 border-white/10',
  bloque:          'bg-red-500/20 text-red-400 border-red-500/20',
  en_verification: 'bg-amber-500/20 text-amber-300 border-amber-500/20',
};
const STATUT_LABEL = { actif: 'Actif', inactif: 'Inactif', bloque: 'Bloqué', en_verification: 'En vérification' };
const SEVERITY_BADGE = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  medium: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  low: 'bg-white/8 text-white/40 border-white/10',
};
const SEVERITY_LABEL = { critical: 'Critique', high: 'Haute', medium: 'Moyenne', low: 'Basse' };

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('fr-FR');
}

export default function ClientDetailPage() {
  const { id } = useParams();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getClient(id).then(({ data }) => setClient(data.data)).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="p-8 space-y-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />)}
      </div>
    );
  }

  if (!client) {
    return (
      <div className="p-8 text-center text-white/30 pt-32">
        <p className="text-lg">Client introuvable</p>
        <Link to="/crm" className="text-indigo-400 text-sm mt-2 inline-block hover:underline">← Retour CRM</Link>
      </div>
    );
  }

  const score = client.conformiteScore;
  const scoreColor = score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400';

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/crm" className="text-xs text-white/30 hover:text-white/60 transition-colors mb-2 inline-block">← Retour CRM</Link>
          <h1 className="text-2xl font-bold text-white">
            <BlurText text={client.raisonSociale} direction="top" delay={60} />
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="font-mono text-xs text-white/30">{client.siret}</span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${STATUT_BADGE[client.statut] ?? ''}`}>
              {STATUT_LABEL[client.statut] ?? client.statut}
            </span>
          </div>
        </div>
        {score != null && (
          <SpotlightCard spotlightColor={`rgba(${score >= 80 ? '52,211,153' : score >= 50 ? '251,191,36' : '248,113,113'},0.2)`} className="px-6 py-4 text-center flex-shrink-0">
            <p className="text-xs font-medium text-white/40 uppercase tracking-widest">Score conformité</p>
            <p className={`text-4xl font-bold mt-1 ${scoreColor}`}>{score}%</p>
          </SpotlightCard>
        )}
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        {client.contact && (
          <SpotlightCard className="p-5 space-y-3">
            <h2 className="text-xs font-semibold text-white/40 uppercase tracking-widest">Contact</h2>
            {client.contact.email && (
              <div className="flex items-center gap-2 text-sm text-white/70">
                <svg className="w-4 h-4 text-white/25" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                </svg>
                {client.contact.email}
              </div>
            )}
            {client.contact.telephone && (
              <div className="flex items-center gap-2 text-sm text-white/70">
                <svg className="w-4 h-4 text-white/25" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                </svg>
                {client.contact.telephone}
              </div>
            )}
            {client.contact.adresse && (
              <p className="text-sm text-white/50">{client.contact.adresse}</p>
            )}
          </SpotlightCard>
        )}

        {client.anomaliesDetectees?.length > 0 && (
          <SpotlightCard spotlightColor="rgba(248,113,113,0.12)" className="p-5 space-y-3">
            <h2 className="text-xs font-semibold text-white/40 uppercase tracking-widest">
              Anomalies ({client.anomaliesDetectees.length})
            </h2>
            <div className="space-y-2">
              {client.anomaliesDetectees.slice(0, 4).map((a, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${SEVERITY_BADGE[a.severity] ?? ''} flex-shrink-0`}>
                    {SEVERITY_LABEL[a.severity] ?? a.severity}
                  </span>
                  <p className="text-xs text-white/55 leading-relaxed">{a.description}</p>
                </div>
              ))}
              {client.anomaliesDetectees.length > 4 && (
                <p className="text-xs text-white/25">+{client.anomaliesDetectees.length - 4} autres…</p>
              )}
            </div>
          </SpotlightCard>
        )}
      </div>

      {client.documents?.length > 0 && (
        <SpotlightCard className="p-5 space-y-3">
          <h2 className="text-xs font-semibold text-white/40 uppercase tracking-widest">
            Documents ({client.documents.length})
          </h2>
          <div className="divide-y divide-white/5">
            {client.documents.map((doc) => (
              <div key={doc._id} className="flex items-center gap-4 py-2.5">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white/80 truncate">{doc.originalName ?? doc._id}</p>
                  <p className="text-xs text-white/30">{formatDate(doc.createdAt)}</p>
                </div>
                {doc.status && <StatusBadge status={doc.status} />}
              </div>
            ))}
          </div>
        </SpotlightCard>
      )}
    </div>
  );
}

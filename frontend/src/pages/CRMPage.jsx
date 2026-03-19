import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getClients, getCRMStats } from '../api/crm';
import BlurText from '../components/ui/BlurText';
import SpotlightCard from '../components/ui/SpotlightCard';

const STATUT_BADGE = {
  actif:           'bg-emerald-500/20 text-emerald-300 border-emerald-500/20',
  inactif:         'bg-white/10 text-white/40 border-white/10',
  bloque:          'bg-red-500/20 text-red-400 border-red-500/20',
  en_verification: 'bg-amber-500/20 text-amber-300 border-amber-500/20',
};
const STATUT_LABEL = { actif: 'Actif', inactif: 'Inactif', bloque: 'Bloqué', en_verification: 'En vérification' };

export default function CRMPage() {
  const [clients, setClients] = useState([]);
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchClients = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await getClients({ search: query || undefined });
      setClients(data.data);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => { fetchClients(); }, [fetchClients]);
  useEffect(() => { getCRMStats().then(({ data }) => setStats(data.data)).catch(() => {}); }, []);

  const { total = 0, byStatut = {} } = stats ?? {};

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">
          <BlurText text="CRM — Clients" direction="top" delay={80} />
        </h1>
        <p className="text-sm text-white/35 mt-1">Gestion et suivi des clients</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total', value: total, color: 'text-white', sc: 'rgba(255,255,255,0.06)' },
          { label: 'Actifs', value: byStatut.actif ?? 0, color: 'text-emerald-400', sc: 'rgba(52,211,153,0.15)' },
          { label: 'En vérif.', value: byStatut.en_verification ?? 0, color: 'text-amber-400', sc: 'rgba(251,191,36,0.15)' },
          { label: 'Bloqués', value: byStatut.bloque ?? 0, color: 'text-red-400', sc: 'rgba(248,113,113,0.15)' },
        ].map(({ label, value, color, sc }) => (
          <SpotlightCard key={label} spotlightColor={sc} className="px-5 py-4">
            <p className="text-xs font-medium text-white/40 uppercase tracking-widest">{label}</p>
            <p className={`text-3xl font-bold mt-2 ${color}`}>{value}</p>
          </SpotlightCard>
        ))}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); setQuery(search); }} className="flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher par raison sociale ou SIRET…"
          className="flex-1 px-4 py-2.5 text-sm bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/25 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
        />
        <button type="submit" className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition-colors">
          Rechercher
        </button>
        {query && (
          <button type="button" onClick={() => { setSearch(''); setQuery(''); }} className="px-4 py-2.5 text-sm text-white/40 border border-white/10 rounded-xl hover:bg-white/5 transition-colors">
            ✕
          </button>
        )}
      </form>

      <div className="spotlight-card overflow-hidden">
        {loading ? (
          <div>{[...Array(5)].map((_, i) => <div key={i} className="h-14 bg-white/5 animate-pulse border-b border-white/5" />)}</div>
        ) : clients.length === 0 ? (
          <div className="py-16 text-center text-white/30 text-sm">Aucun client trouvé</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b border-white/8">
              <tr>
                {['Raison sociale', 'SIRET', 'Statut', 'Score conformité', ''].map((h) => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-medium text-white/35 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {clients.map((c) => (
                <tr key={c._id} className="hover:bg-white/4 transition-colors">
                  <td className="px-5 py-3.5 font-medium text-white/85">{c.raisonSociale}</td>
                  <td className="px-5 py-3.5 text-white/40 font-mono text-xs">{c.siret}</td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${STATUT_BADGE[c.statut] ?? 'bg-white/10 text-white/40 border-white/10'}`}>
                      {STATUT_LABEL[c.statut] ?? c.statut}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    {c.conformiteScore != null ? (
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${c.conformiteScore >= 80 ? 'bg-emerald-400' : c.conformiteScore >= 50 ? 'bg-amber-400' : 'bg-red-400'}`}
                            style={{ width: `${c.conformiteScore}%` }}
                          />
                        </div>
                        <span className="text-xs text-white/40">{c.conformiteScore}%</span>
                      </div>
                    ) : <span className="text-xs text-white/25">—</span>}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <Link to={`/crm/${c._id}`} className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                      Voir →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

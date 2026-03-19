const TYPE_LABELS = {
  facture: 'Facture', devis: 'Devis', attestation: 'Attestation',
  identite: 'Identité', kbis: 'Kbis', autre: 'Autre', inconnu: '—',
};

const COMPARE_FIELDS = [
  {
    key: 'client',
    label: 'Nom du client',
    get: (doc) => doc.extractedData?.client ?? null,
  },
  {
    key: 'fournisseur',
    label: 'Fournisseur',
    get: (doc) => doc.extractedData?.fournisseur ?? null,
  },
  {
    key: 'raisonSociale',
    label: 'Raison sociale',
    get: (doc) => doc.extractedData?.raisonSociale ?? null,
  },
  {
    key: 'siret',
    label: 'SIRET',
    get: (doc) => doc.extractedData?.siret ?? null,
  },
  {
    key: 'montantTTC',
    label: 'Montant TTC',
    get: (doc) => {
      const v = doc.extractedData?.montantTTC;
      return v != null ? v : null;
    },
    format: (v) => `${Number(v).toFixed(2)} €`,
    compare: (vals) => {
      const nums = vals.map(Number);
      return nums.every((n) => Math.abs(n - nums[0]) < 0.01);
    },
  },
  {
    key: 'montantHT',
    label: 'Montant HT',
    get: (doc) => {
      const v = doc.extractedData?.montantHT;
      return v != null ? v : null;
    },
    format: (v) => `${Number(v).toFixed(2)} €`,
    compare: (vals) => {
      const nums = vals.map(Number);
      return nums.every((n) => Math.abs(n - nums[0]) < 0.01);
    },
  },
];

function analyseField(field, docs) {
  const entries = docs.map((doc) => ({ doc, value: field.get(doc) }));
  const withValue = entries.filter((e) => e.value !== null && e.value !== undefined && e.value !== '');

  if (withValue.length === 0) return { status: 'missing', values: entries };
  if (withValue.length === 1) return { status: 'partial', values: entries };

  const vals = withValue.map((e) => e.value);
  const isEqual = field.compare
    ? field.compare(vals)
    : vals.every((v) => String(v).trim().toLowerCase() === String(vals[0]).trim().toLowerCase());

  return { status: isEqual ? 'ok' : 'conflict', values: entries };
}

function StatusIcon({ status }) {
  if (status === 'ok') return (
    <span className="flex items-center gap-1 text-emerald-400 text-xs font-medium">
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
      </svg>
      Cohérent
    </span>
  );
  if (status === 'conflict') return (
    <span className="flex items-center gap-1 text-red-400 text-xs font-medium">
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
      Incohérent
    </span>
  );
  return (
    <span className="text-white/30 text-xs">—</span>
  );
}

export default function DocumentComparePanel({ documents, onClose }) {
  if (!documents || documents.length < 2) return null;

  const results = COMPARE_FIELDS.map((field) => ({
    field,
    ...analyseField(field, documents),
  }));

  const conflicts = results.filter((r) => r.status === 'conflict');
  const okCount = results.filter((r) => r.status === 'ok').length;
  const hasData = results.some((r) => r.status !== 'missing');

  return (
    <div className="spotlight-card overflow-hidden">
      <div className="px-5 py-4 border-b border-white/8 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-indigo-300" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
            </svg>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white/80">Comparaison de {documents.length} documents</h2>
            <p className="text-xs text-white/30 mt-0.5">
              {documents.map((d) => TYPE_LABELS[d.type] ?? d.type).join(' · ')}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasData && (
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
              conflicts.length === 0
                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25'
                : 'bg-red-500/15 text-red-300 border-red-500/25'
            }`}>
              {conflicts.length === 0 ? `${okCount} champ(s) cohérent(s)` : `${conflicts.length} incohérence(s)`}
            </span>
          )}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/8 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/6">
              <th className="text-left px-5 py-3 text-white/35 font-medium w-36">Champ</th>
              {documents.map((doc) => (
                <th key={doc._id} className="text-left px-4 py-3 text-white/50 font-medium min-w-[140px]">
                  <div className="truncate max-w-[160px]" title={doc.originalName}>{doc.originalName}</div>
                  <div className="text-white/25 font-normal mt-0.5">{TYPE_LABELS[doc.type] ?? doc.type}</div>
                </th>
              ))}
              <th className="text-left px-4 py-3 text-white/35 font-medium w-28">Résultat</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/4">
            {results.map(({ field, status, values }) => {
              if (status === 'missing') return null;
              return (
                <tr
                  key={field.key}
                  className={`transition-colors ${
                    status === 'conflict' ? 'bg-red-500/5' : status === 'ok' ? 'bg-emerald-500/3' : ''
                  }`}
                >
                  <td className="px-5 py-3 text-white/45 font-medium">{field.label}</td>
                  {values.map(({ doc, value }) => (
                    <td key={doc._id} className={`px-4 py-3 ${
                      value == null || value === ''
                        ? 'text-white/20 italic'
                        : status === 'conflict'
                          ? 'text-red-300/80'
                          : 'text-white/70'
                    }`}>
                      {value != null && value !== ''
                        ? (field.format ? field.format(value) : String(value))
                        : 'Non renseigné'}
                    </td>
                  ))}
                  <td className="px-4 py-3">
                    <StatusIcon status={status} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {!hasData && (
          <div className="py-10 text-center text-white/30 text-sm">
            aucune donnée extraite disponible sur les documents 
          </div>
        )}
      </div>
    </div>
  );
}

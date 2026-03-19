import { useEffect, useState, useCallback } from 'react';
import DropZone from '../components/DropZone';
import DocumentList from '../components/DocumentList';
import StatsBar from '../components/StatsBar';
import BlurText from '../components/ui/BlurText';
import { uploadDocuments, getDocuments, getDocumentStats, deleteDocument } from '../api/documents';

const STATUS_FILTERS = [
  { value: '', label: 'Tous' },
  { value: 'uploaded', label: 'Uploadés' },
  { value: 'processing', label: 'En traitement' },
  { value: 'validated', label: 'Validés' },
  { value: 'anomaly', label: 'Anomalies' },
  { value: 'rejected', label: 'Rejetés' },
];

export default function UploadPage() {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const { data } = await getDocuments({ status: statusFilter || undefined });
      setDocuments(data.data);
    } catch {
      showToast('Impossible de charger les documents', 'error');
    } finally {
      setLoadingDocs(false);
    }
  }, [statusFilter]);

  const fetchStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const { data } = await getDocumentStats();
      setStats(data.data);
    } catch {
    } finally {
      setLoadingStats(false);
    }
  }, []);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);
  useEffect(() => { fetchStats(); }, [fetchStats]);

  const handleFiles = async (files) => {
    setUploading(true);
    try {
      const { data } = await uploadDocuments(files);
      showToast(`${data.data.length} document(s) uploadé(s) avec succès`);
      await Promise.all([fetchDocuments(), fetchStats()]);
    } catch {
      showToast("Erreur lors de l'upload", 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteDocument(id);
      showToast('Document supprimé');
      await Promise.all([fetchDocuments(), fetchStats()]);
    } catch {
      showToast('Impossible de supprimer le document', 'error');
    }
  };

  return (
    <div className="min-h-screen p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">
          <BlurText text="Interface d'upload" direction="top" delay={80} />
        </h1>
        <p className="text-sm text-white/35 mt-1">Déposez vos documents administratifs pour traitement</p>
      </div>

      <StatsBar stats={stats} loading={loadingStats} />

      <div className="spotlight-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-white/70">Déposer des documents</h2>
        <DropZone onFiles={handleFiles} uploading={uploading} />
      </div>

      <div className="spotlight-card p-6 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h2 className="text-sm font-semibold text-white/70">Documents</h2>
          <div className="flex gap-1.5 flex-wrap">
            {STATUS_FILTERS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setStatusFilter(value)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all
                  ${statusFilter === value
                    ? 'bg-indigo-500/30 text-indigo-200 border border-indigo-500/40'
                    : 'bg-white/5 text-white/40 border border-white/10 hover:bg-white/10 hover:text-white/70'
                  }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <DocumentList documents={documents} onDelete={handleDelete} loading={loadingDocs} />
      </div>

      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium backdrop-blur-md border
          ${toast.type === 'error'
            ? 'bg-red-950/80 text-red-300 border-red-500/30'
            : 'bg-emerald-950/80 text-emerald-300 border-emerald-500/30'
          }`}
        >
          {toast.type === 'error'
            ? <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
            : <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          }
          {toast.message}
        </div>
      )}
    </div>
  );
}

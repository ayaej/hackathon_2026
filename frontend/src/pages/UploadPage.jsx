import { useEffect, useState, useCallback } from 'react';
import DropZone from '../components/DropZone';
import DocumentList from '../components/DocumentList';
import StatsBar from '../components/StatsBar';
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
      // stats non bloquantes
    } finally {
      setLoadingStats(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="font-semibold text-gray-800 text-lg">Validateur de documents</span>
          </div>
          <span className="text-xs text-gray-400">Interface d'upload</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        <StatsBar stats={stats} loading={loadingStats} />

        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
          <h2 className="font-semibold text-gray-700">Déposer des documents</h2>
          <DropZone onFiles={handleFiles} uploading={uploading} />
        </section>

        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h2 className="font-semibold text-gray-700">Documents</h2>
            <div className="flex gap-1.5 flex-wrap">
              {STATUS_FILTERS.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setStatusFilter(value)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors
                    ${statusFilter === value
                      ? 'bg-brand-500 text-white'
                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                    }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <DocumentList
            documents={documents}
            onDelete={handleDelete}
            loading={loadingDocs}
          />
        </section>
      </main>

      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-medium transition-all
          ${toast.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`}
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

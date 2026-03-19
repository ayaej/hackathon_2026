import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import UploadPage from './pages/UploadPage';
import CRMPage from './pages/CRMPage';
import ClientDetailPage from './pages/ClientDetailPage';
import ConformitePage from './pages/ConformitePage';

export default function App() {
  return (
    <div className="flex min-h-screen" style={{ background: '#09090f' }}>
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/crm" element={<CRMPage />} />
          <Route path="/crm/:id" element={<ClientDetailPage />} />
          <Route path="/conformite" element={<ConformitePage />} />
        </Routes>
      </main>
    </div>
  );
}

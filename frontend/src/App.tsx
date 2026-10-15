import { Routes, Route } from 'react-router-dom';
import { Dashboard } from '@/pages/Dashboard';
import { AuditRunDetail } from '@/pages/AuditRunDetail';
import { Fixtures } from '@/pages/Fixtures';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/runs/:id" element={<AuditRunDetail />} />
      <Route path="/fixtures" element={<Fixtures />} />
    </Routes>
  );
}

export default App;
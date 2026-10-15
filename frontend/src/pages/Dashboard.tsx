import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Play, Pause, Clock, CheckCircle, XCircle, AlertCircle, HelpCircle } from 'lucide-react';
import { endpoints } from '@/api/endpoints';
import { AuditRun, Fixture, CreateAuditRunRequest } from '@/types/api';
import { Layout } from '@/components/Layout';
import { Loading } from '@/components/Loading';
import { AuditRunForm } from '@/components/AuditRunForm';
import { clsx } from 'clsx';

const statusConfig = {
  pending: { icon: Clock, color: 'text-gray-600 bg-gray-100', label: 'Pending' },
  running: { icon: Play, color: 'text-blue-600 bg-blue-100', label: 'Running' },
  completed: { icon: CheckCircle, color: 'text-green-600 bg-green-100', label: 'Completed' },
  failed: { icon: XCircle, color: 'text-red-600 bg-red-100', label: 'Failed' },
  cancelled: { icon: Pause, color: 'text-gray-600 bg-gray-100', label: 'Cancelled' },
};

export function Dashboard() {
  const [runs, setRuns] = useState<AuditRun[]>([]);
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [runsRes, fixturesRes] = await Promise.all([
        endpoints.auditRuns.list({ page_size: 20 }),
        endpoints.fixtures.list(1, 50),
      ]);
      setRuns(runsRes.items);
      setFixtures(fixturesRes.items);
      setError(null);
    } catch (err) {
      setError('Failed to load data. Please check if the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRun = async (data: Record<string, unknown>) => {
    setCreating(true);
    try {
      await endpoints.auditRuns.create(data as unknown as CreateAuditRunRequest);
      setShowCreateModal(false);
      await loadData();
    } catch (err) {
      console.error(err);
      alert('Failed to create audit run');
    } finally {
      setCreating(false);
    }
  };

  const handleCancelRun = async (runId: string) => {
    if (!confirm('Are you sure you want to cancel this run?')) return;
    try {
      await endpoints.auditRuns.cancel(runId);
      await loadData();
    } catch (err) {
      console.error(err);
      alert('Failed to cancel run');
    }
  };

  const handleDeleteRun = async (runId: string) => {
    if (!confirm('Are you sure you want to delete this run? This cannot be undone.')) return;
    try {
      await endpoints.auditRuns.delete(runId);
      await loadData();
    } catch (err) {
      console.error(err);
      alert('Failed to delete run');
    }
  };

  if (loading) {
    return (
      <Layout>
        <Loading message="Loading dashboard..." />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 mt-1">Monitor and manage your AI agent audits</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
            disabled={fixtures.length === 0}
          >
            <Plus className="w-5 h-5 mr-2" />
            New Audit Run
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            {error}
            <button onClick={loadData} className="ml-auto text-sm underline hover:text-red-900">
              Retry
            </button>
          </div>
        )}

        {fixtures.length === 0 && (
          <div className="card text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <HelpCircle className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No fixtures available</h3>
            <p className="text-gray-500 mb-4">
              Create a fixture first to define the agent behavior you want to audit.
            </p>
            <Link to="/fixtures" className="btn-primary inline-flex">
              <Plus className="w-5 h-5 mr-2" />
              Create Fixture
            </Link>
          </div>
        )}

        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Suite</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grade</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {runs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      No audit runs yet. Create your first run to get started.
                    </td>
                  </tr>
                ) : (
                  runs.map((run) => {
                    const status = statusConfig[run.status as keyof typeof statusConfig] || statusConfig.pending;
                    const StatusIcon = status.icon;
                    return (
                      <tr key={run.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <Link
                            to={`/runs/${run.id}`}
                            className="font-medium text-gray-900 hover:text-primary-600"
                          >
                            {run.name}
                          </Link>
                          <p className="text-sm text-gray-500 truncate max-w-xs">{run.description || 'No description'}</p>
                        </td>
                        <td className="px-6 py-4">
                          <span className="badge-gray">{run.suite}</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-sm text-gray-600 capitalize">{run.provider_config.type}</span>
                          {run.provider_config.model && (
                            <p className="text-xs text-gray-400">{run.provider_config.model}</p>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={clsx('badge flex items-center gap-1', status.color)}>
                            <StatusIcon className="w-3 h-3" />
                            {status.label}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {run.overall_score !== undefined ? (
                            <span className="font-medium">{Math.round(run.overall_score * 100)}%</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {run.grade ? (
                            <span className={clsx('badge px-2 py-1', {
                              'badge-success': run.grade === 'A',
                              'badge-info': run.grade === 'B',
                              'badge-warning': run.grade === 'C',
                              'bg-orange-100 text-orange-800': run.grade === 'D',
                              'badge-danger': run.grade === 'F',
                            })}>
                              {run.grade}
                            </span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Link
                              to={`/runs/${run.id}`}
                              className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                            >
                              View
                            </Link>
                            {run.status === 'running' && (
                              <button
                                onClick={() => handleCancelRun(run.id)}
                                className="text-orange-600 hover:text-orange-800 text-sm font-medium"
                              >
                                Cancel
                              </button>
                            )}
                            {run.status === 'failed' && (
                              <button
                                onClick={() => handleDeleteRun(run.id)}
                                className="text-red-600 hover:text-red-800 text-sm font-medium"
                              >
                                Delete
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50 transition-opacity" onClick={() => setShowCreateModal(false)} />
            <div className="relative bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-auto">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
                <h2 className="text-xl font-semibold text-gray-900">Create New Audit Run</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
              <div className="p-6">
                <AuditRunForm
                  fixtures={fixtures}
                  onSubmit={handleCreateRun}
                  onCancel={() => setShowCreateModal(false)}
                  isLoading={creating}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
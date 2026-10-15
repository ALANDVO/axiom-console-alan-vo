import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Trash2, FileText } from 'lucide-react';
import { endpoints } from '@/api/endpoints';
import { Fixture } from '@/types/api';
import { Layout } from '@/components/Layout';
import { Loading } from '@/components/Loading';

export function Fixtures() {
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [formName, setFormName] = useState('');
  const [formVersion, setFormVersion] = useState('1.0');
  const [formDomain, setFormDomain] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const loadFixtures = async () => {
    try {
      setLoading(true);
      const res = await endpoints.fixtures.list(1, 50);
      setFixtures(res.items);
      setError(null);
    } catch (err) {
      setError('Failed to load fixtures.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFixtures();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) return;
    setCreating(true);
    try {
      await endpoints.fixtures.create({
        name: formName,
        version: formVersion,
        domain: formDomain || undefined,
        description: formDesc || undefined,
        content: {
          metadata: { name: formName, version: formVersion, domain: formDomain || undefined },
          users: [],
          tools: [],
          permissions: [],
          policies: {},
        },
        governance: undefined,
      });
      setShowCreate(false);
      setFormName('');
      setFormVersion('1.0');
      setFormDomain('');
      setFormDesc('');
      await loadFixtures();
    } catch (err) {
      console.error(err);
      alert('Failed to create fixture');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this fixture? This cannot be undone.')) return;
    try {
      await endpoints.fixtures.delete(id);
      await loadFixtures();
    } catch (err) {
      console.error(err);
      alert('Failed to delete fixture');
    }
  };

  if (loading) {
    return (
      <Layout>
        <Loading message="Loading fixtures..." />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Fixtures</h1>
            <p className="text-gray-500 mt-1">Agent behavior fixtures for audit runs</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="btn-primary"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Fixture
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-3">
            {error}
            <button onClick={loadFixtures} className="ml-auto text-sm underline hover:text-red-900">
              Retry
            </button>
          </div>
        )}

        {showCreate && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <div className="fixed inset-0 bg-black/50 transition-opacity" onClick={() => setShowCreate(false)} />
              <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Create Fixture</h2>
                </div>
                <form onSubmit={handleCreate} className="p-6 space-y-4">
                  <div>
                    <label className="label">Name *</label>
                    <input
                      type="text"
                      className="input"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      placeholder="Fixture name"
                      disabled={creating}
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Version</label>
                    <input
                      type="text"
                      className="input"
                      value={formVersion}
                      onChange={(e) => setFormVersion(e.target.value)}
                      disabled={creating}
                    />
                  </div>
                  <div>
                    <label className="label">Domain</label>
                    <input
                      type="text"
                      className="input"
                      value={formDomain}
                      onChange={(e) => setFormDomain(e.target.value)}
                      placeholder="e.g., customer_support"
                      disabled={creating}
                    />
                  </div>
                  <div>
                    <label className="label">Description</label>
                    <textarea
                      className="input min-h-[100px]"
                      value={formDesc}
                      onChange={(e) => setFormDesc(e.target.value)}
                      placeholder="Optional description"
                      disabled={creating}
                    />
                  </div>
                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowCreate(false)}
                      className="btn-secondary"
                      disabled={creating}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={creating || !formName.trim()}
                    >
                      {creating ? 'Creating...' : 'Create'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {fixtures.length === 0 ? (
          <div className="card text-center py-12">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No fixtures yet. Create one to get started.</p>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Domain</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Built-in</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {fixtures.map((f) => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <span className="font-medium text-gray-900">{f.name}</span>
                      {f.is_builtin && <span className="ml-2 text-xs text-gray-400">• Built-in</span>}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{f.version}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{f.domain || '—'}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{f.is_builtin ? 'Yes' : 'No'}</td>
                    <td className="px-6 py-4 text-right">
                      {!f.is_builtin && (
                        <button
                          onClick={() => handleDelete(f.id)}
                          className="text-red-600 hover:text-red-800 text-sm font-medium"
                        >
                          <Trash2 className="w-4 h-4 inline" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="text-sm text-gray-500">
          <Link to="/" className="text-primary-600 hover:text-primary-800">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    </Layout>
  );
}
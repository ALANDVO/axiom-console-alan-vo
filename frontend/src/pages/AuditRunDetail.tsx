import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Download, FileText, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { endpoints } from '@/api/endpoints';
import { AuditRun } from '@/types/api';
import { Layout } from '@/components/Layout';
import { Loading } from '@/components/Loading';
import { Scorecard } from '@/components/Scorecard';
import { clsx } from 'clsx';

const statusConfig = {
  pending: { icon: Clock, color: 'text-gray-600 bg-gray-100', label: 'Pending', animate: false },
  running: { icon: RefreshCw, color: 'text-blue-600 bg-blue-100', label: 'Running', animate: true },
  completed: { icon: CheckCircle, color: 'text-green-600 bg-green-100', label: 'Completed', animate: false },
  failed: { icon: XCircle, color: 'text-red-600 bg-red-100', label: 'Failed', animate: false },
  cancelled: { icon: AlertCircle, color: 'text-gray-600 bg-gray-100', label: 'Cancelled', animate: false },
};

export function AuditRunDetail() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<AuditRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (id) loadRun();
  }, [id]);

  const loadRun = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await endpoints.auditRuns.get(id);
      setRun(data);
      setError(null);
    } catch (err) {
      setError('Failed to load audit run');
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadRun();
  };

  const downloadReport = (format: 'json' | 'markdown') => {
    if (!run) return;
    const content = format === 'json'
      ? (run.report_json ? JSON.stringify(run.report_json, null, 2) : null)
      : run.report_markdown;
    if (!content) return;
    const blob = new Blob(
      [content],
      { type: format === 'json' ? 'application/json' : 'text/markdown' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${run.name.replace(/\s+/g, '_')}_report.${format === 'json' ? 'json' : 'md'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Layout>
        <Loading message="Loading audit run..." />
      </Layout>
    );
  }

  if (error || !run) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto text-center py-12">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Audit Run Not Found</h2>
          <p className="text-gray-500 mb-6">{error || 'The audit run could not be loaded.'}</p>
          <Link to="/" className="btn-primary">
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Link>
        </div>
      </Layout>
    );
  }

  const status = statusConfig[run.status as keyof typeof statusConfig] || statusConfig.pending;
  const StatusIcon = status.icon;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-gray-500 hover:text-gray-700">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">{run.name}</h1>
            <p className="text-gray-500 mt-1">{run.description || 'No description'}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className={clsx('badge flex items-center gap-1', status.color)}>
              {status.animate && <StatusIcon className={clsx('w-3 h-3', status.animate && 'animate-spin')} />}
              {!status.animate && <StatusIcon className="w-3 h-3" />}
              {status.label}
            </span>
            {run.grade && (
              <span className={clsx('badge px-3 py-1 text-lg', {
                'badge-success': run.grade === 'A',
                'badge-info': run.grade === 'B',
                'badge-warning': run.grade === 'C',
                'bg-orange-100 text-orange-800': run.grade === 'D',
                'badge-danger': run.grade === 'F',
              })}>
                Grade: {run.grade}
              </span>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <div className="card">
            <p className="text-sm text-gray-500">Suite</p>
            <p className="text-2xl font-bold text-gray-900">{run.suite}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Eval Mode</p>
            <p className="text-2xl font-bold text-gray-900 capitalize">{run.eval_mode}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Provider</p>
            <p className="text-2xl font-bold text-gray-900 capitalize">{run.provider_config.type}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Overall Score</p>
            <p className="text-2xl font-bold text-gray-900">
              {run.overall_score !== undefined ? `${Math.round(run.overall_score * 100)}%` : '—'}
            </p>
          </div>
        </div>

        <div className="card">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Scorecard</h2>
            <div className="flex gap-2">
              {run.report_json && (
                <button onClick={() => downloadReport('json')} className="btn-secondary">
                  <Download className="w-4 h-4 mr-2" />
                  JSON
                </button>
              )}
              {run.report_markdown && (
                <button onClick={() => downloadReport('markdown')} className="btn-secondary">
                  <FileText className="w-4 h-4 mr-2" />
                  Markdown
                </button>
              )}
              <button onClick={handleRefresh} disabled={refreshing} className="btn-secondary">
                <RefreshCw className={clsx('w-4 h-4 mr-2', refreshing && 'animate-spin')} />
                Refresh
              </button>
            </div>
          </div>

          <Scorecard
            overallScore={run.overall_score}
            grade={run.grade}
            pillarScores={run.pillar_scores}
          />
        </div>

        {run.error_message && (
          <div className="card bg-red-50 border-red-200">
            <h3 className="font-semibold text-red-800 mb-2 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Error
            </h3>
            <p className="text-red-700 font-mono text-sm">{run.error_message}</p>
          </div>
        )}

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Run Details</h3>
          <dl className="grid gap-4 md:grid-cols-2">
            <div>
              <dt className="text-sm text-gray-500">Run ID</dt>
              <dd className="font-mono text-sm text-gray-900 break-all">{run.id}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Fixture</dt>
              <dd className="text-sm text-gray-900">{run.fixture_id || 'None'}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Created</dt>
              <dd className="text-sm text-gray-900">{new Date(run.created_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Started</dt>
              <dd className="text-sm text-gray-900">
                {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Completed</dt>
              <dd className="text-sm text-gray-900">
                {run.completed_at ? new Date(run.completed_at).toLocaleString() : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Duration</dt>
              <dd className="text-sm text-gray-900">
                {run.started_at && run.completed_at
                  ? `${((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000).toFixed(1)}s`
                  : '—'}
              </dd>
            </div>
          </dl>
        </div>

        {run.report_markdown && (
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Full Markdown Report</h3>
            <div className="prose prose-sm max-w-none bg-gray-50 p-4 rounded-lg">
              <pre className="whitespace-pre-wrap font-mono text-sm">{run.report_markdown}</pre>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
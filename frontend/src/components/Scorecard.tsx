import { InspectionResult, PillarScore } from '@/types/api';
import { CheckCircle, XCircle, HelpCircle, AlertCircle, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';

const statusIcons = {
  pass: CheckCircle,
  fail: XCircle,
  inconclusive: HelpCircle,
  error: AlertCircle,
};

const statusColors = {
  pass: 'text-green-600 bg-green-50',
  fail: 'text-red-600 bg-red-50',
  inconclusive: 'text-yellow-600 bg-yellow-50',
  error: 'text-gray-600 bg-gray-50',
};

const gradeColors: Record<string, string> = {
  A: 'text-green-600 bg-green-50',
  B: 'text-blue-600 bg-blue-50',
  C: 'text-yellow-600 bg-yellow-50',
  D: 'text-orange-600 bg-orange-50',
  F: 'text-red-600 bg-red-50',
};

export function GradeBadge({ grade }: { grade?: string }) {
  if (!grade) return <span className="badge-gray">N/A</span>;
  return (
    <span className={clsx('badge px-3 py-1 text-lg', gradeColors[grade] || 'badge-gray')}>
      {grade}
    </span>
  );
}

export function ScoreBadge({ score }: { score?: number }) {
  if (score === undefined || score === null) return <span className="badge-gray">N/A</span>;
  const percentage = Math.round(score * 100);
  let colorClass = 'badge-gray';
  if (percentage >= 90) colorClass = 'badge-success';
  else if (percentage >= 80) colorClass = 'badge-info';
  else if (percentage >= 70) colorClass = 'badge-warning';
  else if (percentage >= 60) colorClass = 'bg-orange-100 text-orange-800 badge';
  else colorClass = 'badge-danger';
  return <span className={colorClass}>{percentage}%</span>;
}

export function StatusBadge({ status }: { status: InspectionResult['status'] }) {
  const Icon = statusIcons[status];
  return (
    <span className={clsx('badge flex items-center gap-1', statusColors[status])}>
      <Icon className="w-3 h-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export function PillarScoreCard({ pillar }: { pillar: PillarScore }) {
  const percentage = Math.round(pillar.score * 100);
  const weightPercentage = Math.round(pillar.weight * 100);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{pillar.pillar}</h3>
        <ScoreBadge score={pillar.score} />
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
        <div
          className="bg-primary-600 h-3 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-sm text-gray-500">
        <span>Weight: {weightPercentage}%</span>
        <span>{pillar.inspections.length} inspections</span>
      </div>
      <div className="mt-4 space-y-2">
        {pillar.inspections.map((insp) => (
          <InspectionRow key={insp.id} inspection={insp} />
        ))}
      </div>
    </div>
  );
}

export function InspectionRow({ inspection }: { inspection: InspectionResult }) {
  const Icon = statusIcons[inspection.status];
  const mandatory = inspection.mandatory_minimum ? (
    <AlertTriangle className="w-4 h-4 text-red-500" aria-label="Mandatory minimum" />
  ) : null;

  return (
    <div className="flex items-center justify-between py-2 border-t border-gray-100">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <Icon className={clsx('w-4 h-4 flex-shrink-0', statusColors[inspection.status].replace('bg-', 'text-'))} />
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {inspection.name}
            {mandatory}
          </p>
          <p className="text-xs text-gray-500 truncate">{inspection.category}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <StatusBadge status={inspection.status} />
        {inspection.score !== undefined && <ScoreBadge score={inspection.score} />}
      </div>
    </div>
  );
}

export function Scorecard({
  overallScore,
  grade,
  pillarScores,
}: {
  overallScore?: number;
  grade?: string;
  pillarScores?: PillarScore[];
}) {
  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Overall Score</h2>
            <p className="text-gray-500">Weighted average across all pillars</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-5xl font-bold text-gray-900">
                {overallScore !== undefined ? Math.round(overallScore * 100) : '—'}%
              </div>
              <div className="mt-1">
                <GradeBadge grade={grade} />
              </div>
            </div>
            {overallScore !== undefined && (
              <div className="w-48 md:w-64">
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-primary-600 h-4 rounded-full transition-all duration-500"
                    style={{ width: `${Math.round(overallScore * 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {pillarScores && pillarScores.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {pillarScores.map((pillar) => (
            <PillarScoreCard key={pillar.pillar} pillar={pillar} />
          ))}
        </div>
      )}

      {!pillarScores && (
        <div className="card text-center py-12">
          <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No inspection results available</p>
        </div>
      )}
    </div>
  );
}
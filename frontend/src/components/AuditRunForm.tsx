import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Fixture } from '@/types/api';
import { LoadingInline } from './Loading';
import { clsx } from 'clsx';

interface AuditRunFormProps {
  fixtures: Fixture[];
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}






const SUITES = [
  { value: 'smoke', label: 'Smoke (3 tests)', description: 'Quick pipeline verification' },
  { value: 'strategic', label: 'Strategic (8 tests)', description: 'Quick read on riskiest spots' },
  { value: 'essential', label: 'Essential (13 tests)', description: 'Fast first grade (default)' },
  { value: 'core', label: 'Core (32 tests)', description: 'Full graded scorecard' },
  { value: 'extended', label: 'Extended (28 tests)', description: 'Premium preview checks' },
  { value: 'all', label: 'All (60 tests)', description: 'Complete inspection suite' },
];

const EVAL_MODES = [
  { value: 'self', label: 'Self-judged', description: 'Agent grades itself (not citable)' },
  { value: 'single', label: 'Single judge', description: 'One independent judge' },
  { value: 'full', label: 'Full ensemble', description: 'Multiple judges with consensus' },
];

const PROVIDER_TYPES = [
  { value: 'mock', label: 'Mock (deterministic)', description: 'No API key needed, for testing' },
  { value: 'openai', label: 'OpenAI', description: 'GPT models via OpenAI API' },
  { value: 'anthropic', label: 'Anthropic', description: 'Claude models via Anthropic API' },
  { value: 'http', label: 'HTTP Endpoint', description: 'Custom OpenAI-compatible endpoint' },
];

export function AuditRunForm({ fixtures, onSubmit, onCancel, isLoading }: AuditRunFormProps) {
  const [providerType, setProviderType] = useState<'mock' | 'openai' | 'anthropic' | 'http'>('mock');
  const [showProviderConfig, setShowProviderConfig] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm({
    defaultValues: {
      name: '',
      description: '',
      fixture_id: '',
      suite: 'essential',
      eval_mode: 'self',
      provider_config: {
        type: 'mock',
        model: '',
        endpoint: '',
        api_key_env: '',
        timeout_seconds: 30,
      },
      judge_config: [],
    },
  });

  const selectedSuite = watch('suite');

  const handleProviderTypeChange = (type: typeof providerType) => {
    setProviderType(type);
    setValue('provider_config.type', type);
    setShowProviderConfig(true);
  };

  const onFormSubmit = async (data: any) => {
    await onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
        <div className="space-y-4">
          <div>
            <label htmlFor="name" className="label">Run Name *</label>
            <input
              id="name"
              type="text"
              {...register('name', { required: 'Run name is required' })}
              className="input"
              placeholder="My Audit Run"
              disabled={isLoading}
            />
            {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>}
          </div>

          <div>
            <label htmlFor="description" className="label">Description</label>
            <textarea
              id="description"
              {...register('description')}
              className="input min-h-[100px]"
              placeholder="Optional description of this audit run"
              disabled={isLoading}
            />
          </div>

          <div>
            <label htmlFor="fixture_id" className="label">Fixture *</label>
            <select
              id="fixture_id"
              {...register('fixture_id', { required: 'Fixture is required' })}
              className="input"
              disabled={isLoading}
            >
              <option value="">Select a fixture...</option>
              {fixtures.map((fixture) => (
                <option key={fixture.id} value={fixture.id}>
                  {fixture.name} (v{fixture.version}) {fixture.is_builtin && '• Built-in'}
                </option>
              ))}
            </select>
            {errors.fixture_id && <p className="text-sm text-red-600 mt-1">{errors.fixture_id.message}</p>}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Provider Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="label">Provider Type *</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {PROVIDER_TYPES.map((provider) => (
                <button
                  key={provider.value}
                  type="button"
                  onClick={() => handleProviderTypeChange(provider.value as typeof providerType)}
                  className={clsx(
                    'p-4 rounded-lg border-2 text-left transition-all',
                    providerType === provider.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                  disabled={isLoading}
                >
                  <p className="font-medium text-gray-900">{provider.label}</p>
                  <p className="text-sm text-gray-500 mt-1">{provider.description}</p>
                </button>
              ))}
            </div>
          </div>

          {showProviderConfig && (
            <div className="space-y-4 border-t pt-4">
              <div>
                <label htmlFor="provider_model" className="label">Model</label>
                <input
                  id="provider_model"
                  type="text"
                  {...register('provider_config.model')}
                  className="input"
                  placeholder={providerType === 'mock' ? 'mock-model' : 'e.g., gpt-4o, claude-3-5-sonnet'}
                  disabled={isLoading}
                />
              </div>

              {providerType === 'http' && (
                <div>
                  <label htmlFor="provider_endpoint" className="label">Endpoint URL *</label>
                  <input
                    id="provider_endpoint"
                    type="url"
                    {...register('provider_config.endpoint', { required: 'Endpoint is required for HTTP provider' })}
                    className="input"
                    placeholder="https://api.example.com/v1/chat/completions"
                    disabled={isLoading}
                  />
                  {errors.provider_config?.endpoint && (
                    <p className="text-sm text-red-600 mt-1">{errors.provider_config.endpoint.message}</p>
                  )}
                </div>
              )}

              {providerType !== 'mock' && (
                <div>
                  <label htmlFor="provider_api_key_env" className="label">API Key Environment Variable</label>
                  <input
                    id="provider_api_key_env"
                    type="text"
                    {...register('provider_config.api_key_env')}
                    className="input"
                    placeholder="OPENAI_API_KEY"
                    disabled={isLoading}
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    The environment variable name containing the API key (never the key itself)
                  </p>
                </div>
              )}

              <div>
                <label htmlFor="provider_timeout" className="label">Timeout (seconds)</label>
                <input
                  id="provider_timeout"
                  type="number"
                  {...register('provider_config.timeout_seconds', { valueAsNumber: true })}
                  className="input w-32"
                  min={5}
                  max={300}
                  disabled={isLoading}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Evaluation Settings</h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="suite" className="label">Inspection Suite *</label>
            <select
              id="suite"
              {...register('suite', { required: true })}
              className="input"
              disabled={isLoading}
            >
              {SUITES.map((suite) => (
                <option key={suite.value} value={suite.value}>
                  {suite.label}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              {SUITES.find((s) => s.value === selectedSuite)?.description}
            </p>
          </div>

          <div>
            <label htmlFor="eval_mode" className="label">Evaluation Mode *</label>
            <select
              id="eval_mode"
              {...register('eval_mode', { required: true })}
              className="input"
              disabled={isLoading}
            >
              {EVAL_MODES.map((mode) => (
                <option key={mode.value} value={mode.value}>
                  {mode.label}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              {EVAL_MODES.find((m) => m.value === watch('eval_mode'))?.description}
            </p>
          </div>
        </div>

        {selectedSuite === 'core' || selectedSuite === 'all' ? (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Core and All suites require judge configuration for graded results.
              Make sure to configure judge providers in Settings.
            </p>
          </div>
        ) : null}
      </div>

      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={onCancel}
          className="btn-secondary"
          disabled={isLoading}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn-primary"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <LoadingInline size="sm" />
              Creating...
            </>
          ) : (
            'Create Audit Run'
          )}
        </button>
      </div>
    </form>
  );
}



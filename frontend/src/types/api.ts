export interface ProviderConfig {
  type: string;
  model?: string;
  endpoint?: string;
  api_key_env?: string;
  extra_headers?: Record<string, string>;
  timeout_seconds: number;
}

export interface JudgeConfig {
  provider: string;
  model: string;
  api_key_env?: string;
  weight: number;
}

export interface Fixture {
  id: string;
  name: string;
  version: string;
  domain?: string;
  description?: string;
  content: Record<string, any>;
  governance?: Record<string, any>;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

export interface FixtureListResponse {
  items: Fixture[];
  total: number;
  page: number;
  page_size: number;
}

export interface InspectionResult {
  id: string;
  name: string;
  category: string;
  pillar?: string;
  status: 'pass' | 'fail' | 'inconclusive' | 'error';
  score?: number;
  evidence_count: number;
  details?: string;
  error?: string;
  mandatory_minimum: boolean;
}

export interface PillarScore {
  pillar: string;
  score: number;
  weight: number;
  inspections: InspectionResult[];
}

export interface AuditRun {
  id: string;
  name: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  fixture_id?: string;
  provider_config: ProviderConfig;
  judge_config?: JudgeConfig[];
  suite: string;
  eval_mode: string;
  overall_score?: number;
  grade?: string;
  pillar_scores?: PillarScore[];
  inspection_results?: InspectionResult[];
  report_markdown?: string;
  report_json?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditRunListResponse {
  items: AuditRun[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateAuditRunRequest {
  name: string;
  description?: string;
  fixture_id?: string;
  provider_config: ProviderConfig;
  judge_config?: JudgeConfig[];
  suite: string;
  eval_mode: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
}
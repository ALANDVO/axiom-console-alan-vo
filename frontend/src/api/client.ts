import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  AuditRun,
  AuditRunListResponse,
  CreateAuditRunRequest,
  Fixture,
  FixtureListResponse,
  HealthResponse,
} from '@/types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Clear auth and redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Health
  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  // Fixtures
  async listFixtures(page = 1, pageSize = 20): Promise<FixtureListResponse> {
    const response = await this.client.get<FixtureListResponse>('/fixtures', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async listBuiltinFixtures(): Promise<FixtureListResponse> {
    const response = await this.client.get<FixtureListResponse>('/fixtures/builtin');
    return response.data;
  }

  async getFixture(id: string): Promise<Fixture> {
    const response = await this.client.get<Fixture>(`/fixtures/${id}`);
    return response.data;
  }

  async createFixture(data: Omit<Fixture, 'id' | 'is_builtin' | 'created_at' | 'updated_at'>): Promise<Fixture> {
    const response = await this.client.post<Fixture>('/fixtures', data);
    return response.data;
  }

  async updateFixture(id: string, data: Partial<Fixture>): Promise<Fixture> {
    const response = await this.client.patch<Fixture>(`/fixtures/${id}`, data);
    return response.data;
  }

  async deleteFixture(id: string): Promise<void> {
    await this.client.delete(`/fixtures/${id}`);
  }

  // Audit Runs
  async listAuditRuns(params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<AuditRunListResponse> {
    const response = await this.client.get<AuditRunListResponse>('/audit/runs', { params });
    return response.data;
  }

  async getAuditRun(id: string): Promise<AuditRun> {
    const response = await this.client.get<AuditRun>(`/audit/runs/${id}`);
    return response.data;
  }

  async createAuditRun(data: CreateAuditRunRequest): Promise<AuditRun> {
    const response = await this.client.post<AuditRun>('/audit/runs', data);
    return response.data;
  }

  async updateAuditRun(id: string, data: { name?: string; description?: string }): Promise<AuditRun> {
    const response = await this.client.patch<AuditRun>(`/audit/runs/${id}`, data);
    return response.data;
  }

  async deleteAuditRun(id: string): Promise<void> {
    await this.client.delete(`/audit/runs/${id}`);
  }

  async cancelAuditRun(id: string): Promise<AuditRun> {
    const response = await this.client.post<AuditRun>(`/audit/runs/${id}/cancel`);
    return response.data;
  }
}

export const api = new ApiClient();
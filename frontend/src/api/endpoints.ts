import { api } from './client';
import type { Fixture, CreateAuditRunRequest } from '@/types/api';

export const endpoints = {
  health: {
    check: () => api.healthCheck(),
  },
  fixtures: {
    list: (page?: number, pageSize?: number) => api.listFixtures(page, pageSize),
    listBuiltin: () => api.listBuiltinFixtures(),
    get: (id: string) => api.getFixture(id),
    create: (data: Omit<Fixture, 'id' | 'is_builtin' | 'created_at' | 'updated_at'>) => api.createFixture(data),
    update: (id: string, data: Partial<Fixture>) => api.updateFixture(id, data),
    delete: (id: string) => api.deleteFixture(id),
  },
  auditRuns: {
    list: (params?: { page?: number; page_size?: number; status?: string }) =>
      api.listAuditRuns(params),
    get: (id: string) => api.getAuditRun(id),
    create: (data: CreateAuditRunRequest) => api.createAuditRun(data),
    update: (id: string, data: { name?: string; description?: string }) => api.updateAuditRun(id, data),
    delete: (id: string) => api.deleteAuditRun(id),
    cancel: (id: string) => api.cancelAuditRun(id),
  },
};
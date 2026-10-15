import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

vi.mock('@/api/endpoints', () => ({
  endpoints: {
    auditRuns: {
      list: vi.fn(),
      create: vi.fn(),
      cancel: vi.fn(),
      delete: vi.fn(),
    },
    fixtures: {
      list: vi.fn(),
    },
  },
}));

import { Dashboard } from '@/pages/Dashboard';
import { endpoints } from '@/api/endpoints';

vi.mocked(endpoints.fixtures.list).mockResolvedValue({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
});
vi.mocked(endpoints.auditRuns.list).mockResolvedValue({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
});

describe('Dashboard', () => {
  it('shows empty state when no fixtures or runs exist', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No fixtures available/i)).toBeInTheDocument();
    });
  });

  it('prompts to create a fixture when none exist', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Create a fixture first/i)).toBeInTheDocument();
    });
  });
});
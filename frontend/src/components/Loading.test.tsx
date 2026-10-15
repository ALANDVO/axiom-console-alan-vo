import { render, screen } from '@testing-library/react';
import { Loading } from '@/components/Loading';

describe('Loading', () => {
  it('renders with default message', () => {
    render(<Loading />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<Loading message="Fetching audit results..." />);
    expect(screen.getByText('Fetching audit results...')).toBeInTheDocument();
  });
});
import { render, screen } from '@testing-library/react';
import { GradeBadge, ScoreBadge } from '@/components/Scorecard';

describe('GradeBadge', () => {
  it('renders grade A with success styling', () => {
    render(<GradeBadge grade="A" />);
    expect(screen.getByText('A')).toBeInTheDocument();
  });

  it('renders N/A when no grade is provided', () => {
    render(<GradeBadge />);
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('renders grade F with danger styling', () => {
    render(<GradeBadge grade="F" />);
    expect(screen.getByText('F')).toBeInTheDocument();
  });
});

describe('ScoreBadge', () => {
  it('renders percentage for a given score', () => {
    render(<ScoreBadge score={0.85} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('renders N/A when score is undefined', () => {
    render(<ScoreBadge />);
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });
});
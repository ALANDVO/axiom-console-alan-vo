import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { Loading } from '@/components/Loading';

export function NewAuditRun() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // Redirect to dashboard with fixture preselected if provided
    const fixtureId = searchParams.get('fixture');
    if (fixtureId) {
      navigate('/', { state: { preselectedFixture: fixtureId }, replace: true });
    } else {
      navigate('/', { replace: true });
    }
  }, [navigate, searchParams]);

  return (
    <Layout>
      <Loading message="Redirecting..." />
    </Layout>
  );
}
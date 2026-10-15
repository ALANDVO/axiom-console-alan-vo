import { ReactNode } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, FlaskConical } from 'lucide-react';
import { clsx } from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Fixtures', href: '/fixtures', icon: FlaskConical },
]

export function Layout({ children }: { children?: ReactNode }) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold text-primary-600">
                <FlaskConical className="w-8 h-8" />
                <span>Axiom Console</span>
              </Link>
              <div className="hidden md:ml-8 md:flex md:space-x-4">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      location.pathname === item.href
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    )}
                  >
                    <item.icon className="w-5 h-5" />
                    {item.name}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500 hidden sm:block">AI Agent Auditing</span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children ?? <Outlet />}
      </main>

      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
          Axiom Console — Independent AI Agent Auditing • Alan Vo {'<'}alanvo@gmail.com{'>'}
        </div>
      </footer>
    </div>
  );
}
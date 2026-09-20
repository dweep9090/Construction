import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom';
import { HardHat, LogOut } from 'lucide-react';
import { getCurrentUser } from '../../utils/auth';

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = getCurrentUser();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const navLinks = [
    { name: 'My Projects', path: '/projects', roles: ['PROJECT_MANAGER', 'SITE_ENGINEER', 'QUALITY_INSPECTOR', 'CONTRACTOR', 'STORE_KEEPER', 'FINANCE_OFFICER', 'PROJECT_DIRECTOR', 'AUDITOR'] },
    { name: 'Public Projects', path: '/public-projects', roles: ['PROJECT_MANAGER', 'SITE_ENGINEER', 'QUALITY_INSPECTOR', 'CONTRACTOR', 'STORE_KEEPER', 'FINANCE_OFFICER', 'PROJECT_DIRECTOR', 'AUDITOR'] },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-slate-900 text-white shadow-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HardHat className="h-6 w-6 text-amber-500" />
            <h1 className="font-bold text-xl tracking-tight">ConstructFlow</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-300">{user?.name} ({user?.role?.replace('_', ' ')})</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </header>
      
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {navLinks.filter(link => !link.roles || (user && link.roles.includes(user.role))).map((link) => {
              const isActive = location.pathname.startsWith(link.path);
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                    ${isActive 
                      ? 'border-amber-500 text-amber-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {link.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
      
      <div className="flex-1 flex max-w-7xl mx-auto w-full">
        {/* Main Content */}
        <main className="flex-1 p-6 overflow-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

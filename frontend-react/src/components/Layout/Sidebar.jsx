import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
    const { user, logout } = useAuth();

    const getInitials = (name) => {
        return name ? name.substring(0, 1).toUpperCase() : '?';
    };

    const navLinkClasses = ({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
            ? 'bg-accent/10 text-accent border-r-2 border-accent'
            : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
        }`;

    return (
        <aside className="w-64 h-screen bg-black border-r border-zinc-800 flex flex-col shrink-0">
            {/* Header */}
            <div className="p-6 border-b border-zinc-900">
                <Link to="/" className="flex items-center gap-3 group">
                    <div className="text-white group-hover:text-accent transition-colors">
                        <svg width="32" height="32" viewBox="0 0 40 40" fill="none">
                            <rect x="4" y="8" width="32" height="24" rx="2" stroke="currentColor" strokeWidth="2" />
                            <path d="M12 16h4v8h-4z" fill="currentColor" opacity="0.8" />
                            <path d="M18 14h4v10h-4z" fill="currentColor" />
                            <path d="M24 12h4v12h-4z" fill="currentColor" opacity="0.8" />
                        </svg>
                    </div>
                    <span className="font-bold text-lg tracking-wider text-white">
                        HOME<span className="text-accent">GPU</span>
                    </span>
                </Link>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                <NavLink to="/dashboard" end className={navLinkClasses}>
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="3" width="7" height="7" />
                        <rect x="14" y="3" width="7" height="7" />
                        <rect x="14" y="14" width="7" height="7" />
                        <rect x="3" y="14" width="7" height="7" />
                    </svg>
                    <span className="font-medium">Overview</span>
                </NavLink>
                <NavLink to="/dashboard/jobs" className={navLinkClasses}>
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                        <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                        <line x1="12" y1="22.08" x2="12" y2="12" />
                    </svg>
                    <span className="font-medium">Jobs</span>
                </NavLink>
                <NavLink to="/dashboard/new-job" className={navLinkClasses}>
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="16" />
                        <line x1="8" y1="12" x2="16" y2="12" />
                    </svg>
                    <span className="font-medium">New Job</span>
                </NavLink>
                <NavLink to="/dashboard/wallet" className={navLinkClasses}>
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="1" y="4" width="22" height="16" rx="2" />
                        <line x1="1" y1="10" x2="23" y2="10" />
                        <circle cx="18" cy="15" r="1" />
                    </svg>
                    <span className="font-medium">Wallet</span>
                </NavLink>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-zinc-900 bg-zinc-950">
                <div className="flex items-center gap-3 p-2 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div className="w-8 h-8 rounded-full bg-accent/20 text-accent flex items-center justify-center font-bold text-sm">
                        {getInitials(user?.full_name)}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{user?.full_name || 'User'}</p>
                        <p className="text-xs text-zinc-500 truncate">{user?.email}</p>
                    </div>
                    <button
                        onClick={logout}
                        className="p-1.5 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded transition-colors"
                        title="Logout"
                    >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                            <polyline points="16 17 21 12 16 7" />
                            <line x1="21" y1="12" x2="9" y2="12" />
                        </svg>
                    </button>
                </div>
            </div>
        </aside>
    );
}

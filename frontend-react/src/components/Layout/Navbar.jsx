import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
    const { user } = useAuth();

    const getInitials = (name) => {
        return name ? name.substring(0, 2).toUpperCase() : 'ME';
    };

    const navLinkClasses = ({ isActive }) =>
        `relative px-6 py-2 transition-colors duration-300 font-medium text-lg ${isActive
            ? 'text-primary'
            : 'text-secondary hover:text-primary'
        }`;

    return (
        <nav className="fixed top-8 left-1/2 -translate-x-1/2 w-[92%] max-w-7xl z-50 flex items-center justify-between pointer-events-none">

            {/* Logo Container - Floating Glass */}
            <div className="pointer-events-auto bg-white/90 backdrop-blur-xl border border-white/20 shadow-xl rounded-full px-8 py-4">
                <Link to="/" className="flex items-center gap-2 group">
                    <span className="font-serif text-2xl font-bold text-primary tracking-tight group-hover:opacity-80 transition-opacity">
                        Epochly
                    </span>
                </Link>
            </div>

            {/* Center Links - Floating Glass Separate */}
            <div className="pointer-events-auto hidden md:flex items-center gap-6 bg-white/90 backdrop-blur-xl border border-white/20 shadow-xl rounded-full px-8 py-4">
                <NavLink to="/dashboard/new-job" className={navLinkClasses}>
                    New Job
                </NavLink>
                <NavLink to="/dashboard/jobs" className={navLinkClasses}>
                    Jobs
                </NavLink>
                {/* PAYMENT DISABLED - uncomment to re-enable
                <NavLink to="/dashboard/wallet" className={navLinkClasses}>
                    Wallet
                </NavLink>
                */}

            </div>

            {/* Right: Profile - Floating Glass Separate */}
            <div className="pointer-events-auto bg-white/90 backdrop-blur-xl border border-white/20 shadow-xl rounded-full px-6 py-3 flex items-center gap-4">
                <div className="flex items-center gap-3">
                    <div className="text-right hidden sm:block leading-tight">
                        <p className="font-serif font-bold text-sm text-primary">{user?.full_name || 'Guest'}</p>
                        <p className="text-xs text-secondary">Free Plan</p>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-serif font-bold shadow-md">
                        {getInitials(user?.full_name)}
                    </div>
                </div>
            </div>

        </nav>
    );
}

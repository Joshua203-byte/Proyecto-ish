import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function Overview() {
    const [stats, setStats] = useState({
        totalJobs: 0,
        runningJobs: 0,
        totalRuntime: '0h',
        totalSpent: 0
    });
    const [recentJobs, setRecentJobs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                // In a real app we might have a dedicated stats endpoint
                // For now, let's fetch jobs and calculate stats locally or mock if backend doesn't support stats
                const { data: jobs } = await api.get('/jobs/', { params: { _t: Date.now() } });

                const running = jobs.filter(j => j.status === 'running').length;
                const total = jobs.length;
                const spent = jobs.reduce((acc, job) => acc + (job.cost || 0), 0);

                setStats({
                    totalJobs: total,
                    runningJobs: running,
                    totalRuntime: '0h', // Placeholder, would need detailed logs
                    totalSpent: spent
                });
                setRecentJobs(jobs.slice(0, 5));
            } catch (error) {
                console.error("Failed to load dashboard data", error);
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) {
        return <div className="p-8 text-zinc-500 animate-pulse">Loading overview...</div>;
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Overview</h1>
                    <p className="text-zinc-500">Welcome back to your command center.</p>
                </div>
                <Link to="/dashboard/new-job" className="btn btn-primary bg-white text-black hover:bg-zinc-200 px-4 py-2 rounded-md font-medium flex items-center gap-2 transition-colors">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    New Job
                </Link>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Total Jobs"
                    value={stats.totalJobs}
                    icon={<path d="M9 9h6v6H9z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />}
                    color="text-cyan-400"
                    bg="bg-cyan-400/10"
                />
                <StatCard
                    title="Running"
                    value={stats.runningJobs}
                    icon={<polyline points="22 12 18 12 15 21 9 3 6 12 2 12" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />}
                    color="text-emerald-400"
                    bg="bg-emerald-400/10"
                />
                <StatCard
                    title="GPU Hours"
                    value={stats.totalRuntime}
                    icon={<path d="M12 6v6l4 2" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />}
                    color="text-violet-400"
                    bg="bg-violet-400/10"
                />
                <StatCard
                    title="Total Spent"
                    value={`$${stats.totalSpent.toFixed(2)}`}
                    icon={<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />}
                    color="text-orange-400"
                    bg="bg-orange-400/10"
                />
            </div>

            {/* Recent Jobs */}
            <div className="border border-zinc-800 bg-zinc-900/50 rounded-xl overflow-hidden">
                <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
                    <h2 className="text-xl font-bold text-white">Recent Jobs</h2>
                    <Link to="/dashboard/jobs" className="text-sm text-zinc-400 hover:text-white transition-colors">View All</Link>
                </div>

                <div className="p-0">
                    {recentJobs.length === 0 ? (
                        <div className="p-12 text-center text-zinc-500">
                            <div className="w-16 h-16 mx-auto mb-4 text-zinc-700 bg-zinc-800/50 rounded-full flex items-center justify-center">
                                <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <rect x="4" y="4" width="16" height="16" rx="2" />
                                    <path d="M9 9h6v6H9z" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-medium text-white mb-1">No jobs yet</h3>
                            <p className="mb-6">Start your first GPU job to see it here</p>
                            <Link to="/dashboard/new-job" className="text-accent hover:text-blue-400 font-medium">Create First Job →</Link>
                        </div>
                    ) : (
                        <div className="divide-y divide-zinc-800">
                            {recentJobs.map(job => (
                                <div key={job.id} className="p-4 flex items-center justify-between hover:bg-zinc-800/50 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-2 h-2 rounded-full ${getStatusColor(job.status)}`}></div>
                                        <div>
                                            <p className="font-medium text-white">{job.name || 'Untitled Job'}</p>
                                            <p className="text-xs text-zinc-500 font-mono">{job.id.substring(0, 8)}</p>
                                        </div>
                                    </div>
                                    <div className="text-sm text-zinc-400">
                                        {new Date(job.created_at).toLocaleDateString()}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function StatCard({ title, value, icon, color, bg }) {
    return (
        <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/50 flex items-center justify-between group hover:border-zinc-700 transition-colors">
            <div>
                <p className="text-zinc-500 text-sm font-medium mb-1">{title}</p>
                <p className="text-2xl font-bold text-white font-mono">{value}</p>
            </div>
            <div className={`w-12 h-12 rounded-lg ${bg} ${color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none">
                    {icon}
                </svg>
            </div>
        </div>
    );
}

function getStatusColor(status) {
    switch (status) {
        case 'running': return 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)]';
        case 'completed': return 'bg-blue-500';
        case 'failed': return 'bg-red-500';
        default: return 'bg-zinc-500';
    }
}

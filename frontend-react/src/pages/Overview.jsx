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
                const { data: jobs } = await api.get('/jobs/', { params: { _t: Date.now() } });
                const running = jobs.filter(j => j.status === 'running').length;
                const total = jobs.length;
                const spent = jobs.reduce((acc, job) => acc + (job.cost || 0), 0);

                setStats({
                    totalJobs: total,
                    runningJobs: running,
                    totalRuntime: '0h',
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
        return <div className="p-8 text-secondary font-serif text-xl animate-pulse">Loading overview...</div>;
    }

    return (
        <div className="space-y-12 animate-in fade-in duration-500 max-w-6xl mx-auto">
            <header className="flex justify-between items-end border-b border-border pb-8">
                <div>
                    <h1 className="text-5xl font-serif font-medium text-primary mb-2">Overview</h1>
                    <p className="text-secondary text-lg">Your command center.</p>
                </div>
                <Link to="/dashboard/new-job" className="bg-primary text-white hover:bg-primary/90 px-8 py-4 rounded-full font-medium text-lg transition-transform hover:-translate-y-1 shadow-lg">
                    New Job +
                </Link>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                <StatCard
                    title="Total Jobs"
                    value={stats.totalJobs}
                />
                <StatCard
                    title="Running"
                    value={stats.runningJobs}
                    highlight={stats.runningJobs > 0}
                />
                <StatCard
                    title="Total Spent"
                    value={`$${stats.totalSpent.toFixed(2)}`}
                />
            </div>

            {/* Recent Jobs */}
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <h2 className="text-4xl font-serif font-medium text-primary">Recent Activity</h2>
                    <Link to="/dashboard/jobs" className="text-primary hover:text-accent font-medium border-b border-primary hover:border-accent transition-colors">
                        View All Jobs
                    </Link>
                </div>

                <div className="bg-white rounded-3xl border border-border shadow-sm overflow-hidden">
                    {recentJobs.length === 0 ? (
                        <div className="p-16 text-center">
                            <h3 className="text-2xl font-serif text-primary mb-2">No jobs yet</h3>
                            <p className="text-secondary mb-8">Ready to launch your first training run?</p>
                            <Link to="/dashboard/new-job" className="text-accent hover:text-accent/80 font-bold text-lg">
                                Create First Job →
                            </Link>
                        </div>
                    ) : (
                        <div className="divide-y divide-border">
                            {recentJobs.map(job => (
                                <div key={job.id} className="p-8 flex items-center justify-between hover:bg-background transition-colors group">
                                    <div className="flex items-center gap-6">
                                        <div className={`w-3 h-3 rounded-full ${getStatusColor(job.status)}`}></div>
                                        <div>
                                            <p className="font-serif text-xl text-primary font-medium group-hover:text-accent transition-colors">
                                                {job.name || 'Untitled Job'}
                                            </p>
                                            <p className="text-sm text-secondary font-mono mt-1 opacity-60">ID: {job.id.substring(0, 8)}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-primary font-medium">{job.status}</p>
                                        <p className="text-sm text-secondary">
                                            {new Date(job.created_at).toLocaleDateString()}
                                        </p>
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

function StatCard({ title, value, highlight }) {
    return (
        <div className={`
            p-8 rounded-3xl border transition-all duration-300
            ${highlight
                ? 'bg-primary text-white border-primary shadow-xl scale-105'
                : 'bg-white text-primary border-border hover:shadow-lg'}
        `}>
            <p className={`text-sm font-medium mb-2 uppercase tracking-widest ${highlight ? 'text-white/60' : 'text-secondary'}`}>
                {title}
            </p>
            <p className="text-6xl font-serif font-medium">
                {value}
            </p>
        </div>
    );
}

function getStatusColor(status) {
    switch (status) {
        case 'running': return 'bg-accent shadow-[0_0_10px_rgba(234,88,12,0.6)]';
        case 'completed': return 'bg-success';
        case 'failed': return 'bg-error';
        default: return 'bg-secondary';
    }
}

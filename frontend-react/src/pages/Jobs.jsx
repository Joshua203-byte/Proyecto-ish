import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function Jobs() {
    const [jobs, setJobs] = useState([]);
    const [filter, setFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [selectedJob, setSelectedJob] = useState(null);
    const [logs, setLogs] = useState('');
    const [fetchingLogs, setFetchingLogs] = useState(false);

    useEffect(() => {
        let isMounted = true;
        const fetchJobs = async () => {
            try {
                const { data } = await api.get('/jobs/', { params: { _t: Date.now() } });
                if (isMounted) {
                    setJobs(data);
                    console.log(`📊 [JOBS] Fetched ${data.length} jobs`);
                }
            } catch (error) {
                console.error("Failed to fetch jobs", error);
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        fetchJobs();

        // Refresh jobs every 10 seconds
        const interval = setInterval(fetchJobs, 10000);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []); // Only on mount

    const viewLogs = async (job) => {
        setSelectedJob(job);
        setFetchingLogs(true);
        setLogs('Loading logs...');
        try {
            const { data } = await api.get(`/jobs/${job.id}/logs/`);
            setLogs(data.logs || 'No logs available yet.');
        } catch (error) {
            console.error("Failed to fetch logs", error);
            setLogs("Error loading logs from server.");
        } finally {
            setFetchingLogs(false);
        }
    };

    const downloadResults = async (job) => {
        try {
            const response = await api.get(`/jobs/${job.id}/download`, {
                responseType: 'blob',
            });

            // Create blob link to download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `results_${job.id}.zip`);

            // Append to html link element page
            document.body.appendChild(link);

            // Start download
            link.click();

            // Clean up and remove the link
            link.parentNode.removeChild(link);
        } catch (error) {
            console.error("Failed to download results", error);
            alert("Error downloading results. Please try again.");
        }
    };

    const filteredJobs = filter === 'all'
        ? jobs
        : jobs.filter(job => job.status === filter);

    if (loading) return <div className="p-8 text-zinc-500">Loading jobs...</div>;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Jobs</h1>
                    <p className="text-zinc-500">Manage and monitor your training tasks.</p>
                </div>
                <Link to="/dashboard/new-job" className="btn btn-primary bg-white text-black hover:bg-zinc-200 px-4 py-2 rounded-md font-medium flex items-center gap-2">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    New Job
                </Link>
            </header>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-zinc-800 pb-1">
                {['all', 'running', 'completed', 'failed', 'pending'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setFilter(tab)}
                        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${filter === tab
                            ? 'text-white border-b-2 border-accent bg-zinc-900/50'
                            : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/30'
                            }`}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            {/* Jobs List */}
            <div className="grid gap-4">
                {filteredJobs.length === 0 ? (
                    <div className="text-center py-12 text-zinc-500 bg-zinc-900/30 rounded-lg border border-zinc-800/50">
                        No {filter !== 'all' && filter} jobs found.
                    </div>
                ) : (
                    filteredJobs.map(job => (
                        <div key={job.id} className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/50 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-zinc-700 transition-all">
                            <div className="flex items-center gap-4">
                                <StatusIcon status={job.status} />
                                <div>
                                    <h3 className="text-lg font-bold text-white">
                                        {job.name || (job.script_path ? job.script_path.split('/').pop() : 'Untitled Job')}
                                    </h3>
                                    <div className="flex gap-4 text-xs text-zinc-500 font-mono mt-1">
                                        <span>ID: {job.id.substring(0, 8)}</span>
                                        <span>•</span>
                                        <span>{job.created_at ? new Date(job.created_at).toLocaleString() : 'Just now'}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="text-right hidden md:block">
                                    <p className="text-sm text-zinc-400">Duration</p>
                                    <p className="text-white font-mono">{formatDuration(job.runtime_seconds)}</p>
                                </div>
                                <div className="text-right hidden md:block">
                                    <p className="text-sm text-zinc-400">Cost</p>
                                    <p className="text-white font-mono">${Number(job.total_cost || 0).toFixed(2)}</p>
                                </div>
                                <button
                                    onClick={() => viewLogs(job)}
                                    className="px-4 py-1.5 text-sm bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 text-white transition-colors"
                                >
                                    Logs
                                </button>
                                {job.status === 'completed' && (
                                    <button
                                        onClick={() => downloadResults(job)}
                                        className="px-4 py-1.5 text-sm bg-blue-600 border border-blue-500 rounded-lg hover:bg-blue-500 text-white transition-colors flex items-center gap-2"
                                    >
                                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                            <polyline points="7 10 12 15 17 10" />
                                            <line x1="12" y1="15" x2="12" y2="3" />
                                        </svg>
                                        Results
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Logs Modal */}
            {selectedJob && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
                        <div className="p-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
                            <div>
                                <h2 className="text-lg font-bold text-white">Execution Logs</h2>
                                <p className="text-xs text-zinc-500 font-mono">Job: {selectedJob.id}</p>
                            </div>
                            <button
                                onClick={() => setSelectedJob(null)}
                                className="p-2 hover:bg-zinc-800 rounded-full text-zinc-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto p-4 bg-black font-mono text-sm">
                            <pre className="text-emerald-500 whitespace-pre-wrap">
                                {fetchingLogs ? (
                                    <div className="flex items-center gap-2 text-zinc-500">
                                        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                                        </svg>
                                        Fetching logs from system...
                                    </div>
                                ) : (
                                    logs || '// No logs available for this job stage.'
                                )}
                            </pre>
                        </div>
                        <div className="p-4 border-t border-zinc-800 bg-zinc-900/50 flex justify-end">
                            <button
                                onClick={() => viewLogs(selectedJob)}
                                className="text-xs text-accent hover:text-blue-400 font-medium flex items-center gap-1 transition-colors"
                            >
                                <svg className={`w-3 h-3 ${fetchingLogs ? 'animate-spin' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                                </svg>
                                Refresh Logs
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function StatusIcon({ status }) {
    if (status === 'running') {
        return (
            <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
            </div>
        );
    }
    if (status === 'completed') {
        return (
            <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12" />
                </svg>
            </div>
        );
    }
    if (status === 'failed') {
        return (
            <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
            </div>
        );
    }
    return (
        <div className="w-10 h-10 rounded-full bg-zinc-500/10 flex items-center justify-center text-zinc-500">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
            </svg>
        </div>
    );
}

function formatDuration(seconds) {
    if (!seconds) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins === 0) return `${secs}s`;
    return `${mins}m ${secs}s`;
}

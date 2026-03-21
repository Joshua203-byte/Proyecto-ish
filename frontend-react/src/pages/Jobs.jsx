import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'sonner';

export default function Jobs() {
    const [jobs, setJobs] = useState([]);
    const [filter, setFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [selectedJob, setSelectedJob] = useState(null);
    const [logs, setLogs] = useState('');
    const [fetchingLogs, setFetchingLogs] = useState(false);
    const logContainerRef = useRef(null);

    // Confirmation Modal State
    const [confirmAction, setConfirmAction] = useState(null); // { type: 'cancel' | 'delete', job: jobObject }

    useEffect(() => {
        let isMounted = true;
        const fetchJobs = async () => {
            try {
                const { data } = await api.get('/jobs/', { params: { _t: Date.now() } });
                if (isMounted) {
                    setJobs(Array.isArray(data) ? data : (data.jobs || data.items || []));
                    // Update selectedJob if it's open (to get latest status)
                    if (selectedJob) {
                        const updated = data.find(j => j.id === selectedJob.id);
                        if (updated) setSelectedJob(updated);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch jobs", error);
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        fetchJobs();
        const interval = setInterval(fetchJobs, 5000);
        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [selectedJob?.id]);

    // Auto-poll logs when viewing a running job
    useEffect(() => {
        if (!selectedJob) return;

        const fetchLogs = async () => {
            try {
                const { data } = await api.get(`/jobs/${selectedJob.id}/logs/`);
                setLogs(data.logs || 'No logs available yet.');
                // Auto-scroll to bottom
                if (logContainerRef.current) {
                    logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
                }
            } catch (error) {
                // Don't overwrite existing logs on error
            }
        };

        fetchLogs();

        // Poll every 3 seconds for running jobs, every 10s for others
        const isRunning = ['running', 'pending', 'queued'].includes(selectedJob.status);
        const pollInterval = isRunning ? 3000 : null;

        let interval;
        if (pollInterval) {
            interval = setInterval(fetchLogs, pollInterval);
        }

        return () => { if (interval) clearInterval(interval); };
    }, [selectedJob?.id, selectedJob?.status]);

    const viewLogs = async (job) => {
        setSelectedJob(job);
        setFetchingLogs(true);
        setLogs('Loading logs...');
        try {
            const { data } = await api.get(`/jobs/${job.id}/logs/`);
            setLogs(data.logs || 'No logs available yet.');
        } catch (error) {
            setLogs("Error loading logs from server.");
        } finally {
            setFetchingLogs(false);
        }
    };

    // --- Action Handlers (Previously window.confirm) ---

    // 1. Request Cancel
    const requestCancel = (job, e) => {
        if (e) e.stopPropagation();
        setConfirmAction({ type: 'cancel', job });
    };

    // 2. Request Delete
    const requestDelete = (job, e) => {
        if (e) e.stopPropagation();
        setConfirmAction({ type: 'delete', job });
    };

    // 3. Confirm Handler
    const handleConfirm = async () => {
        if (!confirmAction) return;
        const { type, job } = confirmAction;

        try {
            if (type === 'cancel') {
                await api.post(`/jobs/${job.id}/cancel/`);
                toast.success('Job cancellation requested');
            } else if (type === 'delete') {
                await api.delete(`/jobs/${job.id}/`);
                toast.success('Job deleted');
            }

            // Refresh list
            const { data } = await api.get('/jobs/', { params: { _t: Date.now() } });
            setJobs(Array.isArray(data) ? data : (data.jobs || data.items || []));

            // Update modal state if needed
            if (selectedJob && selectedJob.id === job.id) {
                if (type === 'delete') setSelectedJob(null);
                if (type === 'cancel') setSelectedJob(prev => ({ ...prev, status: 'cancelled' }));
            }
        } catch (error) {
            toast.error(`Failed to ${type} job`);
        } finally {
            setConfirmAction(null);
        }
    };

    const copyLogs = () => {
        navigator.clipboard.writeText(logs);
        toast.success('Logs copied to clipboard');
    };

    const filteredJobs = filter === 'all'
        ? jobs
        : jobs.filter(job => job.status === filter);

    if (loading) return <div className="p-8 text-secondary font-serif text-xl animate-pulse">Loading jobs...</div>;

    return (
        <div className="pt-48 space-y-12 animate-in fade-in duration-500 max-w-6xl mx-auto px-6 relative">
            <header className="flex justify-between items-end border-b border-border pb-8">
                <div>
                    <h1 className="text-5xl font-serif font-medium text-primary mb-2">Jobs</h1>
                    <p className="text-secondary text-lg">Manage your transfers.</p>
                </div>
                <Link to="/dashboard/new-job" className="bg-primary text-white hover:bg-primary/90 px-8 py-4 rounded-full font-medium text-lg transition-transform hover:-translate-y-1 shadow-lg">
                    New Job +
                </Link>
            </header>

            {/* Tabs */}
            <div className="flex gap-6 border-b border-border pb-1">
                {['all', 'running', 'completed', 'failed'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setFilter(tab)}
                        className={`pb-4 text-lg font-serif transition-colors ${filter === tab
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-secondary hover:text-primary'
                            }`}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            {/* Jobs List */}
            <div className="space-y-4">
                {filteredJobs.length === 0 ? (
                    <div className="p-16 text-center bg-white rounded-3xl border border-border">
                        <p className="text-secondary text-lg mb-6">No {filter !== 'all' && filter} jobs found.</p>
                    </div>
                ) : (
                    filteredJobs.map(job => (
                        <div key={job.id} onClick={() => viewLogs(job)} className="group cursor-pointer p-8 rounded-3xl bg-white border border-border hover:shadow-lg transition-all duration-300 flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <StatusIcon status={job.status} />
                                <div>
                                    <h3 className="text-2xl font-serif font-medium text-primary group-hover:text-accent transition-colors">
                                        {job.name || (job.script_path ? job.script_path.split('/').pop() : 'Untitled Job')}
                                    </h3>
                                    <div className="flex gap-4 text-sm text-secondary font-mono mt-2">
                                        <span>{job.id.substring(0, 8)}</span>
                                        <span>•</span>
                                        <span>{new Date(job.created_at).toLocaleString()}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-8">
                                <div className="text-right hidden md:block">
                                    <p className="text-sm font-medium text-secondary uppercase tracking-widest">Duration</p>
                                    <JobDuration job={job} />
                                </div>

                                {/* Main Action Button in List */}
                                <div className="flex items-center gap-2">
                                    {['running', 'pending'].includes(job.status) && (
                                        <button
                                            onClick={(e) => requestCancel(job, e)}
                                            className="p-3 text-secondary hover:text-white hover:bg-error rounded-full transition-colors"
                                            title="Cancel Job"
                                        >
                                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        </button>
                                    )}
                                    {job.status === 'completed' && (
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                toast.promise(
                                                    api.get(`/jobs/${job.id}/download`, { responseType: 'blob' })
                                                        .then((response) => {
                                                            const url = window.URL.createObjectURL(new Blob([response.data]));
                                                            const link = document.createElement('a');
                                                            link.href = url;
                                                            link.setAttribute('download', `job_${job.id}_results.zip`);
                                                            document.body.appendChild(link);
                                                            link.click();
                                                            link.remove();
                                                        }),
                                                    {
                                                        loading: 'Preparing download...',
                                                        success: 'Download started',
                                                        error: 'Failed to download results'
                                                    }
                                                );
                                            }}
                                            className="p-3 text-secondary hover:text-primary hover:bg-neutral-100 rounded-full transition-colors"
                                            title="Download Results"
                                        >
                                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                            </svg>
                                        </button>
                                    )}
                                    {['completed', 'failed', 'cancelled'].includes(job.status) && (
                                        <button
                                            onClick={(e) => requestDelete(job, e)}
                                            className="p-3 text-secondary hover:text-error hover:bg-error/10 rounded-full transition-colors"
                                            title="Delete Job"
                                        >
                                            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                            </svg>
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Logs Modal */}
            {selectedJob && (
                <div className="fixed inset-0 z-40 flex items-center justify-end animate-in slide-in-from-right duration-500">
                    <div className="absolute inset-0 bg-primary/20 backdrop-blur-sm" onClick={() => setSelectedJob(null)}></div>
                    <div className="relative w-full max-w-2xl h-full bg-white shadow-2xl flex flex-col">
                        <div className="p-8 border-b border-border flex justify-between items-center bg-background">
                            <div>
                                <h2 className="text-3xl font-serif font-medium text-primary mb-1">Logs</h2>
                                <p className="text-secondary font-mono text-sm uppercase tracking-wider">{selectedJob.status}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={copyLogs}
                                    className="p-2 text-secondary hover:text-primary hover:bg-neutral-100 rounded-lg transition-colors"
                                    title="Copy Logs"
                                >
                                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                                    </svg>
                                </button>

                                {['completed', 'failed', 'cancelled'].includes(selectedJob.status) && (
                                    <button
                                        onClick={(e) => requestDelete(selectedJob, e)}
                                        className="p-2 text-secondary hover:text-error hover:bg-error/10 rounded-lg transition-colors"
                                        title="Delete Job"
                                    >
                                        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                )}

                                {selectedJob.status === 'completed' && (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            const token = localStorage.getItem('token');
                                            // Direct download using window.location to trigger browser download
                                            // We need to pass auth token? The API is protected. 
                                            // Actually, we should fetch a blob or use a signed URL. 
                                            // For simplicity with Bearer auth, we can use a fetch and create an object URL.

                                            toast.promise(
                                                api.get(`/jobs/${selectedJob.id}/download`, { responseType: 'blob' })
                                                    .then((response) => {
                                                        const url = window.URL.createObjectURL(new Blob([response.data]));
                                                        const link = document.createElement('a');
                                                        link.href = url;
                                                        link.setAttribute('download', `job_${selectedJob.id}_results.zip`);
                                                        document.body.appendChild(link);
                                                        link.click();
                                                        link.remove();
                                                    }),
                                                {
                                                    loading: 'Preparing download...',
                                                    success: 'Download started',
                                                    error: 'Failed to download results'
                                                }
                                            );
                                        }}
                                        className="p-2 text-secondary hover:text-primary hover:bg-neutral-100 rounded-lg transition-colors"
                                        title="Download Results"
                                    >
                                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                    </button>
                                )}

                                <button onClick={() => setSelectedJob(null)} className="ml-4 text-secondary hover:text-primary">
                                    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <line x1="18" y1="6" x2="6" y2="18" />
                                        <line x1="6" y1="6" x2="18" y2="18" />
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <div ref={logContainerRef} className="flex-1 overflow-auto p-8 font-mono text-sm bg-white text-primary leading-relaxed whitespace-pre-wrap selection:bg-accent selection:text-white">
                            {fetchingLogs ? 'Loading...' : (logs || 'No logs available.')}
                        </div>
                    </div>
                </div>
            )}

            {/* Custom Confirmation Modal */}
            {confirmAction && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6 animate-in fade-in duration-200">
                    {/* Backdrop */}
                    <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setConfirmAction(null)}></div>

                    {/* Modal Card */}
                    <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl p-8 border border-white/20 scale-100 transition-transform">
                        <div className="flex flex-col items-center text-center">

                            {/* Icon */}
                            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-6 
                                ${confirmAction.type === 'delete' ? 'bg-error/10 text-error' : 'bg-accent/10 text-accent'}`}>
                                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                    {confirmAction.type === 'delete'
                                        ? <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        : <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    }
                                </svg>
                            </div>

                            {/* Text */}
                            <h3 className="text-2xl font-serif font-bold text-primary mb-2">
                                {confirmAction.type === 'delete' ? 'Delete Job?' : 'Stop Running Job?'}
                            </h3>
                            <p className="text-secondary mb-8">
                                {confirmAction.type === 'delete'
                                    ? `This will permanently remove the job "${confirmAction.job.name || 'Untitled'}" and its logs.`
                                    : `Are you sure you want to halt "${confirmAction.job.name || 'Untitled'}"? This cannot be undone.`}
                            </p>

                            {/* Buttons */}
                            <div className="flex gap-4 w-full">
                                <button
                                    onClick={() => setConfirmAction(null)}
                                    className="flex-1 py-3 px-6 rounded-xl font-medium text-secondary hover:bg-neutral-100 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleConfirm}
                                    className={`flex-1 py-3 px-6 rounded-xl font-bold text-white shadow-lg transition-transform hover:-translate-y-0.5
                                        ${confirmAction.type === 'delete' ? 'bg-error hover:bg-error/90' : 'bg-primary hover:bg-primary/90'}`}
                                >
                                    {confirmAction.type === 'delete' ? 'Yes, Delete' : 'Stop Job'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}


function JobDuration({ job }) {
    const [duration, setDuration] = useState(() => computeDuration(job));

    useEffect(() => {
        const updateDuration = () => {
            setDuration(computeDuration(job));
        };

        updateDuration();

        let interval;
        if (job.status === 'running') {
            interval = setInterval(updateDuration, 1000);
        }

        return () => clearInterval(interval);
    }, [job.status, job.started_at, job.completed_at, job.runtime_seconds]);

    return <p className="text-primary font-mono text-lg">{formatDuration(duration)}</p>;
}

function computeDuration(job) {
    // If runtime_seconds is set and > 0, use it
    if (job.runtime_seconds && job.runtime_seconds > 0) {
        return job.runtime_seconds;
    }

    if (!job.started_at) return 0;

    // Parse start time (assume UTC if no timezone info)
    let start;
    const startTs = job.started_at;
    if (typeof startTs === 'string' && !startTs.endsWith('Z') && !startTs.includes('+')) {
        start = new Date(startTs + 'Z').getTime();
    } else {
        start = new Date(startTs).getTime();
    }

    // If job is completed/failed, calculate from started_at to completed_at
    if (['completed', 'failed', 'cancelled'].includes(job.status) && job.completed_at) {
        let end;
        const endTs = job.completed_at;
        if (typeof endTs === 'string' && !endTs.endsWith('Z') && !endTs.includes('+')) {
            end = new Date(endTs + 'Z').getTime();
        } else {
            end = new Date(endTs).getTime();
        }
        return Math.max(0, Math.floor((end - start) / 1000));
    }

    // If still running, calculate from started_at to now
    if (job.status === 'running') {
        const now = Date.now();
        return Math.max(0, Math.floor((now - start) / 1000));
    }

    return 0;
}

function StatusIcon({ status }) {
    if (status === 'running') return <div className="w-4 h-4 rounded-full bg-accent animate-pulse shadow-[0_0_10px_rgba(234,88,12,0.6)]"></div>;
    if (status === 'completed') return <div className="w-4 h-4 rounded-full bg-success"></div>;
    if (status === 'failed') return <div className="w-4 h-4 rounded-full bg-error"></div>;
    if (status === 'cancelled') return <div className="w-4 h-4 rounded-full bg-neutral-400"></div>;
    return <div className="w-4 h-4 rounded-full bg-secondary/50"></div>;
}

function formatDuration(seconds) {
    if (seconds === undefined || seconds === null) return '--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;

    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
}


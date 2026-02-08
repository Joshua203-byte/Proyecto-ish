import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'sonner';

import AdBackground from '../components/Layout/AdBackground';

export default function NewJob() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [showInstructions, setShowInstructions] = useState(false);
    const [script, setScript] = useState(null);
    const [dataset, setDataset] = useState(null);
    const [formData, setFormData] = useState({
        email: '',
        memory: '8g',
        timeout: '3600',
        launchCommand: ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();

        // 1. Script Validation
        if (!script) {
            toast.warning('Please select a Python script');
            return;
        }

        // 2. Email Validation (Mandatory)
        if (!formData.email || !formData.email.trim()) {
            toast.warning('Email is required for job notifications');
            return;
        }

        setLoading(true);
        setUploadProgress(0);

        const data = new FormData();
        data.append('script_file', script);
        if (dataset) data.append('dataset_file', dataset);
        data.append('email', formData.email);
        data.append('memory', formData.memory);
        data.append('timeout', formData.timeout);
        data.append('launch_command', formData.launchCommand || '');

        try {
            // Use XMLHttpRequest for progress tracking
            const token = localStorage.getItem('token');
            const baseURL = api.defaults.baseURL || '';

            await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', `${baseURL}/jobs/`);
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                xhr.timeout = 600000; // 10 minutes timeout

                xhr.upload.onprogress = (event) => {
                    if (event.lengthComputable) {
                        const percent = Math.round((event.loaded / event.total) * 100);
                        setUploadProgress(percent);
                    }
                };

                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve(JSON.parse(xhr.responseText));
                    } else {
                        try {
                            const error = JSON.parse(xhr.responseText);
                            reject(new Error(error.detail || 'Upload failed'));
                        } catch {
                            reject(new Error('Upload failed'));
                        }
                    }
                };

                xhr.onerror = () => reject(new Error('Network error'));
                xhr.ontimeout = () => reject(new Error('Upload timed out (10 min limit)'));
                xhr.send(data);
            });

            toast.success('Job started successfully');
            navigate('/dashboard/jobs');
        } catch (error) {
            console.error("Job submit error:", error);
            const msg = error.message || "Failed to create job.";
            toast.error(msg);
        } finally {
            setLoading(false);
            setUploadProgress(0);
        }
    };

    return (
        <div className="relative min-h-[calc(100vh-80px)] w-full flex items-center justify-center p-6">
            <AdBackground />

            <div className="relative z-10 w-full max-w-6xl flex items-center justify-center gap-12">

                {/* Left: Text (Hidden on small screens) */}
                <div className="hidden lg:block text-primary max-w-sm">
                    <h1 className="text-6xl font-serif font-medium mb-3 leading-none">New Job</h1>
                    <p className="text-xl text-secondary">Deploy specific code to DGX Spark.</p>
                </div>

                {/* Right: Ultra Compact Card */}
                <div className="bg-white/90 backdrop-blur rounded-[2rem] shadow-2xl p-8 w-full max-w-md border border-white/50">
                    <form onSubmit={handleSubmit} className="flex flex-col gap-5">

                        {/* 1. Script (Primary) */}
                        <div className="relative">
                            <label className={`
                                flex items-center gap-4 p-4 rounded-xl border-2 border-dashed cursor-pointer transition-colors
                                ${script ? 'border-accent bg-accent/5' : 'border-neutral-300 hover:border-neutral-400'}
                            `}>
                                <input type="file" accept=".py,.ipynb" onChange={e => setScript(e.target.files[0])} className="hidden" />
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${script ? 'bg-accent text-white' : 'bg-neutral-100 text-neutral-500'}`}>
                                    <span className="font-bold text-lg">{script ? '✓' : '{}'}</span>
                                </div>
                                <div className="min-w-0">
                                    <div className="font-medium text-primary truncate">
                                        {script ? script.name : "Select Script"}
                                    </div>
                                    <div className="text-xs text-secondary">
                                        {script ? "Ready to upload" : "Required (.py or .ipynb)"}
                                    </div>
                                </div>
                            </label>
                        </div>

                        {/* 2. Dataset (Secondary) */}
                        <div className="relative">
                            <input type="file" id="ds" accept=".zip,.csv,.pkl,.tar,.tar.gz,.tgz,application/zip,application/x-tar,application/gzip,application/x-gzip,text/csv" onChange={e => setDataset(e.target.files[0])} className="hidden" />
                            <label htmlFor="ds" className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-neutral-100 transition-colors">
                                <span className={`text-xs font-bold uppercase tracking-wider ${dataset ? 'text-accent' : 'text-secondary'}`}>
                                    {dataset ? 'DATASET ADDED' : '+ ADD DATASET'}
                                </span>
                                {dataset && <span className="text-sm text-primary truncate">{dataset.name}</span>}
                            </label>
                        </div>

                        {/* 3. Settings Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-[10px] uppercase font-bold text-secondary tracking-wider ml-1">Email (Required)</label>
                                <input
                                    type="email"
                                    required
                                    placeholder="name@example.com"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className="w-full bg-neutral-100 border-0 rounded-lg py-2 px-3 text-sm focus:ring-1 focus:ring-primary invalid:ring-red-500/50"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="text-[10px] uppercase font-bold text-secondary tracking-wider ml-1">RAM</label>
                                    <select
                                        value={formData.memory}
                                        onChange={(e) => setFormData({ ...formData, memory: e.target.value })}
                                        className="w-full bg-neutral-100 border-0 rounded-lg py-2 px-1 text-sm text-center font-medium"
                                    >
                                        <option value="8g">8GB</option>
                                        <option value="24g">24GB</option>
                                        <option value="80g">80GB</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase font-bold text-secondary tracking-wider ml-1">Time</label>
                                    <select
                                        value={formData.timeout}
                                        onChange={(e) => setFormData({ ...formData, timeout: e.target.value })}
                                        className="w-full bg-neutral-100 border-0 rounded-lg py-2 px-1 text-sm text-center font-medium"
                                    >
                                        <option value="1800">30m</option>
                                        <option value="3600">1h</option>
                                        <option value="14400">4h</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* 4. Instructions Collapsible */}
                        <div className="border border-neutral-200 rounded-lg overflow-hidden">
                            <button
                                type="button"
                                onClick={() => setShowInstructions(!showInstructions)}
                                className="w-full flex items-center justify-between px-4 py-2 bg-neutral-50 hover:bg-neutral-100 transition-colors"
                            >
                                <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                                    📋 Instructions & Requirements
                                </span>
                                <span className="text-secondary text-lg">{showInstructions ? '−' : '+'}</span>
                            </button>
                            {showInstructions && (
                                <div className="px-4 py-3 text-xs text-secondary space-y-2 bg-white">
                                    <p className="font-semibold text-primary">File Paths:</p>
                                    <ul className="list-disc list-inside space-y-1 ml-1">
                                        <li><code className="bg-neutral-100 px-1 rounded">/workspace/input/</code> — Your script & dataset</li>
                                        <li><code className="bg-neutral-100 px-1 rounded">/workspace/output/</code> — Save results here</li>
                                    </ul>
                                    <p className="font-semibold text-primary pt-2">Script Requirements:</p>
                                    <ul className="list-disc list-inside space-y-1 ml-1">
                                        <li>Use <code className="bg-neutral-100 px-1 rounded">.py</code> or <code className="bg-neutral-100 px-1 rounded">.ipynb</code> files</li>
                                        <li>Dependencies are auto-installed from imports</li>
                                        <li>GPU available via PyTorch/TensorFlow</li>
                                    </ul>
                                    <p className="font-semibold text-primary pt-2">Dataset Tips:</p>
                                    <ul className="list-disc list-inside space-y-1 ml-1">
                                        <li>Supported: .zip, .tar.gz, .csv, .pkl</li>
                                        <li>Max upload time: 10 minutes</li>
                                        <li>Files extracted to <code className="bg-neutral-100 px-1 rounded">/workspace/input/</code></li>
                                    </ul>
                                </div>
                            )}
                        </div>

                        {/* 4. Submit */}
                        {loading ? (
                            <div className="w-full mt-2">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-medium text-primary">
                                        {uploadProgress < 100 ? 'Uploading...' : 'Processing...'}
                                    </span>
                                    <span className="text-sm font-bold text-accent">{uploadProgress}%</span>
                                </div>
                                <div className="w-full bg-neutral-200 rounded-full h-4 overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-accent to-primary rounded-full transition-all duration-300 ease-out"
                                        style={{ width: `${uploadProgress}%` }}
                                    />
                                </div>
                                <p className="text-xs text-secondary text-center mt-2">
                                    {uploadProgress < 100
                                        ? 'Please wait, uploading files...'
                                        : 'Upload complete, starting job...'}
                                </p>
                            </div>
                        ) : (
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-4 rounded-xl font-bold text-lg shadow-lg mt-2 transition-transform hover:-translate-y-0.5 bg-primary text-white hover:bg-primary/90"
                            >
                                Run Job
                            </button>
                        )}
                    </form>
                </div>
            </div>
        </div>
    );
}

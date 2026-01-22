import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'sonner';

export default function NewJob() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [script, setScript] = useState(null);
    const [dataset, setDataset] = useState(null);
    const [formData, setFormData] = useState({
        memory: '8g',
        timeout: '3600'
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!script) {
            toast.warning('Por favor selecciona un script de Python (.py)');
            return;
        }

        setLoading(true);
        const data = new FormData();
        data.append('script_file', script);
        if (dataset) data.append('dataset_file', dataset);
        data.append('memory', formData.memory);
        data.append('timeout', formData.timeout);

        try {
            console.log("🚀 [FRONTEND] Starting job submission...");
            console.log("📂 Script:", script.name);
            if (dataset) console.log("📂 Dataset:", dataset.name);
            console.log("⚙️ Config:", formData);

            const response = await api.post('/jobs/', data, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            console.log("✅ [FRONTEND] Success! Response:", response.data);
            navigate('/dashboard/jobs');
        } catch (error) {
            console.error("❌ Job Submission Error:", error);
            // El toast se maneja automáticamente en api.js
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in slide-in-from-bottom-4 duration-500">
            <header>
                <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Create New Job</h1>
                <p className="text-zinc-500">Upload your Python script and dataset to run on our GPUs.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Form Section */}
                <div className="lg:col-span-2 space-y-6">
                    <form onSubmit={handleSubmit} className="p-8 rounded-xl border border-zinc-800 bg-zinc-900/50 space-y-6">

                        {/* Script Upload */}
                        <div>
                            <label className="block text-sm font-medium text-zinc-300 mb-2">Python Script *</label>
                            <div className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${script ? 'border-accent bg-accent/5' : 'border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/50'}`}>
                                <input
                                    type="file"
                                    accept=".py"
                                    onChange={e => setScript(e.target.files[0])}
                                    className="hidden"
                                    id="script-upload"
                                />
                                <label htmlFor="script-upload" className="cursor-pointer block w-full h-full">
                                    <div className="mb-4 flex justify-center">
                                        <svg className={`w-10 h-10 ${script ? 'text-accent' : 'text-zinc-500'}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                            <polyline points="14 2 14 8 20 8" />
                                            {script && <path d="M9 15l2 2 4-4" />}
                                        </svg>
                                    </div>
                                    <p className="text-sm font-medium text-white">
                                        {script ? script.name : "Drop your .py file here"}
                                    </p>
                                    {!script && <p className="text-xs text-zinc-500 mt-1">or click to browse</p>}
                                </label>
                            </div>
                        </div>

                        {/* Dataset Upload */}
                        <div>
                            <label className="block text-sm font-medium text-zinc-300 mb-2">Dataset (Optional)</label>
                            <div className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${dataset ? 'border-accent bg-accent/5' : 'border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/50'}`}>
                                <input
                                    type="file"
                                    accept=".zip,.csv,.json,.pt,.pkl,.npy,.h5"
                                    onChange={e => setDataset(e.target.files[0])}
                                    className="hidden"
                                    id="dataset-upload"
                                />
                                <label htmlFor="dataset-upload" className="cursor-pointer block w-full h-full">
                                    <div className="flex items-center justify-center gap-3">
                                        <svg className={`w-6 h-6 ${dataset ? 'text-accent' : 'text-zinc-500'}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                            <polyline points="17 8 12 3 7 8" />
                                            <line x1="12" y1="3" x2="12" y2="15" />
                                        </svg>
                                        <span className="text-sm text-zinc-400">
                                            {dataset ? dataset.name : "Upload dataset file"}
                                        </span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        {/* Config Row */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-zinc-300 mb-2">Memory Limit</label>
                                <select
                                    value={formData.memory}
                                    onChange={(e) => setFormData({ ...formData, memory: e.target.value })}
                                    className="w-full bg-zinc-900 border border-zinc-700 rounded-md py-2 px-3 text-white focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
                                >
                                    <option value="4g">4 GB</option>
                                    <option value="8g">8 GB</option>
                                    <option value="16g">16 GB</option>
                                    <option value="24g">24 GB (Full)</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-300 mb-2">Timeout</label>
                                <select
                                    value={formData.timeout}
                                    onChange={(e) => setFormData({ ...formData, timeout: e.target.value })}
                                    className="w-full bg-zinc-900 border border-zinc-700 rounded-md py-2 px-3 text-white focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
                                >
                                    <option value="1800">30 minutes</option>
                                    <option value="3600">1 hour</option>
                                    <option value="7200">2 hours</option>
                                    <option value="14400">4 hours</option>
                                </select>
                            </div>
                        </div>

                        {/* Cost Estimate */}
                        <div className="bg-zinc-900/80 rounded-lg p-4 flex justify-between items-center border border-zinc-800">
                            <span className="text-zinc-400 text-sm">Estimated Cost</span>
                            <span className="text-white font-mono font-bold">~1.0 credits/min</span>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={`w-full py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${loading ? 'bg-zinc-700 text-zinc-400 cursor-not-allowed' : 'bg-accent hover:bg-blue-600 text-white shadow-lg hover:shadow-blue-900/20'
                                }`}
                        >
                            {loading ? (
                                <>
                                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Launching...
                                </>
                            ) : (
                                <>
                                    <span>Launch Job</span>
                                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <polygon points="5 3 19 12 5 21 5 3" />
                                    </svg>
                                </>
                            )}
                        </button>
                    </form>
                </div>

                {/* Sidebar Info */}
                <div className="space-y-6">
                    <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30">
                        <h3 className="text-lg font-bold text-white mb-4">GPU Specifications</h3>
                        <div className="space-y-4">
                            <SpecRow label="Model" value="NVIDIA RTX 4090" />
                            <SpecRow label="VRAM" value="24 GB GDDR6X" />
                            <SpecRow label="CUDA Cores" value="16,384" />
                            <SpecRow label="CUDA Version" value="12.1" />
                            <SpecRow label="PyTorch" value="2.2.0" />
                        </div>
                        <div className="mt-6 pt-6 border-t border-zinc-800">
                            <p className="text-xs text-zinc-500 leading-relaxed">
                                Pre-installed: PyTorch, TensorFlow, Transformers, Pandas, NumPy, and 50+ ML libraries.
                            </p>
                        </div>
                    </div>

                    {/* Developer Guide */}
                    <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30">
                        <h3 className="text-lg font-bold text-white mb-4">📜 Developer Guide</h3>
                        <div className="space-y-4 text-sm text-zinc-400">
                            <div>
                                <h4 className="font-semibold text-zinc-300 mb-1">📂 File Paths</h4>
                                <ul className="list-disc pl-4 space-y-1">
                                    <li>Input Data: <code className="bg-zinc-800 px-1 rounded">/workspace/input</code></li>
                                    <li>Output: <code className="bg-zinc-800 px-1 rounded">/workspace/output</code></li>
                                    <li>Script: <code className="bg-zinc-800 px-1 rounded">/workspace/input/train.py</code></li>
                                </ul>
                            </div>

                            <div>
                                <h4 className="font-semibold text-zinc-300 mb-1">📦 Dependencies</h4>
                                <p>To install extra packages (like transformers), use this at the top of your script:</p>
                                <pre className="bg-zinc-950 p-2 rounded mt-2 text-xs font-mono overflow-x-auto text-green-400">
                                    {`import subprocess, sys
subprocess.check_call([
  sys.executable, "-m", "pip", "install", 
  "transformers", "peft"
])`}
                                </pre>
                            </div>

                            <div>
                                <h4 className="font-semibold text-zinc-300 mb-1">⚠️ Common Pitfalls</h4>
                                <ul className="list-disc pl-4 space-y-1">
                                    <li>Always write results to <code className="bg-zinc-800 px-1 rounded">output/</code> directory.</li>
                                    <li>Use <code className="bg-zinc-800 px-1 rounded">DataLoader</code> for batching data.</li>
                                    <li>Log progress with <code className="bg-zinc-800 px-1 rounded">print()</code> to see it in logs.</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function SpecRow({ label, value }) {
    return (
        <div className="flex justify-between items-center text-sm">
            <span className="text-zinc-500">{label}</span>
            <span className="text-zinc-200 font-mono">{value}</span>
        </div>
    );
}

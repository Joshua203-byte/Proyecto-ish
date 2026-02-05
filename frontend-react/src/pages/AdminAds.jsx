import { useState, useEffect } from 'react';
import api from '../services/api';
import { toast } from 'sonner';
import { getAssetUrl } from '../utils/url';

export default function AdminAds() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [pin, setPin] = useState("");

    const [ads, setAds] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);

    // New Ad Form State
    const [newAdTitle, setNewAdTitle] = useState("");
    const [newAdUrl, setNewAdUrl] = useState("");
    const [newAdFile, setNewAdFile] = useState(null);
    const [newAdPreview, setNewAdPreview] = useState(null);

    const checkPin = (e) => {
        e.preventDefault();
        if (pin === "batman") { // Simple client-side check matching backend
            setIsAuthenticated(true);
            toast.success("Welcome, Admin");
            // Store key for API requests later if we use an interceptor, 
            // but here we'll just pass it explicitly in calls.
            // localStorage.setItem('adminKey', 'batman'); // Removed for security as requested
        } else {
            toast.error("Invalid Access Key");
        }
    };



    const fetchAds = async () => {
        if (!isAuthenticated) return;
        try {
            const { data } = await api.get('/ads/', { headers: adminHeaders });
            setAds(data);
        } catch (error) {
            toast.error("Failed to load ads");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isAuthenticated) fetchAds();
    }, [isAuthenticated]);

    // Headers helper
    const adminHeaders = { 'X-Admin-Key': 'batman' };

    const handleDelete = async (id) => {
        if (!confirm("Are you sure you want to delete this ad?")) return;
        try {
            await api.delete(`/ads/${id}`, { headers: adminHeaders });
            toast.success("Ad deleted");
            fetchAds();
        } catch (error) {
            toast.error("Failed to delete ad");
        }
    };

    const handleToggleActive = async (ad) => {
        try {
            await api.patch(`/ads/${ad.id}?active=${!ad.is_active}`, {}, { headers: adminHeaders });
            toast.success(`Ad ${!ad.is_active ? 'Activated' : 'Paused'}`);
            fetchAds();
        } catch (error) {
            toast.error("Failed to update status");
        }
    };

    const handleFileSelect = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setNewAdFile(file);
        setNewAdPreview(URL.createObjectURL(file));

        // Auto-upload immediately to get URL
        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const { data } = await api.post('/ads/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    ...adminHeaders
                }
            });
            // We assume backend returns relative URL like /uploads/file.png
            // We need to prepend backend URL if it's strictly relative and not served by same origin in dev,
            // but for now let's use what backend returns.
            // If backend returns /uploads/..., and we are on frontend, we might need full URL if serves differ.
            // Let's assume production-like setup where /uploads is proxied or full URL.
            // Actually, for this setup, let's prepend window.location.origin if it starts with /
            // We use the relative URL directly so it works on Ngrok/Localhost automatically
            setNewAdUrl(data.url);
            toast.success("Image uploaded successfully");
        } catch (error) {
            console.error(error);
            toast.error("Image upload failed");
        } finally {
            setUploading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const mediaType = newAdFile?.type.startsWith('video/') ? 'video' : 'image';
            await api.post('/ads/', {
                title: newAdTitle,
                image_url: newAdUrl,
                media_type: mediaType,
                target_url: "", // Optional
                duration_seconds: mediaType === 'video' ? 30 : 15, // Longer default for video
                is_active: true
            }, { headers: adminHeaders });
            toast.success("Ad created!");
            setNewAdTitle("");
            setNewAdUrl("");
            setNewAdFile(null);
            setNewAdPreview(null);
            fetchAds();
        } catch (error) {
            toast.error("Failed to create ad");
        }
    };

    if (!isAuthenticated) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-6">
                <div className="card-natural p-10 max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center text-3xl mb-6 mx-auto">
                        🔒
                    </div>
                    <h1 className="text-2xl font-serif font-bold mb-2">Restricted Area</h1>
                    <p className="text-secondary mb-6 text-sm">Enter the admin security key to verify your identity.</p>

                    <form onSubmit={checkPin} className="flex gap-2">
                        <input
                            type="password"
                            value={pin}
                            onChange={e => setPin(e.target.value)}
                            className="flex-1 bg-neutral-50 border border-neutral-200 rounded-xl px-4 py-3 font-mono text-center tracking-widest focus:ring-2 focus:ring-primary outline-none"
                            placeholder="••••••"
                            autoFocus
                        />
                        <button type="submit" className="bg-primary text-white rounded-xl px-6 font-bold hover:bg-primary/90">
                            →
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-8 pt-32 pb-6 px-6 max-w-7xl mx-auto w-full">
            <header>
                <h1 className="text-4xl font-serif text-primary mb-2">Ad Manager</h1>
                <p className="text-secondary">Manage rotating background advertisements.</p>
            </header>

            {/* Create New Ad Card */}
            <div className="card-natural p-6">
                <h2 className="text-lg font-bold mb-4">Create New Ad</h2>
                <form onSubmit={handleCreate} className="flex flex-col md:flex-row gap-6 items-start">

                    {/* Image/Video Upload Area */}
                    <div className="w-full md:w-1/3 aspect-video bg-neutral-100 rounded-xl relative border-2 border-dashed border-neutral-300 hover:border-accent transition-colors flex flex-col items-center justify-center cursor-pointer overflow-hidden group">
                        {/* Preview / Placeholder Content */}
                        {newAdPreview ? (
                            newAdFile?.type.startsWith('video/') ? (
                                <video src={newAdPreview} className="w-full h-full object-cover pointer-events-none" autoPlay muted loop />
                            ) : (
                                <img src={newAdPreview} className="w-full h-full object-cover pointer-events-none" />
                            )
                        ) : (
                            <div className="text-center p-4 pointer-events-none">
                                <span className="text-2xl mb-2 block">📷 / 🎥</span>
                                <span className="text-sm font-bold text-secondary">Click to Upload Media</span>
                            </div>
                        )}

                        {/* Loading Overlay */}
                        {uploading && (
                            <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white font-bold z-40 pointer-events-none">
                                Uploading...
                            </div>
                        )}

                        {/* Actual Input - Placed LAST to stack on top, Z-50 to ensure clickability */}
                        <input
                            type="file"
                            accept="image/*,video/*"
                            onChange={handleFileSelect}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-50"
                        />
                    </div>

                    {/* Fields */}
                    <div className="flex-1 flex flex-col gap-4 w-full">
                        <div>
                            <label className="text-xs uppercase font-bold text-secondary ml-1">Title</label>
                            <input
                                value={newAdTitle}
                                onChange={e => setNewAdTitle(e.target.value)}
                                className="w-full bg-neutral-50 border border-neutral-200 rounded-lg px-4 py-2"
                                placeholder="e.g. Summer Promo"
                                required
                            />
                        </div>
                        <div>
                            <label className="text-xs uppercase font-bold text-secondary ml-1">Media URL (Auto-filled)</label>
                            <input
                                value={newAdUrl}
                                readOnly
                                className="w-full bg-neutral-100 border-0 rounded-lg px-4 py-2 text-neutral-500 text-sm"
                                placeholder="Upload media first..."
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={!newAdUrl || !newAdTitle}
                            className="bg-primary text-white font-bold py-3 rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                        >
                            Publish Ad
                        </button>
                    </div>
                </form>
            </div>

            {/* Existing Ads Grid */}
            <div>
                <h2 className="text-lg font-bold mb-4">Active Campaign ({ads.length})</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {ads.map(ad => (
                        <div key={ad.id} className="card-natural overflow-hidden group relative">
                            {/* Image/Video Preview */}
                            <div className="aspect-video relative">
                                {ad.media_type === 'video' || ad.image_url.endsWith('.mp4') ? (
                                    <video src={getAssetUrl(ad.image_url)} className="w-full h-full object-cover" muted loop autoPlay />
                                ) : (
                                    <img src={getAssetUrl(ad.image_url)} className="w-full h-full object-cover" />
                                )}
                                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                                    <button
                                        onClick={() => handleToggleActive(ad)}
                                        className="bg-white text-black px-3 py-1 rounded-full text-xs font-bold hover:scale-105 transition-transform"
                                    >
                                        {ad.is_active ? 'Pause' : 'Activate'}
                                    </button>
                                    <button
                                        onClick={() => handleDelete(ad.id)}
                                        className="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold hover:scale-105 transition-transform"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>

                            {/* Info */}
                            <div className="p-4 flex items-center justify-between">
                                <div>
                                    <h3 className="font-bold text-primary">{ad.title}</h3>
                                    <p className="text-xs text-secondary">{ad.duration_seconds}s • {ad.is_active ? <span className="text-green-500">Active</span> : <span className="text-orange-500">Paused</span>}</p>
                                </div>
                                <div className="w-2 h-2 rounded-full bg-primary/20"></div>
                            </div>
                        </div>
                    ))}

                    {ads.length === 0 && !loading && (
                        <div className="col-span-full py-12 text-center text-secondary border-2 border-dashed border-neutral-200 rounded-3xl">
                            No active ads. Create one above!
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

import { useState, useEffect, useRef } from 'react';
import api from '../../services/api';
import { getAssetUrl } from '../../utils/url';

export default function AdBackground() {
    const [ads, setAds] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true);

    // Fetch ads on mount
    useEffect(() => {
        const DEFAULT_ADS = [
            {
                id: "ad_def_1",
                title: "Epochly Pilot",
                image_url: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop",
                target_url: "/dashboard/wallet",
                duration_seconds: 10
            },
            {
                id: "ad_def_2",
                title: "Epochly Researcher",
                image_url: "https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?q=80&w=2574&auto=format&fit=crop",
                target_url: "/dashboard/wallet",
                duration_seconds: 10
            },
            {
                id: "ad_def_3",
                title: "Epochly Lab",
                image_url: "https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?q=80&w=2535&auto=format&fit=crop",
                target_url: "/dashboard/wallet",
                duration_seconds: 10
            }
        ];

        const fetchAds = async () => {
            try {
                const { data } = await api.get('/ads/');
                if (Array.isArray(data) && data.length > 0) {
                    setAds(data);
                } else {
                    console.warn("No ads returned from API, using defaults.");
                    setAds(DEFAULT_ADS);
                }
            } catch (error) {
                console.error("Failed to fetch background ads, using defaults", error);
                setAds(DEFAULT_ADS);
            } finally {
                setLoading(false);
            }
        };
        fetchAds();
    }, []);

    // Cycle ads
    useEffect(() => {
        if (ads.length <= 1) return;

        const currentAd = ads[currentIndex];
        // Default to provided duration or 15s. If video, we might wait for onEnded instead.
        const duration = (currentAd.duration_seconds || 15) * 1000;

        let interval;

        // If it's an image, use simple interval. 
        // If it's a video, we rely on onEnded, UNLESS it's a short looping video.
        const isVideo = currentAd.media_type === 'video' || currentAd.image_url?.endsWith('.mp4');

        if (!isVideo) {
            interval = setInterval(() => {
                setCurrentIndex((prev) => (prev + 1) % ads.length);
            }, duration);
        }

        // If it's a video, we handle it in the render via onEnded event, 
        // or a fallback timeout if we want to enforce duration.

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [ads, currentIndex]);

    const handleVideoEnded = () => {
        setCurrentIndex((prev) => (prev + 1) % ads.length);
    };

    if (loading || ads.length === 0) {
        // Fallback gradient if no ads or loading
        return (
            <div className="fixed inset-0 z-0 bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700"></div>
        );
    }

    const currentAd = ads[currentIndex];

    return (
        <div className="fixed inset-0 z-0 bg-black overflow-hidden">
            {ads.map((ad, index) => {
                const isCurrent = index === currentIndex;
                const isVideo = ad.media_type === 'video' || ad.image_url?.endsWith('.mp4');
                const isSingleAd = ads.length === 1;

                return (
                    <div
                        key={ad.id}
                        className={`absolute inset-0 transition-opacity duration-[1000ms] ease-in-out ${isCurrent ? 'opacity-100' : 'opacity-0'} pointer-events-none`}
                    >
                        {/* Background Content */}
                        {isVideo ? (
                            <VideoPlayer
                                src={getAssetUrl(ad.image_url)}
                                isActive={isCurrent}
                                onEnded={handleVideoEnded}
                                shouldLoop={ad.duration_seconds < 15 || isSingleAd}
                            />
                        ) : (
                            <img
                                src={getAssetUrl(ad.image_url)}
                                alt={ad.title}
                                className="w-full h-full object-cover opacity-90"
                            />
                        )}

                        {/* Overlay Gradient */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>

                        {/* Ad Info / Clickable Area */}
                        {ad.target_url && (
                            <a
                                href={ad.target_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="absolute bottom-8 left-8 py-3 px-6 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-white/90 hover:bg-white/20 transition-colors flex items-center gap-3 cursor-pointer group z-50 pointer-events-auto"
                            >
                                <span className="font-serif italic">Promoted</span>
                                <span className="w-px h-4 bg-white/20"></span>
                                <span className="font-medium tracking-wide group-hover:underline">{ad.title}</span>
                                <svg className="w-4 h-4 opacity-70 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M5 12h14M12 5l7 7-7 7" />
                                </svg>
                            </a>
                        )}
                    </div>
                );
            })}
        </div>
    );
}

function VideoPlayer({ src, isActive, onEnded, shouldLoop }) {
    const videoRef = useRef(null);
    const [videoError, setVideoError] = useState(false);

    useEffect(() => {
        if (isActive && videoRef.current && !videoError) {
            // Force play when active
            videoRef.current.play().catch(e => {
                console.log("Autoplay prevented:", e);
                setVideoError(true); // Fallback to gradient
            });
        } else if (!isActive && videoRef.current) {
            // Pause and reset when not active
            videoRef.current.pause();
            videoRef.current.currentTime = 0;
        }
    }, [isActive, videoError]);

    // Fallback gradient when video fails
    if (videoError) {
        return (
            <div className="w-full h-full bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700 animate-gradient-xy" />
        );
    }

    return (
        <video
            ref={videoRef}
            src={src}
            className="w-full h-full object-cover opacity-90"
            muted
            autoPlay
            playsInline
            onEnded={onEnded}
            loop={shouldLoop}
            onError={() => setVideoError(true)}
        />
    );
}

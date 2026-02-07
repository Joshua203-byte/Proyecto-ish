import { useState, useEffect, useRef } from 'react';
import api from '../../services/api';
import { getAssetUrl } from '../../utils/url';

// Local assets for guaranteed mobile loading
import imgPilot from '../../assets/ads/pilot.webp';
import imgResearcher from '../../assets/ads/researcher.webp';
import imgLab from '../../assets/ads/lab.webp';
import imgShirt from '../../assets/ads/green_shirt.webp';

export default function AdBackground() {
    const [ads, setAds] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [imageLoaded, setImageLoaded] = useState(false);

    // Fetch ads on mount
    useEffect(() => {
        const DEFAULT_ADS = [
            {
                id: "ad_def_1",
                title: "Epochly Pilot",
                image_url: imgPilot,
                target_url: "/dashboard/wallet",
                duration_seconds: 10,
                is_local: true
            },
            {
                id: "ad_def_2",
                title: "Epochly Researcher",
                image_url: imgResearcher,
                target_url: "/dashboard/wallet",
                duration_seconds: 10,
                is_local: true
            },
            {
                id: "ad_def_3",
                title: "Epochly Lab",
                image_url: imgLab,
                target_url: "/dashboard/wallet",
                duration_seconds: 10,
                is_local: true
            }
        ];

        const fetchAds = async () => {
            try {
                // If we want to guarantee local ads ALWAYS show on mobile/slow connections,
                // we could prioritize defaults or mix them.
                // For now, adhering to logic: try API, fallback to defaults.
                // If API returns ads but they fail to load (e.g. Unsplash blocked),
                // the gradient handles it gracefully.
                const { data } = await api.get('/ads/');
                if (Array.isArray(data) && data.length > 0) {
                    setAds(data);
                } else {
                    setAds(DEFAULT_ADS);
                }
            } catch (error) {
                console.error("Failed to fetch background ads, using defaults", error);
                setAds(DEFAULT_ADS);
            }
        };
        fetchAds();
    }, []);

    // Cycle ads
    useEffect(() => {
        if (ads.length <= 1) return;

        const currentAd = ads[currentIndex];
        const duration = (currentAd?.duration_seconds || 15) * 1000;
        const isVideo = currentAd?.media_type === 'video' || currentAd?.image_url?.endsWith('.mp4');

        let interval;
        if (!isVideo) {
            interval = setInterval(() => {
                setImageLoaded(false); // Reset for next image
                setCurrentIndex((prev) => (prev + 1) % ads.length);
            }, duration);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [ads, currentIndex]);

    const handleVideoEnded = () => {
        setImageLoaded(false);
        setCurrentIndex((prev) => (prev + 1) % ads.length);
    };

    // Safety Net: Force image visibility if onLoad doesn't fire (common mobile issue)
    useEffect(() => {
        const timer = setTimeout(() => {
            setImageLoaded(true);
        }, 500);
        return () => clearTimeout(timer);
    }, [currentIndex]);

    const currentAd = ads[currentIndex];
    const isVideo = currentAd?.media_type === 'video' || currentAd?.image_url?.endsWith('.mp4');
    const isSingleAd = ads.length === 1;

    // Helper to resolve image source
    const getAdSrc = (ad) => {
        if (ad.is_local) return ad.image_url;

        const url = getAssetUrl(ad.image_url);
        const cacheBuster = Math.floor(Date.now() / 60000);
        return `${url}?t=${cacheBuster}`;
    };

    return (
        <div className="fixed inset-0 z-0 overflow-hidden w-full h-full min-h-[100dvh]">
            {/* BASE: Always visible animated gradient - the main design */}
            <div
                className="absolute inset-0 bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700"
                style={{
                    animation: 'gradientShift 15s ease infinite',
                    backgroundSize: '400% 400%'
                }}
            />

            {/* OVERLAY: Images/Videos only shown if they load successfully */}
            {currentAd && (
                <div
                    className={`absolute inset-0 transition-opacity duration-1000 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                >
                    {isVideo ? (
                        <VideoPlayer
                            src={getAdSrc(currentAd)}
                            onEnded={handleVideoEnded}
                            shouldLoop={currentAd.duration_seconds < 15 || isSingleAd}
                            onLoadSuccess={() => setImageLoaded(true)}
                            onLoadError={() => setImageLoaded(false)}
                        />
                    ) : (
                        <>
                            <img
                                src={getAdSrc(currentAd)}
                                alt={currentAd.title}
                                className="w-full h-full object-cover"
                                onLoad={() => setImageLoaded(true)}
                                onError={(e) => {
                                    // If ad image fails (e.g. mobile block), swap to guaranteed local asset
                                    if (e.currentTarget.src !== imgPilot) {
                                        e.currentTarget.src = imgPilot;
                                        // Don't set opacity to 0, let it swap
                                    }
                                }}
                            />
                        </>
                    )}

                    {/* Dark overlay for readability */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                </div>
            )}

            {/* Ad badge - only shown if ad loaded */}
            {currentAd?.target_url && imageLoaded && (
                <a
                    href={currentAd.target_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute bottom-8 left-8 py-3 px-6 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-white/90 hover:bg-white/20 transition-colors flex items-center gap-3 cursor-pointer group z-50"
                >
                    <span className="font-serif italic">Promoted</span>
                    <span className="w-px h-4 bg-white/20" />
                    <span className="font-medium tracking-wide group-hover:underline">{currentAd.title}</span>
                    <svg className="w-4 h-4 opacity-70 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                </a>
            )}
        </div>
    );
}

function VideoPlayer({ src, onEnded, shouldLoop, onLoadSuccess, onLoadError }) {
    const videoRef = useRef(null);

    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.play().catch(e => {
                console.log("Autoplay prevented:", e);
                onLoadError();
            });
        }
    }, [src]);

    return (
        <video
            ref={videoRef}
            src={src}
            className="w-full h-full object-cover"
            muted
            autoPlay
            playsInline
            webkit-playsinline="true"
            onEnded={onEnded}
            loop={shouldLoop}
            onLoadedData={onLoadSuccess}
            onError={onLoadError}
        />
    );
}

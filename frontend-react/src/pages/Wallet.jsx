import { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Wallet() {
    const { loading: authLoading, user } = useAuth();
    const [wallet, setWallet] = useState(null);
    const [packs, setPacks] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const DEFAULT_PACKS = [
            { id: "pack_pro_pilot", name: "Epochly Pilot", price_usd: 10, hours: 5, features: ["Access to DGX Spark", "Basic Support", "Standard Queue"] },
            { id: "pack_pro_researcher", name: "Epochly Researcher", price_usd: 50, hours: 30, popular: true, features: ["Priority Access", "Extended Runtime", "Premium Support"] },
            { id: "pack_pro_lab", name: "Epochly Lab", price_usd: 150, hours: 100, features: ["Dedicated Hardware", "24/7 Support", "API Access"] }
        ];

        if (authLoading || !user) return;
        const fetchData = async () => {
            try {
                const [walletRes, packsRes] = await Promise.all([
                    api.get('/wallet/'),
                    api.get('/packs/')
                ]);
                setWallet(walletRes.data);
                setPacks(packsRes.data.packs && packsRes.data.packs.length > 0 ? packsRes.data.packs : DEFAULT_PACKS);
            } catch (err) {
                console.error(err);
                // Fallback to default packs on error
                setPacks(DEFAULT_PACKS);
                // Mock wallet if needed for UI testing
                if (!wallet) setWallet({ balance: 0.00 });
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [authLoading, user]);

    const handlePurchase = async (packId) => {
        try {
            setLoading(true);
            const { data } = await api.post(`/packs/${packId}/checkout`);
            if (data.payment_url) window.location.href = data.payment_url;
        } catch (error) {
            alert("Error");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return null;

    return (
        <div className="fixed inset-0 w-full h-full overflow-hidden flex flex-col pt-32 pb-4 px-4 bg-neutral-50/50">

            {/* Header: Minimal */}
            <header className="flex-shrink-0 text-center mb-4">
                <div className="inline-flex items-center gap-3 bg-white px-5 py-2 rounded-full border border-neutral-200 shadow-sm">
                    <span className="text-xs font-bold text-secondary uppercase tracking-widest">Balance</span>
                    <span className="text-xl font-serif text-accent">
                        ${wallet?.balance ? Number(wallet.balance).toFixed(2) : '0.00'}
                    </span>
                </div>
            </header>

            {/* Cards: Flex row that shrinks to fit */}
            <div className="flex-1 w-full max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0 items-center justify-center">
                {packs.map((pack) => (
                    <div
                        key={pack.id}
                        className={`
                            relative flex flex-col bg-white rounded-2xl border p-5 transition-transform hover:-translate-y-1 hover:shadow-xl
                            ${pack.popular ? 'border-accent/30 ring-1 ring-accent/10 shadow-lg' : 'border-neutral-100 shadow-sm'}
                             h-full max-h-[420px]
                        `}
                    >
                        {pack.popular && (
                            <div className="absolute top-0 right-0 bg-accent text-white text-[9px] font-bold px-2 py-1 rounded-bl-xl rounded-tr-xl">
                                POPULAR
                            </div>
                        )}

                        <div className="mb-4">
                            <h3 className="text-lg font-serif text-primary">{pack.name}</h3>
                            <div className="text-3xl font-serif text-primary mt-1">
                                ${pack.price_usd}
                            </div>
                            <p className="text-[10px] text-secondary uppercase tracking-wider">{pack.hours} HOURS</p>
                        </div>

                        {/* Scrollable features if list is long, but try to fit */}
                        <ul className="flex-1 space-y-2 overflow-y-auto custom-scrollbar my-2">
                            {(pack.features || []).map((feature, i) => (
                                <li key={i} className="flex items-start gap-2 text-xs text-secondary leading-tight">
                                    <span className="text-accent">✓</span>
                                    {feature}
                                </li>
                            ))}
                        </ul>

                        <button
                            onClick={() => handlePurchase(pack.id)}
                            className={`
                                w-full py-3 rounded-lg font-bold text-sm mt-auto
                                ${pack.popular ? 'bg-accent text-white' : 'bg-primary text-white'}
                            `}
                        >
                            Buy
                        </button>
                    </div>
                ))}
            </div>

            <div className="flex-shrink-0 text-center text-[10px] text-neutral-300 mt-2">
                Secure Payment powered by Stripe
            </div>
        </div>
    );
}

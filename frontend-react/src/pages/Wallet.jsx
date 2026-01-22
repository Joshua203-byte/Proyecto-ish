import { useState, useEffect } from 'react';
import api from '../services/api';

export default function Wallet() {
    const [wallet, setWallet] = useState(null);
    const [packs, setPacks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [paymentMessage, setPaymentMessage] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Check if we're returning from a successful payment
                const urlParams = new URLSearchParams(window.location.search);
                const paymentSuccess = urlParams.get('payment') === 'success';
                const monto = urlParams.get('monto');
                const idTransaccion = urlParams.get('idTransaccion');

                console.log('🔍 URL params:', { paymentSuccess, monto, idTransaccion, fullSearch: window.location.search });

                // If returning from Wompi with payment success, confirm the payment
                // Even if we don't have all params, we should try to confirm
                if (paymentSuccess) {
                    console.log('💳 Detecting payment return, confirming...');

                    // If we have monto and transaction, confirm the payment
                    if (monto && idTransaccion) {
                        try {
                            const confirmRes = await api.post('/payments/confirm', {
                                monto: monto,
                                idTransaccion: idTransaccion,
                                idEnlace: urlParams.get('idEnlace'),
                                identificadorEnlaceComercio: urlParams.get('identificadorEnlaceComercio')
                            });
                            console.log('✅ Payment confirm response:', confirmRes.data);

                            if (confirmRes.data.status === 'success') {
                                setPaymentMessage(`✅ ¡Pago confirmado! Se acreditaron $${monto} a tu cuenta.`);
                            } else if (confirmRes.data.status === 'already_processed') {
                                setPaymentMessage(`ℹ️ Este pago ya fue procesado anteriormente.`);
                            }
                        } catch (confirmErr) {
                            console.error('Payment confirmation error:', confirmErr);
                            // Still show a message that payment was detected
                            setPaymentMessage(`✅ ¡Pago detectado! Tu balance se actualizará en breve.`);
                        }
                    } else {
                        // Payment success but missing params - show a helpful message
                        console.log('⚠️ Payment success detected but missing params');
                        setPaymentMessage(`✅ ¡Pago completado! Tu balance debería actualizarse pronto.`);
                    }

                    // Clean URL to prevent re-confirmation on refresh
                    window.history.replaceState({}, document.title, window.location.pathname);
                }

                const walletRes = await api.get('/wallet/');
                console.log("💰 Wallet Data:", walletRes.data);
                setWallet(walletRes.data);

                const packsRes = await api.get('/packs/');
                setPacks(packsRes.data.packs || []);
            } catch (err) {
                console.error("Wallet page data fetch error:", err);
                setError(err.message || "Failed to load data from server");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handlePurchase = async (packId) => {
        try {
            const { data } = await api.post(`/packs/${packId}/checkout`);
            if (data.payment_url) {
                window.location.href = data.payment_url;
            } else {
                alert('No payment URL received');
            }
        } catch (error) {
            alert('Error creating payment link');
            console.error(error);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center min-vh-100 p-8">
            <div className="text-zinc-400 animate-pulse flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
                <p className="text-lg font-medium">Cargando billetera...</p>
            </div>
        </div>
    );

    return (
        <div className="max-w-6xl mx-auto space-y-12 pb-20 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header section */}
            <header className="text-center space-y-4 pt-4">
                <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight">
                    Precios <span className="text-accent">Simples y Transparentes</span>
                </h1>
                <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
                    Compra créditos para potenciar tus entrenamientos. Sin suscripciones, solo lo que necesitas.
                </p>
            </header>

            {/* Payment Success Message */}
            {paymentMessage && (
                <div className="max-w-xl mx-auto p-4 bg-green-500/10 border border-green-500/20 text-green-400 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-500">
                    <svg className="w-6 h-6 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" /><polyline points="9 12 12 15 16 10" />
                    </svg>
                    <span className="text-sm font-medium">{paymentMessage}</span>
                    <button
                        onClick={() => setPaymentMessage(null)}
                        className="ml-auto text-green-400/60 hover:text-green-400"
                    >
                        ✕
                    </button>
                </div>
            )}

            {error && (
                <div className="max-w-xl mx-auto p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl flex items-center gap-3">
                    <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    <span className="text-sm font-medium">{error}</span>
                </div>
            )}

            {/* Balance Widget */}
            <div className="relative group max-w-md mx-auto">
                <div className="absolute -inset-1 bg-gradient-to-r from-accent to-blue-500 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
                <div className="relative p-8 rounded-2xl border border-zinc-800 bg-black flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold uppercase tracking-widest text-zinc-500">Balance Actual</p>
                        <h2 className="text-5xl font-black mt-2 text-white tabular-nums">
                            ${wallet && wallet.balance !== undefined ? Number(wallet.balance).toFixed(2) : '0.00'}
                        </h2>
                    </div>
                    <div className="h-16 w-16 rounded-full bg-accent/10 flex items-center justify-center text-accent">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                            <path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                </div>
            </div>

            {/* Pricing Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch pt-4">
                {packs.map((pack) => (
                    <div
                        key={pack.id}
                        className={`relative flex flex-col p-8 rounded-3xl border transition-all duration-300 ${pack.popular
                            ? 'bg-zinc-900 border-accent shadow-[0_0_40px_-15px_rgba(59,130,246,0.3)] scale-105 z-10'
                            : 'bg-zinc-900/40 border-zinc-800 hover:border-zinc-700'
                            }`}
                    >
                        {pack.popular && (
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-accent text-white px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest shadow-lg">
                                Most Popular
                            </div>
                        )}

                        <div className="mb-8">
                            <h3 className="text-2xl font-bold text-white mb-1">{pack.name}</h3>
                            <div className="flex items-baseline gap-1 mt-4">
                                <span className="text-4xl font-black text-white">${pack.price_usd}</span>
                                <span className="text-zinc-500 font-medium">pago único</span>
                            </div>
                            <p className="text-accent font-bold mt-4 tracking-tight">
                                {pack.hours} Horas de Tiempo de Compute
                            </p>
                        </div>

                        <ul className="flex-1 space-y-4 mb-10">
                            {(pack.features || []).map((feature, idx) => (
                                <li key={idx} className="flex items-start gap-3 group/item">
                                    <div className="mt-1 flex-shrink-0 w-4 h-4 rounded-full bg-accent/20 flex items-center justify-center">
                                        <svg className="w-2.5 h-2.5 text-accent" fill="none" stroke="currentColor" strokeWidth="4" viewBox="0 0 24 24">
                                            <polyline points="20 6 9 17 4 12" />
                                        </svg>
                                    </div>
                                    <span className="text-sm text-zinc-300 group-hover/item:text-white transition-colors">
                                        {feature}
                                    </span>
                                </li>
                            ))}
                        </ul>

                        <button
                            onClick={() => handlePurchase(pack.id)}
                            className={`w-full py-4 rounded-2xl font-black uppercase tracking-widest text-sm transition-all duration-200 ${pack.popular
                                ? 'bg-white text-black hover:bg-zinc-200 hover:scale-[1.02] shadow-xl shadow-white/10'
                                : 'bg-white/5 text-white border border-white/10 hover:bg-white/10'
                                }`}
                        >
                            Comprar Pack
                        </button>
                    </div>
                ))}
            </div>

            {/* Footer Tip */}
            <div className="text-center">
                <p className="text-zinc-500 text-sm">
                    ¿Necesitas más poder? <span className="text-zinc-400 font-medium">Contáctanos</span> para planes enterprise y setups a medida.
                </p>
            </div>
        </div>
    );
}

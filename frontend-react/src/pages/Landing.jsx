import { Link } from 'react-router-dom';

export default function Landing() {
    return (
        <div className="min-h-screen bg-background text-primary selection:bg-accent selection:text-white overflow-x-hidden">
            {/* Background Orbs */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute -top-[200px] -left-[100px] w-[800px] h-[800px] rounded-full bg-violet-600/10 blur-[120px] animate-pulse"></div>
                <div className="absolute -bottom-[100px] -right-[100px] w-[600px] h-[600px] rounded-full bg-cyan-500/10 blur-[120px] animate-pulse"></div>
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20"></div>
            </div>

            {/* Navigation */}
            <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-background/70 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-3 group">
                        <div className="text-zinc-100 group-hover:text-accent transition-colors">
                            <svg width="32" height="32" viewBox="0 0 40 40" fill="none">
                                <rect x="4" y="8" width="32" height="24" rx="2" stroke="currentColor" strokeWidth="2" />
                                <path d="M12 16h4v8h-4z" fill="currentColor" opacity="0.8" />
                                <path d="M18 14h4v10h-4z" fill="currentColor" />
                                <path d="M24 12h4v12h-4z" fill="currentColor" opacity="0.8" />
                            </svg>
                        </div>
                        <span className="font-bold text-xl tracking-wider font-['Orbitron']">
                            HOME<span className="text-accent">GPU</span>CLOUD
                        </span>
                    </Link>

                    <div className="flex gap-4">
                        <Link to="/login" className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white transition-colors">
                            Log In
                        </Link>
                        <Link to="/register" className="px-6 py-2 text-sm font-medium bg-white text-black hover:bg-zinc-200 rounded-full transition-all hover:scale-105">
                            Sign Up
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-32 pb-20 px-6 max-w-7xl mx-auto text-center">
                <div className="space-y-8 max-w-4xl mx-auto">
                    <h1 className="text-5xl md:text-7xl font-black tracking-tight font-['Orbitron']">
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-zinc-500">
                            Unleash AI Power
                        </span>
                        <br />
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-accent to-cyan-400">
                            Within Seconds
                        </span>
                    </h1>

                    <p className="text-xl text-zinc-400 max-w-2xl mx-auto leading-relaxed">
                        Access high-performance NVIDIA GPUs for your Machine Learning workflows.
                        No hidden fees. Pay only for what you use. Instant deployment.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                        <Link to="/register" className="px-8 py-4 text-lg font-bold bg-accent hover:bg-blue-700 text-white rounded-lg shadow-[0_0_30px_rgba(37,99,235,0.3)] hover:shadow-[0_0_50px_rgba(37,99,235,0.5)] transition-all hover:-translate-y-1">
                            Start Training Now
                        </Link>
                        <a href="#pricing" className="px-8 py-4 text-lg font-medium border border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800 rounded-lg transition-all hover:-translate-y-1">
                            View Pricing
                        </a>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-24 px-6 max-w-7xl mx-auto">
                <div className="grid md:grid-cols-3 gap-8">
                    {[
                        { title: 'Lightning Fast', icon: 'M13 10V3L4 14h7v7l9-11h-7z', desc: 'Deploy your Jupyter Notebooks or Python scripts in seconds. Optimized stack ensuring minimal overhead.' },
                        { title: 'Cost Effective', icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z', desc: 'Stop overpaying. Granular billing tracks usage to the second. Prices start as low as $0.50/hour.' },
                        { title: 'Secure & Isolated', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z', desc: 'Your work runs in dedicated Docker containers with strict resource isolation. Your data is yours alone.' },
                    ].map((feature, i) => (
                        <div key={i} className="p-8 rounded-2xl bg-zinc-900/50 border border-zinc-800 hover:border-accent/50 hover:bg-zinc-900 transition-all group">
                            <div className="w-12 h-12 mb-6 text-accent group-hover:scale-110 transition-transform">
                                <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-full h-full">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={feature.icon} />
                                </svg>
                            </div>
                            <h3 className="text-xl font-bold mb-3 font-['Orbitron']">{feature.title}</h3>
                            <p className="text-zinc-400 leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Pricing */}
            <section id="pricing" className="py-24 px-6 border-t border-zinc-900 bg-background/50">
                <div className="max-w-7xl mx-auto">
                    <h2 className="text-4xl font-bold text-center mb-16 font-['Orbitron']">Simple, Transparent Pricing</h2>
                    <div className="grid md:grid-cols-3 gap-8 items-start">
                        {[
                            { name: 'Pilot', price: '5', hours: '10 Hours', features: ['Standard Priority', '1 GPU Instance', '16GB VRAM', 'Basic Support'] },
                            { name: 'Researcher', price: '20', hours: '45 Hours', features: ['High Priority Queue', 'Up to 2 Concurrent Jobs', '32GB VRAM', '5 Bonus Hours included'], popular: true },
                            { name: 'Lab', price: '50', hours: '120 Hours', features: ['Highest Priority', 'Multiple GPUs', '128GB Unified Memory', '20 Bonus Hours included'] },
                        ].map((plan, i) => (
                            <div key={i} className={`relative p-8 rounded-2xl border ${plan.popular ? 'border-accent bg-zinc-900/80 shadow-2xl scale-105 z-10' : 'border-zinc-800 bg-zinc-900/30'}`}>
                                {plan.popular && (
                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 bg-accent text-white px-4 py-1 rounded-b-xl text-xs font-bold uppercase tracking-widest shadow-lg">
                                        Most Popular
                                    </div>
                                )}
                                <div className="text-center mb-8 pt-4">
                                    <h3 className="text-2xl font-bold mb-2 font-['Orbitron']">{plan.name}</h3>
                                    <div className="flex justify-center items-start text-5xl font-black mb-2">
                                        <span className="text-2xl mt-1 opacity-60">$</span>{plan.price}
                                    </div>
                                    <div className="text-accent font-mono text-sm">{plan.hours} compute time</div>
                                </div>
                                <ul className="space-y-4 mb-8">
                                    {plan.features.map((f, fi) => (
                                        <li key={fi} className="flex items-center text-zinc-400 text-sm border-b border-zinc-800 pb-2 last:border-0">
                                            <svg width="20" height="20" className="w-5 h-5 mr-3 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                            </svg>
                                            {f}
                                        </li>
                                    ))}
                                </ul>
                                <Link to={`/register?plan=${plan.name.toLowerCase()}`} className={`block w-full py-3 rounded-lg text-center font-bold transition-all ${plan.popular ? 'bg-white text-black hover:bg-zinc-200' : 'border border-zinc-700 hover:bg-zinc-800'}`}>
                                    Get Started
                                </Link>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <footer className="py-12 border-t border-zinc-900 text-center text-zinc-500 text-sm">
                &copy; 2026 Home GPU Cloud. All rights reserved.
            </footer>
        </div>
    );
}

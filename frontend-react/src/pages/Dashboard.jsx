import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from '../components/Layout/Navbar';
import Wallet from './Wallet';
import NewJob from './NewJob';
import Jobs from './Jobs';
import AdminAds from './AdminAds';

export default function Dashboard() {
    return (
        <div className="min-h-screen bg-background text-primary font-sans selection:bg-accent selection:text-white">
            <Navbar />

            {/* Main Content with padding for fixed navbar */}
            <main className="pt-0 pb-0 px-0"> {/* Padding managed by pages now */}
                <div className="w-full h-full">
                    <Routes>
                        <Route path="/" element={<Navigate to="new-job" replace />} />
                        <Route path="/jobs" element={<Jobs />} />
                        <Route path="/new-job" element={<NewJob />} />
                        <Route path="/new-job" element={<NewJob />} />
                        <Route path="/wallet" element={<Wallet />} />
                        <Route path="/admin" element={<AdminAds />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
}

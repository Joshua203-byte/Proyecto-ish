import { Routes, Route } from 'react-router-dom';
import Sidebar from '../components/Layout/Sidebar';
import Overview from './Overview';
import Wallet from './Wallet';
import NewJob from './NewJob';
import Jobs from './Jobs';

export default function Dashboard() {
    return (
        <div className="flex min-h-screen bg-black text-white font-sans selection:bg-accent selection:text-white">
            <Sidebar />
            <main className="flex-1 p-8 overflow-y-auto h-screen">
                <div className="max-w-7xl mx-auto">
                    <Routes>
                        <Route path="/" element={<Overview />} />
                        <Route path="/jobs" element={<Jobs />} />
                        <Route path="/new-job" element={<NewJob />} />
                        <Route path="/wallet" element={<Wallet />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
}

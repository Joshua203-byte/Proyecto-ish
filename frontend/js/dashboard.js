/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * DASHBOARD JAVASCRIPT
 * Handles dashboard functionality, job management, and wallet operations
 * ═══════════════════════════════════════════════════════════════════════════════
 */

// ─────────────────────────────────────────────────────────────────────────────────
// INITIALIZATION
// ─────────────────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!window.api.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    // Initialize dashboard
    await initDashboard();
});

async function initDashboard() {
    // Load user profile
    await loadUserProfile();

    // Load wallet balance
    await loadWalletBalance();

    // Load dashboard data
    await loadDashboardData();

    // Setup event listeners
    setupNavigation();
    setupUserMenu();
    setupFileUploads();
    setupJobForm();
    setupTopUpModal();
    setupJobFilters();
}

// ─────────────────────────────────────────────────────────────────────────────────
// USER PROFILE
// ─────────────────────────────────────────────────────────────────────────────────

async function loadUserProfile() {
    try {
        const user = await window.api.getProfile();

        document.getElementById('userName').textContent = user.full_name || 'User';
        document.getElementById('userEmail').textContent = user.email;
        document.getElementById('userInitial').textContent = (user.full_name || user.email)[0].toUpperCase();

        // Show admin link if superuser
        if (user.is_superuser) {
            const adminLink = document.getElementById('adminSidebarLink');
            if (adminLink) adminLink.style.display = 'flex';
        }
    } catch (error) {
        console.error('Failed to load profile:', error);
        // If unauthorized, redirect to login
        if (error.message.includes('401') || error.message.includes('unauthorized')) {
            window.api.logout();
            window.location.href = 'login.html';
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// WALLET
// ─────────────────────────────────────────────────────────────────────────────────

async function loadWalletBalance() {
    try {
        const wallet = await window.api.getWallet();
        updateBalanceDisplay(wallet.balance);
    } catch (error) {
        console.error('Failed to load wallet:', error);
    }
}

function updateBalanceDisplay(balance) {
    const balanceStr = parseFloat(balance).toFixed(2);
    const [whole, decimals] = balanceStr.split('.');

    // Header balance
    document.getElementById('creditBalance').textContent = balanceStr;

    // Cost estimate
    const yourBalance = document.getElementById('yourBalance');
    if (yourBalance) {
        yourBalance.textContent = `${balanceStr} credits`;
    }

    // Wallet page
    const walletBalance = document.getElementById('walletBalance');
    const walletDecimals = document.getElementById('walletDecimals');
    if (walletBalance) {
        walletBalance.textContent = whole;
        walletDecimals.textContent = `.${decimals}`;
    }
}

async function loadTransactions() {
    try {
        const data = await window.api.getTransactions(1, 20);
        const list = document.getElementById('transactionsList');

        if (!data.transactions || data.transactions.length === 0) {
            list.innerHTML = `
                <div class="empty-state" style="padding: 2rem;">
                    <p style="color: var(--text-muted);">No transactions yet</p>
                </div>
            `;
            return;
        }

        list.innerHTML = data.transactions.map(tx => {
            const isCredit = ['credit', 'refund', 'release'].includes(tx.transaction_type);
            const icon = isCredit
                ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>';

            return `
                <div class="transaction-item">
                    <div class="transaction-icon ${isCredit ? 'credit' : 'debit'}">
                        ${icon}
                    </div>
                    <div class="transaction-info">
                        <span class="transaction-type">${formatTransactionType(tx.transaction_type)}</span>
                        <span class="transaction-date">${formatDate(tx.created_at)}</span>
                    </div>
                    <span class="transaction-amount ${isCredit ? 'credit' : 'debit'}">
                        ${isCredit ? '+' : '-'}$${parseFloat(tx.amount).toFixed(2)}
                    </span>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

function formatTransactionType(type) {
    const types = {
        'credit': 'Credit Added',
        'debit': 'Job Charge',
        'refund': 'Refund',
        'reservation': 'Reserved',
        'release': 'Released'
    };
    return types[type] || type;
}

// ─────────────────────────────────────────────────────────────────────────────────
// DASHBOARD DATA
// ─────────────────────────────────────────────────────────────────────────────────

async function loadDashboardData() {
    try {
        const jobs = await window.api.getJobs(null, 50);

        // Update stats
        document.getElementById('totalJobs').textContent = jobs.length;
        document.getElementById('runningJobs').textContent =
            jobs.filter(j => j.status === 'running' || j.status === 'preparing').length;

        // Calculate total runtime
        const totalMinutes = jobs.reduce((sum, j) => sum + (j.runtime_seconds || 0) / 60, 0);
        document.getElementById('totalRuntime').textContent = `${Math.round(totalMinutes / 60)}h`;

        // Calculate total spent
        const totalSpent = jobs.reduce((sum, j) => sum + parseFloat(j.total_cost || 0), 0);
        document.getElementById('totalSpent').textContent = totalSpent.toFixed(2);

        // Render recent jobs
        renderRecentJobs(jobs.slice(0, 5));

        // Store jobs for filtering
        window.allJobs = jobs;
        renderJobsGrid(jobs);

    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

function renderRecentJobs(jobs) {
    const list = document.getElementById('recentJobsList');

    if (jobs.length === 0) {
        return; // Keep empty state
    }

    list.innerHTML = jobs.map(job => `
        <div class="job-card glass" onclick="viewLogs('${job.id}')">
            <div class="job-card-header">
                <div>
                    <div class="job-name">${job.script_name || 'train.py'}</div>
                    <div class="job-id">${job.id.slice(0, 8)}</div>
                </div>
                <span class="badge badge-${getStatusBadge(job.status)}">${job.status}</span>
            </div>
            <div class="job-card-body">
                <div class="job-meta">
                    <span class="job-meta-label">Created</span>
                    <span class="job-meta-value">${formatDate(job.created_at)}</span>
                </div>
                <div class="job-meta">
                    <span class="job-meta-label">Runtime</span>
                    <span class="job-meta-value">${formatDuration(job.runtime_seconds || 0)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function renderJobsGrid(jobs) {
    const grid = document.getElementById('jobsGrid');

    if (jobs.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <rect x="4" y="4" width="16" height="16" rx="2"/>
                    <path d="M9 9h6v6H9z"/>
                </svg>
                <h3>No jobs found</h3>
                <p>Create your first job to get started</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = jobs.map(job => `
        <div class="job-card glass">
            <div class="job-card-header">
                <div>
                    <div class="job-name">${job.script_name || 'train.py'}</div>
                    <div class="job-id">${job.id.slice(0, 8)}</div>
                </div>
                <span class="badge badge-${getStatusBadge(job.status)}">${job.status}</span>
            </div>
            <div class="job-card-body">
                <div class="job-meta">
                    <span class="job-meta-label">Created</span>
                    <span class="job-meta-value">${formatDate(job.created_at)}</span>
                </div>
                <div class="job-meta">
                    <span class="job-meta-label">Runtime</span>
                    <span class="job-meta-value">${formatDuration(job.runtime_seconds || 0)}</span>
                </div>
                <div class="job-meta">
                    <span class="job-meta-label">Cost</span>
                    <span class="job-meta-value">$${parseFloat(job.total_cost || 0).toFixed(2)}</span>
                </div>
                <div class="job-meta">
                    <span class="job-meta-label">Memory</span>
                    <span class="job-meta-value">${job.memory_limit || '8g'}</span>
                </div>
            </div>
            <div class="job-card-footer">
                ${job.status === 'running' ? `
                    <button class="btn btn-secondary btn-sm" onclick="cancelJob('${job.id}')">Cancel</button>
                ` : ''}
                <button class="btn btn-ghost btn-sm" onclick="viewLogs('${job.id}')">View Logs</button>
            </div>
        </div>
    `).join('');
}

function getStatusBadge(status) {
    const badges = {
        'pending': 'info',
        'preparing': 'info',
        'running': 'success',
        'completed': 'primary',
        'failed': 'error',
        'cancelled': 'warning',
        'killed_no_credits': 'error'
    };
    return badges[status] || 'info';
}

// ─────────────────────────────────────────────────────────────────────────────────
// NAVIGATION
// ─────────────────────────────────────────────────────────────────────────────────

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            showSection(section);
        });
    });

    // Sidebar toggle (mobile)
    document.getElementById('sidebarToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('active');
    });
}

async function showSection(sectionId) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionId);
    });

    // Update sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    const targetSection = document.getElementById(`section-${sectionId}`);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update title
    const titles = {
        'overview': 'Overview',
        'jobs': 'Jobs',
        'new-job': 'New Job',
        'wallet': 'Wallet',
        'admin': 'Admin Dashboard'
    };
    document.getElementById('pageTitle').textContent = titles[sectionId] || sectionId;

    // Load section-specific data
    if (sectionId === 'wallet') {
        loadTransactions();
    } else if (sectionId === 'admin') {
        loadAdminData();
    }
}

async function loadAdminData() {
    try {
        const [stats, users] = await Promise.all([
            window.api.getAdminStats(),
            window.api.getAdminUsers()
        ]);

        // Update Stats
        document.getElementById('adminTotalUsers').textContent = stats.total_users;
        document.getElementById('adminRevenue').textContent = formatCurrency(stats.total_revenue).replace('$', '');
        document.getElementById('adminActiveJobs').textContent = stats.active_jobs;

        // Render Users Table
        const tableBody = document.getElementById('adminUsersTable');
        tableBody.innerHTML = users.map(u => `
            <tr>
                <td>
                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <span class="user-avatar-sm">${(u.full_name || u.email)[0].toUpperCase()}</span>
                        <div>
                            <div style="font-weight:500;">${u.full_name}</div>
                            <div style="font-size:0.8rem; color:var(--text-muted);">${u.id.slice(0, 8)}...</div>
                        </div>
                    </div>
                </td>
                <td>${u.email}</td>
                <td><span class="badge ${u.is_superuser ? 'badge-primary' : 'badge-secondary'}">${u.is_superuser ? 'Admin' : 'User'}</span></td>
                <td>$${u.balance.toFixed(2)}</td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('Failed to load admin data:', error);
        Toast.error('Failed to load admin data');
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(amount);
}

// ─────────────────────────────────────────────────────────────────────────────────
// USER MENU
// ─────────────────────────────────────────────────────────────────────────────────

function setupUserMenu() {
    const userCard = document.getElementById('userCard');
    const dropdown = document.getElementById('userDropdown');

    userCard.addEventListener('click', () => {
        dropdown.classList.toggle('active');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!userCard.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        window.api.logout();
        Toast.success('Logged out successfully');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 500);
    });
}

// ─────────────────────────────────────────────────────────────────────────────────
// FILE UPLOADS
// ─────────────────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────────────────
// FILE UPLOADS
// ─────────────────────────────────────────────────────────────────────────────────

function setupFileUploads() {
    // Check if window.files exists (loaded from files.js)
    if (window.files && window.files.initDropZone) {
        window.files.initDropZone('scriptDropZone', 'scriptInput', 'scriptDisplay');
    }

    // Legacy setup if needed for other inputs
}

// Helper to show file info (called from files.js via event or UI observation)
function updateFileDisplay(input, display) {
    if (input.files.length > 0) {
        const file = input.files[0];
        display.querySelector('.filename').textContent = file.name;
        display.style.display = 'flex';
        display.classList.add('has-file');

        // Hide dropzone content or zone itself? 
        // Let's hide the dropzone visual to show clean state
        const dropZone = document.getElementById('scriptDropZone');
        if (dropZone) dropZone.style.display = 'none';

        // Add remove handler
        display.onclick = () => {
            input.value = '';
            display.style.display = 'none';
            display.classList.remove('has-file');
            if (dropZone) dropZone.style.display = 'block';
        };
    }
}

// Observer for file input changes (since files.js updates it)
const scriptInput = document.getElementById('scriptInput');
if (scriptInput) {
    scriptInput.addEventListener('change', () => {
        const display = document.getElementById('scriptDisplay');
        updateFileDisplay(scriptInput, display);
    });
}

// ─────────────────────────────────────────────────────────────────────────────────
// JOB FORM
// ─────────────────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────────────────
// JOB FORM
// ─────────────────────────────────────────────────────────────────────────────────

function setupJobForm() {
    const form = document.getElementById('newJobForm');
    if (!form) return;

    // Load balance for the form
    const updateFormBalance = async () => {
        try {
            const wallet = await window.api.getWallet();
            const balanceEl = document.getElementById('newJobBalance');
            if (balanceEl) {
                balanceEl.textContent = `$${parseFloat(wallet.balance).toFixed(2)}`;
            }
        } catch (e) { console.error(e); }
    };

    // Update when showing section
    const originalShowSection = window.showSection;
    window.showSection = (sectionId) => {
        originalShowSection(sectionId);
        if (sectionId === 'new-job') {
            updateFormBalance();
        }
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('[type="submit"]');
        const scriptInput = document.getElementById('scriptInput');

        if (!scriptInput.files.length) {
            Toast.error('Please upload a training script');
            return;
        }

        const originalHTML = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner spinner-sm"></span> Launching Job...';

        try {
            const formData = new FormData();
            const scriptFile = scriptInput.files[0];

            // 1. Append File (using name="script" as requested)
            formData.append('script', scriptFile);

            // 2. Append Job Data JSON as Blob (User fix)
            const jobPayload = {
                script_name: scriptFile.name,
                docker_image: form.elements['dockerImage'].value,
                resource_config: {
                    memory_limit: "8g", // Default
                    cpu_count: 4,      // Default
                    timeout_seconds: parseInt(form.elements['timeout'].value)
                }
            };

            formData.append('job_data', new Blob([JSON.stringify(jobPayload)], { type: 'application/json' }));

            // 3. Send Request
            const response = await fetch(`${window.api.baseURL}/jobs/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                    // Do NOT set Content-Type
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create job');
            }

            const job = await response.json();

            Toast.success('Job launched successfully!');
            form.reset();

            // Clear file UI
            document.getElementById('scriptDisplay').classList.remove('has-file');
            document.getElementById('scriptDisplay').style.display = 'none';
            document.getElementById('scriptDropZone').style.display = 'block';

            // Refresh data and go to jobs
            await loadDashboardData();
            await loadWalletBalance();
            showSection('jobs');

        } catch (error) {
            console.error(error);
            Toast.error(error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHTML;
        }
    });
}

// ─────────────────────────────────────────────────────────────────────────────────
// JOB ACTIONS
// ─────────────────────────────────────────────────────────────────────────────────

async function cancelJob(jobId) {
    if (!confirm('Are you sure you want to cancel this job?')) return;

    try {
        await window.api.cancelJob(jobId);
        Toast.success('Job cancelled');
        await loadDashboardData();
    } catch (error) {
        Toast.error(error.message);
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// LIVE JOB MONITORING (TERMINAL & CHARTS)
// ─────────────────────────────────────────────────────────────────────────────────

let currentLiveJob = null;
let liveTerminal = null;
let trainingChart = null;
let chartData = {
    labels: [],
    datasets: [
        {
            label: 'Loss',
            data: [],
            borderColor: '#ff5f56',
            backgroundColor: 'rgba(255, 95, 86, 0.1)',
            tension: 0.4,
            yAxisID: 'y'
        },
        {
            label: 'Accuracy',
            data: [],
            borderColor: '#27c93f',
            backgroundColor: 'rgba(39, 201, 63, 0.1)',
            tension: 0.4,
            yAxisID: 'y1'
        }
    ]
};

async function viewLogs(jobId) {
    currentLiveJob = jobId;
    const modal = document.getElementById('jobDetailsModal');

    // 1. Reset & Show Modal
    modal.classList.add('active');
    document.getElementById('jobDetailsTitle').textContent = `Job: ${jobId.slice(0, 8)}`;
    document.getElementById('liveEpoch').textContent = '-';
    document.getElementById('liveAccuracy').textContent = '-%';
    document.getElementById('liveLoss').textContent = '-';

    // 2. Initialize Terminal
    if (!liveTerminal) {
        liveTerminal = new LiveTerminal('#liveTerminal', {
            theme: 'dark',
            autoScroll: true
        });
    }
    liveTerminal.clear();
    liveTerminal.connect(jobId);

    // 3. Initialize Chart
    initTrainingChart();

    // 4. Hook into terminal logs to update chart
    const originalAddLine = liveTerminal.addLine.bind(liveTerminal);
    liveTerminal.addLine = (content, type, timestamp) => {
        originalAddLine(content, type, timestamp);
        if (type === 'log') {
            parseMetrics(content);
        }
    };
}

function initTrainingChart() {
    const ctx = document.getElementById('trainingChart').getContext('2d');

    // Reset data
    chartData.labels = [];
    chartData.datasets[0].data = [];
    chartData.datasets[1].data = [];

    if (trainingChart) {
        trainingChart.destroy();
    }

    trainingChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: { display: false },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Loss', color: '#666' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Accuracy', color: '#666' },
                    grid: { drawOnChartArea: false },
                    min: 0, max: 1
                }
            },
            plugins: {
                legend: { labels: { color: '#ccc' } }
            }
        }
    });
}

function parseMetrics(logLine) {
    // Expected format: "1/5 [====>.] - loss: 0.1234 - acc: 0.9876"

    // Extract Epoch
    if (logLine.includes('Epoch')) {
        const epochMatch = logLine.match(/Epoch\s+(\d+)\/(\d+)/);
        if (epochMatch) {
            document.getElementById('liveEpoch').textContent = `${epochMatch[1]}/${epochMatch[2]}`;
        }
    }

    // Extract Metrics
    const lossMatch = logLine.match(/loss:\s*([0-9.]+)/);
    const accMatch = logLine.match(/acc:\s*([0-9.]+)/);

    if (lossMatch && accMatch) {
        const loss = parseFloat(lossMatch[1]);
        const acc = parseFloat(accMatch[1]);

        // Update Stats
        document.getElementById('liveLoss').textContent = loss.toFixed(4);
        document.getElementById('liveAccuracy').textContent = `${(acc * 100).toFixed(1)}%`;

        // Update Chart
        if (trainingChart) {
            const label = new Date().toLocaleTimeString();
            chartData.labels.push(label);
            chartData.datasets[0].data.push(loss);
            chartData.datasets[1].data.push(acc);

            // Limit to last 50 points
            if (chartData.labels.length > 50) {
                chartData.labels.shift();
                chartData.datasets[0].data.shift();
                chartData.datasets[1].data.shift();
            }

            trainingChart.update('none'); // 'none' for performance
        }
    }
}

// Clean up when closing modal
const originalCloseModal = window.closeModal;
window.closeModal = (modalId) => {
    originalCloseModal(modalId);
    if (modalId === 'jobDetailsModal' && liveTerminal) {
        liveTerminal.disconnect();
    }
};

function setupJobFilters() {
    const tabs = document.querySelectorAll('#jobTabs .tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const filter = tab.dataset.filter;
            let filtered = window.allJobs || [];

            if (filter !== 'all') {
                filtered = filtered.filter(j => j.status === filter);
            }

            renderJobsGrid(filtered);
        });
    });
}

// ─────────────────────────────────────────────────────────────────────────────────
// TOP UP MODAL
// ─────────────────────────────────────────────────────────────────────────────────

function setupTopUpModal() {
    const topUpBtn = document.getElementById('topUpBtn');
    const confirmBtn = document.getElementById('confirmTopUp');

    if (!topUpBtn || !confirmBtn) return;

    topUpBtn.addEventListener('click', () => {
        document.getElementById('topUpModal').classList.add('active');
    });

    confirmBtn.addEventListener('click', async () => {
        const packId = document.querySelector('input[name="credit_pack"]:checked')?.value;

        if (!packId) {
            Toast.error('Selecciona un paquete de créditos');
            return;
        }

        // Close modal and open Wompi checkout
        closeModal('topUpModal');

        if (window.payments && window.payments.openCheckout) {
            await window.payments.openCheckout(packId);
        } else {
            Toast.error('Sistema de pagos no disponible');
        }
    });
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ─────────────────────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────────────────────

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;

    return date.toLocaleDateString();
}

function formatDuration(seconds) {
    if (!seconds) return '0s';

    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hrs > 0) return `${hrs}h ${mins}m`;
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
}

// Make functions globally available
window.showSection = showSection;
window.closeModal = closeModal;
window.cancelJob = cancelJob;
window.viewLogs = viewLogs;
window.clearFile = clearFile;

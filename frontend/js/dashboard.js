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
        <div class="job-card glass" onclick="showJobDetails('${job.id}')">
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

function showSection(sectionId) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionId);
    });

    // Update sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`section-${sectionId}`).classList.add('active');

    // Update title
    const titles = {
        'overview': 'Overview',
        'jobs': 'Jobs',
        'new-job': 'New Job',
        'wallet': 'Wallet'
    };
    document.getElementById('pageTitle').textContent = titles[sectionId] || sectionId;

    // Load section-specific data
    if (sectionId === 'wallet') {
        loadTransactions();
    }
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

function setupFileUploads() {
    setupFileUpload('scriptUpload', 'scriptPreview');
    setupFileUpload('datasetUpload', 'datasetPreview');
}

function setupFileUpload(uploadId, previewId) {
    const upload = document.getElementById(uploadId);
    const preview = document.getElementById(previewId);
    const input = upload.querySelector('input');

    // Drag and drop
    upload.addEventListener('dragover', (e) => {
        e.preventDefault();
        upload.classList.add('drag-over');
    });

    upload.addEventListener('dragleave', () => {
        upload.classList.remove('drag-over');
    });

    upload.addEventListener('drop', (e) => {
        e.preventDefault();
        upload.classList.remove('drag-over');

        if (e.dataTransfer.files.length) {
            input.files = e.dataTransfer.files;
            showFilePreview(input, preview, upload);
        }
    });

    // File selection
    input.addEventListener('change', () => {
        showFilePreview(input, preview, upload);
    });
}

function showFilePreview(input, preview, upload) {
    if (input.files.length === 0) {
        preview.style.display = 'none';
        upload.querySelector('.file-upload-icon').style.display = '';
        upload.querySelector('.file-upload-text').style.display = '';
        upload.querySelector('.file-upload-hint').style.display = '';
        return;
    }

    const file = input.files[0];
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);

    preview.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span class="file-preview-name">${file.name} (${sizeMB} MB)</span>
        <span class="file-preview-remove" onclick="clearFile('${input.name}')">✕</span>
    `;

    preview.style.display = 'flex';
    upload.querySelector('.file-upload-icon').style.display = 'none';
    upload.querySelector('.file-upload-text').style.display = 'none';
    upload.querySelector('.file-upload-hint').style.display = 'none';
}

function clearFile(inputName) {
    const input = document.querySelector(`input[name="${inputName}"]`);
    const upload = input.closest('.file-upload');
    const preview = upload.querySelector('.file-preview');

    input.value = '';
    preview.style.display = 'none';
    upload.querySelector('.file-upload-icon').style.display = '';
    upload.querySelector('.file-upload-text').style.display = '';
    upload.querySelector('.file-upload-hint').style.display = '';
}

// ─────────────────────────────────────────────────────────────────────────────────
// JOB FORM
// ─────────────────────────────────────────────────────────────────────────────────

function setupJobForm() {
    const form = document.getElementById('newJobForm');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('[type="submit"]');
        const originalHTML = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner spinner-sm"></span> Launching...';

        try {
            const formData = new FormData(form);

            // Call API to create job
            const response = await fetch(`${window.api.baseURL}/jobs/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
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
            clearFile('script');
            clearFile('dataset');

            // Refresh data and go to jobs
            await loadDashboardData();
            await loadWalletBalance();
            showSection('jobs');

        } catch (error) {
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

async function viewLogs(jobId) {
    try {
        const logs = await window.api.getJobLogs(jobId);

        // Simple modal to show logs
        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal" style="max-width: 800px; max-height: 80vh;">
                <div class="modal-header">
                    <h3 class="modal-title">Job Logs</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
                    <pre style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; white-space: pre-wrap; color: var(--text-secondary);">${logs.logs || 'No logs available'}</pre>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

    } catch (error) {
        Toast.error('Failed to load logs');
    }
}

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

    topUpBtn.addEventListener('click', () => {
        document.getElementById('topUpModal').classList.add('active');
    });

    confirmBtn.addEventListener('click', async () => {
        const packId = document.querySelector('input[name="credit_amount"]:checked').value;

        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="spinner spinner-sm"></span> Redirecting to Wompi...';

        try {
            // Call backend to get Wompi Checkout URL
            const response = await fetch(`${CONFIG.API_URL}/packs/${packId}/checkout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const err = await response.json();
                let msg = 'Failed to initiate payment';
                if (err.detail) {
                    msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
                }
                throw new Error(msg);
            }

            const data = await response.json();

            if (data.payment_url) {
                // Redirect user to Wompi
                window.location.href = data.payment_url;
            } else {
                throw new Error('No payment URL received');
            }

        } catch (error) {
            console.error('Payment Error:', error);
            Toast.error(error.message);
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = 'Add Credits';
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

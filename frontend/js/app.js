/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * HOME-GPU-CLOUD - Main JavaScript
 * Handles animations, interactions, and API calls
 * ═══════════════════════════════════════════════════════════════════════════════
 */

// ─────────────────────────────────────────────────────────────────────────────────
// CONFIGURATION
// ─────────────────────────────────────────────────────────────────────────────────

const CONFIG = {
    API_URL: 'http://localhost:8000/api/v1',
    TYPEWRITER_SPEED: 80,
    TYPEWRITER_PAUSE: 2000,
    COUNTER_DURATION: 2000,
};

// Typewriter phrases
const TYPEWRITER_PHRASES = [
    'On Demand',
    'For Everyone',
    'Made Simple',
    'At Your Fingertips',
    'Without Limits',
];

// ─────────────────────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────────────────────

/**
 * Wait for DOM to be ready
 */
function domReady(callback) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', callback);
    } else {
        callback();
    }
}

/**
 * Select single element
 */
function $(selector, context = document) {
    return context.querySelector(selector);
}

/**
 * Select multiple elements
 */
function $$(selector, context = document) {
    return [...context.querySelectorAll(selector)];
}

/**
 * Create element with attributes
 */
function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => {
        if (key === 'class') {
            el.className = value;
        } else if (key.startsWith('data')) {
            el.setAttribute(key, value);
        } else {
            el[key] = value;
        }
    });
    children.forEach(child => {
        if (typeof child === 'string') {
            el.appendChild(document.createTextNode(child));
        } else {
            el.appendChild(child);
        }
    });
    return el;
}

/**
 * Format number with commas
 */
function formatNumber(num, decimals = 0) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(amount);
}

/**
 * Format time duration
 */
function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// ─────────────────────────────────────────────────────────────────────────────────
// TYPEWRITER EFFECT
// ─────────────────────────────────────────────────────────────────────────────────

class Typewriter {
    constructor(element, phrases, options = {}) {
        this.element = element;
        this.phrases = phrases;
        this.speed = options.speed || CONFIG.TYPEWRITER_SPEED;
        this.pause = options.pause || CONFIG.TYPEWRITER_PAUSE;
        this.currentPhraseIndex = 0;
        this.currentCharIndex = 0;
        this.isDeleting = false;
        this.start();
    }

    start() {
        this.tick();
    }

    tick() {
        const currentPhrase = this.phrases[this.currentPhraseIndex];

        if (this.isDeleting) {
            this.currentCharIndex--;
        } else {
            this.currentCharIndex++;
        }

        this.element.textContent = currentPhrase.substring(0, this.currentCharIndex);

        let typeSpeed = this.speed;

        if (this.isDeleting) {
            typeSpeed /= 2;
        }

        if (!this.isDeleting && this.currentCharIndex === currentPhrase.length) {
            typeSpeed = this.pause;
            this.isDeleting = true;
        } else if (this.isDeleting && this.currentCharIndex === 0) {
            this.isDeleting = false;
            this.currentPhraseIndex = (this.currentPhraseIndex + 1) % this.phrases.length;
            typeSpeed = 500;
        }

        setTimeout(() => this.tick(), typeSpeed);
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// COUNTER ANIMATION
// ─────────────────────────────────────────────────────────────────────────────────

class Counter {
    constructor(element, options = {}) {
        this.element = element;
        this.target = parseFloat(element.dataset.target);
        this.duration = options.duration || CONFIG.COUNTER_DURATION;
        this.decimals = this.target % 1 !== 0 ? 1 : 0;
        this.started = false;
    }

    start() {
        if (this.started) return;
        this.started = true;

        const startTime = performance.now();
        const startValue = 0;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / this.duration, 1);
            const easeProgress = this.easeOutQuart(progress);
            const currentValue = startValue + (this.target - startValue) * easeProgress;

            this.element.textContent = formatNumber(currentValue, this.decimals);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.element.textContent = formatNumber(this.target, this.decimals);
            }
        };

        requestAnimationFrame(animate);
    }

    easeOutQuart(x) {
        return 1 - Math.pow(1 - x, 4);
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// PARTICLES BACKGROUND
// ─────────────────────────────────────────────────────────────────────────────────

class ParticleBackground {
    constructor(container, count = 30) {
        this.container = container;
        this.count = count;
        this.init();
    }

    init() {
        for (let i = 0; i < this.count; i++) {
            this.createParticle();
        }
    }

    createParticle() {
        const particle = document.createElement('div');
        particle.className = 'particle';

        const size = Math.random() * 4 + 2;
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        const tx = (Math.random() - 0.5) * 200;
        const ty = -Math.random() * 300 - 100;
        const duration = Math.random() * 10 + 10;
        const delay = Math.random() * 10;
        const hue = Math.random() > 0.5 ? 270 : 180; // Purple or cyan

        particle.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            left: ${x}%;
            top: ${y}%;
            --tx: ${tx}px;
            --ty: ${ty}px;
            animation-duration: ${duration}s;
            animation-delay: ${delay}s;
            background: hsl(${hue}, 70%, 60%);
            box-shadow: 0 0 ${size * 2}px hsl(${hue}, 70%, 60%);
        `;

        this.container.appendChild(particle);
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// SCROLL ANIMATIONS
// ─────────────────────────────────────────────────────────────────────────────────

class ScrollAnimations {
    constructor() {
        this.observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
        );
        this.init();
    }

    init() {
        $$('[data-animate]').forEach(el => {
            this.observer.observe(el);
        });

        // Also observe counters
        $$('.counter').forEach(el => {
            this.observer.observe(el);
        });
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');

                // Start counter if it's a counter element
                if (entry.target.classList.contains('counter')) {
                    const counter = new Counter(entry.target);
                    counter.start();
                }

                this.observer.unobserve(entry.target);
            }
        });
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// NAVIGATION
// ─────────────────────────────────────────────────────────────────────────────────

class Navigation {
    constructor() {
        this.navbar = $('.navbar');
        this.toggle = $('#navToggle');
        this.links = $('#navLinks');
        this.init();
    }

    init() {
        // Mobile toggle
        if (this.toggle) {
            this.toggle.addEventListener('click', () => this.toggleMobile());
        }

        // Scroll effect
        window.addEventListener('scroll', () => this.handleScroll());

        // Smooth scroll for anchor links
        $$('a[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => this.smoothScroll(e));
        });
    }

    toggleMobile() {
        this.links.classList.toggle('active');
        this.toggle.classList.toggle('active');
    }

    handleScroll() {
        if (window.scrollY > 50) {
            this.navbar.classList.add('scrolled');
        } else {
            this.navbar.classList.remove('scrolled');
        }
    }

    smoothScroll(e) {
        const href = e.currentTarget.getAttribute('href');
        if (href.startsWith('#') && href.length > 1) {
            e.preventDefault();
            const target = $(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// GPU STATS SIMULATION (for demo)
// ─────────────────────────────────────────────────────────────────────────────────

class GPUStatsSimulator {
    constructor() {
        this.utilization = $('.progress-fill');
        this.timer = $('.job-time span');
        this.seconds = 9257; // Starting from 02:34:17
        this.init();
    }

    init() {
        // Update timer every second
        setInterval(() => this.updateTimer(), 1000);

        // Update metrics occasionally
        setInterval(() => this.updateMetrics(), 3000);
    }

    updateTimer() {
        if (this.timer) {
            this.seconds++;
            this.timer.textContent = formatDuration(this.seconds);
        }
    }

    updateMetrics() {
        $$('.progress-fill').forEach(bar => {
            const currentWidth = parseFloat(bar.style.width);
            const delta = (Math.random() - 0.5) * 10;
            const newWidth = Math.max(20, Math.min(95, currentWidth + delta));
            bar.style.width = `${newWidth}%`;

            // Update corresponding value
            const metricValue = bar.closest('.metric')?.querySelector('.metric-value');
            if (metricValue && metricValue.textContent.includes('%')) {
                metricValue.textContent = `${Math.round(newWidth)}%`;
            }
        });
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// API CLIENT
// ─────────────────────────────────────────────────────────────────────────────────

class APIClient {
    constructor(baseURL = CONFIG.API_URL) {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth endpoints
    async register(email, password, fullName) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name: fullName }),
        });
    }

    async login(email, password) {
        const response = await this.request(`/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
            method: 'POST',
        });
        if (response.access_token) {
            this.token = response.access_token;
            localStorage.setItem('auth_token', this.token);
        }
        return response;
    }

    async getProfile() {
        return this.request('/auth/me');
    }

    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }

    // Wallet endpoints
    async getWallet() {
        return this.request('/wallet');
    }

    async topUp(amount) {
        return this.request('/wallet/topup', {
            method: 'POST',
            body: JSON.stringify({ amount }),
        });
    }

    async getTransactions(page = 1, pageSize = 20) {
        return this.request(`/wallet/transactions?page=${page}&page_size=${pageSize}`);
    }

    // Job endpoints
    async getJobs(status = null, limit = 20) {
        let url = `/jobs?limit=${limit}`;
        if (status) url += `&status_filter=${status}`;
        return this.request(url);
    }

    async getJob(jobId) {
        return this.request(`/jobs/${jobId}`);
    }

    async getJobLogs(jobId) {
        return this.request(`/jobs/${jobId}/logs`);
    }

    async cancelJob(jobId) {
        return this.request(`/jobs/${jobId}/cancel`, { method: 'POST' });
    }

    isAuthenticated() {
        return !!this.token;
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// FORM HANDLING
// ─────────────────────────────────────────────────────────────────────────────────

class FormHandler {
    constructor(form, options = {}) {
        this.form = form;
        this.options = options;
        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Password visibility toggle
        $$('.input-toggle', this.form).forEach(toggle => {
            toggle.addEventListener('click', () => this.togglePassword(toggle));
        });
    }

    async handleSubmit(e) {
        e.preventDefault();

        const submitBtn = this.form.querySelector('[type="submit"]');
        const originalText = submitBtn.innerHTML;

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner spinner-sm"></span> Loading...';

        try {
            const formData = new FormData(this.form);
            const data = Object.fromEntries(formData);

            if (this.options.onSubmit) {
                await this.options.onSubmit(data);
            }
        } catch (error) {
            if (this.options.onError) {
                this.options.onError(error);
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    togglePassword(toggle) {
        const input = toggle.previousElementSibling;
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';

        // Update icon
        const eyeOpen = toggle.querySelector('.eye-open');
        const eyeClosed = toggle.querySelector('.eye-closed');
        if (eyeOpen && eyeClosed) {
            eyeOpen.style.display = isPassword ? 'none' : 'block';
            eyeClosed.style.display = isPassword ? 'block' : 'none';
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ─────────────────────────────────────────────────────────────────────────────────

class Toast {
    static container = null;

    static init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(this.container);
        }
    }

    static show(message, type = 'info', duration = 5000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-fade-in-right`;
        toast.style.cssText = `
            padding: 16px 20px;
            border-radius: 12px;
            min-width: 300px;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
        `;

        const colors = {
            success: { bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)', color: '#10b981' },
            error: { bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)', color: '#ef4444' },
            warning: { bg: 'rgba(249, 115, 22, 0.15)', border: 'rgba(249, 115, 22, 0.3)', color: '#f97316' },
            info: { bg: 'rgba(6, 182, 212, 0.15)', border: 'rgba(6, 182, 212, 0.3)', color: '#06b6d4' },
        };

        const style = colors[type] || colors.info;
        toast.style.background = style.bg;
        toast.style.border = `1px solid ${style.border}`;
        toast.style.color = style.color;

        toast.innerHTML = `
            <span>${message}</span>
            <button style="margin-left: auto; background: none; border: none; color: inherit; cursor: pointer; opacity: 0.7;">✕</button>
        `;

        toast.querySelector('button').addEventListener('click', () => {
            toast.remove();
        });

        this.container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    static success(message) { this.show(message, 'success'); }
    static error(message) { this.show(message, 'error'); }
    static warning(message) { this.show(message, 'warning'); }
    static info(message) { this.show(message, 'info'); }
}

// ─────────────────────────────────────────────────────────────────────────────────
// INITIALIZATION
// ─────────────────────────────────────────────────────────────────────────────────

domReady(() => {
    console.log('🚀 Home GPU Cloud initialized');

    // Initialize navigation
    new Navigation();

    // Initialize scroll animations
    new ScrollAnimations();

    // Initialize typewriter
    const typewriterEl = $('#typewriter');
    if (typewriterEl) {
        new Typewriter(typewriterEl, TYPEWRITER_PHRASES);
    }

    // Initialize particles
    const particlesEl = $('#particles');
    if (particlesEl) {
        new ParticleBackground(particlesEl, 25);
    }

    // Initialize GPU stats simulation (for demo)
    new GPUStatsSimulator();

    // Make API client available globally
    window.api = new APIClient();
    window.Toast = Toast;
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, Toast, FormHandler };
}

/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * WEBSOCKET CLIENT - Real-time log streaming
 * ═══════════════════════════════════════════════════════════════════════════════
 */

class LogStreamClient {
    constructor(options = {}) {
        this.baseURL = options.baseURL || CONFIG.API_URL.replace('http', 'ws');
        this.token = localStorage.getItem('auth_token');
        this.socket = null;
        this.jobId = null;
        this.onLog = options.onLog || (() => { });
        this.onStatus = options.onStatus || (() => { });
        this.onConnect = options.onConnect || (() => { });
        this.onDisconnect = options.onDisconnect || (() => { });
        this.onError = options.onError || (() => { });
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.pingInterval = null;
    }

    connect(jobId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.disconnect();
        }

        this.jobId = jobId;
        const url = `${this.baseURL}/ws/logs/${jobId}?token=${this.token}`;

        try {
            this.socket = new WebSocket(url);

            this.socket.onopen = () => {
                console.log(`[WebSocket] Connected to job ${jobId}`);
                this.reconnectAttempts = 0;
                this.onConnect(jobId);
                this.startPing();
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('[WebSocket] Failed to parse message:', e);
                }
            };

            this.socket.onclose = (event) => {
                console.log(`[WebSocket] Disconnected (code: ${event.code})`);
                this.stopPing();
                this.onDisconnect(event.code, event.reason);

                // Attempt reconnection only for unexpected disconnections
                if (event.code !== 1000 && event.code !== 4001 && event.code !== 4003 && event.code !== 4004) {
                    this.attemptReconnect();
                }
            };

            this.socket.onerror = (error) => {
                console.error('[WebSocket] Error:', error);
                this.onError(error);
            };

        } catch (error) {
            console.error('[WebSocket] Connection failed:', error);
            this.onError(error);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'connected':
                console.log(`[WebSocket] ${data.message}`);
                break;
            case 'log':
                this.onLog(data.content, data.timestamp);
                break;
            case 'status':
                this.onStatus(data.status, data.details);
                break;
            case 'pong':
                // Heartbeat received
                break;
            default:
                console.log('[WebSocket] Unknown message type:', data.type);
        }
    }

    startPing() {
        // Send ping every 30 seconds to keep connection alive
        this.pingInterval = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send('ping');
            }
        }, 30000);
    }

    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('[WebSocket] Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            if (this.jobId) {
                this.connect(this.jobId);
            }
        }, delay);
    }

    disconnect() {
        this.stopPing();
        if (this.socket) {
            this.socket.close(1000, 'Client disconnected');
            this.socket = null;
        }
        this.jobId = null;
    }

    isConnected() {
        return this.socket && this.socket.readyState === WebSocket.OPEN;
    }
}


/**
 * Live Terminal Display Component
 */
class LiveTerminal {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;
        this.options = {
            maxLines: options.maxLines || 1000,
            autoScroll: options.autoScroll !== false,
            showTimestamps: options.showTimestamps || false,
            theme: options.theme || 'dark',
        };
        this.lines = [];
        this.client = null;
        this.jobId = null;
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="terminal ${this.options.theme}">
                <div class="terminal-header">
                    <div class="terminal-controls">
                        <span class="terminal-dot red"></span>
                        <span class="terminal-dot yellow"></span>
                        <span class="terminal-dot green"></span>
                    </div>
                    <div class="terminal-title">
                        <span class="terminal-status-icon"></span>
                        <span class="terminal-job-id">No job connected</span>
                    </div>
                    <div class="terminal-actions">
                        <button class="terminal-btn" title="Clear" onclick="this.closest('.terminal').terminal.clear()">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                        <button class="terminal-btn" title="Download Logs" onclick="this.closest('.terminal').terminal.download()">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="terminal-body">
                    <div class="terminal-output"></div>
                </div>
                <div class="terminal-footer">
                    <span class="terminal-line-count">0 lines</span>
                    <span class="terminal-connection-status">
                        <span class="status-dot offline"></span>
                        Disconnected
                    </span>
                </div>
            </div>
        `;

        this.output = this.container.querySelector('.terminal-output');
        this.statusIcon = this.container.querySelector('.terminal-status-icon');
        this.jobIdEl = this.container.querySelector('.terminal-job-id');
        this.lineCountEl = this.container.querySelector('.terminal-line-count');
        this.connectionStatusEl = this.container.querySelector('.terminal-connection-status');

        // Make terminal accessible from DOM
        this.container.querySelector('.terminal').terminal = this;
    }

    connect(jobId) {
        this.jobId = jobId;
        this.jobIdEl.textContent = `Job: ${jobId.slice(0, 8)}`;

        this.client = new LogStreamClient({
            onLog: (content, timestamp) => this.addLine(content, 'log', timestamp),
            onStatus: (status, details) => this.updateStatus(status, details),
            onConnect: () => this.setConnectionStatus('connected'),
            onDisconnect: () => this.setConnectionStatus('disconnected'),
            onError: (err) => this.addLine(`[Error] ${err.message || 'Connection error'}`, 'error'),
        });

        this.client.connect(jobId);
        this.addLine(`Connecting to job ${jobId.slice(0, 8)}...`, 'system');
    }

    disconnect() {
        if (this.client) {
            this.client.disconnect();
            this.client = null;
        }
        this.addLine('Disconnected from log stream', 'system');
    }

    addLine(content, type = 'log', timestamp = null) {
        const line = {
            content,
            type,
            timestamp: timestamp || new Date().toISOString(),
        };

        this.lines.push(line);

        // Trim if exceeds max lines
        if (this.lines.length > this.options.maxLines) {
            this.lines.shift();
            this.output.firstChild?.remove();
        }

        // Create line element
        const lineEl = document.createElement('div');
        lineEl.className = `terminal-line ${type}`;

        if (this.options.showTimestamps) {
            const time = new Date(line.timestamp).toLocaleTimeString();
            lineEl.innerHTML = `<span class="terminal-timestamp">${time}</span><span class="terminal-content">${this.escapeHtml(content)}</span>`;
        } else {
            lineEl.innerHTML = `<span class="terminal-content">${this.escapeHtml(content)}</span>`;
        }

        this.output.appendChild(lineEl);

        // Update line count
        this.lineCountEl.textContent = `${this.lines.length} lines`;

        // Auto scroll
        if (this.options.autoScroll) {
            this.output.scrollTop = this.output.scrollHeight;
        }
    }

    updateStatus(status, details) {
        this.addLine(`[Status] Job status changed to: ${status}`, 'status');

        // Update status icon
        const statusClasses = {
            running: 'running',
            completed: 'completed',
            failed: 'failed',
            pending: 'pending',
        };

        this.statusIcon.className = `terminal-status-icon ${statusClasses[status] || ''}`;
    }

    setConnectionStatus(status) {
        const dot = this.connectionStatusEl.querySelector('.status-dot');
        const text = this.connectionStatusEl.childNodes[1];

        if (status === 'connected') {
            dot.className = 'status-dot online';
            text.textContent = ' Connected';
        } else {
            dot.className = 'status-dot offline';
            text.textContent = ' Disconnected';
        }
    }

    clear() {
        this.lines = [];
        this.output.innerHTML = '';
        this.lineCountEl.textContent = '0 lines';
    }

    download() {
        const content = this.lines.map(l => {
            const time = new Date(l.timestamp).toISOString();
            return `[${time}] ${l.content}`;
        }).join('\n');

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `job-${this.jobId || 'logs'}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use
window.LogStreamClient = LogStreamClient;
window.LiveTerminal = LiveTerminal;

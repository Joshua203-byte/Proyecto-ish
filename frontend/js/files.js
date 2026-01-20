/**
 * Files handler for Home GPU Cloud Dashboard
 */
const files = {
    // Max file size (50MB)
    MAX_SIZE: 50 * 1024 * 1024,

    // Allowed extensions
    ALLOWED_EXTENSIONS: ['.py', '.ipynb', '.zip', '.txt'],

    // Upload a file
    async upload(file) {
        if (!file) {
            throw new Error('No file selected');
        }

        // Check size
        if (file.size > this.MAX_SIZE) {
            throw new Error(`File too large. Max size is ${this.MAX_SIZE / 1024 / 1024}MB`);
        }

        // Check extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.ALLOWED_EXTENSIONS.includes(ext)) {
            throw new Error(`File type not allowed. Allowed: ${this.ALLOWED_EXTENSIONS.join(', ')}`);
        }

        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('access_token');
        if (!token) throw new Error('Not authenticated');

        try {
            const response = await fetch(`${API_BASE_URL}/files/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Upload Error:', error);
            throw error;
        }
    },

    // UI Helper for file input with drag & drop
    initDropZone(dropZoneId, fileInputId, displayId) {
        const dropZone = document.getElementById(dropZoneId);
        const fileInput = document.getElementById(fileInputId);
        const display = document.getElementById(displayId);

        if (!dropZone || !fileInput) return;

        // Drag enter
        dropZone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-active');
        });

        // Drag over
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-active');
        });

        // Drag leave
        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-active');
        });

        // Drop
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-active');

            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                updateDisplay(e.dataTransfer.files[0]);
            }
        });

        // Click to select
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // Input change
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                updateDisplay(fileInput.files[0]);
            }
        });

        function updateDisplay(file) {
            if (display) {
                display.textContent = file.name;
                display.classList.add('has-file');

                // Add remove button logic if needed
            }
        }
    }
};

window.files = files;

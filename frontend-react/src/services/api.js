import axios from 'axios';
import { toast } from 'sonner';

const api = axios.create({
    // Use relative path so vite proxy or production same-origin works
    baseURL: '/api/v1',
    timeout: 10000, // 10 seconds timeout
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.params || config.data || '');
    const token = localStorage.getItem('auth_token'); // matches legacy key
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
});

// Response interceptor to handle 401s auto-logout
api.interceptors.response.use(
    (response) => {
        console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status);

        // Auto-toast success messages for POST/PUT/DELETE if it's meant to be user-facing
        if (['post', 'put', 'delete'].includes(response.config.method?.toLowerCase()) && response.status < 300) {
            // We ignore background operations like polling if needed
            if (!response.config.url?.includes('/logs') && !response.config.url?.match(/\/jobs\/?$/)) {
                toast.success('Operación exitosa');
            }
        }

        return response;
    },
    (error) => {
        const isLoginAttempt = error.config?.url?.includes('/auth/login');
        const detail = error.response?.data?.detail;
        const msg = typeof detail === 'string' ? detail : (error.response?.data?.message || 'Error de conexión con el servidor');

        console.error(`❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
            status: error.response?.status,
            message: error.message,
            data: error.response?.data
        });

        // Show toast for all errors with HIGHER duration for visibility
        toast.error(msg, {
            description: `Status: ${error.response?.status || 'Network Error'}`,
            duration: 10000, // 10 seconds to ensure user sees it
        });

        // Handle 401s
        if (error.response && error.response.status === 401) {
            console.warn("API returned 401. Since we are in Guest Mode, this might mean token expired but we continue as guest.");
            // We do NOT redirect to login anymore
        }
        return Promise.reject(error);
    }
);

export default api;

import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// The backend URL is now configured via Heroku config vars
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

console.log(`Starting server on port ${PORT}`);
console.log(`Proxying /api requests to: ${BACKEND_URL}`);

// Proxy API requests
app.use(
    '/api',
    createProxyMiddleware({
        target: BACKEND_URL,
        changeOrigin: true,
        pathRewrite: (path, req) => req.originalUrl,
        // Forward the ngrok anti-abuse header so API calls succeed on free ngrok
        on: {
            proxyReq: (proxyReq, req, res) => {
                proxyReq.setHeader('ngrok-skip-browser-warning', 'true');
            }
        }
    })
);

// Serve static files from the React app
app.use(express.static(path.join(__dirname, 'dist')));

// The "catchall" handler: for any request that doesn't
// match one above, send back React's index.html file.
app.use((req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

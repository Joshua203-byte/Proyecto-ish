/**
 * Constructs a full URL for an asset hosted on the backend.
 * @param {string} path - The relative path from the backend root (e.g., "/uploads/image.png")
 * @returns {string} - The full URL (e.g., "https://api.example.com/uploads/image.png")
 */
export const getAssetUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) return path;

    // Get API URL from env, removing '/api/v1' suffix if present to get root
    let baseUrl = import.meta.env.VITE_API_URL || '';

    // If we are in local dev (no env var), relative paths work fine usually, 
    // BUT if we are on Vercel without env var, valid relative path fails.
    // However, the requirement is to use VITE_API_URL.

    // Clean up base URL to be the HOST, not the API prefix
    // e.g. https://my-api.com/api/v1 -> https://my-api.com
    if (baseUrl.endsWith('/api/v1')) {
        baseUrl = baseUrl.slice(0, -7);
    }

    // Ensure path starts with /
    const cleanPath = path.startsWith('/') ? path : `/${path}`;

    // If no absolute base url is set (local dev), return relative
    if (!baseUrl) return cleanPath;

    return `${baseUrl}${cleanPath}`;
};

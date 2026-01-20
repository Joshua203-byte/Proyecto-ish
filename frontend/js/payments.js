/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * WOMPI EL SALVADOR PAYMENTS INTEGRATION
 * Uses Payment Links API (redirect-based checkout)
 * ═══════════════════════════════════════════════════════════════════════════════
 */

window.payments = {
    /**
     * Create a payment link and redirect user to Wompi checkout.
     * @param {string} packId - The pack ID (pack_pilot, pack_researcher, pack_lab)
     */
    async openCheckout(packId) {
        try {
            const token = localStorage.getItem('auth_token');

            if (!token) {
                Toast.error('Debes iniciar sesión para comprar créditos');
                return;
            }

            // Show loading state
            Toast.info('Creando link de pago...');

            // Create payment link via backend
            const response = await fetch(`${window.api.baseURL}/payments/create-link`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pack_id: packId })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al crear el link de pago');
            }

            const data = await response.json();

            Toast.success(`Redirigiendo a Wompi para pagar $${data.amount_usd}...`);

            // Redirect to Wompi payment page
            setTimeout(() => {
                window.location.href = data.payment_url;
            }, 1000);

        } catch (error) {
            console.error('Payment error:', error);
            Toast.error(error.message || 'Error al procesar el pago');
        }
    },

    /**
     * Load available credit packs from backend.
     */
    async getPacks() {
        try {
            const response = await fetch(`${window.api.baseURL}/payments/packs`);
            if (!response.ok) throw new Error('Failed to load packs');
            return await response.json();
        } catch (error) {
            console.error('Error loading packs:', error);
            return { packs: [] };
        }
    }
};

// Check for payment success on page load
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.get('payment') === 'success') {
        const ref = urlParams.get('ref');
        Toast.success('¡Gracias por tu compra! Tus créditos serán agregados en breve.');

        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);

        // Reload wallet balance after a delay (webhook may take a moment)
        setTimeout(() => {
            if (typeof loadWalletBalance === 'function') {
                loadWalletBalance();
            }
            if (typeof loadTransactions === 'function') {
                loadTransactions();
            }
        }, 3000);
    }
});

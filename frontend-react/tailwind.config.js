/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['"Montserrat"', 'sans-serif'],
                serif: ['"Montserrat"', 'sans-serif'],
            },
            colors: {
                background: '#fcfbf9', // Warm paper
                surface: '#ffffff',    // Pure clean white
                primary: '#1c1917',    // Stone-900 (Warm black)
                secondary: '#57534e',  // Stone-600
                accent: '#ea580c',     // Orange-600 (Terracotta/Clay vibe - distinct but natural)
                border: '#e7e5e4',     // Stone-200

                // Keep these for semantic meaning but updated tones
                success: '#65a30d',    // Lime-600 (Natural green)
                error: '#dc2626',      // Red-600
                warning: '#d97706',    // Amber-600
            },
            borderRadius: {
                '4xl': '2rem',
                '5xl': '3rem',
            }
        },
    },
    plugins: [],
}

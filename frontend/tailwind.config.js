/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#FFF8F1',
        blush: '#F6DCD8',
        dusty: '#D9AAA4',
        rosebrown: '#A96868',
        rosegold: '#C58B83',
        cocoa: '#442B2B',
        // Soft derived tints used for surfaces
        petal: '#FBEDE8',
        shell: '#FDF1EA',
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Georgia', 'Times New Roman', 'serif'],
        sans: ['"Inter Variable"', 'Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        script: ['"Great Vibes"', 'cursive'],
      },
      boxShadow: {
        soft: '0 8px 30px -12px rgba(169, 104, 104, 0.25)',
        card: '0 4px 18px -8px rgba(68, 43, 43, 0.18)',
        lift: '0 18px 40px -16px rgba(169, 104, 104, 0.4)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        'pop-in': {
          '0%': { opacity: '0', transform: 'scale(.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'fade-up': 'fade-up .5s ease-out both',
        'pop-in': 'pop-in .2s ease-out both',
      },
    },
  },
  plugins: [],
};

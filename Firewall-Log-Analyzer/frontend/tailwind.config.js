/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E6EDF5',
          100: '#CCDBEB',
          200: '#99B7D7',
          300: '#6693C3',
          400: '#336FAF',
          500: '#0C2D57', // Main primary color
          600: '#0A2547',
          700: '#081D37',
          800: '#061527',
          900: '#040D17',
          950: '#02060B',
        },
        accent: {
          50: '#FFF4F0',
          100: '#FFE9E1',
          200: '#FFD3C3',
          300: '#FFBDA5',
          400: '#FFA787',
          500: '#FC6736', // Main accent color
          600: '#E85D2F',
          700: '#D45328',
          800: '#C04921',
          900: '#AC3F1A',
          950: '#983513',
        },
        light: {
          50: '#FFFEFE',
          100: '#FFFDFD',
          200: '#FFFBFB',
          300: '#FFF9F9',
          400: '#FFF7F7',
          500: '#FFB0B0', // Light pink/coral
          600: '#E69E9E',
          700: '#CC8C8C',
          800: '#B37A7A',
          900: '#996868',
        },
        neutral: {
          50: '#F9F9F9',
          100: '#F5F5F5',
          200: '#F0F0F0',
          300: '#EBEBEB',
          400: '#E6E6E6',
          500: '#EFECEC', // Main neutral color
          600: '#D6D3D3',
          700: '#BDBABA',
          800: '#A4A1A1',
          900: '#8B8888',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          850: '#1a202c',
          900: '#111827',
          950: '#0d1117',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          600: '#d97706',
        },
      },
      animation: {
        'fade-in': 'fade-in 0.5s ease-in-out',
        'fade-in-up': 'fade-in-up 0.5s ease-out',
        'fade-in-down': 'fade-in-down 0.5s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounce-subtle 2s infinite',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'fade-in-up': {
          '0%': {
            opacity: '0',
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        'fade-in-down': {
          '0%': {
            opacity: '0',
            transform: 'translateY(-10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        'scale-in': {
          '0%': {
            opacity: '0',
            transform: 'scale(0.9)',
          },
          '100%': {
            opacity: '1',
            transform: 'scale(1)',
          },
        },
        'slide-in-right': {
          '0%': {
            opacity: '0',
            transform: 'translateX(-10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateX(0)',
          },
        },
        'bounce-subtle': {
          '0%, 100%': {
            transform: 'translateY(-2%)',
            'animation-timing-function': 'cubic-bezier(0.8, 0, 1, 1)',
          },
          '50%': {
            transform: 'translateY(0)',
            'animation-timing-function': 'cubic-bezier(0, 0, 0.2, 1)',
          },
        },
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'card': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'card-hover': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}


/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        studio: {
          bg: '#0B0B0F',
          surface: '#15151B',
          elevated: '#1D1D25',
          card: '#15151B',
          border: '#2B2B35',
          borderSubtle: '#23232C',
          cherry: '#C62845',
          cherryHover: '#D93655',
          cherryDark: '#8E1B32',
          cherryMuted: '#2A141A',
          cherryGlow: 'rgba(198, 40, 69, 0.25)',
          text: '#F7F4F5',
          textMuted: '#A9A4AA',
          textSubtle: '#736E76',
          success: '#35C98B',
          successBg: '#112A20',
          warning: '#E8A83E',
          warningBg: '#2E2211',
          error: '#E05260',
          errorBg: '#2C1418',
          info: '#4A90E2',
          infoBg: '#142233',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

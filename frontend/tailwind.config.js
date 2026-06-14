/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0D1117',
          secondary: '#161B22',
          surface: '#1C2128',
          elevated: '#232A34',
        },
        mc: {
          emerald: '#2ECC71',
          diamond: '#45D9FF',
          gold: '#F5C542',
          redstone: '#FF5D5D',
          amethyst: '#B388FF',
          copper: '#D88C4A',
        },
        status: {
          online: '#2ECC71',
          offline: '#7F8C8D',
          warning: '#F5C542',
          error: '#FF5D5D',
          starting: '#45D9FF',
          stopping: '#FF8A65',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#C7CDD5',
          muted: '#8A94A6',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        pixel: ['Silkscreen', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'mc-sm': '1px 1px 0px 0px rgba(0, 0, 0, 0.4)',
        'mc-md': '2px 2px 0px 0px rgba(0, 0, 0, 0.4)',
        'mc-lg': '4px 4px 0px 0px rgba(0, 0, 0, 0.5)',
      }
    },
  },
  plugins: [],
}

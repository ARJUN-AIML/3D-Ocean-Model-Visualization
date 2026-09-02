import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          950: '#030712',
          900: '#0a1120',
          850: '#0f172a',
          800: '#162036',
          700: '#1e2942',
          600: '#2a3859',
        },
        cyan: {
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          glow: '#00f2fe',
        },
        scientific: {
          accent: '#00e5ff',
          alert: '#ef4444',
          warning: '#f59e0b',
          success: '#10b981',
          purple: '#a855f7',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0, 242, 254, 0.25)',
        'panel-dark': '0 10px 30px -5px rgba(0, 0, 0, 0.8), 0 0 1px 1px rgba(56, 189, 248, 0.15)',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
export default config

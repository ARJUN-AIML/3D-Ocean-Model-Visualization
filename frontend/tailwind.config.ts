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
          950: '#061024',
          900: '#0F2854',
          800: '#1C4D8D',
          700: '#4988C4',
          100: '#BDE8F5',
        },
        navy: {
          darker: '#061024',
          deep: '#0F2854',
          ocean: '#1C4D8D',
          sky: '#4988C4',
          ice: '#BDE8F5',
          muted: '#7FA9C9',
        }
      },
      fontFamily: {
        heading: ['Space Grotesk', 'sans-serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'panel': '0 4px 20px -2px rgba(6, 16, 36, 0.7), 0 0 1px 1px rgba(73, 136, 196, 0.25)',
        'subtle': '0 2px 10px rgba(6, 16, 36, 0.5)',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      }
    },
  },
  plugins: [],
}
export default config

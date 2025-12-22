import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme base colors
        dark: {
          900: '#0a0a0a',
          800: '#121212',
          700: '#1a1a1a',
          600: '#242424',
          500: '#2e2e2e',
        },
        // Neon green accent (cyber/tech aesthetic)
        neon: {
          50: '#e6ffed',
          100: '#b3ffc6',
          200: '#80ff9f',
          300: '#4dff78',
          400: '#1aff51',
          500: '#00ff41', // Primary neon green
          600: '#00e639',
          700: '#00cc32',
          800: '#00b32b',
          900: '#009924',
        },
        // Complementary colors
        cyber: {
          blue: '#00d9ff',
          purple: '#b300ff',
          pink: '#ff00e5',
        },
        // Semantic colors for dark theme
        success: {
          500: '#00ff41',
          600: '#00e639',
        },
        warning: {
          500: '#ffaa00',
          600: '#ff8800',
        },
        danger: {
          500: '#ff1744',
          600: '#ff0028',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 2s linear infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #00ff41, 0 0 10px #00ff41, 0 0 15px #00ff41' },
          '100%': { boxShadow: '0 0 10px #00ff41, 0 0 20px #00ff41, 0 0 30px #00ff41' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, rgba(0, 255, 65, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(0, 255, 65, 0.05) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
export default config;

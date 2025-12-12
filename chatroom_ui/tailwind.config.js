/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // M3 Agent品牌色
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        // 暗色主题
        dark: {
          bg: '#1e1e1e',
          surface: '#2d2d2d',
          border: '#444',
          text: '#e0e0e0',
        },
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}

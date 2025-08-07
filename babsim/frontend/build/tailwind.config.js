/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-blue': '#0f172a',
        'dark-gray': '#1e293b',
        'purple-accent': '#8b5cf6',
        'green-accent': '#10b981',
        'pink-accent': '#ec4899',
        'orange-accent': '#f97316',
        'blue-accent': '#3b82f6',
      },
    },
  },
  plugins: [],
} 
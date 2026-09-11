/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f5ff',
          100: '#dce6ff',
          500: '#3b5bdb',
          600: '#2f49b0',
          700: '#253a8a',
        },
      },
    },
  },
  plugins: [],
}

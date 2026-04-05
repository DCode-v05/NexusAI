/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        teal: {
          DEFAULT: '#005A70',
          50:  '#E6F2F5',
          100: '#CCE4EB',
          200: '#99C9D7',
          300: '#66AEC3',
          400: '#3393AF',
          500: '#005A70',
          600: '#004E61',
          700: '#004557',
          800: '#003A49',
          900: '#002F3B',
        },
        success: '#16A34A',
        error:   '#DC2626',
        warning: '#D97706',
        info:    '#0284C7',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
      },
    },
  },
  plugins: [],
}

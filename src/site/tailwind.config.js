/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/site/templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        'mocha-bg': '#1e1e2e',
        'mocha-surface': '#313244',
        'mocha-overlay': '#45475a',
        'mocha-text': '#cdd6f4',
        'mocha-subtext': '#a6adc8',
        'mocha-red': '#f38ba8',
      }
    },
  },
  plugins: [],
}

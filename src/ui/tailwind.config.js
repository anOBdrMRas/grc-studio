// fidonis-brand: 1 – rebuilt from the token values of DESIGN.md (the shared originals were not available)
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        brand: ['Manrope', 'IBM Plex Sans', 'system-ui', 'sans-serif'],
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    logs: false,
    themes: [
      {
        'fidonis-light': {
          primary: '#0a2f4d',
          secondary: '#1b5e8c',
          accent: '#c8972a',
          neutral: '#2a323c',
          'base-100': '#ffffff',
          'base-200': '#f3f5f7',
          'base-300': '#e0e5ea',
          'base-content': '#0b0e12',
          info: '#1b6f9e',
          success: '#0d724e',
          warning: '#8a6014',
          error: '#c53c3c',
          '--rounded-box': '0.75rem',
          '--rounded-btn': '0.5rem',
        },
      },
      {
        'fidonis-dark': {
          primary: '#2b6fa8',
          secondary: '#4ba5dd',
          accent: '#d1a33c',
          neutral: '#272c32',
          'base-100': '#17191c',
          'base-200': '#101214',
          'base-300': '#272c32',
          'base-content': '#eef1f4',
          info: '#4ba5dd',
          success: '#46c98a',
          warning: '#e0a63a',
          error: '#ef6a6a',
          '--rounded-box': '0.75rem',
          '--rounded-btn': '0.5rem',
        },
      },
    ],
    darkTheme: 'fidonis-dark',
  },
};

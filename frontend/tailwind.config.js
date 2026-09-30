/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F4F6F9",
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#243247",
          soft: "#59697D",
          faint: "#69798C",
        },
        line: "#DFE5ED",
        brand: {
          DEFAULT: "#456786",
          dark: "#304E6B",
          soft: "#EAF0F6",
        },
        warn: {
          DEFAULT: "#86652D",
          soft: "#F7F1E5",
        },
        danger: {
          DEFAULT: "#9C5055",
          soft: "#F8ECEC",
        },
        nav: {
          DEFAULT: "#14211D",
          hover: "#1D302A",
        },
      },
      fontFamily: {
        sans: ["'Source Sans 3'", "system-ui", "sans-serif"],
        display: ["'Source Sans 3'", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        lg: "10px",
      },
    },
  },
  plugins: [],
};

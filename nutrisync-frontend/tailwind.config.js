/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: "#1a7a4a",
        canvas: "#f7fbf5",
        surface: "#edf3ec",
        ink: "#123524",
        mist: "#6c7c72",
        sand: "#d7e7db",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      boxShadow: {
        soft: "0 20px 50px rgba(16, 51, 33, 0.08)",
      },
    },
  },
  plugins: [],
};

/** @type {import("tailwindcss").Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        sahool: {
          bg: "#0D1F17",
          primary: "#1B4D3E",
          light: "#2D6A4F",
          dark: "#14352B",
          accent: "#F4D03F",
          "accent-light": "#F7DC6F",
          success: "#27AE60",
          warning: "#E67E22",
          danger: "#E74C3C",
          info: "#3498DB",
        },
      },
    },
  },
  plugins: [],
};
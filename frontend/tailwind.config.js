/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F4F0FA",
        card: "#ECE4F9",
        ink: "#282836",
        muted: "#6F6A85",
        line: "#D9CEF0",
        primary: "#7140CF",
        terracotta: "#B4532A",
        ochre: "#B07D0E",
      },
      fontFamily: {
        sans: ["var(--font-poppins)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      keyframes: {
        rise: { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "none" } },
        ring: { "0%": { boxShadow: "0 0 0 0 var(--ring)" }, "100%": { boxShadow: "0 0 0 12px transparent" } },
      },
      animation: {
        rise: "rise 0.35s ease-out both",
        ring: "ring 1.8s ease-out infinite",
      },
    },
  },
  plugins: [],
};

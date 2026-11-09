/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F6F2EA",
        card: "#FFFDF8",
        ink: "#1C1B18",
        muted: "#7B766A",
        line: "#E5DFD2",
        forest: "#1F4D3A",
        terracotta: "#B4532A",
        ochre: "#B07D0E",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(28,27,24,0.04), 0 8px 24px -12px rgba(28,27,24,0.12)",
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

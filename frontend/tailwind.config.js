/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07080c",
        panel: "#0e1017",
        line: "#232736",
        muted: "#8a90a6",
        accent: "#8b5cf6",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      keyframes: {
        rise: { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "none" } },
        ring: { "0%": { boxShadow: "0 0 0 0 var(--ring)" }, "100%": { boxShadow: "0 0 0 14px transparent" } },
      },
      animation: {
        rise: "rise 0.28s ease-out both",
        ring: "ring 1.6s ease-out infinite",
      },
    },
  },
  plugins: [],
};

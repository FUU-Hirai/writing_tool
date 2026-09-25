import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f3efe4",
        ink: "#1f1a14",
        teal: "#0e6b62",
        line: "#e2dacb",
        card: "#fffdf8",
      },
      fontFamily: {
        serif: ["var(--font-newsreader)", "serif"],
        sans: ["var(--font-figtree)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

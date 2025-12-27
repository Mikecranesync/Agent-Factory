import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        rivet: {
          orange: "#FF6B35",  // Primary CTA, highlights
          dark: "#1a1a2e",    // Main background
          gray: "#16213e",    // Secondary background
          light: "#e8e8e8",   // Hover states
        },
      },
    },
  },
  plugins: [],
};
export default config;

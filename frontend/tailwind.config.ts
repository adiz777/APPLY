import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#050914",
          900: "#091024",
          800: "#101b38",
          700: "#192952",
        },
        cyber: {
          blue: "#0ea5e9",
          glow: "#38bdf8",
          gold: "#f59e0b",
          goldLight: "#fbbf24",
        },
      },
    },
  },
  plugins: [],
};
export default config;

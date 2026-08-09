/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        court: {
          void: "#01060d",
          page: "#020914",
          panel: "#03101d",
          inset: "#020b16",
          raised: "#061523",
          line: "#075675",
          "line-soft": "#08364b",
          cyan: "#00e7ff",
          green: "#63ff00",
          success: "#25e83f",
          warning: "#ffd51f",
          danger: "#ff3748",
          text: "#eef6fa",
          muted: "#8d9aa7",
        },
      },
      fontFamily: {
        sans: ["Rajdhani", "Segoe UI", "sans-serif"],
        display: ["Rajdhani", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      boxShadow: {
        panel: "0 18px 45px rgba(0, 0, 0, 0.24)",
        cyan: "0 0 18px rgba(0, 231, 255, 0.18)",
        green: "0 0 20px rgba(99, 255, 0, 0.26)",
        "green-strong": "0 0 8px rgba(99, 255, 0, 0.75), 0 0 28px rgba(99, 255, 0, 0.34)",
      },
      backgroundImage: {
        "tactical-grid":
          "linear-gradient(rgba(0, 231, 255, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 231, 255, 0.035) 1px, transparent 1px)",
        "panel-glow":
          "radial-gradient(circle at 80% 0%, rgba(0, 231, 255, 0.09), transparent 38%)",
      },
      backgroundSize: {
        "tactical-grid": "32px 32px",
      },
      letterSpacing: {
        tactical: "0.08em",
        label: "0.12em",
      },
      borderRadius: {
        panel: "0.5rem",
      },
      keyframes: {
        "status-pulse": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.62", transform: "scale(0.88)" },
        },
        "scan-line": {
          "0%": { transform: "translateY(-120%)", opacity: "0" },
          "15%": { opacity: "0.22" },
          "85%": { opacity: "0.12" },
          "100%": { transform: "translateY(820%)", opacity: "0" },
        },
      },
      animation: {
        "status-pulse": "status-pulse 1.8s ease-in-out infinite",
        "scan-line": "scan-line 8s linear infinite",
      },
    },
  },
  plugins: [],
}

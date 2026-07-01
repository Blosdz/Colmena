import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1800,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("react-plotly.js") || id.includes("plotly.js")) {
            return "plotly-vendor";
          }
          if (id.includes("react-router-dom") || id.includes("@tanstack/react-query")) {
            return "app-vendor";
          }
          return undefined;
        },
      },
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5174,
    allowedHosts: [".trycloudflare.com"],
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
  },
});

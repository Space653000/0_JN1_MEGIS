import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { createProgressStatePlugin } from "./progress-state-plugin";

export default defineConfig({
  plugins: [react(), createProgressStatePlugin()],
  server: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:4174", changeOrigin: false } },
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:4174", changeOrigin: false } },
  },
});

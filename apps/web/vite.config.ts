import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API_TARGET = "http://127.0.0.1:8000";
const PROXIED = [
  "/v1",
  "/translate",
  "/preview",
  "/presets",
  "/glossary",
  "/logs",
  "/settings",
  "/healthz",
];

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      PROXIED.map((path) => [path, { target: API_TARGET, changeOrigin: true }])
    ),
  },
});

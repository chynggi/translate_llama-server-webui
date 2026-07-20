import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const API_TARGET = "http://127.0.0.1:8000";
const PROXIED = [
  "/v1",
  "/translate",
  "/preview",
  "/presets",
  "/glossary",
  "/logs",
  "/settings",
  "/conversations",
  "/chat",
  "/healthz",
];

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      PROXIED.map((path) => [path, { target: API_TARGET, changeOrigin: true }])
    ),
  },
});

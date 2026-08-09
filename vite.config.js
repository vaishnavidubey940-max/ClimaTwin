import { defineConfig } from "vite";

export default defineConfig({
  root: "frontend",
  plugins: [{
    name: "dharatwin-frontend-paths",
    transformIndexHtml(html) { return html.replaceAll("/frontend/", "/"); },
    transform(code, id) { return id.endsWith("/frontend/index.html") ? code.replaceAll("/frontend/", "/") : null; }
  }],
  server: {
    host: "127.0.0.1",
    port: 3000,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:5000" }
  },
  build: { outDir: "../dist", emptyOutDir: true }
});

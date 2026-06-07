import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "src/test.setup.js",
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    strictPort: false,
    // Em Linux com fs.inotify.max_user_watches baixo, o watcher do Vite estoura
    // com ENOSPC. O fix definitivo é elevar o limite do SO:
    //   sudo sysctl fs.inotify.max_user_watches=524288   (persistir em /etc/sysctl.d)
    // Fallback sem sudo: VITE_USE_POLLING=true npm run dev — usa polling (sem
    // inotify). Opt-in via env para não degradar quem não precisa.
    watch: process.env.VITE_USE_POLLING
      ? { usePolling: true, interval: 300 }
      : undefined,
  },
});

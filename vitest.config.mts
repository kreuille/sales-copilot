import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    setupFiles: ["dotenv/config"],
    // DB-backed tests share one Postgres connection through Prisma's local
    // dev proxy, which mishandles concurrent prepared statements across
    // parallel test files (protocol error 08P01). Run files sequentially.
    fileParallelism: false,
  },
  resolve: {
    alias: {
      "@": import.meta.dirname,
    },
  },
});

import { defineConfig } from "vitest/config";
import { createProgressStatePlugin } from "./progress-state-plugin";

export default defineConfig({
  plugins: [createProgressStatePlugin()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: true,
  },
});

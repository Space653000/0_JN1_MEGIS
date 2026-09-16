import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "vite";

const progressModuleId = "virtual:ui0-progress";
const resolvedProgressModuleId = `\0${progressModuleId}`;

const progressStatePlugin = {
  name: "megis-progress-state",
  resolveId(id: string) {
    return id === progressModuleId ? resolvedProgressModuleId : undefined;
  },
  load(id: string) {
    if (id !== resolvedProgressModuleId) return undefined;
    const source = readFileSync(
      resolve(process.cwd(), "../../execution/ui0/progress-state.json"),
      "utf8",
    );
    return `export default ${source}`;
  },
};

export default defineConfig({
  plugins: [react(), progressStatePlugin],
  server: { host: "127.0.0.1", port: 4173, strictPort: true },
  preview: { host: "127.0.0.1", port: 4173, strictPort: true },
});

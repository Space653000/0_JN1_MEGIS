import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const progressModuleId = "virtual:ui0-progress";
const resolvedProgressModuleId = `\0${progressModuleId}`;

export function createProgressStatePlugin() {
  return {
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
}

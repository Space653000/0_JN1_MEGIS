import { readFileSync } from "node:fs";
import { resolve } from "node:path";

type ProgressDevServer = {
  watcher: {
    add(path: string): void;
    on(event: "change", callback: (file: string) => void): void;
  };
  moduleGraph: {
    getModuleById(id: string): object | undefined;
    invalidateModule(module: object): void;
  };
  ws: { send(payload: { type: "full-reload"; path: string }): void };
};

const progressModuleId = "virtual:project-progress";
const resolvedProgressModuleId = `\0${progressModuleId}`;
const progressPath = resolve(process.cwd(), "../../execution/WORK_QUEUE.yaml");

export function createProgressStatePlugin() {
  return {
    name: "megis-progress-state",
    resolveId(id: string) {
      return id === progressModuleId ? resolvedProgressModuleId : undefined;
    },
    load(id: string) {
      if (id !== resolvedProgressModuleId) return undefined;
      const source = readFileSync(progressPath, "utf8");
      return `export default ${source}`;
    },
    configureServer(server: ProgressDevServer) {
      server.watcher.add(progressPath);
      server.watcher.on("change", (file) => {
        if (resolve(file) !== progressPath) return;
        const module = server.moduleGraph.getModuleById(resolvedProgressModuleId);
        if (module) server.moduleGraph.invalidateModule(module);
        server.ws.send({ type: "full-reload", path: "*" });
      });
    },
  };
}

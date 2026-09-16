import source from "virtual:project-progress";
import type { ProgressState } from "../types/progress";

export interface ProgressAdapter {
  getSnapshot(): ProgressState;
}

export const repositoryProgressAdapter: ProgressAdapter = {
  getSnapshot: () => source,
};

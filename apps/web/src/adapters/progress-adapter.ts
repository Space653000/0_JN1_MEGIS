import source from "virtual:ui0-progress";
import type { ProgressState } from "../types/progress";

export interface ProgressAdapter {
  getSnapshot(): ProgressState;
}

export const repositoryProgressAdapter: ProgressAdapter = {
  getSnapshot: () => source,
};


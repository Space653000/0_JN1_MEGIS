/// <reference types="vite/client" />

declare module "virtual:project-progress" {
  import type { ProgressState } from "./types/progress";
  const state: ProgressState;
  export default state;
}

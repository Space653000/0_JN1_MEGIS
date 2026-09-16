/// <reference types="vite/client" />

declare module "virtual:ui0-progress" {
  import type { ProgressState } from "./types/progress";
  const state: ProgressState;
  export default state;
}


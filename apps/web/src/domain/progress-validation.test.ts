import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { ProgressState } from "../types/progress";
import { validateProgressState } from "./progress-validation";

const repoRoot = resolve(process.cwd(), "../..");
const loadState = () => JSON.parse(readFileSync(resolve(repoRoot, "execution/ui0/progress-state.json"), "utf8")) as ProgressState;

describe("UI-0 progress truthfulness contract", () => {
  it("accepts the repository progress source with working evidence", () => {
    expect(validateProgressState(loadState(), { evidenceExists: (path) => existsSync(resolve(repoRoot, path)) })).toEqual([]);
  });

  it("rejects a done item with broken evidence", () => {
    const state = structuredClone(loadState());
    state.workItems[0].evidence = ["missing/evidence.txt"];
    expect(validateProgressState(state, { evidenceExists: (path) => existsSync(resolve(repoRoot, path)) })).toContain("UI0-FND-001 has broken evidence: missing/evidence.txt");
  });

  it("rejects an illegal transition when dependencies are incomplete", () => {
    const state = structuredClone(loadState());
    state.workItems[0].status = "planned";
    expect(validateProgressState(state)).toContain("UI0-PRG-001 cannot be in_progress before UI0-FND-001 is done");
  });
});


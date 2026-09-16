import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { ProgressState } from "../types/progress";
import { validateProgressState } from "./progress-validation";

const repoRoot = resolve(process.cwd(), "../..");
const loadState = () => JSON.parse(readFileSync(resolve(repoRoot, "execution/WORK_QUEUE.yaml"), "utf8")) as ProgressState;
const getWorkItem = (state: ProgressState, id: string) => {
  const item = state.workItems.find((candidate) => candidate.id === id);
  if (!item) throw new Error(`Missing test work item: ${id}`);
  return item;
};

describe("Project progress truthfulness contract", () => {
  it("accepts the repository progress source with working evidence", () => {
    expect(validateProgressState(loadState(), { evidenceExists: (path) => existsSync(resolve(repoRoot, path)) })).toEqual([]);
  });

  it("rejects a done item with broken evidence", () => {
    const state = structuredClone(loadState());
    const repositoryItem = getWorkItem(state, "G0-REP-001");
    repositoryItem.acceptanceResults[2] = {
      criterion: "控制面可由自動化命令驗證",
      status: "passed",
      evidence: ["scripts/verify-control-plane.mjs"],
    };
    repositoryItem.evidence = ["missing/evidence.txt"];
    expect(validateProgressState(state, { evidenceExists: (path) => existsSync(resolve(repoRoot, path)) })).toContain("G0-REP-001 has broken evidence: missing/evidence.txt");
  });

  it("rejects an illegal transition when dependencies are incomplete", () => {
    const state = structuredClone(loadState());
    getWorkItem(state, "G0-REP-001").status = "planned";
    getWorkItem(state, "G0-ENV-001").status = "in_progress";
    getWorkItem(state, "G0-CAD-001").status = "planned";
    state.currentWorkItem = "G0-ENV-001";
    expect(validateProgressState(state)).toContain("G0-ENV-001 cannot be in_progress before G0-REP-001 is done");
  });

  it("rejects a done item with pending acceptance", () => {
    const state = structuredClone(loadState());
    const repositoryItem = getWorkItem(state, "G0-REP-001");
    repositoryItem.acceptanceResults[0].status = "pending";
    repositoryItem.acceptanceResults[0].evidence = [];
    expect(validateProgressState(state)).toContain("G0-REP-001 is done with pending acceptance");
  });

  it("rejects more than one in-progress item", () => {
    const state = structuredClone(loadState());
    const secondItem = state.workItems.find((item) => item.id !== state.currentWorkItem && item.status !== "in_progress");
    if (!secondItem) throw new Error("Missing a second work item for WIP validation");
    secondItem.status = "in_progress";
    expect(validateProgressState(state)).toContain("Expected exactly one in-progress item, found 2");
  });
});

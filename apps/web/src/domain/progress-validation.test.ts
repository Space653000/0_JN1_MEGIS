import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { ProgressState } from "../types/progress";
import { validateProgressState } from "./progress-validation";

const repoRoot = resolve(process.cwd(), "../..");
const loadState = () => JSON.parse(readFileSync(resolve(repoRoot, "execution/WORK_QUEUE.yaml"), "utf8")) as ProgressState;

describe("Project progress truthfulness contract", () => {
  it("accepts the repository progress source with working evidence", () => {
    expect(validateProgressState(loadState(), { evidenceExists: (path) => existsSync(resolve(repoRoot, path)) })).toEqual([]);
  });

  it("rejects a done item with broken evidence", () => {
    const state = structuredClone(loadState());
    state.workItems[0].status = "done";
    state.workItems[0].acceptanceResults[2] = {
      criterion: "控制面可由自動化命令驗證",
      status: "passed",
      evidence: ["scripts/verify-control-plane.mjs"],
    };
    state.workItems[0].verification = "passed";
    state.workItems[0].commitSha = "a".repeat(40);
    state.workItems[0].evidence = ["missing/evidence.txt"];
    state.workItems[1].status = "in_progress";
    state.currentWorkItem = state.workItems[1].id;
    expect(validateProgressState(state, { evidenceExists: (path) => existsSync(resolve(repoRoot, path)) })).toContain("G0-REP-001 has broken evidence: missing/evidence.txt");
  });

  it("rejects an illegal transition when dependencies are incomplete", () => {
    const state = structuredClone(loadState());
    state.workItems[1].status = "in_progress";
    state.currentWorkItem = state.workItems[1].id;
    expect(validateProgressState(state)).toContain("G0-ENV-001 cannot be in_progress before G0-REP-001 is done");
  });

  it("rejects a done item with pending acceptance", () => {
    const state = structuredClone(loadState());
    state.workItems[0].status = "done";
    state.workItems[0].acceptanceResults[0].status = "pending";
    state.workItems[0].acceptanceResults[0].evidence = [];
    state.workItems[0].verification = "passed";
    state.workItems[0].commitSha = "a".repeat(40);
    expect(validateProgressState(state)).toContain("G0-REP-001 is done with pending acceptance");
  });

  it("rejects more than one in-progress item", () => {
    const state = structuredClone(loadState());
    state.workItems[1].status = "in_progress";
    expect(validateProgressState(state)).toContain("Expected exactly one in-progress item, found 2");
  });
});

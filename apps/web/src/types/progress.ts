export type GateStatus = "planned" | "active" | "blocked" | "accepted";
export type WorkStatus = "planned" | "ready" | "in_progress" | "blocked" | "done";

export interface Gate {
  id: string;
  title: string;
  status: GateStatus;
  dependsOn: string[];
}

export interface WorkItem {
  id: string;
  title: string;
  gate: string;
  status: WorkStatus;
  dependsOn: string[];
  acceptance: string[];
  acceptanceResults: Array<{
    criterion: string;
    status: "pending" | "passed";
    evidence: string[];
  }>;
  verificationCommands?: string[];
  blockedBy: string[];
  evidence: string[];
  verification: "not_run" | "passed" | "failed";
  commitSha: string | null;
}

export interface ProgressState {
  schemaVersion: string;
  updatedAt: string;
  baselineCommit: string;
  currentWorkItem: string;
  gates: Gate[];
  workItems: WorkItem[];
  blockers: Array<{ id: string; title: string; owner: string; fallback: string }>;
  risks: Array<{ id: string; title: string; impact: string; mitigation: string }>;
}

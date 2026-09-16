import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = process.cwd();
const readJsonYaml = (path) => JSON.parse(readFileSync(resolve(repoRoot, path), "utf8"));
const queue = readJsonYaml("execution/WORK_QUEUE.yaml");
const blockers = readJsonYaml("execution/BLOCKERS.yaml");
const projectState = readFileSync(resolve(repoRoot, "execution/PROJECT_STATE.md"), "utf8");
const errors = [];

const requiredFiles = [
  "execution/PROJECT_STATE.md",
  "execution/WORK_QUEUE.yaml",
  "execution/BLOCKERS.yaml",
  "execution/LAST_VERIFICATION.json",
  "execution/schemas/work-queue.schema.json",
  "docs/UI0_ACCEPTANCE.md",
];
for (const path of requiredFiles) if (!existsSync(resolve(repoRoot, path))) errors.push(`Missing control-plane file: ${path}`);

const blueprintQueueIds = [
  "G0-REP-001", "G0-ENV-001", "G0-CAD-001", "G0-DRW-001", "G0-SIM-001", "G0-CI-001",
  "G1-IR-001", "G1-IR-002", "G1-IR-003", "G1-MIG-001",
  "G2-CAD-001", "G2-CAD-002", "G2-CAD-003", "G2-CAD-004",
  "G3-RUL-001", "G3-VAL-001", "G3-VAL-002", "G3-BEN-001",
  "G4-MOD-001", "G4-MOD-002", "G4-IMP-001",
  "G5-PKG-001", "G5-BOM-001", "G5-DRW-001", "G5-REP-001",
  "G6-UI-001", "G6-QST-001", "G6-E2E-001", "G7-ACO-001", "G8-ROB-001",
];

const itemIds = new Set(queue.workItems.map((item) => item.id));
for (const id of blueprintQueueIds) if (!itemIds.has(id)) errors.push(`Missing blueprint work item: ${id}`);
if (itemIds.size !== queue.workItems.length) errors.push("Duplicate work item ID");

const gateIds = new Set(queue.gates.map((gate) => gate.id));
if (gateIds.size !== queue.gates.length) errors.push("Duplicate gate ID");
const activeGates = queue.gates.filter((gate) => gate.status === "active");
if (activeGates.length !== 1) errors.push(`Expected exactly one active gate, found ${activeGates.length}`);
for (const gate of queue.gates) {
  for (const dependency of gate.dependsOn) {
    const dependencyGate = queue.gates.find((candidate) => candidate.id === dependency);
    if (!dependencyGate) errors.push(`${gate.id} has missing gate dependency ${dependency}`);
    if (["active", "accepted"].includes(gate.status) && dependencyGate?.status !== "accepted") {
      errors.push(`${gate.id} cannot be ${gate.status} before ${dependency} is accepted`);
    }
  }
}

const inProgress = queue.workItems.filter((item) => item.status === "in_progress");
if (inProgress.length !== 1) errors.push(`Expected exactly one in-progress work item, found ${inProgress.length}`);
if (inProgress[0]?.id !== queue.currentWorkItem) errors.push("currentWorkItem does not match the in-progress item");
const current = queue.workItems.find((item) => item.id === queue.currentWorkItem);
if (!current) errors.push(`Unknown currentWorkItem: ${queue.currentWorkItem}`);
if (current && !activeGates.some((gate) => gate.id === current.gate)) errors.push("Current work item is not in the active gate");

const requiredItemFields = ["id", "title", "gate", "status", "dependsOn", "inputs", "outputs", "acceptance", "acceptanceResults", "verificationCommands", "rollbackBoundary", "blockedBy", "evidence", "verification", "commitSha"];
for (const item of queue.workItems) {
  for (const field of requiredItemFields) if (!(field in item)) errors.push(`${item.id ?? "unknown"} missing field ${field}`);
  if (!gateIds.has(item.gate)) errors.push(`${item.id} references unknown gate ${item.gate}`);
  for (const dependency of item.dependsOn) {
    const dependencyItem = queue.workItems.find((candidate) => candidate.id === dependency);
    if (!dependencyItem) errors.push(`${item.id} has missing dependency ${dependency}`);
    if (["ready", "in_progress", "done"].includes(item.status) && dependencyItem?.status !== "done") {
      errors.push(`${item.id} cannot be ${item.status} before ${dependency} is done`);
    }
  }
  const acceptance = new Set(item.acceptance);
  const results = new Map(item.acceptanceResults.map((result) => [result.criterion, result]));
  if (acceptance.size !== item.acceptance.length) errors.push(`${item.id} has duplicate acceptance criteria`);
  if (results.size !== item.acceptanceResults.length) errors.push(`${item.id} has duplicate acceptance results`);
  for (const criterion of acceptance) if (!results.has(criterion)) errors.push(`${item.id} missing acceptance result: ${criterion}`);
  for (const result of item.acceptanceResults) {
    if (!acceptance.has(result.criterion)) errors.push(`${item.id} has unknown acceptance result: ${result.criterion}`);
    if (result.status === "passed" && result.evidence.length === 0) errors.push(`${item.id} passed acceptance without evidence`);
    for (const path of result.evidence) if (!existsSync(resolve(repoRoot, path))) errors.push(`${item.id} has broken acceptance evidence: ${path}`);
  }
  if (item.status === "done") {
    if (item.acceptanceResults.some((result) => result.status !== "passed")) errors.push(`${item.id} is done with pending acceptance`);
    if (item.verification !== "passed") errors.push(`${item.id} is done without passed verification`);
    if (!/^[0-9a-f]{40}$/.test(item.commitSha ?? "")) errors.push(`${item.id} is done without a valid commit SHA`);
    if (item.evidence.length === 0) errors.push(`${item.id} is done without evidence`);
  }
  for (const path of item.evidence) if (!existsSync(resolve(repoRoot, path))) errors.push(`${item.id} has broken evidence: ${path}`);
}

if (JSON.stringify(queue.blockers) !== JSON.stringify(blockers.blockers)) errors.push("WORK_QUEUE and BLOCKERS blocker lists differ");
if (!projectState.includes(`Current gate: \`${activeGates[0]?.id}`)) errors.push("PROJECT_STATE current gate is stale");
if (!projectState.includes(`Current work item: \`${queue.currentWorkItem}`)) errors.push("PROJECT_STATE current work item is stale");

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Control plane valid: ${queue.workItems.length} work items, ${queue.gates.length} gates, current ${queue.currentWorkItem}`);

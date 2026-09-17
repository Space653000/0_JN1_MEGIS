import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = process.env.MEGIS_REPO_ROOT
  ? resolve(process.env.MEGIS_REPO_ROOT)
  : process.cwd();
const readJsonYaml = (path) => JSON.parse(readFileSync(resolve(repoRoot, path), "utf8"));
const queue = readJsonYaml("execution/WORK_QUEUE.yaml");
const blockers = readJsonYaml("execution/BLOCKERS.yaml");
const projectState = readFileSync(resolve(repoRoot, "execution/PROJECT_STATE.md"), "utf8");
const readme = readFileSync(resolve(repoRoot, "README.md"), "utf8");
const requiredWorkItems = readJsonYaml("execution/schemas/v3-required-work-items.json");
const errors = [];

const requiredFiles = [
  "execution/PROJECT_STATE.md",
  "execution/WORK_QUEUE.yaml",
  "execution/BLOCKERS.yaml",
  "execution/LAST_VERIFICATION.json",
  "execution/schemas/work-queue.schema.json",
  "execution/schemas/v3-required-work-items.json",
  "MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md",
  "docs/decisions/ADR-0001-adopt-v3-blueprint.md",
  "docs/UI0_ACCEPTANCE.md",
];
for (const path of requiredFiles) if (!existsSync(resolve(repoRoot, path))) errors.push(`Missing control-plane file: ${path}`);

const blueprintQueueIds = requiredWorkItems.requiredWorkItemIds;

const itemIds = new Set(queue.workItems.map((item) => item.id));
for (const id of blueprintQueueIds) if (!itemIds.has(id)) errors.push(`Missing blueprint work item: ${id}`);
if (itemIds.size !== queue.workItems.length) errors.push("Duplicate work item ID");
if (new Set(blueprintQueueIds).size !== blueprintQueueIds.length) errors.push("Duplicate required blueprint work item ID");
if (!readme.includes("MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md")) {
  errors.push("README does not point to the v3.0-claude-code blueprint");
}

const immutableCompletedItems = {
  "G0-REP-001": "09f19ea3633189bdbb58e254d8e5798736950bfb",
  "G0-ENV-001": "629c02831b6b3eae30fb8a8ef8f9519f3bfbafaf",
  "G0-CAD-001": "b8a0dddd2f3ab763cde4a466e851f3a733f3099a",
  "G0-DRW-001": "ed81af5ac3f55c72285010afec0091a36f3fc92f",
  "G0-SIM-001": "28a415ea4c4457daef2bed5f3d72f1be1f67bb0f",
  "G0-CI-001": "86b9b67513822538e8bd3147d403f24521bb0815",
  "G1-IR-001": "a2229343e453301ca2aee8053be4509e43514964",
  "G1-IR-002": "c05af93d16e064dd939753fb1b7ac6d108ac01bc",
  "G1-IR-003": "6160784f8b3280152bef6d006baf0fd033e9097a",
  "G1-MIG-001": "be573a0c8dc151ba9a199770146855a10b64540f",
  "G2-CAD-001": "1cd6a270f5a5013d2ffba16c680cbbe68bc20356",
  "G2-CAD-002": "6b3d8a6aa15a3797f21cec516a3b2a4554db5c73",
  "G2-CAD-003": "b8473653ed8e0b8c2c329997b6e4570f368adfb7",
};
for (const [id, commitSha] of Object.entries(immutableCompletedItems)) {
  const item = queue.workItems.find((candidate) => candidate.id === id);
  if (item?.status !== "done" || item?.commitSha !== commitSha) {
    errors.push(`${id} changed after v3 adoption baseline`);
  }
}

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

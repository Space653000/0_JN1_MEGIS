import type { ProgressState, WorkItem } from "../types/progress";

export interface ProgressValidationOptions {
  evidenceExists?: (path: string) => boolean;
}

export function validateProgressState(state: ProgressState, options: ProgressValidationOptions = {}) {
  const errors: string[] = [];
  const ids = new Set(state.workItems.map((item) => item.id));
  if (!ids.has(state.currentWorkItem)) errors.push(`Unknown current work item: ${state.currentWorkItem}`);
  for (const item of state.workItems) {
    for (const dependency of item.dependsOn) {
      const dependencyItem = state.workItems.find((candidate) => candidate.id === dependency);
      if (!dependencyItem) errors.push(`${item.id} has missing dependency ${dependency}`);
      if (["ready", "in_progress", "done"].includes(item.status) && dependencyItem?.status !== "done") {
        errors.push(`${item.id} cannot be ${item.status} before ${dependency} is done`);
      }
    }
    validateAcceptanceResults(item, options, errors);
    validateDoneItem(item, options, errors);
  }
  return errors;
}

function validateAcceptanceResults(item: WorkItem, options: ProgressValidationOptions, errors: string[]) {
  const acceptance = new Set(item.acceptance);
  const resultCriteria = new Set(item.acceptanceResults.map((result) => result.criterion));
  if (resultCriteria.size !== item.acceptanceResults.length) errors.push(`${item.id} has duplicate acceptance results`);
  for (const criterion of acceptance) {
    if (!resultCriteria.has(criterion)) errors.push(`${item.id} is missing an acceptance result for: ${criterion}`);
  }
  for (const result of item.acceptanceResults) {
    if (!acceptance.has(result.criterion)) errors.push(`${item.id} has an unknown acceptance result: ${result.criterion}`);
    if (result.status === "passed" && result.evidence.length === 0) {
      errors.push(`${item.id} passed acceptance without evidence: ${result.criterion}`);
    }
    if (options.evidenceExists) {
      for (const path of result.evidence) {
        if (!options.evidenceExists(path)) errors.push(`${item.id} has broken acceptance evidence: ${path}`);
      }
    }
  }
}

function validateDoneItem(item: WorkItem, options: ProgressValidationOptions, errors: string[]) {
  if (item.status !== "done") return;
  if (item.acceptanceResults.some((result) => result.status !== "passed")) {
    errors.push(`${item.id} is done with pending acceptance`);
  }
  if (item.verification !== "passed") errors.push(`${item.id} is done without passed verification`);
  if (!item.commitSha || !/^[0-9a-f]{40}$/.test(item.commitSha)) errors.push(`${item.id} is done without a valid commit SHA`);
  if (item.evidence.length === 0) errors.push(`${item.id} is done without evidence`);
  if (options.evidenceExists) {
    for (const path of item.evidence) if (!options.evidenceExists(path)) errors.push(`${item.id} has broken evidence: ${path}`);
  }
}

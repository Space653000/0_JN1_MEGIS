import { auditRepository } from "./lib/artifact-policy.mjs";

const repoRoot = process.env.MEGIS_REPO_ROOT || process.cwd();
const result = auditRepository(repoRoot);
if (result.errors.length > 0) {
  for (const error of result.errors) console.error(error);
  console.error(`Artifact policy failed: ${result.errors.length} issue(s)`);
  process.exit(1);
}
console.log(`Artifact policy passed: ${JSON.stringify(result.summary)}`);

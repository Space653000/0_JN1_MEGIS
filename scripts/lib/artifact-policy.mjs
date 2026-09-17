import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { lstatSync, readFileSync } from "node:fs";
import { extname, resolve } from "node:path";

const normalizePath = (value) => value.replaceAll("\\", "/");
const isUnder = (path, root) => path === root || path.startsWith(`${root}/`);
const lineSet = (text) =>
  new Set(
    text
      .split(/\r?\n/u)
      .map((line) => line.trim())
      .filter((line) => line.length > 0 && !line.startsWith("#")),
  );

const validatePolicyShape = (policy) => {
  const errors = [];
  if (policy.policyVersion !== "1.0.0") errors.push("Unsupported artifact policy version");
  if (policy.genericTrackedFileMaxBytes !== 1_048_576) errors.push("Generic tracked-file budget must be 1 MiB");
  if (policy.evidenceJson?.maxFileBytes !== 51_200) errors.push("Evidence JSON budget must be 50 KiB");
  if (policy.golden?.maxFileBytes !== 204_800) errors.push("Golden file budget must be 200 KiB");
  if (policy.golden?.maxTotalBytes !== 5_242_880) errors.push("Golden aggregate budget must be 5 MiB");
  for (const key of ["heavyArtifactExtensions", "requiredGitAttributes", "requiredGitIgnore", "legacyHeavyArtifactAllowlist"]) {
    if (!Array.isArray(policy[key])) errors.push(`Artifact policy ${key} must be an array`);
  }
  return errors;
};

export function auditInventory({ files, attributesText, ignoreText, policy }) {
  const errors = validatePolicyShape(policy);
  if (errors.length > 0) return { errors, summary: null };

  const normalizedFiles = files.map((file) => ({ ...file, path: normalizePath(file.path) }));
  const byPath = new Map(normalizedFiles.map((file) => [file.path, file]));
  const allowlist = new Map(policy.legacyHeavyArtifactAllowlist.map((entry) => [entry.path, entry]));
  const attributes = lineSet(attributesText);
  const ignores = lineSet(ignoreText);

  for (const required of policy.requiredGitAttributes) {
    if (!attributes.has(required)) errors.push(`Missing required .gitattributes rule: ${required}`);
  }
  for (const required of policy.requiredGitIgnore) {
    if (!ignores.has(required)) errors.push(`Missing required .gitignore rule: ${required}`);
  }

  let goldenTotalBytes = 0;
  let evidenceJsonCount = 0;
  let heavyArtifactCount = 0;
  for (const file of normalizedFiles) {
    if (file.symlink) {
      errors.push(`Tracked symlink is outside artifact policy: ${file.path}`);
      continue;
    }
    if (file.bytes > policy.genericTrackedFileMaxBytes) {
      const exception = allowlist.get(file.path);
      if (!exception || exception.sha256 !== file.sha256 || exception.adr.length === 0) {
        errors.push(`Tracked file exceeds 1 MiB without exact ADR allowlist: ${file.path} (${file.bytes} bytes)`);
      }
    }
    if (isUnder(file.path, policy.evidenceJson.root) && file.path.toLowerCase().endsWith(".json")) {
      evidenceJsonCount += 1;
      if (file.bytes > policy.evidenceJson.maxFileBytes) {
        errors.push(`Evidence JSON exceeds 50 KiB: ${file.path} (${file.bytes} bytes)`);
      }
    }
    if (policy.golden.roots.some((root) => isUnder(file.path, root))) {
      goldenTotalBytes += file.bytes;
      if (file.bytes > policy.golden.maxFileBytes) {
        errors.push(`Golden file exceeds 200 KiB: ${file.path} (${file.bytes} bytes)`);
      }
    }
    const extension = extname(file.path).toLowerCase();
    if (isUnder(file.path, "artifacts") && policy.heavyArtifactExtensions.includes(extension)) {
      heavyArtifactCount += 1;
      const exception = allowlist.get(file.path);
      if (!exception) {
        errors.push(`Tracked heavy artifact is not legacy-allowlisted: ${file.path}`);
      } else if (exception.bytes !== file.bytes || exception.sha256 !== file.sha256) {
        errors.push(`Legacy heavy artifact no longer matches its exact allowlist: ${file.path}`);
      }
    }
  }
  if (goldenTotalBytes > policy.golden.maxTotalBytes) {
    errors.push(`Golden aggregate exceeds 5 MiB: ${goldenTotalBytes} bytes`);
  }
  for (const exception of policy.legacyHeavyArtifactAllowlist) {
    const file = byPath.get(exception.path);
    if (!file) errors.push(`Legacy heavy artifact allowlist entry is not tracked: ${exception.path}`);
    if (!exception.adr.match(/^ADR-[0-9]{4}$/u)) errors.push(`Invalid ADR reference for ${exception.path}`);
  }

  return {
    errors,
    summary: {
      trackedFiles: normalizedFiles.length,
      evidenceJsonCount,
      goldenTotalBytes,
      heavyArtifactCount,
      legacyAllowlistCount: policy.legacyHeavyArtifactAllowlist.length,
      largestTrackedFileBytes: Math.max(0, ...normalizedFiles.map((file) => file.bytes)),
    },
  };
}

export function auditRepository(repoRoot) {
  const policy = JSON.parse(readFileSync(resolve(repoRoot, "config/artifact-policy/policy-1.0.0.json"), "utf8"));
  const tracked = execFileSync("git", ["ls-files", "-z"], { cwd: repoRoot, encoding: "utf8" })
    .split("\0")
    .filter(Boolean);
  const files = tracked.map((path) => {
    const absolute = resolve(repoRoot, path);
    const stat = lstatSync(absolute);
    const payload = stat.isSymbolicLink() ? Buffer.alloc(0) : readFileSync(absolute);
    return {
      path,
      bytes: stat.size,
      sha256: createHash("sha256").update(payload).digest("hex"),
      symlink: stat.isSymbolicLink(),
    };
  });
  return auditInventory({
    files,
    attributesText: readFileSync(resolve(repoRoot, ".gitattributes"), "utf8"),
    ignoreText: readFileSync(resolve(repoRoot, ".gitignore"), "utf8"),
    policy,
  });
}

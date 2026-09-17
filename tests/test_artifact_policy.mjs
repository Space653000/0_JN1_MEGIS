import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { auditInventory, auditRepository } from "../scripts/lib/artifact-policy.mjs";

const policy = JSON.parse(readFileSync("config/artifact-policy/policy-1.0.0.json", "utf8"));
const attributesText = policy.requiredGitAttributes.join("\n");
const ignoreText = policy.requiredGitIgnore.join("\n");
const fixture = (overrides = {}) => ({
  path: "docs/example.md",
  bytes: 20,
  sha256: "a".repeat(64),
  symlink: false,
  ...overrides,
});
const audit = (files, overrides = {}) =>
  auditInventory({ files, attributesText, ignoreText, policy, ...overrides });

test("current repository satisfies artifact policy", () => {
  const result = auditRepository(process.cwd());
  assert.deepEqual(result.errors, []);
  assert.equal(result.summary.heavyArtifactCount, 5);
  assert.equal(result.summary.legacyAllowlistCount, 5);
});

test("rejects generic tracked files over 1 MiB", () => {
  const result = audit([fixture({ bytes: 1_048_577 })]);
  assert.match(result.errors.join("\n"), /exceeds 1 MiB/u);
});

test("rejects evidence JSON over 50 KiB", () => {
  const result = audit([fixture({ path: "artifacts/example/verification.json", bytes: 51_201 })]);
  assert.match(result.errors.join("\n"), /Evidence JSON exceeds 50 KiB/u);
});

test("rejects golden file and aggregate budget violations", () => {
  const files = Array.from({ length: 26 }, (_, index) =>
    fixture({ path: `tests/golden/${index}.json`, bytes: 204_801, sha256: String(index).padStart(64, "0") }),
  );
  const result = audit(files);
  assert.match(result.errors.join("\n"), /Golden file exceeds 200 KiB/u);
  assert.match(result.errors.join("\n"), /Golden aggregate exceeds 5 MiB/u);
});

test("rejects a new tracked heavy artifact", () => {
  const result = audit([fixture({ path: "artifacts/new/model.step" })]);
  assert.match(result.errors.join("\n"), /not legacy-allowlisted/u);
});

test("rejects changed bytes for a legacy heavy artifact", () => {
  const entry = policy.legacyHeavyArtifactAllowlist[0];
  const result = audit([
    fixture({ path: entry.path, bytes: entry.bytes, sha256: "0".repeat(64) }),
  ]);
  assert.match(result.errors.join("\n"), /no longer matches its exact allowlist/u);
});

test("rejects missing attributes and ignore guards", () => {
  const result = audit([fixture()], { attributesText: "", ignoreText: "" });
  assert.match(result.errors.join("\n"), /Missing required \.gitattributes rule/u);
  assert.match(result.errors.join("\n"), /Missing required \.gitignore rule/u);
});

test("rejects tracked symlinks", () => {
  const result = audit([fixture({ symlink: true })]);
  assert.match(result.errors.join("\n"), /Tracked symlink/u);
});

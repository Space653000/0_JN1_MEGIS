// Secret scan for tracked files. Runs on every baseline CI push so a committed
// credential (API key, private key, token) fails the pipeline instead of leaking.
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = process.env.MEGIS_REPO_ROOT
  ? resolve(process.env.MEGIS_REPO_ROOT)
  : process.cwd();

const patterns = [
  { id: "private-key", re: /-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----/u },
  { id: "aws-access-key", re: /\bAKIA[0-9A-Z]{16}\b/u },
  { id: "github-token", re: /\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{36,}\b/u },
  { id: "github-pat", re: /\bgithub_pat_[A-Za-z0-9_]{30,}\b/u },
  { id: "slack-token", re: /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/u },
  { id: "google-api-key", re: /\bAIza[0-9A-Za-z_-]{35}\b/u },
];

// Exact allowlist for intentional fixtures only. A path must be listed before
// its scanner pattern is ignored; never disable a pattern globally.
const allowlist = [
  "tests/golden/",
  "docs/research/",
];

const isAllowed = (path) => allowlist.some((prefix) => path.startsWith(prefix));

const tracked = execFileSync("git", ["ls-files", "-z"], { cwd: repoRoot, encoding: "utf8" })
  .split("\0")
  .filter((path) => path.length > 0 && !isAllowed(path));

const findings = [];
for (const path of tracked) {
  const absolute = resolve(repoRoot, path);
  const source = readFileSync(absolute, "utf8");
  for (const { id, re } of patterns) {
    const match = source.match(re);
    if (match) findings.push({ path, pattern: id, line: 1 + source.slice(0, match.index).split("\n").length - 1, snippet: match[0].slice(0, 40) });
  }
}

if (findings.length > 0) {
  for (const finding of findings) {
    console.error(`Secret scan hit: ${finding.path}:${finding.line} [${finding.pattern}] near '${finding.snippet}...'`);
  }
  console.error(`Secret scan failed: ${findings.length} potential secret(s) in tracked files`);
  process.exit(1);
}

console.log(`Secret scan passed: ${tracked.length} tracked files scanned, 0 potential secrets`);

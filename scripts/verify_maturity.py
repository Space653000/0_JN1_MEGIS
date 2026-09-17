from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.governance.classification import render_issues, verify_repository_manifests  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify v3 classification and maturity rules for every manifest.json."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    scan_root = args.root.resolve()
    manifests, issues = verify_repository_manifests(scan_root)
    if issues:
        print(render_issues(issues, scan_root), file=sys.stderr)
        print(
            f"Manifest maturity scan failed: {len(issues)} issue(s) in {len(manifests)} manifest(s)",
            file=sys.stderr,
        )
        return 1
    print(f"Manifest maturity scan passed: {len(manifests)} manifest(s) verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

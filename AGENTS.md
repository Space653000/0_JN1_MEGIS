# MEGIS repository instructions

## Codex entry

Codex is the builder for implementation, edits, tests, and fixes. Before every construction task, read `.ai/CODEX_WORKER.md`, then `.ai/BLUEPRINT.md`, `.ai/ACCEPTANCE.md`, and `.ai/STATUS.md` in that order. Check the live execution control plane before choosing work; `.ai/STATUS.md` is a human-readable snapshot and may lag the queue. Claude Code owns blueprint planning, independent review, and acceptance support; the user retains final acceptance authority.

## Language

- User-facing text and reports use Traditional Chinese.
- Code, commands, schema identifiers, and engineering terms may remain in English.

## Workspace boundary

- All project writes, caches, temporary files, environments, downloads, test artifacts, and generated artifacts must stay under `C:\0_JN1_MEGIS`.
- Do not modify, link, share environments with, or depend on `C:\0_JN1_AERIS` or `C:\0_JN1_Offline-Local-Voice-Agent`.
- Do not create symlinks, junctions, shared virtual environments, or shared package stores outside this repository.
- Bind local services to `127.0.0.1` only. Do not add analytics, telemetry, external fonts, CDNs, or unapproved APIs.

## Workflow

- Follow Explore → Plan → Code → Commit.
- Run the relevant baseline before edits and verification after edits.
- Keep WIP to one vertical work item.
- Use concise English commit messages in `type: summary` format.
- After verified construction, update `.ai/STATUS.md`, commit, and push the current GitHub branch as the user directed on 2026-09-24. Verify the remote commit after push.
- Never force-push, delete remote data, change `main`, or publish a site without explicit user authorization for that action.

## UI-0 boundary

- UI-0 is an honest UX prototype, not the blueprint's G6 engineering capability.
- UI-0 may use only versioned `PrototypeViewModel` demo data through a replaceable adapter seam.
- Every simulated result must permanently display `Synthetic demo data` and `No engineering artifact generated`.
- UI-0 must not generate STEP, engineering drawings, release packages, or other artifacts that could be mistaken for engineering output.
- Real CAD, IR, validation, upload parsing, multi-user, cloud, and release behavior remain outside UI-0.


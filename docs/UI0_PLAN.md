# UI-0 Reconciled Implementation Plan

> 文件治理
> - 目的：保存 UI-0 經核准施工計畫。
> - 目前內容：UI-0A～D 路徑、驗收與誠實能力邊界。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## Decision

UI-0 is a complete, interactive, local-only UX prototype that the user can review before core engineering construction begins. It is not G6 and cannot claim engineering capability. Successful acceptance is recorded only as `UX PROTOTYPE ACCEPTED`.

## Fixed points

- Originating blueprint: `MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v2.0 Codex.md`
- Remote: `https://github.com/Space653000/0_JN1_MEGIS.git`
- Remote baseline: `main@2448b7ac7d1074fed9707884e9ab05a7a5a28eec`
- Deployment: local-only, bound to `127.0.0.1`
- Push policy: local commits only until the user explicitly authorizes push

## UI-0A minimal foundation

UI-0A is limited to Git bootstrap, a locked front-end toolchain, UI-0 progress-state data and schema, local verification scaffolding, and local run instructions. It does not complete G0 and must not start CadQuery, FreeCAD, COMSOL, core IR, rules, or geometry work.

## Sitemap and capability matrix

| Route | Purpose | UI-0 capability | Future gate |
|---|---|---|---|
| `/progress` | Gate, work item, evidence, blocker, and risk status | Real UI-0 repository state | G0 control-plane migration |
| `/design` | Guided Fixture / Enclosure configuration | Fully interactive prototype | G6 real UI-to-IR |
| `/review` | Facts, defaults, unknowns, and unsupported scope review | PrototypeViewModel only | G1/G6 |
| `/run` | Simulated job lifecycle and transparent limitations | Synthetic simulation only | G2–G6 |
| `/results` | CAD/DFM/BOM/package information architecture | Demo presentation; no engineering artifacts | G2–G6 |
| `/roadmap` | Acoustic and Robot visibility | Roadmap / unsupported only | G7/G8 |

Fixture / Enclosure is the only end-to-end interactive prototype. Authentication, cloud, multi-user, real upload/parsing, production release, Acoustic generation, and Robot generation are outside UI-0.

## Architecture

- React + TypeScript + Vite for the local working surface.
- Components depend on `PrototypeViewModel`, not Engineering IR.
- All demo data access goes through one adapter interface so later API replacement does not require rewriting route components.
- Construction progress has one source file with schema validation; route components do not duplicate status.
- No external runtime assets, fonts, scripts, analytics, telemetry, or APIs.

## Truthfulness rules

- Generate actions are labeled as prototype simulation.
- Demo values carry `user`, `demo-derived`, `demo-default`, or `unknown` provenance.
- Results permanently show `Synthetic demo data` and `No engineering artifact generated`.
- UI-0 does not create STEP, engineering PDF, or prototype packages.
- `done` progress items require an evidence path, verification result, and commit SHA. Broken evidence invalidates completion.

## Acceptance

- All sitemap routes render and the Fixture flow completes through the synthetic result screen.
- Loading, empty, error, and success states are represented where relevant.
- Keyboard-only navigation completes the primary flow with visible focus and no keyboard trap.
- Automated accessibility checks and manual focus/label review pass.
- Desktop and mobile visual evidence is captured; no unintended horizontal scrolling occurs.
- Browser console errors are zero during the acceptance flow.
- Normal use makes no external network request; server binds only to `127.0.0.1`.
- Progress schema, illegal transition, and broken-evidence tests pass.
- Adapter replacement tests prove route components are independent of the demo source.
- Lint, type-check, unit tests, browser tests, and production build pass.
- A non-CAD user usability review remains required before UI-0 can be marked accepted.

## Rollback boundaries

- UI-0A foundation is one commit.
- Each coherent UI slice is a separate local commit after verification.
- No destructive Git operation is used to reconcile local and remote history.
- G0 must migrate UI-0 progress state into the blueprint control plane with a migration test.

## Adversarial review disposition

All four blocking and all six high-severity findings were accepted. The plan now separates UI-0 from G6, adds UI-0A, fixes the Git and workspace boundaries, closes scope, isolates mock contracts, strengthens truthfulness and usability acceptance, defines progress-data integrity, and verifies local-only networking.

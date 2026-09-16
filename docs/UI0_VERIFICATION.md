# UI-0 Verification Report

## Automated verification

Verified on 2026-09-16 against local commit `cefb1a05b7c477a56c25c975951c9732bf70fb29`.

| Check | Result |
|---|---|
| ESLint | Passed |
| TypeScript type-check | Passed |
| Vitest | 6 / 6 passed |
| Production build | Passed |
| Progress-state valid source | Passed |
| Broken evidence rejection | Passed |
| Illegal status transition rejection | Passed |
| Adapter replacement seam | Passed |
| Prototype acknowledgement gate | Passed |
| Permanent synthetic-result warning | Passed |

## Browser verification

| Scenario | Result |
|---|---|
| Construction progress route responds | HTTP 200 |
| Guided Fixture flow reaches results | Passed |
| Generate remains disabled before acknowledgement | Passed |
| Critical unknown remains visible | Passed |
| Artifact download links | 0 |
| External resource elements | 0 |
| Browser console errors/warnings in clean flow | 0 |
| Desktop horizontal overflow | None |
| Mobile 390 px horizontal overflow | None |
| Mobile navigation affordance | Visible |

The initial development tab recorded one stale Vite HMR error while `App.tsx`
was replaced during authoring. A new clean browser session was created after the
build; the complete acceptance flow then produced zero console errors or
warnings.

## Truthfulness checks

- Results permanently display `NO ENGINEERING ARTIFACT GENERATED`.
- Geometry is labeled `SCHEMATIC — NOT CAD`.
- Demo values carry `user`, `demo-default`, or `unknown` provenance.
- STEP, Drawing PDF, BOM CSV, and release manifest downloads are unavailable.
- Acoustic and Robot are roadmap-only and labeled unsupported.

## Pending human acceptance

UI-0D remains `in_progress` until the user completes a non-CAD usability review
and explicitly accepts or requests changes. G0 must not start before that
decision.

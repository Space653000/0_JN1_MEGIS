# UI-0 Toolchain Feasibility Evidence

> 文件治理
> - 目的：記錄 UI-0 工具鏈 feasibility。
> - 目前內容：本機 Node、Vite、React 與瀏覽器可行性。
> - Owner：MEGIS Builder
> - 最後審查 commit：`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

## Baseline

- Host: Windows ARM64
- Node.js: 24.17.0
- npm: 11.13.0
- Git baseline: `2448b7ac7d1074fed9707884e9ab05a7a5a28eec`
- Local server bind: `127.0.0.1:4173`

## Sites starter decision

The bundled Vinext starter was evaluated first. Its dependency installation
failed because `workerd` does not support `win32 arm64 LE`. The failure log was
written to repository-local npm cache only.

Fallback: retain React, TypeScript, Vite, the local-only preview workflow, and
the requested acceptance surface while removing Cloudflare, Vinext, Wrangler,
and Workerd runtime dependencies. The fallback production build passed.

Unused starter files remain ignored and are not part of the UI-0 source or Git
commit. They were not recursively deleted because the environment rejected the
safe PowerShell deletion operation; this does not affect the build inputs.

## Verified commands

- `npm run lint`: passed
- `npm run typecheck`: passed
- `npm run build`: passed
- HTTP `GET /progress`: 200
- Mobile viewport: no horizontal overflow after correction
- Desktop viewport: no horizontal overflow
- Browser console warnings/errors: zero at the first meaningful preview

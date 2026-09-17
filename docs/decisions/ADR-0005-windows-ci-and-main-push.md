# ADR-0005：使用 Windows x64 CI 並允許驗證後推送 main

> 文件治理
> - 目的：記錄 D4 的 CI 平台與 push 授權範圍。
> - 目前內容：GitHub Actions Windows x64、main 同步與禁止 force 的決策。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D4
- 決策者：使用者
- 相關工作項目：V3C-DEC-001、G0-CI-001、V3C-DET-001、V3C-ART-001

## 背景

CadQuery/OCP 的現有支援基線是 Windows x64；本機 Windows ARM64 透過 x64 emulation 執行。使用者要求每個完成小段落同步到指定 GitHub `main`，並已持續明確授權 push。

## 決策

CI 使用 GitHub Actions `windows-latest`，工具鏈測試必須驗證 x64/AMD64 執行環境。Builder 可在本機驗證通過、先 fetch 並確認遠端沒有分歧後，推送到指定 repository 的 `main`。每次 push 後必須重新 fetch、核對本機/遠端 SHA，並等待同 SHA CI 終態。

禁止 force push、history rewrite、刪除遠端資料、推送到其他 repository，以及把 workflow credential 留給後續步驟。

## 考慮過的替代方案

1. 只保留本機：無異地 fixed point，也無獨立 CI 證據。
2. PR-only 流程：對目前 single-user 持續施工增加額外分支流程，使用者已選擇直接同步 main。
3. 驗證後推送 main 並禁止 force：符合目前授權與可追溯性，因此採用。

## 後果

- 推送授權只涵蓋目前明確指定的 GitHub repository。
- CI 綠燈不取代 fresh-session review 或 E4 sign-off。
- V3 新增的 fingerprint、maturity、size budget 與 secret scan 必須由後續工作補齊。

## 證據

- `.github/workflows/baseline-ci.yml`
- `AGENTS.md`
- `docs/decisions/ADR-0001-adopt-v3-blueprint.md`

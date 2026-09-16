# G0 Baseline CI

## 驗收範圍

`G0-CI-001` 建立一條 Windows x64 baseline，對本機與 GitHub Actions 使用相同的 `scripts/run-baseline-ci.ps1` 驗證入口。它涵蓋：

- 控制面 schema 與依賴關係
- Python dependency integrity 與鎖定 CAD toolchain smoke test
- Python unit tests
- STEP、STL、DXF、FCStd、SVG 與 COMSOL 決策證據的 artifact hash smoke test
- 前端 lint、typecheck、unit tests 與 production build

## 本機重跑

```powershell
cd C:\0_JN1_MEGIS
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

腳本把 TEMP、pip cache 與 npm cache 固定在 repository 內。它使用既有 `.venv` 與 `apps/web/node_modules`，不下載或啟動 FreeCAD，也不需要 COMSOL。

## GitHub Actions 邊界

`.github/workflows/baseline-ci.yml` 使用 `windows-latest`，精確鎖定 Python 3.11.9、Node.js 24.17.0、pip 26.2.1 與 npm 11.13.0。三個官方 setup actions 以不可變 commit SHA 固定，workflow 只有 `contents: read` 權限，checkout 不保留 credentials。

所有專案 dependency、cache、TEMP 與 npm CLI 都寫入 `${{ github.workspace }}` 內。FreeCAD runtime 不存在於 Git，CI 只驗證已版控 FCStd/SVG 及其 hashes；重新產生圖面仍由隔離的 FreeCAD spike 負責。

## 結果語意

CI 全綠只證明目前 baseline 可重跑與 versioned evidence 未漂移，不把 feasibility spike 升級成量產能力，也不代表 COMSOL、工程簽核或製造放行已完成。

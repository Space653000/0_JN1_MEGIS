# Artifact 儲存與 Git 大小預算政策

> 文件治理
> - 目的：說明 MEGIS tracked、golden、spike、Design Run 與 CI artifacts 的儲存界線。
> - 目前內容：Artifact policy 1.0.0、預算、Git attributes/ignore、白名單及驗證命令。
> - Owner：MEGIS Maintainer
> - 最後審查 commit：`ef486e000ce90b9e3ffcf519feb1b51f32106e57`

## 目的

MEGIS 將可稽核的小型文字證據版本化，但不把 Git 當作 CAD、Design Run 或 CI 重型製品儲存空間。政策同時避免 Windows/Linux checkout 改變 byte hash，並讓任何新增例外都需要 ADR 而非靜默放寬。

## 儲存矩陣

| 製品 | 位置 | Git tracked | 預算／保留 |
|---|---|---|---|
| Golden inputs/oracles | `tests/golden/`、既有 `contracts/g1/golden/` | 是 | 單檔 ≤ 200 KiB；合計 ≤ 5 MiB |
| Gate evidence JSON | `artifacts/<item>/*.json` | 是 | 單檔 ≤ 50 KiB |
| Spike 重型製品 | `artifacts/<item>/` | 新增禁止 | 由命令重生；五個歷史例外見 ADR-0011 |
| Design Run | `.runs/` | 否 | 90 天或 hold；清理器尚未實作 |
| CI artifact | GitHub Actions artifact storage | 否 | 目標保留 30 天；上傳流程尚未實作 |
| 其他 tracked file | repository | 是 | 單檔 ≤ 1 MiB；例外必須有精確 hash + ADR |

KiB/MiB 採二進位單位：1 KiB = 1,024 bytes，1 MiB = 1,048,576 bytes。

## Checkout 規則

`.gitattributes` 讓一般文字以 LF 儲存與 checkout。STEP、STP、STL、FCStd、GLB、glTF、PDF，以及 `artifacts/` 下需要 byte-stable 的 DXF/SVG 使用 `binary`，禁止 Git 行尾正規化。`.gitignore` 阻止新的 spike 重型製品與 `.runs/` 進入 Git；已追蹤的五個 G0 歷史檔不因 ignore 規則消失。

## 自動驗證

```powershell
node scripts/verify-artifact-policy.mjs
node --test tests/test_artifact_policy.mjs
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

`scripts/verify-control-plane.mjs` 也直接執行同一個 audit module，檢查所有 `git ls-files`：tracked symlink、通用 1 MiB 上限、evidence/golden 預算、重型製品精確白名單，以及必要 attributes/ignore rules。負向測試覆蓋每一種主要失敗模式。

## 能力邊界

政策只治理 repository storage 與 checkout；它不證明 artifact 工程正確、可製造、安全或具成熟度。Design Run retention 自動清理、CI artifact 上傳與 LFS/外部 object storage 都尚未實作。若未來單一 golden 必須超過預算，需先新增 ADR、評估 Git LFS 或可重建替代方案，並升級 policy version。

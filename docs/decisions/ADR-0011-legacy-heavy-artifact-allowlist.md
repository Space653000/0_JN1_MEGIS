# ADR-0011：既有 G0 重型製品採精確白名單，後續 spike 製品禁止入 Git

> 文件治理
> - 目的：記錄 V3 §5.9 導入時既有重型製品的不可變白名單與新增禁制。
> - 目前內容：五個 G0 製品的 path、bytes、SHA-256 白名單及後續儲存政策。
> - Owner：MEGIS Maintainer
> - 最後審查 commit：`ef486e000ce90b9e3ffcf519feb1b51f32106e57`

- 狀態：accepted
- 日期：2026-09-17
- 決策者：V3 §5.9 migration policy，由 MEGIS Builder 依 tracked inventory 落實
- 相關工作項目：V3C-ART-001、G0-CI-001、G5-PKG-001

## 背景

V3 §5.9 要求 spike 重型製品不追蹤於 Git，改由命令重生；同時明確禁止為了導入政策而改寫既有 Git history。V3 導入前，G0 已追蹤 STEP、STL、DXF、FCStd 與 fallback SVG 共五個製品，並由既有 artifact smoke 與 fingerprint 證據引用。直接刪除會破壞既有 Gate 的可追溯性，繼續允許任意重型製品入庫則會造成 repository 膨脹。

## 決策

保留五個既有 G0 重型製品，但以 `config/artifact-policy/policy-1.0.0.json` 記錄精確 path、byte count、SHA-256 與本 ADR。任一 path、bytes 或 hash 變化都視為白名單失配並使 CI 失敗；變更必須透過新 ADR 與政策版本，不得靜默更新 hash。

`.gitignore` 阻止 `artifacts/` 下後續新增 STEP、STP、STL、DXF、FCStd、SVG、GLB、glTF、PDF；`.gitattributes` 將工程二進位與需要 byte-stable 的 artifact DXF/SVG 標成 `binary`，其他文字固定 LF。新的長期 regression oracle 如確實需要版本化，必須放入 golden 目錄並受單檔 200 KiB、總量 5 MiB 預算；不能藉白名單規避。

## 精確白名單

| Path | Bytes | SHA-256 |
|---|---:|---|
| `artifacts/g0-cad/reference_case.step` | 48,798 | `62a380d7de5f92d59bfc4a82e24c79938c1d226669aa80c40ebb92829521c0ca` |
| `artifacts/g0-cad/reference_case.stl` | 103,084 | `e3bdc5a7c73439cde8ddf102d4399631eb0f643079bb375b088fc04ffaa89caa` |
| `artifacts/g0-cad/reference_case_section_z10.dxf` | 16,221 | `b3b5a988d77c9227220dbc2e2ef996f826e0a2223f6f95aa0b129da216b6b8e4` |
| `artifacts/g0-freecad/reference_case_techdraw.FCStd` | 12,824 | `fa65bb0d9e15f7d5d6f81dc84e30f05f18a9b5498ddbe686b338f1629fc81b2c` |
| `artifacts/g0-freecad/reference_case_techdraw_fallback.svg` | 2,541 | `b6d413b720f66e578ec559322323f04381f4203c8eb1fe002ff0e1bb2731c05e` |

## 考慮過的替代方案

1. 刪除既有二進位並改寫 history：破壞已 accepted Gate 證據且違反 V3 migration rule，拒絕。
2. 只設 1 MiB 通用上限：這五個檔案雖未超限，仍會讓大量小型 binary 不受控累積，拒絕。
3. 允許 glob 白名單：無法偵測新增或替換，拒絕。
4. 精確白名單 + 新增禁制 + golden 預算：保留歷史、阻止膨脹並可由 CI 驗證，採用。

## 後果

- G0 生成器仍可在本機重建製品，但若 bytes 改變，必須先處理 deterministic regression 或建立新 ADR，不可直接更新白名單。
- Git 不再是 Design Run 或 CI 重型 artifact storage；Design Run 使用 `.runs/`，CI 產物使用有期限的 CI artifact storage。
- 本 ADR 不表示五個 spike 製品具有工程 maturity；它們仍是 `FEASIBILITY_SPIKE` 或相應的 G0 evidence。
- 未來需要加入例外時，必須更新 machine policy、schema、tests、文件與 ADR，並達 E3。

## 證據

- `config/artifact-policy/policy-1.0.0.json`
- `scripts/verify-artifact-policy.mjs`
- `tests/test_artifact_policy.mjs`
- `artifacts/v3c-art-001/verification.json`
- `MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md` §5.8、§5.9

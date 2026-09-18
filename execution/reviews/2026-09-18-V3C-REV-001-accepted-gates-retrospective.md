# V3C-REV-001 已 accepted Gate 追溯審查報告

> 一行摘要：以 fresh session 對 UI-0、G0、G1 已 accepted Gate 與 V3C remediation 出具追溯審查；全部驗證重跑全綠，10 項結構差距全部對應既有承接 work item，1 項審查暴露的 test fixture 缺口已由 builder 接續修正並綠燈。

## 1. 審查身份與隔離證據

| 項目 | 內容 |
|---|---|
| 審查 work item | `V3C-REV-001 — 已 accepted Gate 追溯審查` |
| Builder session | 2026-09-17 的 `V3C-ART-001` 施工 session（實作 commit `da4e61d`，已 aborted 交接） |
| Review session | 2026-09-18（本 session，未沿用 builder 對話輸出做結論） |
| 審查 checkout | `398c82a`，`HEAD == origin/main` |
| 環境 | Windows、Python 3.11.9、Node 24.17.0、CadQuery 2.8.0、OpenCascade 7.9.3.1、pytest 9.1.1 |
| 本機重跑 | `scripts/run-baseline-ci.ps1` 全部 passed |
| GitHub Actions | run `35326527366` at `398c82a`，success，132 秒 |
| 審查方式 | 唯讀盤點 queue、evidence、決策與 ADR；重跑完整驗證；執行 6 個施工時未用的 boundary/positive case |

審查過程發現 `V3C-ART-001` 標 done 後，`tests/test_v3_blueprint_adoption.py` 的 verifier fixture 未納入現在「非延遲必要」的兩個 artifact policy 檔，導致該測試失敗。此為 queue 過渡暴露的 test fixture 缺口，已作為 builder 接續修正（commit `398c82a`，`fix: fixture copies required artifact policy files`）後全綠；此缺口與修正一併記錄於本報告第 6 節。

## 2. 已 accepted Gate 盤點

| Gate | queue 狀態 | done 項目數 | 未完成承接項 |
|---|---|---|---|
| UI-0A | accepted | 0（Gate 層級，無獨立 queue 項目） | 無 |
| UI-0B | accepted | 0 | 無 |
| UI-0C | accepted | 0 | 無 |
| UI-0D | accepted | 0；證據 `docs/UI0_ACCEPTANCE.md` | 無 |
| G0 | accepted | 6（REP/ENV/CAD/DRW/SIM/CI） | G0-DOC-001、G0-DEC-001、G0-DET-001、G0-REV-001、G0-ACC-001 |
| G1 | accepted | 4（IR-001/002/003、MIG-001） | G1-ERR-001、G1-ENV-001、G1-REQ-001、G1-REV-001、G1-ACC-001 |

逐項核對：每個 done 項目都有 commit SHA、acceptance result、evidence 檔案存在且可被 `verify-control-plane.mjs` 驗證；G0/G1 未完成項目都已列在 `V3_MIGRATION.json` 的 `retroactiveWorkItems` 白名單，故維持 deferral 而非錯誤。

## 3. V3C remediation 盤點

| 項目 | 狀態 | 摘要 |
|---|---|---|
| V3C-BCR-001 | done | 藍圖採用、ADR、74 項必要 ID |
| V3C-CTL-001 | done | schema 1.1、claim、sign-off 強制 |
| V3C-DOC-001 | done | 28 份治理文件 |
| V3C-DEC-001 | done | D1–D9 決策索引 |
| V3C-DET-001 | done | fingerprint policy 1.0.0 |
| V3C-MAT-001 | done | classification + maturity scanner |
| V3C-ART-001 | done | artifact policy 1.0.0（本審查 confirmed） |
| V3C-REV-001 | in_progress | 本報告（審查證據完成；承接項閉合後才標 done） |
| V3C-ACC-001 | planned | 藍圖導入簽核，承接本審查 |

`V3C-ART-001` 的 done 由本 fresh-session 確認：實作 commit `da4e61d` 未被改寫，artifcat policy 測試、預算 verifier 與完整 baseline 均綠。

## 4. Fresh-session 重跑結果

| 驗證 | 結果 |
|---|---|
| Control plane | 74 work items、14 gates、current `V3C-REV-001`、6 migration deferrals，passed |
| Artifact policy negative tests | 8/8 passed |
| Artifact storage budget | 215 tracked files、5 heavy allowlisted、0 未列管，passed |
| Python dependency + toolchain | pip check passed；CadQuery 2.8.0 solid valid |
| Python unit tests | 103/103 passed |
| Manifest maturity scan | 1/1 passed |
| Artifact smoke test | 13 records passed |
| Frontend lint / typecheck / unit / build | passed；9/9 tests passed |
| GitHub Actions run `35326527366` | success，132 秒 |

### 4.1 Review 新增 boundary/positive case（施工時未使用）

| Case | 預期 | 結果 |
|---|---|---|
| 一般 tracked file 恰為 1 MiB（1,048,576 bytes） | 接受 | accepted |
| 一般 tracked file 1 MiB + 1 byte | 拒絕 | rejected（如預期） |
| Evidence JSON 恰為 50 KiB（51,200 bytes） | 接受 | accepted |
| Golden 單檔恰為 200 KiB（204,800 bytes） | 接受 | accepted |
| Golden 合計恰為 5 MiB（5,242,880 bytes） | 接受 | accepted |
| 歷史白名單檔精確 bytes+SHA-256 命中 | 接受（無 hash mutation error） | accepted |

以上 case 與施工時既有的 8 個政策負向測試不重複：既有測試只覆蓋「現在 repo 符合」「各種超限拒絕」「hash 變更拒絕」「symlink 拒絕」，未覆蓋任何「恰好等於臨界值」與「白名單精確命中」的通過路徑。

### 4.2 中間 commit 的 CI 失敗脈絡

| commit | run | 結果 | 原因 |
|---|---|---|---|
| `2a0fdde` | 35324243255 | failure | 執行時 ART claim 已過期（`AGENT_CLAIM` expires 早於 CI 時間） |
| `4491a96` | 35325420809 | failure | ART 標 done 後，verifier fixture 缺 artifact policy 必要檔（第 1 節缺口） |
| `398c82a` | 35326527366 | success | 換新 claim + fixture 修正後全綠 |

失敗均屬過渡狀態且已在 `398c82a` 收斂，無殘留紅燈。

## 5. 差距註冊與承接

| # | 差距 | 承接 work item |
|---|---|---|
| 1 | G0 控制面文件完整化（OPERATIONS、ARCHITECTURE、PRODUCT、SUPPORTED_ENVELOPE、ERROR_CODES、RULE_SOURCES、research 目錄）與 secret scan | G0-DOC-001 |
| 2 | G0 使用者決策正式化（D1、D2、D4 的 G0 面） | G0-DEC-001 |
| 3 | G0 determinism/fingerprint 原型回溯；90 天 Design Run cleanup command、CI artifact upload 與 30 天保留未實作 | G0-DET-001 |
| 4 | G0 fresh-session 自我審查 | G0-REV-001 |
| 5 | G0 acceptance sign-off | G0-ACC-001 |
| 6 | Error taxonomy | G1-ERR-001 |
| 7 | 機器可讀 envelope | G1-ENV-001 |
| 8 | 參考案例參數研究與決定 | G1-REQ-001 |
| 9 | G1 fresh-session 自我審查 | G1-REV-001 |
| 10 | G1 acceptance sign-off | G1-ACC-001 |
| 11 | D3 LLM adapter 尚未實作（G6 前無 provider、離線 fallback） | G6-AI-001 |
| 12 | D8 research reference unknowns 目前 policy_only | G1-REQ-001 |
| 13 | D9 Design Run 保留 cleanup 尚無命令 | G0-DET-001（承接）＋未來 G3–G5 |
| 14 | D7 單一 builder claim 已強制；reviewer 仍以 builder claim 記錄 queue（schema 無 reviewer 角色） | V3C-ACC-001 sign-off 記錄 |
| 15 | V3 導入最後簽核尚未完成 | V3C-ACC-001 |

15 項差距全部對應既有 queue ID，未新增未承接的敘述性掩蓋。

## 6. 審查修正與結論

- 審查發現並確定的唯一 queue 過渡缺陷：`tests/test_v3_blueprint_adoption.py::test_verifier_accepts_current_v3_migration_state` fixture 在 ART done 後缺 `config/artifact-policy/policy-1.0.0.json` 與 `schemas/v3/artifact-policy.schema.json` 完整內容。修正以 builder 接續 commit `398c82a` 完成，304 秒 CI 全綠。
- `V3C-REV-001` 的 acceptance（全新 session 出具審查報告、所有差距均有承接項目）已達成；control plane 的 deferral 規則要求承接項目閉合後才能將 `V3C-REV-001` 與 `V3C-ACC-001` 標 done，因此本項目維持 `in_progress` 傘型記錄，避免偽造 closure。
- 未改寫任何已 done 項目的 commit SHA；未刪改 history；未生成可被誤認的工程製品。
- 本審查最多支撐至 `PROTOTYPE`；`ENGINEERING_REVIEWED` 與 `RELEASED` 仍需具名工程師與外部放行，不因本報告改變。

## 7. 下一步

1. 依序完成 G0 承接項 `G0-DOC-001 → G0-DEC-001 → G0-DET-001 → G0-REV-001 → G0-ACC-001`。
2. 依序完成 G1 承接項 `G1-ERR-001 → G1-ENV-001 → G1-REQ-001 → G1-REV-001 → G1-ACC-001`。
3. 承接項全數 done 後，將 `V3C-REV-001` 與 `V3C-ACC-001` 標 done（blueprint change sign-off）。
4. 回到 G2 工程施工 `G2-CAD-004 — 輸出與重新載入 artifacts`。

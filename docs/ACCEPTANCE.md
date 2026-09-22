# Gate 驗收索引

> 文件治理
> - 目的：集中索引 Gate、commit、review、CI 與 sign-off。
> - 目前內容：UX-0／G0～G5 驗收基線與 V3C 追溯審查結果；G5 以 `SO-0006`（E4）accepted、G6 active；G6-UI-001（`7870b41`）、G6-QST-001（`9c1c671`）、G6-AI-001～004 已閉合（E3），G6-A11Y-001 in_progress。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：`d27d16e17ed81eb0fb8ac4e8b0be83891df14d82`

## 目前內容

| Gate | 既有狀態 | 基線證據 | V3 追溯狀態 |
|---|---|---|---|
| UI-0A | accepted | `docs/UI0_ACCEPTANCE.md` | review：`V3C-REV-001`（2026-09-18，passed）；sign-off：`V3C-ACC-001`（2026-09-21，closed） |
| UI-0B | accepted | `docs/UI0_ACCEPTANCE.md` | review：`V3C-REV-001`（2026-09-18，passed）；sign-off：`V3C-ACC-001`（2026-09-21，closed） |
| UI-0C | accepted | `docs/UI0_ACCEPTANCE.md` | review：`V3C-REV-001`（2026-09-18，passed）；sign-off：`V3C-ACC-001`（2026-09-21，closed） |
| UI-0D | accepted | `docs/UI0_ACCEPTANCE.md` | review：`V3C-REV-001`（2026-09-18，passed）；sign-off：`V3C-ACC-001`（2026-09-21，closed） |
| G0 | accepted | `docs/G0_BASELINE_CI.md` 與 G0 evidence | review：`V3C-REV-001`（passed）；簽核 `SO-0001`（2026-09-19） |
| G1 | accepted | G1 contract、golden、migration evidence | review：`G1-REV-001`（2026-09-21，54 tests passed）；簽核 `SO-0002`（2026-09-21） |
| G2 | accepted | G2-CAD-001～004、G2-NEG-001、G2-REV-001、G2-ACC-001 已完成 | review：`G2-REV-001`（2026-09-21，乾淨 checkout 92 tests + 4 script 全綠）；簽核 `SO-0003`（2026-09-21，E4 gate_acceptance） |
| G3 | accepted | G3-RUL-001～G3-ACC-001 全數閉合；`G4` active | 規則／驗證 gate 全數閉合；`G3-ACC-001` gate acceptance 已簽核（`SO-0004`，E4，2026-09-22），G4 — 模組與限制條件組合 已啟動 |
| G4 | accepted | G4-MOD-001～G4-ACC-001 全數閉合（G4-REV-001 @ `eef0afc`，E3；G4-ACC-001 `SO-0005`，E4） | G4 gate_acceptance 已簽核，G5 — 原型套件與可重現性 已啟動 |
| G5 | accepted | G5-PKG-001～G5-ACC-001 全數閉合（G5-REV-001 @ `51259f6`，E3；G5-ACC-001 `SO-0006`，E4） | G5 gate_acceptance 已簽核，G6 — 引導式介面工程整合 已啟動 |
| G6 | active | G6-UI-001（`7870b41`）、G6-QST-001（`9c1c671`）、G6-AI-001（`5d890be`）、G6-AI-002（`6694507`）、G6-AI-003（`555d10c`）、G6-AI-004（`d27d16e`）已閉合（E3） | G6-A11Y-001 自動化已通過（`cf91984`），真人鍵盤／螢幕閱讀器抽查 pending；G6 尚未 Gate acceptance |

審查證據：`execution/reviews/2026-09-18-V3C-REV-001-accepted-gates-retrospective.md`、`execution/reviews/2026-09-21-G1-REV-001-review.md` 與 `execution/reviews/2026-09-21-G2-REV-001-review.md`。
CI 證據：GitHub Actions run `35326527366`（`398c82a`）與 run `35327571839`（`4fa15e2`）皆 green；G2 另以本機 baseline-ci（147 Python + 9 Frontend）與乾淨 checkout（92 G1+G2 tests + 4 個 G2 驗證腳本）全綠佐證。

V3C 追溯（`V3C-REV-001`／`V3C-ACC-001`）已於 2026-09-21 閉合；G1 以 `SO-0002`、G2 以 `SO-0003` 完成新式 E4 簽核。

## Holdout 封存（§18.1）

依藍圖 §18.1 的「先封存、後施工」：G3-BEN-001 的 holdout oracle 於本 commit（`contracts/g3/holdout/holdout-corpus.json`，corpus_version 1）獨立封存，禁止在基準 metrics 實作後修改；修改 oracle 視同 golden 更新，需 ADR。

- Holdout oracle SHA-256：`73a25950c4b45d904daa6bab963a16ae11599f6bfa660966582ba0d60ed5a96b`
- Holdout 規模：10 cases（7 defect、3 clean）；corpus_id `benchmark-g3-holdout@1.0.0`
- 封存時間：2026-09-22T12:00:00+08:00；此做法無法完全排除施工者偏誤，列為 `R-AGT-002`
- 閉合核對（2026-09-22T13:00:00+08:00）：benchmark metrics 實作後以 `scripts/verify_g3_ben_001.py` 重跑，holdout SHA-256 仍為封存值且 10/10 cases passed、FP 0、false release 0，`R-AGT-002` 已解除。
- 自我審查（2026-09-22T14:00:00+08:00）：G3-REV-001 以乾淨 clone 重跑 G3 全部驗證 passed（159 tests + 6 支驗證腳本 95 checks），審查報告 `execution/reviews/2026-09-22-G3-REV-001-review.md`。
- Gate acceptance（2026-09-22T14:30:00+08:00）：G3 以 `SO-0004`（E4 gate_acceptance）簽核，`artifacts/g3-acc-001/verification.json` 可追溯至 G3 審查與 CI；G4 gate 轉 active，`G4-MOD-001` 施工開始。
- V3.0 盤點（2026-09-22，G6-QST-001 閉合）：G6-UI-001 capability-driven guided flow 已閉合（E3，`7870b41`，`artifacts/g6-ui-001/verification.json`）；G6-QST-001 question ordering 與 abstention 已閉合（E3，`9c1c671`，`artifacts/g6-qst-001/verification.json`；18 corpus cases、523 Python + 12 Frontend 全綠）；G6 active，`G6-AI-001`（AI provider adapter 與離線 fallback）in_progress。
- V3.0 盤點（2026-09-22，G6-AI-001 閉合）：optional provider adapter 預設關閉；recorded local stub、timeout／呼叫／token／成本限制、MEGIS-AI fallback 與 versioned audit 皆通過（E3，`5d890be`，`artifacts/g6-ai-001/verification.json`；9 checks、540 Python + 12 Frontend 全綠）；無外部 provider 呼叫、無工程製品；`G6-AI-002` in_progress。
- V3.0 盤點（2026-09-22，G6-AI-002 閉合）：AI Requirement draft 以 JSON Schema、intent SHA-256、exact evidence span 與 `llm_proposed` quarantine 約束；schema-invalid／無根據數值拒收為 `MEGIS-AI-002`，未確認值不進 confirmed IR（E3，`6694507`，`artifacts/g6-ai-002/verification.json`；3 recorded fixtures、7 checks、558 Python + 12 Frontend 全綠）；`G6-AI-003` in_progress。
- V3.0 盤點（2026-09-22，G6-AI-003 閉合）：54 筆六類平衡 intent corpus 與 case-level KPI report 通過（E3，`555d10c`，`artifacts/g6-ai-003/verification.json`；9 checks、unsafe hallucination 0/41、injection resistance 9/9、570 Python + 12 Frontend 全綠）；explanation grounding 不在本工項虛報，明確 deferred 至 `G6-AI-004`（in_progress）。
- V3.0 盤點（2026-09-22，G6-AI-004 閉合）：grounded explanation 將全部數值 token 綁定來源 SHA-256 與 JSON Pointer，只接受 IR／rule result／manifest；漏引、錯值、錯 pointer 與來源竄改 fail closed（E3，`d27d16e`，`artifacts/g6-ai-004/verification.json`；8 checks、4/4 example numbers grounded、15 tests、585 Python + 12 Frontend 全綠）；`G6-A11Y-001` in_progress。
- V3.0 盤點（2026-09-22，G6-A11Y-001 自動化段）：axe-core 以 WCAG 2.2 A／AA tags 掃描五路由為 0 violations；8 組核心 palette 對比、skip link、route focus、行動選單焦點循環與 ARIA state 共 9 tests 全綠（`cf91984`，`artifacts/g6-a11y-001/verification.json`；585 Python + 21 Frontend 全綠）。真人鍵盤與螢幕閱讀器抽查尚無具名紀錄，因此工項維持 in_progress、`closureEligible: false`。

## Owner

MEGIS Builder；使用者保有否決權。

## 最後審查 commit

`d27d16e17ed81eb0fb8ac4e8b0be83891df14d82`

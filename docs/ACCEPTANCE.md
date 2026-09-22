# Gate 驗收索引

> 文件治理
> - 目的：集中索引 Gate、commit、review、CI 與 sign-off。
> - 目前內容：UX-0／G0／G1／G2 驗收基線與 V3C 追溯審查結果（2026-09-21）。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：`127ff0789e68b182fc269dd9b209efc8d76a8cb4`

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
| G3 | active | G3-RUL-001、G3-SRC-001、G3-VAL-001、G3-VAL-002、G3-MAT-001 已閉合；G3-BEN-001 施工中 | 規則／驗證 gate：`rule schema / governance / waiver`、來源登錄、geometry/collision/clearance validators、CNC DFM rule pack 與 maturity evaluator 已閉合，`G3-BEN-001` benchmark metrics 進行中 |

審查證據：`execution/reviews/2026-09-18-V3C-REV-001-accepted-gates-retrospective.md`、`execution/reviews/2026-09-21-G1-REV-001-review.md` 與 `execution/reviews/2026-09-21-G2-REV-001-review.md`。
CI 證據：GitHub Actions run `35326527366`（`398c82a`）與 run `35327571839`（`4fa15e2`）皆 green；G2 另以本機 baseline-ci（147 Python + 9 Frontend）與乾淨 checkout（92 G1+G2 tests + 4 個 G2 驗證腳本）全綠佐證。

V3C 追溯（`V3C-REV-001`／`V3C-ACC-001`）已於 2026-09-21 閉合；G1 以 `SO-0002`、G2 以 `SO-0003` 完成新式 E4 簽核。

## Holdout 封存（§18.1）

依藍圖 §18.1 的「先封存、後施工」：G3-BEN-001 的 holdout oracle 於本 commit（`contracts/g3/holdout/holdout-corpus.json`，corpus_version 1）獨立封存，禁止在基準 metrics 實作後修改；修改 oracle 視同 golden 更新，需 ADR。

- Holdout oracle SHA-256：`73a25950c4b45d904daa6bab963a16ae11599f6bfa660966582ba0d60ed5a96b`
- Holdout 規模：10 cases（7 defect、3 clean）；corpus_id `benchmark-g3-holdout@1.0.0`
- 封存時間：2026-09-22T12:00:00+08:00；此做法無法完全排除施工者偏誤，列為 `R-AGT-002`

## Owner

MEGIS Builder；使用者保有否決權。

## 最後審查 commit

`43f2e0f32a695c61c76efd39a2c02bddd572fab8`

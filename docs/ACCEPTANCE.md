# Gate 驗收索引

> 文件治理
> - 目的：集中索引 Gate、commit、review、CI 與 sign-off。
> - 目前內容：UX-0／G0／G1 驗收基線與 V3C 追溯審查結果（2026-09-18）。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：`4fa15e27011759b6b29df9a3d97fb095162e7c0c`

## 目前內容

| Gate | 既有狀態 | 基線證據 | V3 追溯狀態 |
|---|---|---|---|
| UI-0A～UI-0D | accepted | `docs/UI0_ACCEPTANCE.md` | review：`V3C-REV-001`（2026-09-18，passed）；sign-off 待 `V3C-ACC-001` |
| G0 | accepted | `docs/G0_BASELINE_CI.md` 與 G0 evidence | review：`V3C-REV-001`（passed）；承接 `G0-DOC-001`→`G0-ACC-001` 閉合中 |
| G1 | accepted | G1 contract、golden、migration evidence | review：`V3C-REV-001`（passed）；承接 `G1-ERR-001`→`G1-ACC-001` 閉合中 |
| G2 | active | G2-CAD-001～003 已完成 | V3C 完成前不可 accepted |

審查證據：`execution/reviews/2026-09-18-V3C-REV-001-accepted-gates-retrospective.md`。
CI 證據：GitHub Actions run `35326527366`（`398c82a`）與 run `35327571839`（`4fa15e2`）皆 green。

目前不存在 V3 Gate acceptance sign-off（`V3C-ACC-001` 未完成）；本表不得被解讀為已完成新式 E4 簽核。

## Owner

MEGIS Builder；使用者保有否決權。

## 最後審查 commit

`4fa15e27011759b6b29df9a3d97fb095162e7c0c`

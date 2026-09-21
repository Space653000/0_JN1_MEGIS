# 規則來源登錄表

> 文件治理
> - 目的：追蹤工程規則來源、型別、狀態、版次、owner、URL、取用日期與複查期限。
> - 目前內容：G3-SRC-001 機器登錄（`config/rule-sources/sources.yaml`）的人工可讀對映（2026-09-21）。
> - Owner：MEGIS Builder；使用者可否決來源決策
> - 最後審查 commit：`162d09d95df517c5123e4f7916ff19a0e2cfb087`

## 目的

Repository 只保存參數、條號與原創摘要，不保存受著作權保護的標準原文或整表。來源未核准（或在 `needs_review`／`draft`）時，規則不得設為 `approved`；來源核准必須附 URL 與取用日期。機器登錄檔 `config/rule-sources/sources.yaml` 為唯一事實來源（schema：`schemas/v3/rule-source.schema.json`），本表為其人工可讀對映。

## 目前內容

| 來源 ID | 型別 | 狀態 | 版次 | Owner | 複查期限 |
|---|---|---|---|---|---|
| SRC-ISO-2768-1 | standard | needs_review | 2026-A | mechanical_engineering | 2026-12-31 |
| SRC-ISO-273 | standard | needs_review | 2026-A | mechanical_engineering | 2026-12-31 |
| SRC-ISO-261-262 | standard | needs_review | 2026-A | mechanical_engineering | 2026-12-31 |
| SRC-ISO-4762 | standard | needs_review | 2026-A | mechanical_engineering | 2026-12-31 |
| SRC-USB-TYPEC | datasheet | needs_review | 2026-A | mechanical_engineering | 2026-12-31 |
| SRC-IPC-2221 | standard | needs_review | 2026-A | mechanical_engineering | 2026-12-31 |
| SRC-INTERNAL-ME-001 | internal | draft | 2026-A | mechanical_engineering | 2026-12-31 |
| SRC-CNC-DFM-001 | internal | draft | 2026-A | mechanical_engineering | 2026-12-31 |

註：`contracts/g3/golden/rule-governance.json` 內的 `sourceStatus` 屬 schema／生命週期測試用 fixture，不等於實際來源核准；實際核准以 `config/rule-sources/sources.yaml` 為準。

## 來源過期與 needs_review

`approved` 來源的 `review_due` 一旦通過（`at > review_due`），機器登錄自動視為 `needs_review`，該來源將無法再支撐核准規則；受影響 Design Run 不得以此來源的規則作為 `approved` 評估依據。`draft`／`needs_review`／`retired` 來源皆不可被核准。

## Owner

MEGIS Builder；使用者可否決來源決策。

## 最後審查 commit

`162d09d95df517c5123e4f7916ff19a0e2cfb087`

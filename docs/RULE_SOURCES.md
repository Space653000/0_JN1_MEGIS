# 規則來源登錄表

> 文件治理
> - 目的：追蹤工程規則來源、版次、授權、owner 與複查日期。
> - 目前內容：V3 來源 ID 的待查核骨架；尚無 approved 規則來源。
> - Owner：MEGIS Builder
> - 最後審查 commit：`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

## 目的

Repository 只保存參數、條號與原創摘要，不保存受著作權保護的標準原文或整表。查證前不得把規則設為 `approved`。

## 目前內容

| 來源 ID | 類型 | 狀態 | 版次／取得方式 | Owner | 下次審查 |
|---|---|---|---|---|---|
| SRC-ISO-2768-1 | 一般公差 | needs_review | 待 G3 公開查證 | Builder | G3-SRC-001 |
| SRC-ISO-273 | 緊固件通孔 | needs_review | 待 G3 公開查證 | Builder | G3-SRC-001 |
| SRC-ISO-261-262 | 公制螺紋 | needs_review | 待 G3 公開查證 | Builder | G3-SRC-001 |
| SRC-ISO-4762 | 內六角圓柱頭螺絲 | needs_review | 待 G3 公開查證 | Builder | G3-SRC-001 |
| SRC-USB-TYPEC | USB Type-C | needs_review | 優先實際零件 datasheet | Builder | G1-REQ-001 |
| SRC-IPC-2221 | PCB 通則 | needs_review | 只作 warning／info | Builder | G3-SRC-001 |
| SRC-INTERNAL-ME-001 | 內部機構準則 | draft | 必須附公開依據 | Builder | G3-SRC-001 |

所有 URL、取用日期與研究比較存於 `docs/research/`；目前沒有來源可支撐 `approved` 規則。

## Owner

MEGIS Builder；使用者可否決來源決策。

## 最後審查 commit

`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`


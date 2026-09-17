# 錯誤碼登錄表

> 文件治理
> - 目的：提供 `MEGIS-<DOMAIN>-NNN` 錯誤碼的唯一登錄入口。
> - 目前內容：V3 taxonomy 規則、domain 保留範圍與 legacy 缺口。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 目的

錯誤必須具有穩定 code、message、domain、severity、retryable、context 與 cause chain；UI 只翻譯顯示，不以字串猜測類型。

## 目前內容

| Domain | 範圍 | 狀態 |
|---|---|---|
| CTL | 控制面、claim、Gate 狀態 | reserved |
| IR | schema、reference、unit、migration | reserved |
| GEO | geometry planning、kernel、timeout | reserved |
| IMP | 不可信 STEP／DXF import | reserved |
| RUL | rule evaluation／source | reserved |
| PKG | package、manifest、BOM、drawing | reserved |
| AI | provider、schema output、grounding | reserved |

現有 `GeometryErrorCode` 仍是 v2 legacy enum，尚未符合 V3 prefix；`G1-ERR-001` 負責建立正式 schema、唯一性測試與映射。此處不提前宣稱任何 V3 code 已核准。

## Owner

MEGIS Builder；新增 code 必須同時新增測試與本表紀錄。

## 最後審查 commit

`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

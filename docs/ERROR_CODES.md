# 錯誤碼登錄表

> 文件治理
> - 目的：提供 `MEGIS-<DOMAIN>-NNN` 錯誤碼的唯一登錄入口。
> - 目前內容：V3 已核准錯誤碼登錄與 v2 legacy 映射。
> - Owner：MEGIS Builder
> - 最後審查 commit：`162d09d95df517c5123e4f7916ff19a0e2cfb087`

## 目的

錯誤必須具有穩定 code、message、domain、severity、retryable、context 與 cause chain；UI 只翻譯顯示，不以字串猜測類型。

## 已核准錯誤碼（MEGIS-<DOMAIN>-<NNN>）

| Code | Domain | Severity | Retry | 繁體中文訊息 |
|---|---|---|---|---|
| MEGIS-SCH-001 | SCH | error | no | 輸入的單位或型別不符合定義。 |
| MEGIS-REF-001 | REF | error | no | 參照的物件不存在。 |
| MEGIS-ENV-001 | ENV | error | no | 輸入超出支援範圍。 |
| MEGIS-GEO-001 | GEO | error | no | 幾何輸入資料無效。 |
| MEGIS-GEO-002 | GEO | error | no | 不支援此幾何操作。 |
| MEGIS-GEO-003 | GEO | error | no | 幾何尺寸無效。 |
| MEGIS-GEO-004 | GEO | fatal | no | 幾何後端違反契約。 |
| MEGIS-VAL-001 | VAL | error | no | 檢測到碰撞或佈局衝突。 |
| MEGIS-VAL-002 | VAL | error | no | 元件間餘隙不足。 |
| MEGIS-VAL-003 | VAL | error | no | 驗證輸入幾何無效。 |
| MEGIS-RUL-001 | RUL | error | no | 規則來源未經核准。 |
| MEGIS-RUL-002 | RUL | error | no | 規則狀態轉換無效。 |
| MEGIS-RUL-003 | RUL | error | no | 規則不可豁免或豁免條件無效。 |
| MEGIS-RUL-004 | RUL | error | no | 規則來源登錄無效或不存在。 |
| MEGIS-PKG-001 | PKG | error | no | 套件指紋不符。 |
| MEGIS-PKG-002 | PKG | error | no | 套件 manifest 內容不符。 |
| MEGIS-PKG-003 | PKG | error | no | BOM 數量與 IR component quantity 不一致。 |
| MEGIS-BOM-001 | BOM | error | no | BOM CSV 或指紋不符。 |
| MEGIS-BOM-002 | BOM | error | no | BOM 宣告內容或 IR 欄位不符。 |
| MEGIS-DRW-001 | DRW | error | no | 草圖 SVG 指紋或尺寸與 IR 不符。 |
| MEGIS-DRW-002 | DRW | error | no | 草圖宣告內容不符。 |
| MEGIS-REP-001 | REP | error | no | 乾淨環境重建指紋不符，需 ADR。 |
| MEGIS-UI-001 | UI | error | no | 存在不安全的未知值，阻止建立 IR。 |
| MEGIS-UI-002 | UI | error | no | 要求的能力超出已驗證的 capability envelope。 |
| MEGIS-JOB-001 | JOB | error | yes | 工作逾時。 |
| MEGIS-AI-001 | AI | error | yes | AI 輸出格式無效。 |
| MEGIS-IMP-001 | IMP | error | no | 輸入檔案超出限制。 |
| MEGIS-IMP-002 | IMP | error | no | 檔案副檔名與內容不符。 |
| MEGIS-IMP-003 | IMP | error | no | 匯入檔案無法解析。 |
| MEGIS-IMP-004 | IMP | error | yes | 匯入處理逾時或超出實體數量上限。 |
| MEGIS-SYS-001 | SYS | fatal | no | 本機工具鏈版本不符。 |

v2 legacy `GeometryErrorCode` 映射（severity／retryable／訊息由 `megis/errors/registry.py` 統一管理）：

| v2 value | v3 code |
|---|---|
| INVALID_IR | MEGIS-GEO-001 |
| UNSUPPORTED_OPERATION | MEGIS-GEO-002 |
| INVALID_DIMENSION | MEGIS-GEO-003 |
| BACKEND_CONTRACT_VIOLATION | MEGIS-GEO-004 |

唯一性防退化：`tests/test_g1_err_001.py` 對 `MEGIS-<DOMAIN>-<NNN>` 格式、domain 內連續編號、v3 物件 schema 合規與 legacy 映射完整性做自動化檢查；新增 code 必須同步更新 `megis/errors/registry.py` 與本表。

## Owner

MEGIS Builder；新增 code 必須同時新增測試與本表紀錄。

## 最後審查 commit

`162d09d95df517c5123e4f7916ff19a0e2cfb087`

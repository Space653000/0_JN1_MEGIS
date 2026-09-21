# 規則治理與豁免（G3-RUL-001）

> 文件治理
> - 目的：定義 MEGIS 規則生命週期、規則 schema 必填欄位、waiver 格式與到期失效、不可豁免類別及對應錯誤碼。
> - 目前內容：G3-RUL-001 規則治理契約與 G3-SRC-001 來源登錄契約（2026-09-21）。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：`162d09d95df517c5123e4f7916ff19a0e2cfb087`

## 目的

本文件說明工程規則從建立到停用的完整治理流程，確保每一條規則的來源、嚴重度、版本、適用範圍、測試與豁免都可追溯，並讓「不可 waive 類別」由自動化強制執行而非靠人工自律。

## 規則生命週期

規則狀態固定為 `draft → in_review → approved → deprecated`：

| 狀態 | 意義 | 來源條件 |
|---|---|---|
| `draft` | 建立中；僅供內部迭代 | 未限制 |
| `in_review` | 施工者以全新 session 查核來源 | 未限制 |
| `approved` | 已核准，可被 Design Run 評估 | 來源必須為 `approved`，且 `reviewed_by` 必填對應 sign-off |
| `deprecated` | 保留歷史；不再評估新 Design Run | 只能由 `approved` 轉入 |

規則版本依 SemVer 遞增；`approved` 後不就地修改，只能以新版本取代。來源未經核准（`docs/RULE_SOURCES.md` 未登錄為 `approved`）之規則不得設為 `approved`，違反時回傳 `MEGIS-RUL-001`；非正規狀態轉換回傳 `MEGIS-RUL-002`。

## 規則來源登錄

來源登錄以 `config/rule-sources/sources.yaml` 為唯一事實來源（schema：`schemas/v3/rule-source.schema.json`），人工可讀對映見 `docs/RULE_SOURCES.md`。`approved` 來源的 `review_due` 通過後自動降為 `needs_review`，且核准必須附 URL 與取用日期；`draft`／`needs_review`／`retired` 來源不可支撐核准規則。未知來源回傳 `MEGIS-RUL-004`。

draft（或 in_review／deprecated）規則一律不得被評估為 approved，違反時回傳 `MEGIS-RUL-001`。


## 規則 schema 必填欄位

每一條規則（`schemas/v3/rule.schema.json`）必須具備：`rule_id`、`version`、`status`、`source`、`source_revision`、`source_clause`、`owner`、`reviewed_by`、`scope`、`condition`、`severity`、`recommendation`、`auto_fix`、`effective_date`、`applicability`、`waiver_category`、`waiver_policy`、`tests`（positive／negative／boundary 三類齊備）。

## Waiver 格式與到期失效

Waiver 存放於 `execution/signoffs/WV-<NNNN>.yaml`（`schemas/v3/waiver.schema.json`），必須具備：`waiver_id`、`rule_id`、`rule_version`、`design_id`、`revision`、`entity_refs`、`reason`、`risk_accepted`、`owner`、`approved_by_signoff`、`expires_when`、`affected_artifacts`、`revalidation_required`。

`expires_when` 至少一項，支援：

| 條件 | 語意 | 範例 |
|---|---|---|
| `input_changed` | 輸入變更時立即失效並觸發 maturity 重算 | `"expires_when": ["input_changed"]` |
| `rule_version_changed` | 規則版本變更時立即失效 | `"expires_when": ["rule_version_changed"]` |
| `date: <YYYY-MM-DD>` | 指定日期到達後失效（含當天） | `"expires_when": [{"date": "2026-12-31"}]` |

Waiver 失效後受影響 Design Run 的成熟度必須重新計算（此重算由 G3-MAT-001 evaluator 實作）。

## 不可豁免類別

`waiver_category` 為 `safety` 或 `unsafe_to_default` 的規則一律不得被 waive；只有 `standard` 類別且 `waiver_policy.waivable: true` 的規則允許 Waiver。違反時回傳 `MEGIS-RUL-003`。

## 錯誤碼

| Code | Severity | 語意 |
|---|---|---|
| `MEGIS-RUL-001` | error | 規則來源未經核准 |
| `MEGIS-RUL-002` | error | 規則狀態轉換無效 |
| `MEGIS-RUL-003` | error | 規則不可豁免或豁免條件無效 |
| `MEGIS-RUL-004` | error | 規則來源登錄無效或不存在 |

## Owner

MEGIS Builder；使用者保有否決權。

## 最後審查 commit

`162d09d95df517c5123e4f7916ff19a0e2cfb087`

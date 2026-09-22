# Fixed-Template Draft Drawing（G5-DRW-001）

> 文件治理
> - 目的：描述 `megis/package/drawing.py` 如何落實現圖 §13 圖面政策：IR metadata 驅動、固定 Fixture 模板、dimension whitelist、DRAFT 水印、QA checklist 寫入 manifest。
> - 目前內容：圖面政策、模板規格、公開 API、QA checklist、失敗碼、golden corpus 與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G5-DRW-001 實作 commit（獨立 commit，§13 回滾邊界）。

## 圖面政策

圖面由 Engineering IR／feature metadata 驅動，**不從 STEP 猜 critical dimension**。第一版只允許單一固定 `fixture-a4-landscape@1.0.0` 模板，加上呼叫做法者提供的 `dimension_whitelist`；每一張圖永久標示 `DRAFT - ENGINEERING REVIEW REQUIRED` 與 `NOT FOR MANUFACTURING`。這是 draft，不是 release drawing；到達 ENGINEERING_REVIEWED 之前，所有輸出都要顯示 maturity 與 `ENGINEERING REVIEW REQUIRED`。

## 模板規格

- A4 landscape（297×210 mm），`template_version: fixture-a4-landscape@1.0.0`。
- 主視圖為 Fixture base 的 top view，外框由 IR 的 width／depth（mm）與固定比例 0.38 縮放繪製，內框為虛線孔的示意；height 以側邊 `H <value> mm` 標註。
- 尺寸標註只印白名單內、且數值與 IR 完全一致者。
- 標題欄：`design_id`、`revision`、material（IR materials designation 排序後）、general tolerance、unit（mm）、projection（top view）、view scale。
- 水印：對角留白處與標題欄大字 `DRAFT - ENGINEERING REVIEW REQUIRED`；頁尾 `NOT FOR MANUFACTURING`。

SVG 不含時間戳，同一 IR＋白名單產出完全相同 bytes，`svgSemanticFingerprint` 為其 SHA-256；§12 的「drawing 以向量元素集合（排序後）正規化」由「固定渲染順序＋無 runtime 欄位」達成，可納入 package manifest 指紋鏈。

## 公開 API

```python
from megis.package import (
    build_draft_drawing,
    qa_all_passed,
    verify_draft_drawing,
    DEFAULT_WHITELIST,
)

doc = build_draft_drawing(ir, dimension_whitelist=DEFAULT_WHITELIST)
assert qa_all_passed(doc)          # release gate helper
verify_draft_drawing(doc, ir)      # 重算 QA 與 SVG fingerprint
```

`dimension_whitelist` 是 caller 釘住的白名單：只有出現在 IR `components[].dimensions[].quantity.id` 的維度會被印出；白名單內缺漏的維度會以 `qa` 的 `whitelist:<id>` fail row 記錄，擋住 release 但保留有效 artifact。

## QA checklist（每張圖）

| 項目 | 判定 |
|---|---|
| 標題欄 design_id／revision／material／tolerance／unit／projection | 缺任一 → fail |
| 白名單尺寸全部出現且數值與 IR 一致 | 缺漏 → fail；數值以 IR nominal 印出 |
| 無重複或矛盾尺寸 | 同一 dimension id 出現複數次 → 重複 fail；數值不一致 → 矛盾 fail |
| 水印存在 | `DRAFT - ENGINEERING REVIEW REQUIRED` 與 `NOT FOR MANUFACTURING` 都在 SVG 內 |
| 視圖比例標示 | `view_scale` 非空 |

QA 結果以 `doc["qa"]` 的 `pass／fail／N/A` 逐項記錄，必須寫入 manifest（blueprint：drawing QA 結果已記錄才到 PROTOTYPE）。

## 失敗碼

| 錯誤碼 | 情境 | retryable |
|---|---|---|
| `MEGIS-DRW-001` | SVG fingerprint 與重建值不符，或 whitelist dimension 數值與 IR 不一致 | no |
| `MEGIS-DRW-002` | 宣告不符：title block 缺欄位、水印／NOT FOR MANUFACTURING 缺失、QA checklist 偏離 IR、revision／design_id 與 IR 不符、IR 本身無效 | no |

## Golden corpus 與驗證

`contracts/g5/golden/drawing-corpus.json`（12 cases）由 `drawing-corpus.schema.json` 描述，以 `contracts/g1/golden/reference-fixture.json` 為基底：

- positive：預設白名單、白名單子集、IR component 順序反轉仍穩定、尺寸數值釘住、未知白名單記錄 QA fail（artifact 有效但 gate blocked）。
- negative：竄改 SVG、尺寸數值偏離（`MEGIS-DRW-001`）；移除水印／NOT FOR MANUFACTURING、title 欄位缺漏、QA 狀態竄改、revision 偏離（`MEGIS-DRW-002`）。

驗證命令：`pytest tests/test_g5_drw_001.py`（21 tests）。完整 baseline CI 全量重跑亦須全綠。

## 邊界（人工 QA）

自動化 QA 可確定的項目以程式認定；標題欄、投影法與整體圖面是否符合工程慣例、是否可放行，仍需工程師人工審查（E4 簽核）。本工項輸出的 SVG 屬 draft，不含 release 宣告。

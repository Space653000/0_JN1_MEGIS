# BOM Exporter（G5-BOM-001）

> 文件治理
> - 目的：描述 `megis/package/bom.py` 如何落實現圖 §13 BOM 規格：固定十二欄、item 升冪、UTF-8／LF CSV、數量與 IR 一致、來源可追溯。
> - 目前內容：欄位規格、公開 API、CSV 規範、數量政策、module 追溯、失敗碼、golden corpus 與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G5-BOM-001 實作 commit（獨立 commit，§13 回滾邊界）。

## 目的

BOM 是 Design Run 套件的組件清單。`build_bom` 只從「已驗證的 Engineering IR」產出 CSV，完全不從 filename 猜測欄位：part_id／description／quantity／material／revision／provenance 全部來自 IR，module 資訊來自 G4-MOD-002 寫入的 `module:<id>@<version>` provenance marker。`verify_bom` 會重算 CSV 並與 IR 交叉核對，任何不一致都以結構化錯誤拒絕。

## 欄位規格（§13）

| 欄位 | 來源 | 政策 |
|---|---|---|
| `item` | 依 `part_id` 升冪指派 1..N | 排序固定、item 升冪 |
| `part_id` | IR `components[].id` | 不從 filename 推測 |
| `description` | IR `components[].name` | 不臆測 |
| `quantity` | IR component quantity（現行 v2 schema 無此欄，因此誠實值為 1） | BOM 數量必須等於 IR component quantity，否則 `MEGIS-PKG-*` |
| `material` | `components[].materialId` → `materials[].designation`（缺 designation 用 `name`） | 無 `materialId` 時為空字串，絕不臆測材料 |
| `finish`／`standard`／`size` | IR component（現行 v2 schema 未定義，因此為空字串） | 不臆測 |
| `module_ref`／`module_version` | provenance marker `module:<id>@<version>` | 只有 provenance 有 marker 才填 |
| `revision` | IR `revision` | 與 IR 一致 |
| `provenance` | component `provenanceIds`（排序後以 `\|` 連接） | 可追溯 |

## CSV 規範

- 編碼 UTF-8、換行 LF（`lineterminator="\n"`），RFC 4180 minimal quoting。
- 表頭為上述十二欄固定順序。
- `csvSemanticFingerprint` 是 CSV UTF-8 bytes 的 SHA-256，與 `megis.package` 的 L2 text fingerprint 同族，可納入 package manifest 指紋。

## 數量政策（誠實原則）

現行 v2 IR schema 的 `components[].quantity` 不被允許（`additionalProperties: false`），因此合法 IR 的每個 component 都是 1 件，BOM 就輸出 1，這是唯一不臆測的值。`_read_quantity` 保留「非正整數直接拒絕（`MEGIS-BOM-002`）」的防護，為未來 IR 擴充 quantity 欄位準備；更大於 1 的每個料件數量需要先以 ADR 擴充 IR schema，不能由 exporter 自行補數。

## 公開 API

```python
from megis.package import build_bom, verify_bom

bom = build_bom(ir)          # ir 為已驗證的 v2 Engineering IR
ledger = verify_bom(bom, ir) # 重算 CSV 並與 IR 交叉核對
```

## 失敗碼

| 錯誤碼 | 情境 | retryable |
|---|---|---|
| `MEGIS-PKG-003` | BOM row quantity 與 IR component quantity 不一致（blueprint 指定 `MEGIS-PKG-*`） | no |
| `MEGIS-BOM-001` | CSV 與 rows 不服，或 `csvSemanticFingerprint` 與重算值不符 | no |
| `MEGIS-BOM-002` | BOM 宣告不符或 IR 欄位無效（schema、part 集合、material、revision、非正整數 quantity、dangling material） | no |

三個碼皆登錄於 `megis/errors/registry.py` 與 `docs/ERROR_CODES.md`。

## Golden corpus 與驗證

`contracts/g5/golden/bom-corpus.json`（12 cases）由 `bom-corpus.schema.json` 描述，測試以 `contracts/g1/golden/reference-fixture.json` 為基底套用 IR／BOM dials：

- positive：預設 fixture、module provenance 帶入、IR component 順序反轉仍固定排序、共享 material 解析、無材料 PCB 為空。
- negative：竄改 row quantity（`MEGIS-PKG-003`）、刪除／新增 row、revision／material 偏離、dangling material（`MEGIS-BOM-002`）、竄改 CSV（`MEGIS-BOM-001`）。

驗證命令：`pytest tests/test_g5_bom_001.py`（25 tests）。完整 baseline CI 全量重跑亦須全綠。

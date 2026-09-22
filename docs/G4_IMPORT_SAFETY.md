# Safe Import Extraction（G4-IMP-001）

> 文件治理
> - 目的：描述 `megis/importing` 如何落實現圖 §12 Import 政策：untrusted STEP／DXF 只能在隔離 subprocess 內被解析，只抽取「可證明」的 metadata，拒絕不安全輸入。
> - 目前內容：安全模型、供應鏈隔離、可證明欄位、錯誤碼對應、實體預算、結構完整性、golden corpus 與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G4-IMP-001 實作 commit。

## 目的

匯入是 untrusted 檔案進入系統的第一個面。`megis/importing` 確保任何 STEP／DXF 內容都不會在主要程序內被直接解析：parser 以獨立 subprocess 執行、有 timeout 與實體數量上限，父程序只回收單一 JSON 文件。抽出資料只包含「從檔內能證明的事實」，材料、負載、供應商、電氣／聲學屬性與安裝意圖一律不得在此階段被編造。

## 安全模型（§12 import policy）

| 層級 | 機制 | 位置 | 失敗碼 |
|---|---|---|---|
| 副檔名與 magic | 副檔名存在、大小預算、內容 marker（STEP `ISO-10303-21;`、DXF `SECTION`） | `guard.py`（父程序） | `MEGIS-IMP-001`／`MEGIS-IMP-002` |
| 隔離解析 | worker 以 `python -m megis.importing.worker` 執行 | `extract.py` → subprocess | `MEGIS-IMP-003` |
| 資源預算 | `WORKER_TIMEOUT_SECONDS`（60 s）；STEP record 數／DXF entity 數 ≤ 可注入 `max_entities` | `policy.py` + `worker.py` | `MEGIS-IMP-004` |
| 結構完整性 | STEP 的 `ISO-10303-21;`／`DATA;`／`ENDSEC;`／`END-ISO-10303-21;`；DXF 的 `SECTION`／`ENDSEC`／`EOF` | `worker.py` | `MEGIS-IMP-003` |

預設上限：`MAX_FILE_BYTES = 50 MiB`、`WORKER_TIMEOUT_SECONDS = 60`、`MAX_ENTITY_COUNT = 250_000`。測試可縮小任一上限驗證拒絕路徑。

## 可證明欄位

worker 只產出下列欄位，且一律 `derivedFromImport: true`、`capabilityLevel: null`：

- `boundingBoxMm`：由 `CARTESIAN_POINT`（STEP）或群組碼 `10/20` 座標（DXF）推得；無座標時為 `null` 且附 parser warning。
- `solids`／`shells`／`faces`／`edges`：STEP 實體計數（`MANIFOLD_SOLID_BREP`、`CLOSED_SHELL`、`ADVANCED_FACE`、`EDGE_CURVE`）；DXF 以 geometry entity 總數填 `edges`。
- `candidateHoles`：STEP 的 `CYLINDRICAL_SURFACE` 數、DXF 的 `CIRCLE` 數。
- `candidatePlanarSections`：STEP 的 `PLANE` 數、DXF 的 `LWPOLYLINE`／`POLYLINE`／`HATCH` 數。
- `fileUnit`：STEP 由 `SI_UNIT` 的長度單位標記（`.MILLI.,.METRE.`→`millimetre`、`.INCH.`→`inch`、`.METRE.`→`metre`）判定；DXF 只信任緊接 `$INSUNITS` 的群組碼 `70`。未標記為 `null`；無法明確判定為 `unknown`。
- `parserWarnings`：掃描期間的可稽核警示（例如無座標導致 bbox 不可得）。

材料、負載、供應商、電氣／聲學與 mount intent 不在 schema 中；`import-report.schema.json` 以 `additionalProperties: false` 封鎖任何額外欄位。

## 錯誤碼對應

| 錯誤碼 | 情境 | retryable |
|---|---|---|
| `MEGIS-IMP-001` | 檔案超過大小或結構上限 | no |
| `MEGIS-IMP-002` | 副檔名與內容不符（unsupported extension／wrong magic） | no |
| `MEGIS-IMP-003` | parser 拒收或解析失敗（含組構不完整） | no |
| `MEGIS-IMP-004` | worker timeout 或超出實體數量上限 | yes |

所有 `IMP` 錯誤都已登錄在 `megis/errors/registry.py` 與 `docs/ERROR_CODES.md`，唯一性由 `verify_error_codes` 檢查。

## 公開 API

```python
from megis.importing import extract_import_metadata

report = extract_import_metadata(
    "part.step",
    expected_format=None,
    max_bytes=50 * 1024 * 1024,
    timeout_seconds=60,
    max_entities=250_000,
)
```

傳入 untrusted 檔案回傳 `ImportReport`；任何拒絕、timeout 或解析失敗會拋 `MegisError` 且帶 `MEGIS-IMP-*` 碼。`max_entities` 會穿線到 worker 的 `--max-entities`，讓測試與部署能收緊實體預算。

## Golden corpus 與驗證

`contracts/g4/golden/import-corpus.json` 提供 16 個 declarative cases（`import-corpus.schema.json` 描述），測試端依規格生成臨時檔案並透過公開 API 重跑：

- positive：metric STEP（bounding box／counts／`millimetre`）、imperial STEP（`inch`）、metre STEP、zero-entity STEP、imperial DXF、metric DXF。
- negative：oversized（`MEGIS-IMP-001`）、truncated／missing EOF（`MEGIS-IMP-003`）、deeply nested（`MEGIS-IMP-004`）、wrong extension／bad magic（`MEGIS-IMP-002`）。

驗證命令：`pytest tests/test_g4_imp_001.py`（32 tests：public API、unit-level、corpus-driven、schema contract）。完整 baseline CI 全量重跑亦全綠。

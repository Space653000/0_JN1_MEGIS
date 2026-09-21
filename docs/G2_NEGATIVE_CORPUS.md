# G2-NEG-001 Boundary 與 Negative Geometry Corpus

> 文件治理
> - 目的：定義並強制 Reference Fixture 幾何的 boundary／negative corpus，落實不變量 18（越界不 clamp）與「0 個看似成功輸出」。
> - 目前內容：corpus 結構、envelope 強制、錯誤碼、驗證腳本與單元測試。
> - Owner：MEGIS Builder
> - 最後審查 commit：施工完成後更新為最新 commit

## 目的

`G2-NEG-001` 建立一份可重跑的機器可讀語料，分為 boundary 與 negative 兩類：

- boundary（10 例）：在已驗證 envelope 邊界與內部極值上的輸入必須 100% 產生 kernel-valid 且尺寸合格的幾何，不得 undershoot（cap 值必須被實際產出，而不是被悄悄縮小）。
- negative（14 例）：無效輸入必須 100% 回傳預期錯誤碼，silent success 強制為 0；越界輸入回傳 `MEGIS-ENV-001`，且錯誤 metadata 保留原始（未被 clamp）的輸入值。

## Envelope 強制

Geometry planning 邊界（`megis/geometry/planning.py`）現在對 fixture base 外尺寸呼叫 `check_within_envelope`（讀取 `config/envelope/envelope.yaml`）。超出已驗證範圍（120×80×20 mm；wall 下限 2.0 mm）的輸入會從 planning 層被拒絕：

- `plan_fixture_base`：讀取 width/depth/height 後立即檢查，任何一軸超過範圍即拋出 `MEGIS-ENV-001`。
- `plan_fixture_assembly`：讀取 base 外尺寸後做相同檢查。

此強制同時覆蓋 CAD backend 之前「一切照常構建」的隱性接受路徑，因此 negative corpus 中不再有任何「看似成功」的輸出。boundary 在 `<=` 語意下恰好等於 cap 仍屬合格，與 G1-ENV-001 的 envelope 測試一致。

## Corpus 結構

語料位於 `contracts/g2/golden/geometry-corpus.json`，schema 為 `schemas/v2/geometry-corpus.schema.json`。每個 case 由 `edits`（結構化操作，非自由字串路徑）套用在 golden IR `contracts/g1/golden/reference-fixture.json` 的深拷貝上：

- `set_dimensions`：覆寫指定 component 的量測 nominal。
- `set_wall`：覆寫 minimum wall constraint 的 min/max。
- `delete_dimension`／`add_dimension`：製造「缺失／重複」量測。
- `set_path`：以型別化 path 製造 dangling reference（僅用於 IR 結構性 negative）。

## 錯誤碼對照

| corpus 類別 | 期望錯誤碼 | 來源 |
|---|---|---|
| 越界（單軸或複合） | `MEGIS-ENV-001` | `MegisError`（V3 envelope taxonomy） |
| 尺寸無效（零／負／缺失／重複、wall 過厚） | `INVALID_DIMENSION` | `GeometryContractError`（legacy GEO-003） |
| IR 結構無效（dangling reference） | `INVALID_IR` | `GeometryContractError`（legacy GEO-001） |

## 驗證

```powershell
.venv/Scripts/python.exe scripts/verify_g2_neg_001.py
.venv/Scripts/python.exe -m pytest tests/test_g2_neg_001.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

`scripts/verify_g2_neg_001.py` 只做記憶體內幾何，不輸出任何工程製品；唯一產出是可 commit 的 `artifacts/g2-neg-001/verification.json`（27 項 checks）。摘要欄位證明：`boundaryPassed = 10/10`、`negativeErrored = 14/14`、`silentSuccess = 0`，且每個 `MEGIS-ENV-001` case 的 `engineer_detail` 均保留原始越界數值（未 clamp 到 120×80×20）。

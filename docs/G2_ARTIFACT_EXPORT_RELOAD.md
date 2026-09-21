# G2-CAD-004 Artifact Export and Reload

> 文件治理
> - 目的：說明 STEP、STL、DXF 輸出與重新載入管線，以及 stdlib-only glTF bridge。
> - 目前內容：export/reload 契約、backend 實作、驗證腳本、單元測試與過渡假設。
> - Owner：MEGIS Builder
> - 最後審查 commit：`0a5531e`（本段施工完成後更新為最新 commit）

## 目的

`G2-CAD-004` 讓 Reference Fixture assembly 元件實際輸出 STEP、STL、DXF 三種工程格式，並證明每個輸出檔都可重新載入且幾何不為空。這是後續 G3 驗證、G5 release 與可重現性 work item 的前置能力：geometry capability contract 一直保持 kernel-neutral，只有 CadQuery adapter 會接觸 CAD kernel。

## 能力邊界

- `export_formats` 宣告 `{"STEP", "STL", "DXF"}`。
- `export_model(model_token, output_path, export_format)` 從不透明 token 取出 shape，透過 CadQuery exporter 輸出，並回傳 byte count、SHA-256、體積與 `TopologyMetrics`。
- `reload_model(input_path, import_format)` 依格式分派：
  - STEP：`importStep` 幾何重載，驗證 valid、non-null 與正體積，並套用 `normalize_step_file`。
  - STL：結構化二進位驗證（`84 + triangles*50`），計算 mesh 體積、vertex 數與 bbox，套用 `normalize_stl_file`。
  - DXF：以 `dxf_vector_semantic_fingerprint` 解析 LINE 向量，套用 `normalize_dxf_file`。
  - GLTF：由 stdlib-only `megis/adapters/gltf.py` bridge 產生並結構重載，不新增第三方依賴。
- 錯誤一律透過 `GeometryContractError` 回報穩定 code：`UNSUPPORTED_OPERATION` 或 `BACKEND_CONTRACT_VIOLATION`。

## 過渡假設

本段輸出的是工程幾何製品，不屬於 release artifact。STEP 檔在 normalize 前仍可能含 OCCT runtime 的 FILE_NAME 與 translator 版本資訊，因此以 `normalize_step_file` 產出確定性內容；STL 只接受 binary 且 header 由 `normalize_stl_file` 固定；DXF 的 `$FINGERPRINTGUID`、時間變數與 CLASS 排序由 `normalize_dxf_file` 正規化。glTF 由 STL 衍生，標示為 MEGIS bridge 產生，不做任何工程解析宣稱。

## 驗證

```powershell
.venv/Scripts/python.exe scripts/verify_g2_cad_004.py
.venv/Scripts/python.exe -m pytest tests/test_g2_cad_004.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

`scripts/verify_g2_cad_004.py` 會把 STEP、STL、DXF 與 glTF 寫到 `artifacts/g2-cad-004/`（git-ignored），並產生唯一可 commit 的 `verification.json`。驗證紀錄包含每個元件的 byte count、SHA-256、正規化後 SHA-256、體積、拓墣與 bbox 交叉比對。

# 確定性與雙層指紋政策 1.0.0

> 文件治理
> - 目的：定義 artifact 完整性與工程語意可重現性的不同證據層。
> - 目前內容：V3 fingerprint policy 1.0.0、STEP/DXF/STL 正規化與 replay 邊界。
> - Owner：MEGIS Builder
> - 最後審查 commit：`0c34596a2561534adf9abafd52fc4c3f5738d9ed`

## 目的

MEGIS 不把檔案 bytes 完全相同誤當成工程語意相同，也不把語意相同誤當成檔案沒有遭竄改。每個正式 artifact 必須能分別提供 L1 `byte_sha256` 與 L2 `semantic_fingerprint`。

## 目前內容

機器可讀政策位於 `config/fingerprint/policy-1.0.0.json`，schema 位於 `schemas/v3/fingerprint-policy.schema.json`。版本 1.0.0 使用 canonical UTF-8 JSON、排序 key、無多餘空白，並使用 `ROUND_HALF_EVEN`：長度 0.001 mm、面積 0.01 mm²、體積 0.01 mm³。

### L1：Byte integrity

`byte_sha256` 對檔案原始 bytes 計算，用於傳輸、儲存、checkout 與竄改偵測。同一工程語意若只改 STL header，L1 必須改變。

### L2：Semantic reproducibility

幾何 canonical record 包含 solid/shell/face/edge/vertex 數、體積、面積、bounding box、center of mass 與排序後 semantic feature IDs。工程浮點先依政策捨入並轉為字串，再計算 canonical JSON SHA-256。

目前 policy 沒有 `informationalFields`。若 ARM64 emulation 與 x64 CI 證明某拓樸欄位不穩定，不能直接忽略；必須建立 ADR、記錄差異證據並升級 policy version。

## 格式正規化

| 格式 | 正規化 | L2 語意 |
|---|---|---|
| STEP | `FILE_NAME` 時間固定為 Unix epoch；author、organization 與 processor 固定為 MEGIS；OpenCascade export sequence 固定為 0；LF line ending | 重新載入 B-Rep 的 geometry canonical record |
| DXF | 固定 create/update time、elapsed timer、handle seed、GUID、last-saved-by 與 ezdxf metadata timestamp | 排序後 LINE endpoint 向量集合 |
| STL | 強制 binary；固定 80-byte header | 排序後、0.001 mm 捨入的 triangle vertex 集合摘要 |
| Manifest | 不變更保存內容 | fingerprint 排除時間、duration 與自身 fingerprint 欄位 |

正規化後，同一平台相同輸入的 STEP、DXF、STL byte hash 也應一致；這只是附加證據，跨平台的正式通過標準仍是 L2 semantic fingerprint。

## Replay 驗證

`tests/test_v3_determinism.py` 在兩個 repository-local 暫存目錄重建 Reference Case，檢查：

- 三種格式的 normalized byte hash 逐一一致。
- Source B-Rep 與 STEP reload 的 geometry semantic fingerprint 一致。
- STL header 改變會改 L1、但不改 L2；triangle 改變會改 L2。
- Manifest runtime timestamp 改變不影響 L2，工程尺寸改變必須影響 L2。
- Binary STL 長度必須符合 `84 + triangle_count × 50`。

## 限制

- DXF policy 1.0.0 只接受此 reference slice 的 linear `LINE` entities；遇到 arc、spline 或 polyline 必須擴充 policy 與 tests，不可靜默忽略。
- Fingerprint 只證明可重現性與內容一致性，不證明設計正確、可製造、安全或經工程師簽核。
- `V3C-MAT-001` 尚未修正既有 spike maturity；本政策不改變 maturity。

## Owner

MEGIS Builder；policy version、rounding、included fields 或 informational fields 變更必須有 ADR、replay 差異與 fresh-session review。

## 最後審查 commit

`0c34596a2561534adf9abafd52fc4c3f5738d9ed`

# Package Manifest 與 Content Hashes（G5-PKG-001）

> 文件治理
> - 目的：描述 `megis/package` 如何落實現圖 §G5「清單（Manifest）必備資訊」與 §12 Package 政策：每個 artifact 以 L1 `byte_sha256` 與 L2 `semantic_fingerprint` 釘住，manifest 可重建且所有 hash 可驗證。
> - 目前內容：manifest 必備欄位、L1／L2 hash 政策、builder／verifier 公開 API、竄改與宣告不符的失敗碼、golden corpus 與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G5-PKG-001 實作 commit。

## 目的

Design Run 的產物必須可重建、可稽核。`megis/package` 產生一個 `PROTOTYPE_PACKAGE` manifest：檔頭明確標示 prototype、不含 Production Ready 宣告；每個產物同時帶 byte-level 與 semantic 兩個 hash，任何竄改 1 byte 都會讓 `verify_package_manifest` 拒絕；清單自身的 semantic fingerprint 另加封裝，runtime 欄位（`generated_at` 等）不參與指紋以便 clean-environment 重跑得到相同摘要。

## Hash 政策（§12）

| 等級 | 名稱 | 定義 | 用途 |
|---|---|---|---|
| L1 | `byte_sha256` | 檔案原始 bytes 的 SHA-256 | 傳輸／儲存完整性、竄改偵測 |
| L2 | `semantic_fingerprint` | 依檔案型別做決定性正規化後的 SHA-256 | 語意重現、版本比對 |

L2 依副檔名路由（`megis/package/manifest.py::semantic_fingerprint_for_path`）：

| 型別 | 正規化 | `fingerprint_kind` |
|---|---|---|
| `.stl` | binary STL 三角形排序＋`.3f` 四捨五入後 hash | `stl_triangles` |
| `.dxf` | LINE 端點排序＋`.3f` 後 hash | `dxf_vectors` |
| `.step` | `FILE_NAME` 等 runtime 欄位正規化後之 text hash | `step_normalized_text` |
| `.json` | 去除 runtime 欄位後 canonical JSON hash | `json_canonical` |
| 其他 text | LF 正規化後 hash | `utf8_text_lf` |
| 其他 binary | 直接 byte hash（semantic == byte-level） | `binary_bytes` |

指紋政策版本固定為 `1.0.0`（與 `megis/determinism` 一致）。

## Manifest 必備欄位（§G5）

`schemaVersion`、`package_kind: PROTOTYPE_PACKAGE`、`classification: DESIGN_RUN`、`design_id`／`revision`、`generated_at`、`package_builder`、`fingerprint_policy_version`、`input_hashes`、`artifact_hashes`、`versions`（schema／engine／libraries／rules／models／solvers）、`runtime`（`platform.machine()` 與 emulation 旗標）、`random_seed`、`executed_validations`、`gates`（passed／failed／waived／skipped）、`assumptions`、`unknowns`、`human_signoffs`、`maturity`（由 `megis.maturity` evaluator 計算，附 `inputs_digest`）、`envelope_ref`、`dna_ref`、`module_versions`、`ai_involvement`、`manifestSemanticFingerprint`。`schemas/v3/package-manifest.schema.json` 以 `additionalProperties: false` 封鎖任何未列出的欄位。

## 公開 API

```python
from megis.package import build_package_manifest, verify_package_manifest

manifest = build_package_manifest(
    design_id="fixture-001",
    revision="A",
    artifact_paths={"CAD/reference_case.step": step_path},
    input_hashes={"requirement.yaml": requirement_sha},
    versions={"schema": "1.0.0", "engine": "...", "libraries": {...},
              "rules": "...", "models": "none", "solvers": "none"},
    random_seed="seed-0001",
    executed_validations=["geometry-valid"],
    gates={"passed": ["G0", "G1"], "failed": [], "waived": [], "skipped": []},
    maturity={"state": "PROTOTYPE", "achieved_index": 2, "blocking_reasons": [],
              "inputs_digest": "...", "evaluator_version": "megis.maturity@1.0.0"},
    envelope_ref="envelope/fixture@1.0.0",
    dna_ref="dna/fixture@1.0.0",
)
verify_package_manifest(manifest, artifacts_dir)
```

`build_package_manifest` 只從「呼叫者提供的欄位＋檔案實體」產出資料，不補任何虛構數字；每筆 `artifact_hashes` 的 `bytes`、`byte_sha256`、`semantic_fingerprint` 均由檔案當下內容算出。

## 失敗碼（§12 Package）

| 錯誤碼 | 情境 | retryable |
|---|---|---|
| `MEGIS-PKG-001` | artifact `byte_sha256`／`bytes`／`semantic_fingerprint` 或 `manifestSemanticFingerprint` 與重建值不符 | no |
| `MEGIS-PKG-002` | manifest 宣告不符：schema 無效、非 `PROTOTYPE_PACKAGE`、`classification` 非 `DESIGN_RUN`、出現 Production Ready 宣告、`maturity` 為 `RELEASED`、宣告的 artifact 遺失 | no |

兩個 `PKG` 碼皆登錄於 `megis/errors/registry.py` 與 `docs/ERROR_CODES.md`，唯一性由 `verify_error_codes` 檢查。

## Golden corpus 與驗證

`contracts/g5/golden/manifest-corpus.json`（18 cases）由 `manifest-corpus.schema.json` 描述，測試端依 `artifact_kinds` 生成臨時檔案、以公開 API 建 manifest 後套用 `tamper`／`dial` 再重跑驗證：

- positive：單一型別與混合型別（STEP＋STL＋DXF＋JSON＋text）的完整 hash 鏈 all match。
- negative：flip／append／truncate 任一 artifact（`MEGIS-PKG-001`）、manifest 被改動使 `manifestSemanticFingerprint` 失效（`MEGIS-PKG-001`）、宣告的 artifact 遺失（`MEGIS-PKG-002`）、Production Ready 宣告／`maturity` RELEASED／非 `PROTOTYPE_PACKAGE`／未註冊 `fingerprint_policy_version`（`MEGIS-PKG-002`）。

驗證命令：`pytest tests/test_g5_pkg_001.py`（25 tests：schema contract、corpus schema、可重建性、truthfulness、check ledger、runtime 預設、corpus 全案例）。完整 baseline CI 全量重跑亦須全綠。

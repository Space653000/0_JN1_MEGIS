# Clean-Environment Reproducibility（G5-REP-001）

> 文件治理
> - 目的：描述 G5-REP-001 的可重現契約、凍存 golden fingerprints、依 README 重建相同內容 hash 的步驟，以及「差異需 ADR」的觸發規則。
> - 目前內容：可重現契約、byte-stable 集合、STEP/DXF 已知 delta、凍存 golden、重建步驟、ADR 規則與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G5-REP-001 實作 commit（§26.8 回滾邊界）。

## 可重現契約

G5-REP-001 依藍圖 §26.8「乾淨環境與 CI 重建 fingerprint 一致或差異已 ADR」與 WORK_QUEUE 驗收「乾淨環境可依 README 重建相同內容 hash」。可重現單位是 **semantic fingerprint**（G1 fingerprint policy 1.0.0）：

| Artifact | Fingerprint kind | byte-穩定 |
|---|---|---|
| `reference_case.step` | `step_normalized_text` | 否（exporter 寫入 FILE_NAME metadata） |
| `reference_case.stl` | `stl_triangles` | 是 |
| `reference_case_section_z10.dxf` | `dxf_vectors` | 否（exporter 寫入 metadata） |
| `bom.csv` | `utf8_text_lf` | 是 |
| `draft_drawing.svg` | `utf8_text_lf` | 是 |

同鎖定工具鏈（`environment/toolchain.lock.json`、`requirements.lock`）下的乾淨重建，五個 artifact 的 semantic fingerprint 必須與 `contracts/g5/golden/repro-fingerprints.json` 完全一致；byte-穩定集合還必須 byte-identical（byte_sha256 一致）。STEP／DXF 的 bytes 因 exporter 內嵌 run metadata 會在不同 run 間略有差異，但 semantic fingerprint 穩定——這是有紀錄的已知 delta，不是 content drift，不需 ADR。

## 凍存 Golden

- 檔案：`contracts/g5/golden/repro-fingerprints.json`
- corpusId：`g5-repro-fingerprints@1.0.0`
- Schema：`schemas/v3/repro-fingerprints.schema.json`
- `reportFingerprint` 只由 semantic fingerprints（及 byte-穩定 artifact 的 byte_sha256）計算，不含 file size，因此跨 run 穩定。
- 內含 toolchain 身分（os／python／machine／cadquery／cadquery-ocp／fingerprint policy），證明凍存值只對該支援邊界有效。

## 重建與比對

```powershell
cd C:\0_JN1_MEGIS
.\.venv\Scripts\python.exe scripts\verify_g5_rep_001.py
```

驗證腳本依序執行：

1. 在主樹 `.runs/g5-rep-001-source` 重建五個 artifact，比對 golden。
2. 在 `.runs/g5-rep-001-clean`（git-ignored）以 `git clone` 建立釘版 commit 的乾淨 checkout，以**子程序**在乾淨樹內重建並寫出 clean report。
3. 比對 source report、clean report 與 golden 三者的 `reportFingerprint`。
4. 交叉核對 frozen 的 STEP/STL/DXF semantic fingerprints 與已交付的 `artifacts/g0-cad/*`。

結果寫入 `artifacts/g5-rep-001/verification.json`（`allChecksPassed`）。

單元層可重現證據：`tests/test_g5_rep_001.py`（6 tests）驗證二次重建確定性、text 產物 byte-identical、STEP/DXF byte drift 僅存在於 metadata 層、g0-cad 語意指紋對齊、竄改 BOM 會攔截為 `MEGIS-REP-001` 差異。

## ADR 規則

任何乾淨重建產生的 **semantic fingerprint** 與凍存 golden 不一致，皆屬 `MEGIS-REP-001`（clean-environment rebuild fingerprint drift）：

- 屬 shift/regression，需先產出 ADR（`docs/decisions/`），說明差異成因、影響與新指紋快照。
- 在 ADR 核准並更新 golden 前，該狀態視為未達 G5-REP-001 驗收。
- 修改 `repro-fingerprints.json` 視同 golden 更新，套用同一 ADR 規則。

本工項首次執行記錄：三路（source／clean／golden）`reportFingerprint` 全等、g0-cad 三格式語意指紋對齊，**semantic drift = 0，無需 ADR**。

## 邊界

- 可重現只涵蓋 golden IR + 鎖定工具鏈的支援邊界（Windows 10/11 x64、或具 x64 emulation 的 Windows 11 ARM64；Python 3.11.9、CadQuery 2.8.0、OCP 7.9.3.1.1）。
- 重建中間檔（STEP/STL/DXF）一律落在 `.runs/`／`.temp/`（git-ignored），不重複提交重型製品。
- 本工項不產生 engineering／release artifact；SVG 仍為 `DRAFT - ENGINEERING REVIEW REQUIRED` 且 `NOT FOR MANUFACTURING`。
- 所有寫入僅限 `C:\0_JN1_MEGIS`；`AERIS` 與 `Offline-Local-Voice-Agent` 唯讀未變更。

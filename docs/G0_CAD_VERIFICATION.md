# G0-CAD-001 CadQuery 可行性驗證

> 文件治理
> - 目的：記錄 CadQuery Reference Case feasibility。
> - 目前內容：STEP、binary STL、DXF 產出、有效性與雙層指紋證據。
> - Owner：MEGIS Builder
> - 最後審查 commit：`0c34596a2561534adf9abafd52fc4c3f5738d9ed`

## 結論

`G0-CAD-001` 的固定 Reference Case 已以 CadQuery 2.8.0／cadquery-ocp 7.9.3.1.1 產出 STEP、binary STL 與 Z=10 mm 的 2D DXF section，三種格式均通過重新載入與內容檢查。此結論只證明 G0 工具路徑可行，不等同 G2 production geometry backend，也不是製造放行。

## 固定輸入

- 外形：120 × 80 × 35 mm
- 開頂單腔 envelope：2 mm floor／wall
- 緊固特徵：四個 3.4 mm M3 clearance holes
- 宣告 metadata：Aluminum 6061、3-axis CNC
- DXF section：Z=10 mm

## 驗證結果

| 格式 | 重新載入路徑 | 驗證結果 |
|---|---|---|
| STEP | CadQuery `importStep`／OCP STEP reader | 1 個 valid solid；120 × 80 × 35 mm；體積在 1e-6 mm³ 公差內一致 |
| STL | OCP `StlAPI_Reader` | valid shape；2,060 faces；120 × 80 × 35 mm（0.05 mm 公差） |
| DXF | CadQuery／ezdxf importer | 8 edges、2 closed wires；外框 120 × 80 mm；內框 116 × 76 mm |

產物的 byte count 與 SHA-256 記錄於 `artifacts/g0-cad/manifest.json`。Manifest 永久標示：

- `classification: FEASIBILITY_SPIKE`
- `maturity: null`（可行性 spike 不具有工程成熟度）
- `engineeringReviewRequired: true`

## V3 雙層指紋補強

`V3C-DET-001` 以 policy 1.0.0 補入兩層證據：

- L1 `byte_sha256`：對正規化後檔案 bytes 計算，驗證傳輸與 checkout 完整性。
- L2 `semantic_fingerprint`：STEP 重新載入 B-Rep、binary STL triangle 集合與 DXF line vectors 各自建立 canonical engineering record。

STEP 的時間、作者、組織與 OpenCascade export sequence 已固定；DXF 的時間、timer、GUID、handle seed 與 ezdxf metadata timestamp 已固定；STL 改為 binary 並固定 80-byte header。兩個隔離目錄連續重建必須同時得到相同 normalized byte hash 與 semantic fingerprint。

Machine policy：`config/fingerprint/policy-1.0.0.json`。詳細邊界：`docs/FINGERPRINT_POLICY.md`。

## 重跑

所有暫存與 pytest 輸出固定在 repository 內：

```powershell
cd C:\0_JN1_MEGIS
$env:TEMP = 'C:\0_JN1_MEGIS\.temp'
$env:TMP = 'C:\0_JN1_MEGIS\.temp'
.\.venv\Scripts\python.exe -m spikes.g0_cad.reference_case --output-dir artifacts\g0-cad
.\.venv\Scripts\python.exe -m pytest
```

## 非目標

- 未建立 cover、PCB envelopes、USB-C cutout 或 assembly。
- 未實作 G2 geometry capability contract、feature ordering 或 structured error taxonomy。
- 未宣稱材料、製程或 M3 特徵已通過 DFM／工程審查。
- 未產生 release package 或 `RELEASED` 製品。

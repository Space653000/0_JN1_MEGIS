# G2-CAD-003 Fixture Assembly

> 文件治理
> - 目的：說明 Reference Fixture assembly 幾何切片。
> - 目前內容：cover、fastener、cutout、PCB envelope 與間隙證據。
> - Owner：MEGIS Builder
> - 最後審查 commit：`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

## 目的

本工作項目建立 Reference Fixture 的可替換 assembly plan 與 CadQuery 實作，涵蓋中空 base、cover、四個 fastener、counterbore、PCB envelope 與 USB-C cutout。所有 CAD kernel 物件仍封裝在 adapter 內，核心服務只接收不可變資料契約。

## 驗收範圍

- base、cover、PCB envelope 與四個 fastener 均為單一、kernel-valid solid。
- USB-C cutout 實際穿透 base 側壁。
- cover clearance hole 對 M3 fastener 具有正的徑向間隙。
- PCB envelope 對側壁及 cover 具有正間隙。
- base、cover 與 PCB envelope 之間沒有非預期體積干涉。
- 相同 IR 重跑得到相同 opaque model token 與量測結果。
- 不可能的 wall 輸入明確失敗，不做 silent clamp。

## 過渡假設與能力邊界

既有 v2 golden IR 只提供 base 外形與 minimum wall，未提供完整 PCB 與 USB-C 尺寸。因此本段把 PCB envelope、USB-C opening、cover 與 fastener 的 Reference Fixture 固定值集中隔離在 `megis/geometry/planning.py`，不回改已完成的 G1 golden 歷史。這些值不是 V3 研究結論；V3 `G1-REQ-001` 必須依公開官方資料研究並取代它們。

本工作項只在記憶體中建立與檢查幾何，不輸出 STEP、STL、DXF、glTF、工程圖或 release package；artifact export 屬於 `G2-CAD-004`。

## 驗證

```powershell
.venv/Scripts/python.exe scripts/verify_fixture_assembly.py
.venv/Scripts/python.exe -m pytest tests/test_g2_fixture_assembly.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

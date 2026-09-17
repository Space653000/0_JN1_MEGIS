# G2 Geometry Capability Contract

> 文件治理
> - 目的：說明 kernel-neutral geometry adapter seam。
> - 目前內容：capability negotiation、planning、service 與錯誤邊界。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 邊界設計

`G2-CAD-001` 建立三層可替換邊界：

1. `planning.py` 驗證 Engineering IR，從 Reference Fixture golden IR 擷取 base 的 width、depth、height 與 coordinate semantics。
2. `contracts.py` 只定義 immutable dataclasses、capability negotiation、stable error codes 與 `GeometryBackend` Protocol。
3. `service.py` 只依賴 Protocol，先檢查 backend 是否支援所需 operation，再驗證 adapter 回傳的 plan、backend identity、component 與 solid metadata。

核心契約不 import CadQuery 或 OpenCascade，也不允許 CAD kernel shape 穿越邊界。`model_token` 是不透明識別碼；後續 CadQuery adapter 自行管理實體 shape，核心只能讀取經驗證的尺寸、體積、solid count 與 validity metadata。

## 目前 capability envelope

- 輸入：合法 V2 Reference Fixture Engineering IR。
- 已規劃 operation：fixture base 的 `box`。
- 尺寸：只接受 `length/mm` 且具有正 nominal 的 width、depth、height。
- 失敗：invalid IR、invalid dimension、unsupported operation、backend contract violation 都有穩定 error code。
- 尚未產生工程製品；CadQuery adapter 與 base solid 在 `G2-CAD-002` 實作。

## 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_g2_geometry_contract.py
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

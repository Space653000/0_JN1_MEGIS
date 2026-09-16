# G0 COMSOL 可行性證據

`inventory.json` 由 `scripts/inventory-comsol.ps1` 以唯讀方式產生。盤點只記錄指令、標準路徑、registry key 與環境變數是否存在，不擷取授權內容、環境變數值或憑證。

本目錄的 `out_of_scope` 決策表示目前本機沒有可驗證的 COMSOL 安裝與授權，因此沒有執行求解；這不是模擬成功證據，也不阻塞不依賴 COMSOL 的核心 Gate。


# G0 COMSOL 可行性決策

> 文件治理
> - 目的：記錄 COMSOL 能力與授權決策。
> - 目前內容：本機 out_of_scope、非阻塞核心的決策證據。
> - Owner：MEGIS Builder
> - 最後審查 commit：`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

## 結論

`G0-SIM-001` 決策為 `out_of_scope`，且 `blocksCoreGate = false`。

本機唯讀盤點沒有找到 `comsol`、`comsolbatch` 或 `mphserver` 指令，也沒有找到標準 Windows 安裝路徑、COMSOL registry key 或常見授權設定的存在跡象。因此本次沒有啟動 COMSOL、沒有驗證 license checkout、沒有呼叫 API，也沒有產生任何模擬結果。

## 官方能力邊界

COMSOL 6.4 官方文件說明，Windows 無 GUI batch 求解使用 `comsolbatch -inputfile ... -outputfile ...`；batch job 仍依賴安裝內容與適用授權。Floating Network License 的 batch feature 亦有獨立授權語意。這證明未來整合路徑存在，但不能在缺少本機安裝與合法授權時宣稱已驗證。

- [COMSOL 6.4：Windows command 與 batch 語法](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_running.38.31.html)
- [COMSOL：Batch licenses 說明](https://www.comsol.com/support/knowledgebase/1304)

## 唯讀盤點範圍

- PATH：`comsol`、`comsolbatch`、`mphserver`
- 標準路徑：`C:\Program Files\COMSOL`、`C:\Program Files (x86)\COMSOL`、`C:\COMSOL`
- Registry：HKLM 64-bit、HKLM WOW6432Node、HKCU 的明確 COMSOL key
- 環境變數：只記錄名稱是否存在；不讀入證據檔的值

可重跑命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\inventory-comsol.ps1
.\.venv\Scripts\python.exe -m pytest tests\test_g0_comsol_decision.py
```

## 未來解鎖條件

未來只有在具備支援版本、合法授權、可安全呼叫的 `comsolbatch`、受版本控制的 adapter，以及可重現的授權 reference model smoke test 後，才能把決策升級為 `pass`。授權檔、server 位址、帳密與 license token 不得寫入 repository。

## 工程聲明

本決策沒有產生 COMSOL 模擬結果，不構成物理求解、設計驗證、工程簽核或製造依據。

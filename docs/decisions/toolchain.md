# G0 工具鏈版本決策

> 文件治理
> - 目的：固定可重現的本機與 CI 工具鏈。
> - 目前內容：Python、Node、CadQuery、OpenCascade 與平台基線。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 決策

`G0-ENV-001` 固定使用 Windows CPython 3.11 x64、pip 26.2.1、Node.js 24.17.0、npm 11.13.0、CadQuery 2.8.0、`cadquery-ocp` 7.9.3.1.1（OCP module 7.9.3.1）與 VTK 9.6.2。Python 完整傳遞依賴記錄於根目錄 `requirements.lock`，機器可讀版本與支援邊界記錄於 `environment/toolchain.lock.json`。

FreeCAD 鎖定 1.1.3，但此工作項目不宣稱已安裝或已通過 headless TechDraw；下載、repository 內隔離安裝與 `pass`／`fallback`／`out_of_scope` 決策屬於 `G0-DRW-001`。COMSOL license、API 與 batch 可行性則明確保留給 `G0-SIM-001`，不阻塞本工具鏈鎖定。

## Windows ARM64 相容邊界

目前主機為 Windows ARM64。CadQuery 2.8.0 所需的 `cadquery-ocp` 7.9.3.1.1 沒有 Windows ARM64 wheel，因此原生 ARM64 Python 3.12.10 無法重建 CAD 環境。MEGIS 改用既有 CPython 3.11.9 x64，透過 Windows x64 emulation 執行；自動驗證要求 `platform.machine() == "AMD64"`，避免未來誤用不相容的 ARM64 環境。

支援範圍是 Windows 10/11 x64，以及具 x64 emulation 的 Windows 11 ARM64。其他 OS、Python minor 或 architecture 尚未驗證，不應推定可重現。

## 重建

所有環境與快取均留在 `C:\0_JN1_MEGIS`：

```powershell
cd C:\0_JN1_MEGIS
py -3.11 -m venv .venv
$env:PIP_CACHE_DIR = 'C:\0_JN1_MEGIS\.pip-cache'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
.\.venv\Scripts\python.exe -m pip install pip==26.2.1
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
```

驗證指令：

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\verify_toolchain.py
.\.venv\Scripts\python.exe -m pytest
```

`verify_toolchain.py` 同時驗證 repository-local Python 路徑、Python／pip／Node／npm／CadQuery／OCP／VTK 版本，並建立有效的 10×20×30 單一 solid，確認體積為 6000。

## 版本來源

- CadQuery 2.8.0：<https://pypi.org/project/cadquery/>
- CadQuery releases：<https://github.com/CadQuery/cadquery/releases>
- cadquery-ocp 7.9.3.1.1：<https://pypi.org/project/cadquery-ocp/7.9.3.1.1/>
- FreeCAD 1.1.3：<https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3>
- Node.js 24.17.0：<https://nodejs.org/en/blog/release/v24.17.0>
- pytest 9.1.1：<https://pypi.org/project/pytest/>

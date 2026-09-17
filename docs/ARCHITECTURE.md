# MEGIS 架構

> 文件治理
> - 目的：固定分層、依賴方向、資料流與 adapter seam。
> - 目前內容：現有 contract／geometry／UI 模組與 V3 目標架構的誠實對照。
> - Owner：MEGIS Builder
> - 最後審查 commit：`0c34596a2561534adf9abafd52fc4c3f5738d9ed`

## 目的

核心工程資料必須獨立於 CAD kernel、UI、AI provider 與外部工具；所有外部能力透過可替換 adapter 進入，錯誤在邊界轉成穩定契約。

## 依賴方向

```text
UI / CLI
  → application services
    → contracts + domain models
      ← adapters (CadQuery / FreeCAD fallback / future AI provider)
```

Domain 與 contract 不得 import CadQuery、OCP、FreeCAD、React 或 provider SDK。Adapter 可以依賴核心契約；核心不可反向依賴 adapter 實作。

## 目前內容

- `megis/contracts`：既有 IR validation、serialization、consumer、migration。
- `megis/geometry`：kernel-neutral plan、capability 與 service boundary。
- `megis/determinism`：不依賴 CAD kernel 型別的 canonical fingerprint，以及格式正規化邊界。
- `megis/adapters/cadquery_backend.py`：唯一 CAD backend；kernel shape 不跨出 adapter。
- `apps/web`：UX-0 原型，仍以 `PrototypeViewModel` 合成資料運作。
- `execution`：Gate、work item、claim、evidence 與 migration deferral 控制面。

V3 規定但尚未完成的 maturity、rules、module、package、AI 與 thin-slice 模組保留在工作佇列，不在本文件宣稱已實作。

## 資料流

Requirement → confirmed Engineering IR → deterministic geometry plan → adapter result → validations → package manifest。AI 只能產生 `llm_proposed` 草稿，使用者確認前不得進入 confirmed IR。

## Owner

MEGIS Builder；架構基線變更需 ADR。

## 最後審查 commit

`0c34596a2561534adf9abafd52fc4c3f5738d9ed`

# Supported Envelope

> 文件治理
> - 目的：公開目前實際驗證的能力範圍與尚未驗證的 V3 目標。
> - 目前內容：legacy Reference Fixture 幾何範圍、機器可讀 envelope 與 V3 目標待辦界線。
> - Owner：MEGIS Builder
> - 最後審查 commit：`74675ec86102c88ac538cc422740f4d3394298bc`

## 目的

所有 UI、API、question engine、geometry 與 maturity 判斷必須共用同一 envelope；超出範圍時要明確拒絕，不得 silent clamp。

## 目前內容

目前有自動化證據的 legacy G2 slice 為固定 Reference Fixture：base envelope `120 × 80 × 20 mm`、minimum wall `2 mm`、AL6061、3-axis CNC、固定 cover／四 fastener／PCB envelope／USB-C cutout。PCB 與 USB-C 的現有數值是隔離的 v2 過渡假設，不是研究核准值。

V3 目標案例為外形 `120 × 80 × 35 mm`、兩片 PCB、USB-C、M3 removable cover；`G1-ENV-001` 已建立機器可讀 `config/envelope/envelope.yaml`，並以 `tests/test_g1_env_001.py` 與本文件做一致性測試；但 V3 目標仍需 `G1-REQ-001` 公開來源研究核准後才視為已驗證 envelope。

## 變更規則

Envelope 變更需要 ADR、sign-off、golden／boundary／negative regression、UI capability filter 與 maturity 重算。`config/envelope/envelope.yaml` 為唯一機器設定來源，與本文件由一致性測試把守，不得各自硬編碼範圍。

## Owner

MEGIS Builder；擴張範圍需要使用者決策。

## 最後審查 commit

`74675ec86102c88ac538cc422740f4d3394298bc`

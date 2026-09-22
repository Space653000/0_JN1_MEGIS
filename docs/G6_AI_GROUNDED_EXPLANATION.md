# G6-AI-004 Grounded Explanation Contract

> 文件治理
> - 目的：定義 AI 白話解釋的允許來源、數值引用與拒收條件。
> - 目前內容：schema、來源指紋、JSON Pointer 比對與誠實邊界。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：`9b0e08ac0b84f9e8595cb726481a8cb1826bdc1d`。

AI 解釋不是新的工程事實來源。它只能把已存在於 Engineering IR、rule result 或 package manifest 的資料轉成繁體中文白話說明。

## 強制流程

1. 呼叫端提供具名的 trusted source documents 與其類型。
2. Provider output 必須符合 `grounded-explanation.schema.json`，並固定 `locale: zh-TW`。
3. Output 必須列出全部來源的 canonical SHA-256；核心重新計算並逐一比對。
4. 每段文字中的每一次獨立數值出現，都必須有且只有一筆 citation。
5. Citation 的 JSON Pointer 必須解析到數值，且與文字 token 數值相等。
6. 任一條件失敗時，整份 output 回 `MEGIS-AI-002`，不得修補、猜測或部分採用。

`M3`、版本字串等嵌在英文字母或識別碼中的字元不視為獨立工程數值；若要表達螺紋尺寸，應由來源資料提供獨立的 numeric field，再以數值 citation 引用。純文字且不含數值的段落可以沒有 citation。

## 誠實邊界

- 此模組不寫入 IR、規則、manifest、maturity 或幾何。
- 驗證的是「輸出數值與指定來源一致」，不代表來源資料本身已通過工程簽核。
- 來源指紋綁定防止 provider 引用過期或遭竄改資料。
- CI 與 verifier 使用 recorded data，不連線任何外部 provider。

# HLAPI 測試資料正規化規格（XLSX -> Markdown）

## 1. Source

- 檔案：`docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx`
- 轉換範圍：從 `QoS_LLAPI`（sheet #4）到最後一個 sheet。
- 目的：建立可追溯的 `HLAPITestCase` markdown + machine index，供 CLI/GUI/分析引擎共用。

## 2. Sheet Inventory（from workbook parsing）

| Sheet | Non-empty Rows | Header Snapshot |
|---|---:|---|
| `QoS_LLAPI` | 33 | Object, Parameter Name, HLAPI, LLAPI, Implemented by, 4.0.1 Test Result, Comment, BCM v4.0.3 Test Result, BCM v4.0.3 Comment |
| `QoS_Test_Results` | 12 | LLAPI, Description, Test Steps, 4.0.1 Command Output, BCM v4.0.3 Test Result, BCM v4.0.3 Comment |
| `Wifi_LLAPI` | 422 | Object, Parameter Name, HLAPI, LLAPI, Implemented by, Test Steps, Command Output, ... |
| `Ethernet_LLAPI` | 37 | Object, Parameter Name, HLAPI, LLAPI, Implemented by, Test Steps, Command Output, Test Result, Comment, ... |
| `Button_LLAPI` | 2 | Object, Parameter Name, HLAPI, LLAPI, Implemented by, Test Steps, Command Output, Test Result, comment, ... |
| `LED_LLAPI` | 5 | DataModel, Parameter Name, HLAPI, LLAPI, Implemented by, Test Steps, Command Output, Test Result, Comment, ... |
| `SFP_LLAPI` | 98 | Object, Parameter, HLAPI, LLAPI, Implemented by, Test Steps, Command Output, Test Result, Comment, ... |
| `XPON_LLAPI` | 8 | Object, Parameter Name, HLAPI, LLAPI, Implemented by, Test Steps, Command Output, Test Result, Comment, ... |

## 3. Header Canonicalization

將 header 正規化為 snake_case，換行與多空白合併成單一 `_`：

- `Object` / `DataModel` -> `object_path`
- `Parameter Name` / `Parameter` -> `parameter_name`
- `HLAPI` -> `hlapi_command`
- `LLAPI` -> `llapi_support`
- `Test Steps` -> `test_steps`
- `Command Output` / `4.0.1 Command Output` -> `command_output`
- `Test Result` / `BCM v4.0.3 Test Result` -> `result_status`
- `Comment` / `BCM v4.0.3 Comment` -> `comment`

若同義欄位同時存在，套用優先序：

1. `BCM v4.0.3` 欄位
2. `4.0.1` 欄位
3. 通用欄位（未標版本）

## 4. Record Mapping

每一列（row >= 2）轉為一筆 `HLAPITestCase`：

```yaml
case_id: "<sheet>-r<row>"
source_file: "docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx"
source_sheet: "<sheet_name>"
source_row: <row_number>
object_path: "<mapped field>"
parameter_name: "<mapped field>"
hlapi_command: "<mapped field>"
llapi_support: "<mapped field>"
test_steps: "<mapped field>"
command_output: "<mapped field>"
result_status: "<pass|fail|not-supported|skip|unknown>"
comment: "<mapped field>"
tags:
  - "llapi"
  - "<sheet_name>"
```

## 5. Result Normalization

- `Pass`, `pass`, `PASS` -> `pass`
- `Fail`, `fail`, `FAIL` -> `fail`
- `Not Supported`, `Not support`, `Not Support` -> `not-supported`
- `skip`, `Skip`, `N/A` -> `skip`
- 空值 -> `unknown`

## 6. Output Layout（Obsidian Native）

```text
<vault>/<project>/<run_or_date>/
├── notes/
│   ├── testcases/
│   │   ├── QoS_LLAPI.md
│   │   ├── Wifi_LLAPI.md
│   │   └── ...
│   ├── trace-index.md
│   └── run-summary.md
├── assets/
│   ├── raw/
│   │   └── 6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx
│   └── logs/
└── index/
    ├── hlapi-testcases.json
    ├── lineage.json
    └── run.json
```

## 7. Backlink Requirements

每筆 testcase 必須建立雙向關聯：

- testcase -> run-summary
- testcase -> trace-index
- testcase -> root-cause card（若有）
- testcase -> patch-proposal（若有）

## 8. Security & Redaction

- 匯入時需先套用 `masking` 規則，避免敏感資訊進入 note 與 index。
- 原始檔案保留於 `assets/raw`，不在摘要頁展示完整內容。

## 9. Future Discovery Integration

target 自動 discovery 產生的新 API 必須寫入同一模型並標記來源：

- `source_sheet = "__discovery__"`
- `source_row = 0`
- `tags += ["discovery", "<provider>"]`

藉此確保人工資料與自動探勘資料可在同一查詢面管理。

## 10. Compression & Lexicon Integration

正規化輸出需支援後續壓縮流程，並可反譯：

- testcase/index 需保留 `semantic_tags`（例：`hlapi-read`, `hlapi-write`, `not-supported`）。
- 若字串命中壓縮字典，需寫入 `compression_refs`：
  - `tier`: `dedup|aggregate|summary|semantic`
  - `token`: 例如 `[tc_ndev_ev]`
  - `lexicon_id`: 字典條目 ID
- 壓縮僅可作用於副本欄位，不得覆寫 `command_output` 原值。
- 每批資料需執行一次 round-trip 驗證（壓縮->反譯）：
  - 語意等價率必須為 `100%`
  - 關鍵 lineages（file/sheet/row）保留率必須為 `100%`

## 11. Workflow and Skill Linkage

每筆 testcase 應可被 workflow runtime 直接引用：

- `trace-capture-flow`：掛載 testcase 與 trace 事件關聯。
- `root-cause-flow`：產生 root-cause card 時，必須回鏈 testcase。
- `patch-proposal-flow`：如有修正建議，需附 testcase 與 evidence refs。
- `memory-promote-flow`：若 testcase 導致 candidate memory，需保存 promotion decision。

最終輸出須可對應以下查詢鏈：

`testcase -> trace-index -> consensus -> patch-proposal -> long-memory`

## 12. Obsidian Relation Integrity

Obsidian 為主資料結構，驗收時需檢查：

- 每個 testcase note 至少包含：
  - `run_id`
  - `source_sheet`
  - `source_row`
  - `links`
- `run-summary.md` 必須包含 testcase 統計（pass/fail/not-supported/unknown）。
- `trace-index.md` 必須可依 `case_id` 反查相關事件。
- `root-cause` 卡片若存在，必須能回鏈到 testcase note。

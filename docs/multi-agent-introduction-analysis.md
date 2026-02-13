# Multi-Agent 導入分析：LSP + eBPF + TraceZone + GUI Log 流程

## 1. 範圍
本文件分析在「LSP 定位 -> eBPF/tracezone 觀測 -> serialwrap 擷取 -> GUI log 輸出」流程中，哪些階段適合導入 multi-agent，並定義分工、交付物與風險控制。

## 2. 流程切段與導入時機

## Phase A：環境與能力盤點（可立即導入）
目標：快速判斷 target/host 能力，決定觀測策略（full eBPF 或降級）。

可導入 agent：
- `agent-env-check`
  - 任務：檢查 LSP 可用性、serial session、tracefs/kprobe 介面、CLI 可用命令。
  - 輸出：`capability_report.json`。
- `agent-policy-gate`
  - 任務：套用決策規則（例如 tracefs 缺失 -> 禁止進入動態 probe 分支）。
  - 輸出：`strategy_decision.json`。

導入價值：
- 降低人工反覆確認成本。
- 提前阻止不可行路徑（例如本案 tracefs 缺失）。

## Phase B：Source Path Mapping（可立即導入）
目標：建立 HLAPI 到底層來源的候選 call chain。

可導入 agent：
- `agent-lsp-mapper`
  - 任務：LSP `definition/reference/call hierarchy`。
  - 異常處理：若 LSP 失敗，輸出錯誤摘要給 fallback agent。
- `agent-fallback-mapper`
  - 任務：`rg + compile_commands + ctags/cscope` 建立替代路徑。
- `agent-chain-normalizer`
  - 任務：把多來源路徑正規化成統一結構（節點、邊、可信度）。

導入價值：
- LSP 失效時仍可持續工作。
- 自動合併重複路徑，便於 GUI 顯示。

## Phase C：觀測計畫生成（建議第二階段導入）
目標：由 source path 自動推導觀測點（kprobe/uprobe/tracezone）。

可導入 agent：
- `agent-observation-planner`
  - 任務：生成探針候選與 tracezone 清單，附優先序。
- `agent-feasibility-checker`
  - 任務：以 capability_report 過濾不可用觀測點。
- `agent-command-builder`
  - 任務：輸出可直接送 `serialwrap` 的命令集，含 quoting 與回滾命令。

導入價值：
- 減少手動拼接命令錯誤（括號、引號、ash 語法）。
- 讓「可觀測點」和「受限點」同時可視化。

## Phase D：Runtime Capture 與證據聚合（可立即導入）
目標：穩定執行命令、分段擷取 log、自動建立證據索引。

可導入 agent：
- `agent-serial-executor`
  - 任務：送命令、檢查 prompt 狀態、卡住自動 Ctrl-C/重啟 attach。
- `agent-log-window`
  - 任務：插入 run marker、做 windowed logread 擷取。
- `agent-evidence-indexer`
  - 任務：把 `seq`、symbol、source line 關聯成 evidence map。

導入價值：
- 避免長輸出淹沒後續命令。
- 把 raw transcript 轉成可追溯索引。

## Phase E：關聯分析與共識決策（建議第三階段導入）
目標：自動比對數值一致性與因果鏈，生成可解釋結論。

可導入 agent：
- `agent-correlation`
  - 任務：執行數值關聯（例如 `SSID.4 == wl0 + wl0.1`）。
- `agent-root-cause-hypothesis`
  - 任務：輸出多個 root-cause 假說與信心分數。
- `agent-consensus`
  - 任務：綜合前述證據，產出 `pass/warn/error` 與 veto reason。

導入價值：
- 讓結論可重現、可審計。
- 降低單一 agent 偏誤。

## Phase F：GUI/交付物產出（可立即導入）
目標：輸出 `run.json + evidence.md + logs/*` 並驗證前端可載入。

可導入 agent：
- `agent-artifact-writer`
  - 任務：生成 run/evidence/log 清單。
- `agent-ui-validator`
  - 任務：DevTools headless 驗證（run select、Core Block Flow 是否展開）。
- `agent-pr-preparer`
  - 任務：彙整 commit message、PR body、變更摘要。

導入價值：
- 交付格式一致。
- PR 內容品質穩定。

## 3. 建議導入路線（分三波）

## Wave 1（立即）
- Phase A + B + D + F
- 原因：這幾段低風險、可直接提高穩定性與可追溯性。

## Wave 2（短期）
- Phase C
- 原因：觀測計畫可被規則化，但需先固化 target capability 模型。

## Wave 3（中期）
- Phase E
- 原因：共識模型與假說評分需要更多樣本 run 才能穩定。

## 4. Agent 介面契約（最小版）

### 4.1 輸入契約（共通）
```json
{
  "run_id": "run-YYYYMMDD-NNN",
  "target": "COM0",
  "default_path": "WiFi.SSID.{i}.Stats.MulticastPacketsSent",
  "context": {
    "repo": "...",
    "compile_db": "..."
  }
}
```

### 4.2 輸出契約（共通）
```json
{
  "agent": "agent-name",
  "status": "ok|warn|error",
  "artifacts": ["path1", "path2"],
  "evidence_refs": ["serial-seq-546", "src:dm_action.c:362"],
  "message": "..."
}
```

## 5. 風險與防呆

1. 多 agent 競態覆寫
- 解法：所有 agent 只寫自己命名空間；由 orchestrator 合併。

2. 錯誤傳播擴大
- 解法：每 phase 必須有 gate；上一階段 `error` 時只允許 fallback 分支。

3. UART session 不穩定
- 解法：建立 `serial health watchdog` 與自動 recovery policy。

4. LSP 不可用導致全流程中斷
- 解法：LSP 永遠是「可選優先」，不是必經。

## 6. 驗收指標（可量測）

- 平均完成時間（單 run）
- 無人工介入成功率
- 可追溯證據覆蓋率（event 是否都有 evidence ref）
- GUI 可載入率（run json 驗證 + DevTools check）
- 錯誤降級成功率（LSP fail / tracefs fail 時流程不中斷）

## 7. 對本案的具體結論

以本次 `MulticastPacketsSent` 追查經驗，最應先導入 multi-agent 的是：
1. Phase A（能力盤點）
2. Phase D（serial/log 擷取）
3. Phase F（交付物與 UI 驗證）

原因：
- 這三段已有穩定規則與清楚輸入輸出，投資回收最快。
- 能直接降低「LSP 卡住」「shell 卡住」「log 淹沒」造成的人工作業負擔。

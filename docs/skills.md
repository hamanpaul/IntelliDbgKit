# Skills：LSP + eBPF + TraceZone + Serialwrap 整合追查手冊

## 1. 目標與適用場景
本手冊用於追查 `ubus-cli/ba-cli` 讀值與底層統計來源不一致的問題，並把結果輸出成可被 GUI 載入的分析 log。

典型案例：
- `WiFi.SSID.{i}.Stats.MulticastPacketsSent` 與 `/proc/net/dev_extstats` 對不上。
- 需要建立從 HLAPI -> 模組函式 -> kernel/procfs 的可視化關聯鏈。

## 2. 前置條件

### 2.1 Host 工具
- `rg`, `fd`, `jq`
- `serialwrap`（建議 `~/.paul_tools/serialwrap` 與 daemon）
- LSP MCP（clangd backend）
- 可選：`ctags` / `cscope`

### 2.2 Target 能力檢查
先檢查以下能力，再決定觀測策略：

```sh
/bin/sh -c 'which ba-cli 2>/dev/null; which ubus-cli 2>/dev/null; uname -a'
ls -ld /sys/kernel/debug /sys/kernel/debug/tracing /sys/kernel/tracing 2>&1
ls -l /sys/kernel/debug/kprobes 2>&1
/bin/sh -c 'zcat /proc/config.gz 2>/dev/null | grep -E "CONFIG_(BPF|KPROBE_EVENTS|UPROBE_EVENTS|TRACEFS|FTRACE|TRACING)="'
```

判斷：
- 若 `tracefs`/`kprobe_events` 缺失，動態 eBPF probe 視為 blocked，流程自動降級到 `TraceZone + procfs + source mapping`。

## 3. LSP 定位流程（含降級）

### 3.1 優先：LSP
1. 啟動 LSP `c` server。
2. `go_to_definition` / `find_references` 串出讀值路徑。
3. 將關鍵函式與檔案行號寫入事件 evidence。

### 3.2 異常：LSP 被外部專案阻斷
常見錯誤：`EACCES ... scandir .../att-prpl/.../ssl/private`。

降級流程：
- 用 `rg` 直接定位符號定義與呼叫關係。
- 用 `compile_commands.json` 補語意上下文。
- 若可用，再補 `ctags/cscope`。

### 3.3 建議最小定位清單（MulticastPacketsSent）
- `dm_get_stats`
- `mod_wifi_get_object_content`
- `handle_get_object_content`
- `wifi_bdk_get_object`
- `wldm_SSID_TrafficStats`
- `whm_brcm_rad_get_counters_fromline`
- `devextstats_seq_printf_stats`
- `dev_get_stats`

## 4. eBPF 觀測點設計

## 4.1 kprobe（kernel）
優先順序：
1. `dev_get_stats`
2. `devextstats_seq_printf_stats`
3. `devextstats_seq_show`

### 4.2 uprobe（userspace）
候選：
- `whm_brcm_rad_get_counters_fromline`
- `whm_brcm_rad_stats`
- `wldm_SSID_TrafficStats`

### 4.3 掛點嘗試範例
```sh
/bin/sh -c 'echo p:idk_probe_dev_get_stats dev_get_stats > /sys/kernel/debug/tracing/kprobe_events'
```

若失敗（`nonexistent directory` / `unknown filesystem type 'tracefs'`）：
- 記錄為 `probe.attach.blocked` 事件。
- 保留「已規劃但被 target 限制」的觀測點資訊，供 GUI 呈現。

## 5. TraceZone Callflow 追蹤

## 5.1 注意 CLI 語法
在此類 target，函式呼叫建議使用 `ba-cli`：
- `ba-cli 'WiFi.set_trace_zone(zone="pwifi", level=500)'`

常見陷阱：
- `ubus-cli WiFi.set_trace_zone(...)` 可能被 shell 視為語法錯誤。
- `WiFi.set_log_level(level=500)` 在某些映像可能 `function not found`。

## 5.2 建議 zone（MulticastPacketsSent）
- `pwifi`
- `mwifi`
- `brcmRad`
- `brcmMod`
- `brcmMain`

設定範例：
```sh
ba-cli 'WiFi.set_trace_zone(zone="pwifi", level=500)'
ba-cli 'WiFi.set_trace_zone(zone="mwifi", level=500)'
ba-cli 'WiFi.set_trace_zone(zone="brcmRad", level=500)'
ba-cli 'WiFi.set_trace_zone(zone="brcmMod", level=500)'
ba-cli 'WiFi.set_trace_zone(zone="brcmMain", level=500)'
/bin/sh -c "ba-cli 'WiFi.list_trace_zones()' | grep -E 'pwifi|mwifi|brcmRad|brcmMod|brcmMain'"
```

## 6. Serialwrap 實務流程

### 6.1 會話狀態
```sh
/home/paul_chen/.paul_tools/serialwrap session list
/home/paul_chen/.paul_tools/serialwrap session attach --selector COM0
```

### 6.2 指令送出與結果抓取
```sh
/home/paul_chen/.paul_tools/serialwrap cmd submit --selector COM0 --cmd "ubus-cli 'WiFi.SSID.*.Stats.MulticastPacketsSent?'" --source agent:codex
```

### 6.3 卡住復位
若 shell 進入 `>` continuation 或長輸出卡住：
- 送 `Ctrl-C`（`\003`）
- 必要時重啟 daemon 後重新 attach

## 7. 證據收斂與關聯驗證

## 7.1 最小證據集
1. HLAPI 回值：`WiFi.SSID.4.Stats.MulticastPacketsSent=...`
2. `/proc/net/dev_extstats` 中 `wl0`, `wl0.1` 的 tx multicast
3. source call chain（函式 + 行號）
4. tracezone level 設定結果
5. eBPF 是否可掛點（成功或 blocked）

## 7.2 關聯檢查模板
```text
SSID.4.MulticastPacketsSent = X
wl0.txmcast = A
wl0.1.txmcast = B
assert X == A + B
```

## 8. GUI 載入格式建議

### 8.1 run json 必備欄位
- `run`: `run_id`, `target_id`, `summary`, `consensus_state`
- `nodes`: 節點定義（HLAPI/TR181/MODWIFI/BDK/KERN/EBPF/TRACEZONE/CNS...）
- `edges`: 靜態關聯
- `events`: 時序事件（每筆要有 `flow`、`symbol`、`address`、`evidence`）

### 8.2 事件欄位範例
```json
{
  "id": "m10",
  "time": "17:56:31",
  "phase": "TEST_LOOP",
  "tool": "serialwrap",
  "title": "Capture wl0 and wl0.1 multicast tx counters",
  "status": "ok",
  "flow": ["KERN", "EVT"],
  "symbol": "/proc/net/dev_extstats",
  "address": "serial-seq-548",
  "evidence": ["wl0 txmcast=21857", "wl0.1 txmcast=21851"],
  "consensus": "pending"
}
```

### 8.3 檔案命名規範
- run: `run-YYYYMMDD-NNN.json`
- evidence: `run-YYYYMMDD-NNN-evidence.md`
- raw logs: `logs/run-YYYYMMDD-NNN-*.log`

## 9. 常見失敗與處置

1. LSP 啟動失敗（EACCES）
- 立即降級到 `rg + compile_commands + serial runtime evidence`

2. `set_log_level` 不存在
- 改用 zone 級別 `set_trace_zone(..., level=500)`

3. `tracefs` 不支援
- eBPF 動態掛點標記 blocked，不中止整體流程

4. serial 輸出淹沒或卡住
- 加 run marker（`logger RUN_xxx_START/END`）
- `logread | tail -n N | grep ...` 做 windowed 取樣

## 10. 最終交付清單
- 一份 GUI 可載入 run json
- 一份 evidence markdown
- 三類原始 log：
  - serialwrap transcript
  - LSP block/error record
  - DevTools/DOM 驗證結果
- 一段結論：
  - 值關聯是否成立
  - eBPF 是否可用
  - 下一步 patch/觀測建議

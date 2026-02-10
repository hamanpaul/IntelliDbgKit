# Feature Specification: IntelliDbgKit Debug-Observe Core

**Feature Branch**: `001-debug-loop`  
**Created**: 2026-02-09  
**Status**: Draft  
**Input**: User description: "建立 Core+Plugin 的嵌入式除錯與觀測平台，先期整合 HLAPI/LLAPI 測試與 TraceZone，可追溯到 symbol 與 source map，支援多 Agent 收斂分析與 CI patch 建議"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CLI 除錯閉環 (Priority: P1)

韌體工程師以 CLI 觸發單次測試，收集 TraceZone/UART/GDB/eBPF 資料，並在同一次 run 中得到可追溯 root-cause 候選與 patch 建議。

**Why this priority**: 先建立最小可用除錯閉環，才能支撐後續 GUI 與多 Agent 擴充。

**Independent Test**: 使用單一 HLAPI 測項執行一次 run，驗證可輸出 trace、symbol 對齊結果、root-cause 卡片、patch 建議。

**Acceptance Scenarios**:

1. **Given** 已設定 target 與 collector，**When** 執行 CLI 測試 run，**Then** 系統建立完整 run artifact（trace、symbol index、分析報告）。
2. **Given** run 失敗，**When** 進入分析階段，**Then** 系統輸出至少一個含證據鏈的 root-cause 候選。
3. **Given** root-cause 候選成立，**When** 產出修正建議，**Then** 系統輸出可審核 patch proposal（不自動合併）。

---

### User Story 2 - 統一插件介面與跨工具封裝 (Priority: P1)

平台工程師透過單一 wrapper 入口整合 UART/ADB/SSH/Telnet/本機工具，對上只暴露統一 API，避免工具參數不相容擴散到核心流程。

**Why this priority**: 無統一介面會導致插件不相容，後期擴充成本不可控。

**Independent Test**: 對同一個 `CommandIntent` 分別走 UART 與 SSH provider，皆能得到一致語意結果與標準化回傳。

**Acceptance Scenarios**:

1. **Given** 동일 intent，**When** 指向不同 provider，**Then** 執行結果以同一 `ExecResult` schema 回傳。
2. **Given** provider 不支援某 capability，**When** 執行命令，**Then** 回傳結構化不支援原因，不得 silent fallback。

---

### User Story 3 - GUI 回放與下鑽分析 (Priority: P2)

工程師在 Host 端 GUI 觀看 HLAPI→LLAPI 時序，並基於 TraceZone 先行顯示 func flow，能對節點進行下鑽查看關聯證據。

**Why this priority**: 可視化降低追問題認知負荷，是導入多工具流程的主要使用者價值。

**Independent Test**: 對單次 run 開啟 GUI timeline，能播放、定位節點、查看對應 evidence 與 source map 關聯。

**Acceptance Scenarios**:

1. **Given** 已完成 run，**When** 開啟 GUI timeline，**Then** 可看到 HLAPI→LLAPI 事件流與 TraceZone 函式流。
2. **Given** 點擊節點，**When** 執行下鑽，**Then** 顯示對應 symbol、來源檔位址、相關 trace 與 root-cause 關聯。

---

### User Story 4 - HLAPI 測試知識匯入與探勘 (Priority: P2)

測試工程師先使用既有 xlsx 測試報告建立 HLAPI 測試 markdown 資料庫；中後期再由 target 自動探勘支援 HLAPI 並回填同一模型。

**Why this priority**: 先利用既有測試資產可快速啟動，後續探勘可降低人工維護成本。

**Independent Test**: 使用指定 xlsx 建立 markdown + machine index；再跑 discovery 原型新增至少一筆新 HLAPI 記錄。

**Acceptance Scenarios**:

1. **Given** `6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx`，**When** 執行匯入，**Then** 產生每個測試 sheet 的 markdown 清單與索引。
2. **Given** target 具 CLI/ubus 探測能力，**When** 執行 discovery，**Then** 新發現 API 記錄可追溯到採集來源與時間。

---

### User Story 5 - 多 Agent 收斂分析 (Priority: P3)

主控代理透過 Copilot SDK 平行調度 codex/copilot/gemini 等子代理，收集結構化證據，最後輸出單一共識結論與異議列表。

**Why this priority**: 跨模型交叉驗證可降低單模型誤判，提升 root-cause 可信度。

**Independent Test**: 同一事件由至少兩個代理輸出不同結論，系統仍可產生可審核共識結果與 dissent。

**Acceptance Scenarios**:

1. **Given** 多代理平行分析，**When** 證據衝突，**Then** 主控代理輸出加權結果與衝突來源。
2. **Given** 證據不足，**When** 收斂流程結束，**Then** 標記為未收斂並要求更多觀測資料，不得輸出確定性結論。

---

### Edge Cases

- collector 中途失聯（UART cable reset、gdb session drop、probe attach fail）。
- 同名命令跨 provider 參數不相容，需經 adapter 映射後才可執行。
- 行為結果一致但統計量（pkt/cpu/memory）有抖動，需套用分層一致性判定。
- 部分 target 不支援 eBPF，需降級到 TraceZone + GDB + UART 模式。
- 測試資料欄位含換行或合併儲存格，xlsx 匯入需保留語意且可追溯原列。
- 敏感資訊欄位（密碼、token）需在輸出報告自動遮罩。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST 以 `symbol file` 作為靜態/動態關聯的主索引鍵之一。
- **FR-002**: System MUST 提供單一事件匯流排與統一事件 schema，所有插件不得繞過。
- **FR-003**: System MUST 支援 TraceZone、UART(serialwrap)、GDB、eBPF 作為 Phase 1 可接入 collector。
- **FR-004**: System MUST 支援 `CommandIntent -> provider command -> ExecResult` 三段式 wrapper 流程。
- **FR-005**: System MUST 支援 provider adapter（UART/ADB/SSH/Telnet/本機）能力聲明與健康檢查。
- **FR-006**: System MUST 將 run 流程固化為可審計狀態機，含時間戳與狀態轉移原因。
- **FR-007**: System MUST 產生 root-cause 候選，並附上可追溯 evidence links。
- **FR-008**: System MUST 輸出 patch proposal，但 MUST NOT 自動 merge 到主分支。
- **FR-009**: System MUST 在 GUI 顯示 HLAPI→LLAPI 回放與 TraceZone func call flow。
- **FR-010**: System MUST 支援節點下鑽，顯示 symbol、source 위치、trace 關聯與共識結果。
- **FR-011**: System MUST 以 Obsidian 原生結構寫入每日 run 摘要、root-cause 卡片、trace 索引。
- **FR-012**: System MUST 維持 Obsidian note 與 machine index（JSON）雙軌一致性。
- **FR-013**: System MUST 支援從 `docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx` 的 `QoS_LLAPI` 後續 sheets 轉成 markdown 測試資料。
- **FR-014**: System MUST 保留 xlsx row-level lineage（sheet 名稱、row 編號、欄位映射）。
- **FR-015**: System MUST 提供 HLAPI discovery 最小原型，可從 target 收集支援 API 並回填資料模型。
- **FR-016**: System MUST 支援多 Agent 平行分析與結構化證據交換（非完整上下文互傳）。
- **FR-017**: System MUST 提供共識引擎，輸出 weighted conclusion 與 dissent 記錄。
- **FR-018**: System MUST 以分層門檻驗證重製一致性（行為/控制流/統計分開判定）。
- **FR-019**: System MUST 對敏感欄位做遮罩後再進入報告或知識庫。
- **FR-020**: System MUST 保留 CLI-first 操作，GUI 不得成為唯一入口。
- **FR-021**: System MUST 提供 CI 可用 evidence bundle（trace、index、consensus、patch proposal）。
- **FR-022**: System MUST 支援 plugin 版本相容性檢查，阻止不相容插件註冊。
- **FR-023**: System MUST 對不支援能力提供結構化錯誤碼與替代建議。
- **FR-024**: System MUST 排除影音/素材處理、風格化/比例化、自動剪接、音樂/歌詞生成等非本案能力。

### Key Entities *(include if feature involves data)*

- **ProjectRun**: 單次測試與除錯閉環執行單位，包含狀態機、target、artifact 路徑。
- **TraceEvent**: 事件匯流排的最小交換單元，承載 phase/tool/symbol/address/payload。
- **SourceMapNode / SourceMapEdge**: 靜態與動態關聯圖節點/邊，支援下鑽與可視化。
- **CommandIntent**: 對上統一語意命令，對下映射到 provider-specific 指令。
- **ExecResult**: provider 執行回傳，含 stdout/stderr/rc/latency/normalized fields。
- **HLAPITestCase**: 從 xlsx 轉入的測試案例，保留欄位語意與來源 lineage。
- **HLAPIDiscoveryRecord**: 從 target 自動探勘得到的 API 支援記錄。
- **EvidenceRecord**: 子代理分析產生的結構化證據。
- **ConsensusRecord**: 主控代理收斂後的最終判定與異議集合。
- **PatchProposal**: 可審核修正建議，連結到對應 evidence 與 run。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 針對單一 P1 測項，工程師可在 15 分鐘內完成一次 `run -> 分析 -> 報告` 閉環。
- **SC-002**: Phase 1 工具鏈（TraceZone/UART/GDB/eBPF）在可用環境下可成功接入率達 95% 以上。
- **SC-003**: 重製一致性採分層判定：行為類 100%、控制流拓樸 100%、統計類 >= 80%。
- **SC-004**: 每個 root-cause 結論都能回溯到至少 2 條 evidence references。
- **SC-005**: GUI 回放可覆蓋 100% 的 HLAPI→LLAPI 事件序列，且節點下鑽成功率達 95%。
- **SC-006**: xlsx 匯入後，`QoS_LLAPI` 起各 sheet 的案例轉換完整率 100%，欄位 lineage 缺失率 0%。
- **SC-007**: 多 Agent 共識流程對衝突案例可產出可審核 dissent 記錄比例 100%。
- **SC-008**: CI pipeline 每次執行都可輸出 evidence bundle 與 patch proposal；自動 merge 次數必須為 0。

## Assumptions

- `serialwrap` 已可直接於環境使用。
- 使用者可提供先期 HLAPI/LLAPI 測試資料與初步通過條件。
- 中後期可從 target 存取必要控制介面以執行 HLAPI discovery 原型。

## Out of Scope

- 影音素材管線、風格化/比例化、自動剪接、音樂與歌詞生成、素材整理。
- 自動批准並合併修正到主幹分支。

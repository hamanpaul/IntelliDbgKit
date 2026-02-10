# Feature Specification: IntelliDbgKit PI Core Debug Hub

**Feature Branch**: `001-debug-loop`  
**Created**: 2026-02-10  
**Status**: Draft  
**Input**: User description: "以 PI 核心為中樞重構除錯平台，支援長記憶、壓縮降噪、技能化工作流與多 Agent 共識分析"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PI Core 可控閉環 (Priority: P1)

韌體工程師可在不污染核心的前提下，完成一次 `測試 -> 追蹤 -> 分析 -> 修正建議` 閉環。

**Why this priority**: 若核心邊界不先鎖定，後續插件擴張會破壞可維護性與可信度。

**Independent Test**: 單次 run 完成後，核心狀態只由狀態機與事件匯流排改變，插件無直接寫入核心資料。

**Acceptance Scenarios**:

1. **Given** 插件註冊成功，**When** 執行 run，**Then** 插件只能透過 EventBus 與 WorkflowAction 影響流程。
2. **Given** 插件嘗試直寫核心狀態，**When** 核心邊界檢查啟用，**Then** 系統拒絕並記錄違規事件。

---

### User Story 2 - Trace 養分化與長記憶升級 (Priority: P1)

每次 trace flow 都可作為知識養分，經過壓縮與驗證後升級為長記憶。

**Why this priority**: 長期除錯效率依賴歷史案例沉澱，不可只靠短期上下文。

**Independent Test**: 同類問題跨兩次 run 重現且共識分數達門檻，成功寫入 long-memory；不達標不得升級。

**Acceptance Scenarios**:

1. **Given** candidate memory 產生，**When** `repro_count >= 2` 且 `consensus_score >= threshold`，**Then** 升級到 long-memory。
2. **Given** 只符合單一條件，**When** 執行升級流程，**Then** 記錄為 pending，不得寫入 long-memory。

---

### User Story 3 - 四層壓縮與可逆反譯 (Priority: P1)

平台對 trace 做四層壓縮以濾除雜訊，但保留可逆反譯能力與證據鏈。

**Why this priority**: 降噪是規模化分析前提，但不可破壞可追溯性。

**Independent Test**: 壓縮後資料可反譯回原語意；關鍵行為證據不可遺失。

**Acceptance Scenarios**:

1. **Given** 重複事件流，**When** 執行去重與語意聚合，**Then** 事件量下降且關鍵路徑完整。
2. **Given** 已壓縮紀錄，**When** 執行反譯，**Then** 還原文字與原始語意一致。

---

### User Story 4 - 技能化工作流 (Priority: P2)

speckit 規劃的工具能力被封裝為可調度 skill/workflow，透過核心 workflow runtime 依序執行。

**Why this priority**: 工具散落會造成流程不一致，技能化可提升重用與治理。

**Independent Test**: 單次 run 至少可執行 `trace-capture-flow`, `root-cause-flow`, `patch-proposal-flow` 並產生標準輸出。

**Acceptance Scenarios**:

1. **Given** workflow 定義存在，**When** 觸發 flow，**Then** 各 step 依 guard 條件執行並可審計。
2. **Given** step 缺少前置證據，**When** workflow runtime 判定，**Then** flow 進入 blocked 狀態並回報缺口。

---

### User Story 4A - ToolCard 命令導引與介接一致性 (Priority: P1)

開發者與 Agent 可透過統一 `description + examples + help` 方式理解與調用工具，且工具差異由 wrapper/adaptor 吸收。

**Why this priority**: 工具介接不一致會直接破壞閉環自動化與可維護性。

**Independent Test**: 任一註冊工具都能由 `idk tools` 查詢說明、範例與健康狀態，並由 workflow 以統一格式調度。

**Acceptance Scenarios**:

1. **Given** 工具已註冊 ToolCard，**When** 執行 `idk tools show <tool_id>`，**Then** 回傳 description/examples/help 與 I/O 契約。
2. **Given** 底層工具參數格式不同，**When** 經 wrapper 調用，**Then** 上層收到一致 `ExecResult`。

---

### User Story 5 - 多 Agent 共識與否決 (Priority: P2)

主控代理平行調度多代理分析，遇到關鍵證據不足時必須否決，不可強行輸出結論。

**Why this priority**: 錯誤確定性結論比無結論更危險。

**Independent Test**: 衝突案例可產生 weighted result；關鍵證據缺失時產生 `vetoed=true`。

**Acceptance Scenarios**:

1. **Given** 多代理結果衝突，**When** 收斂執行，**Then** 輸出 winning claim 與 dissent 清單。
2. **Given** 缺關鍵證據，**When** 收斂完成，**Then** 輸出 veto 記錄並要求補觀測資料。

---

### User Story 6 - 可視化與知識面一致 (Priority: P3)

GUI 能播放 HLAPI->LLAPI->TraceZone flow 並下鑽節點；Obsidian 知識面可直接回鏈到 trace 與結論。

**Why this priority**: 減少認知負荷並提高跨人員傳遞效率。

**Independent Test**: GUI 節點點擊可打開對應 evidence 與 Obsidian 卡片；卡片反向連回 run。

**Acceptance Scenarios**:

1. **Given** 已完成 run，**When** 在 GUI 下鑽，**Then** 可看到 symbol/source/evidence/consensus 關聯。
2. **Given** 在 Obsidian 開啟 root-cause 卡片，**When** 點擊回鏈，**Then** 可回到 run 與關鍵 trace。

---

### Edge Cases

- collector 中途失聯（UART reset、gdb detach、probe attach fail）。
- 某 target 不支援 eBPF，流程需自動降級到 TraceZone + GDB + UART。
- 事件壓縮後語意歧義，必須回退到上一壓縮層再分析。
- 同名 command 在不同 provider 參數衝突，需靠 adapter 映射處理。
- 工具存在但 `help` 不可用或回傳非預期格式，需標記 degraded 並禁止自動調度。
- 多代理全數低信心或互斥，系統需標記未收斂而非輸出假結論。
- 匯入測試資料含敏感字串時，必須遮罩後才可進知識庫。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST 實作 PI Core，核心僅含狀態機、事件匯流排、證據收斂、工作流執行器。
- **FR-002**: System MUST 禁止插件直接寫入核心狀態與 long-memory。
- **FR-003**: System MUST 透過統一 `TraceEvent` schema 管理所有插件輸入輸出。
- **FR-004**: System MUST 以 `symbol file` 作為靜態/動態關聯主索引之一。
- **FR-005**: System MUST 支援 TraceZone、UART(serialwrap)、GDB、eBPF collector（可降級）。
- **FR-006**: System MUST 支援 `CommandIntent -> provider adapter -> ExecResult` 單一命令語意流程。
- **FR-007**: System MUST 實作 provider capability matrix 與健康檢查。
- **FR-008**: System MUST 將 run 固化為可審計狀態機，含每次轉移原因。
- **FR-009**: System MUST 實作四層壓縮：去重、語意聚合、跨 run 摘要、語意壓縮。
- **FR-010**: System MUST 支援語意壓縮查表與反譯（可逆）。
- **FR-011**: System MUST 在壓縮後保留證據鏈與原始索引引用。
- **FR-012**: System MUST 將記憶分為 `raw`, `working`, `candidate`, `long` 四層。
- **FR-013**: System MUST 僅在 `repro_count >= 2` 且 `consensus_score >= threshold` 時升級 long-memory。
- **FR-014**: System MUST 對未達升級條件的候選記憶標記 pending 並保存原因。
- **FR-015**: System MUST 將 speckit 工具能力以 skill/workflow 方式註冊與調度。
- **FR-016**: System MUST 提供 workflow guard 條件與 blocked 狀態回報。
- **FR-017**: System MUST 支援多 Agent 平行分析與結構化證據交換。
- **FR-018**: System MUST 實作加權收斂與否決條件（veto）。
- **FR-019**: System MUST 在 veto 時輸出補觀測指令，不得輸出確定性 root cause。
- **FR-020**: System MUST 在 GUI 顯示 HLAPI->LLAPI 回放與 TraceZone func flow。
- **FR-021**: System MUST 支援 GUI 節點下鑽到 symbol/source/evidence/consensus。
- **FR-022**: System MUST 以 Obsidian 原生結構保存 run 與 long-memory，並維持雙向連結。
- **FR-023**: System MUST 保留 machine index 供程式查詢與重放。
- **FR-024**: System MUST 支援從 `QoS_LLAPI` 起所有 sheet 匯入 HLAPI 測試資料。
- **FR-025**: System MUST 保留 xlsx row-level lineage（file/sheet/row/header mapping）。
- **FR-026**: System MUST 提供 target HLAPI discovery 最小原型並回填同一資料模型。
- **FR-027**: System MUST 對敏感資料先遮罩再寫入報告與知識庫。
- **FR-028**: System MUST 在 CI 產出 evidence bundle 與 patch proposal。
- **FR-029**: System MUST NOT 自動 merge 修正到主分支。
- **FR-030**: System MUST 排除影音素材處理、風格化、剪輯與音樂歌詞生成能力。
- **FR-031**: System MUST 以 `ToolCard` 管理每個工具之 `description/examples/help/input/output/risk`。
- **FR-032**: System MUST 提供 `idk tools list`、`idk tools show <tool_id>`、`idk tools doctor`。
- **FR-033**: System MUST 透過 wrapper/adaptor 將異質工具介面正規化為統一 `ExecResult`。
- **FR-034**: System MUST 支援 busybox-link 風格的 alias 對應，同一意圖可映射到多工具。
- **FR-035**: System MUST 讓既有 `hlapi_ingest`、`hlapi_discovery` 以同一命令註冊機制暴露。
- **FR-036**: System MUST 提供工具介接治理狀態（healthy/degraded/blocked）並回報原因。

### Key Entities *(include if feature involves data)*

- **ProjectRun**: 單次除錯閉環執行單位。
- **TraceEvent**: 匯流排標準事件。
- **CommandIntent / ExecResult**: 跨 provider 的語意命令與結果。
- **MemoryRecord**: 記憶層級資料單元（raw/working/candidate/long）。
- **MemoryPromotionDecision**: 記憶升級判定紀錄。
- **CompressionLexiconEntry**: 壓縮映射字典條目。
- **WorkflowDefinition / WorkflowRun**: 技能化流程定義與執行紀錄。
- **EvidenceRecord / ConsensusRecord / VetoReason**: 多代理證據、收斂與否決資訊。
- **HLAPITestCase / HLAPIDiscoveryRecord**: 測試案例與探勘記錄。
- **PatchProposal**: 可審核修正建議。
- **ToolCard / ToolCatalogEntry**: 工具說明、範例、help 契約、健康狀態與 alias 對應。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 單一 P1 測項可在 15 分鐘內完成一次閉環分析與報告產出。
- **SC-002**: 行為類一致性 100%，控制流拓樸一致性 100%，統計類一致性 >= 80%。
- **SC-003**: 壓縮後事件量下降至少 40%，且關鍵路徑保留率 100%。
- **SC-004**: 壓縮反譯語意等價率 100%（round-trip 驗證）。
- **SC-005**: 候選記憶升級 long-memory 時，100% 具備雙條件判定紀錄。
- **SC-006**: 多代理衝突案例 100% 產出 dissent 或 veto，不得靜默覆蓋。
- **SC-007**: GUI 下鑽成功率 >= 95%，且每次下鑽可追溯到至少 2 條證據。
- **SC-008**: xlsx 匯入完整率 100%，lineage 缺失率 0%。
- **SC-009**: CI 每次均輸出 evidence bundle 與 patch proposal，auto-merge 次數固定為 0。
- **SC-010**: ToolCard 覆蓋率 100%，所有可調度工具皆可由 `idk tools show` 取得可執行說明。
- **SC-011**: wrapper 正規化後 `ExecResult` 欄位完整率 100%，degraded 工具不得被 workflow 自動執行。

## Assumptions

- `serialwrap` 可直接使用。
- 可取得 TraceZone 與 target 基本控制介面。
- 可提供初期 HLAPI/LLAPI 測試資料作為 baseline。

## Out of Scope

- 影音素材管線、風格化/比例化、自動剪接、音樂與歌詞生成、素材整理。
- 自動批准並合併修正到主幹分支。

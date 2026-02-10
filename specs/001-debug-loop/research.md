# Research Notes: IntelliDbgKit PI Core Debug Hub

## Decision 1: PI Core 嚴格邊界

- **Decision**: Core 只保留狀態機、事件匯流排、工作流、證據收斂；插件不可直寫核心狀態與 long-memory。
- **Rationale**:
  - 核心越小，越不易被外部功能汙染。
  - 可將風險集中在 adapter/plugin 層隔離。
  - 有利於後續多 Agent 與多工具擴充。
- **Alternatives considered**:
  - 軟性邊界：彈性高但容易漂移。
  - 無邊界：短期快，長期不可維護。

## Decision 2: 長記憶雙條件升級

- **Decision**: candidate memory 需同時滿足 `repro_count >= 2` 與 `consensus_score >= threshold` 才能升級 long-memory。
- **Rationale**:
  - 降低單次偶發噪聲污染長記憶。
  - 保留可追溯判定依據，便於稽核。
- **Alternatives considered**:
  - 單次高信心即升級：污染風險偏高。
  - 全人工審核：自動化收益不足。

## Decision 3: 四層壓縮 + 語意壓縮可逆

- **Decision**:
  1. Dedup
  2. Semantic aggregation
  3. Cross-run summary
  4. Semantic codec（可逆）
- **Rationale**:
  - 壓縮可降低雜訊與儲存成本。
  - 可逆語意壓縮能保留法證級追溯能力。
  - 可實作關鍵字壓縮（如 `entered blocking state -> blocking`）與字串樣板壓縮（如 `[tc_ndev_ev]`）。
- **Alternatives considered**:
  - 只摘要：容易失真。
  - 只去重：降噪不足。

## Decision 4: 多 Agent 收斂採加權 + 否決

- **Decision**: 先加權收斂，再執行否決條件；缺關鍵證據時輸出 `veto` 而非硬結論。
- **Rationale**:
  - 錯誤確定性結論風險高於未收斂。
  - 可引導系統自動補觀測而非誤修正。
- **Alternatives considered**:
  - 純加權：可能掩蓋證據缺口。
  - 全人工裁決：不利閉環自動化。

## Decision 5: Speckit 工具技能化

- **Decision**: 將 speckit 規劃工具封裝成 `skill` + `workflow`，由 core workflow runtime 一致調度。
- **Rationale**:
  - 統一流程可降低跨工具行為差異。
  - 避免工具邏輯散落且難以審計。
- **Alternatives considered**:
  - 僅腳本鏈接：缺少治理。
  - sidecar-only：流程收斂成本高。

## Decision 6: Obsidian 為知識主結構

- **Decision**: run 與 long-memory 直接寫入 Obsidian 結構，JSON 作 machine index。
- **Rationale**:
  - 支援人類閱讀與機器回放雙需求。
  - 降低匯入匯出一致性問題。
- **Alternatives considered**:
  - JSON 主存再轉 markdown：偏離使用流程。
  - 純 markdown 無索引：大規模查詢效率不足。

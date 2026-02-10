# Research Notes: IntelliDbgKit Debug-Observe Core

## Decision 1: TraceZone-first, GDB/eBPF 補強

- **Decision**: 初期以 TraceZone 作為主要 runtime call flow 來源；GDB/eBPF 依案例與環境能力補強。
- **Rationale**:
  - TraceZone 在既有 prplOS 工作流中導入成本最低。
  - 可先完成 HLAPI→LLAPI 可視化主路徑，再逐步擴展低層探針。
  - 降低 eBPF 不可用平台（舊 kernel/受限板）導入風險。
- **Alternatives considered**:
  - GDB/eBPF 優先：觀測精度高，但早期 setup 較重。
  - 三者同權融合：完整但超出 MVP 可控範圍。

## Decision 2: 一致性採分層門檻，不採固定 90%

- **Decision**:
  - 行為類（例如連線是否成功、設定是否生效）= 100%
  - 控制流拓樸（關鍵 state/call path）= 100%
  - 統計類（pkt/cpu/memory 等）>= 80%
- **Rationale**:
  - 板端資源與流量統計具有非決定性抖動。
  - 若統一要求 100%，會把噪聲誤判為功能回歸，降低分析效率。
  - 分層規則可同時保留功能正確性與工程可操作性。
- **Alternatives considered**:
  - 全指標 100%：過嚴，誤報率高。
  - 固定 90%：可解釋性不足，無法區分功能失敗與量測噪聲。

## Decision 3: Obsidian 原生為主，不做後置匯出

- **Decision**: run、trace、root-cause、decision 都直接落在 Obsidian vault 結構；JSON 僅作 machine index。
- **Rationale**:
  - 符合知識管理主目標與使用者流程。
  - 直接建立雙向連結與追蹤索引，避免匯入匯出同步誤差。
  - 讓人類可讀與機器可查同時成立。
- **Alternatives considered**:
  - 先 JSON 再轉 markdown：機器友善但偏離使用者主工作流。
  - 純 markdown 無 index：可讀性佳但大型查詢與 replay 效能受限。

## Decision 4: 統一 wrapper 入口 + provider adapter

- **Decision**: 對上僅暴露 `CommandIntent`；對下由 adapter 轉成 UART/ADB/SSH/Telnet/本機實際命令。
- **Rationale**:
  - 解耦命令語意與平台語法差異。
  - 提前處理「相同指令語意但參數不相容」問題。
  - 可對 provider 做能力宣告與健康檢查治理。
- **Alternatives considered**:
  - Busybox 式別名直連：遷移快，但治理與審計分散。
  - 核心直接拼命令：短期可行，長期不可維護。

## Decision 5: 多 Agent 平行分析 + 主控收斂

- **Decision**: 透過 Copilot SDK 平行啟動多代理，由主控代理（orchestrator）執行遞迴分派與最終收斂。
- **Rationale**:
  - 保留多模型互補與交叉驗證優勢。
  - 避免無主控造成結果無法收斂。
  - 以結構化證據交換，降低 context 汙染與敏感資訊擴散。
- **Alternatives considered**:
  - 平行獨立 + 人工比對：自動化不足。
  - 單代理：簡單但降低可靠性。

## Decision 6: HLAPI 測試資料雙來源（匯入 + 探勘）

- **Decision**: 先匯入既有 xlsx（`QoS_LLAPI` 起所有 sheet）為 markdown/index；中後期加上 target 自動 discovery 原型。
- **Rationale**:
  - 可立即利用現有測試資產，快速形成 baseline。
  - discovery 原型補上新增 API 的持續維護能力。
  - 兩者共用同一 `HLAPITestCase`/`HLAPIDiscoveryRecord` 模型，避免資料分裂。
- **Alternatives considered**:
  - 僅人工維護 markdown：更新成本高且易遺漏。
  - 一次做到完整 discovery：前期成本高，偏離 MVP。

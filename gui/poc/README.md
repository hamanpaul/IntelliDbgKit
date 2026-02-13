# UI POC（Mock API）

## 啟動

```bash
cd /home/paul_chen/IntelliDbgKit
make ui-poc
```

開啟 `http://localhost:8080`。

## POC 範圍

- Run 切換（`runs.json`）
- HLAPI Path 切換（`path_contexts`）
- Core block flow mind-list（固定骨架 + Focus 鏈 + 父子連線）
- 點 list item（如 `ModesSupported`）可展開新 block，再點一次收折
- 每個 block 可由標題列拖曳自由定位
- 拖曳時自動避免 block 互相重疊
- 拖曳改為整個 block 可抓取（功能按鈕除外）
- 連線錨點對齊展開來源項目與子 block 標題
- Node drilldown（顯示關聯 events）
- Timeline replay（側欄收合）
- Event detail + evidence（側欄收合）
- Advanced filters（`phase/tool/keyword` 預設收合）

## Mock Data

- `gui/poc/mock-data/runs.json`
- `gui/poc/mock-data/run-20260210-001.json`
- `gui/poc/mock-data/run-20260210-002.json`
- `gui/poc/mock-data/run-20260213-001.json`
- `gui/poc/mock-data/run-20260213-001-evidence.md`
- `gui/poc/mock-data/run-20260213-002.json`
- `gui/poc/mock-data/run-20260213-002-evidence.md`
- `gui/poc/mock-data/logs/run-20260213-002-serialwrap-seq-524-572.log`
- `gui/poc/mock-data/logs/run-20260213-002-lsp-block.log`
- `gui/poc/mock-data/logs/run-20260213-002-devtools-dom-check.log`
- `gui/poc/mock-data/hlapi-context.json`

## Known Issues

- 目前 `Call Flow Focus` 已有 `From/Transition(+/-/=)` 與固定骨架，但「跨 step 因果」仍是推論式呈現，對第一次看的使用者可讀性仍不足。
- 目前只有節點層級 (`event.flow`) 的前後差異，沒有顯式「邊/觸發條件」資料（例如 `Step1 -> Step2` 的實際 trigger），所以仍可能看起來像片段切換。
- 後續要補強：引入明確 transition event schema（who/why/edge），用顯式因果鏈取代純節點差分顯示。

## Mock API 對應

- `listRuns()`
- `getRun(runId)`
- `getGraph(runId)`
- `getTimeline(runId, filters)`
- `getEventDetail(runId, eventId)`
- `getNodeDetail(runId, nodeId)`
- `getHlapiContext()`
- `getPathContext(path)`

實作位置：`gui/poc/mock-api.js`

## 參考來源

- compile_commands: `/home/paul_chen/arc_prj/compile_commands/PR65BE4445B-S-ZA-1b5d4586.json`
- ODL:
  - `/home/paul_chen/arc_prj/att-prpl/targets/968375GWO_WL25DX_WLMLO_OPENWRT_PRPL_FASTMCASTD/fs/etc/amx/wld/wld_accesspoint.odl`
  - `/home/paul_chen/arc_prj/att-prpl/targets/968375GWO_WL25DX_WLMLO_OPENWRT_PRPL_FASTMCASTD/fs/etc/amx/wld/wld_radio.odl`

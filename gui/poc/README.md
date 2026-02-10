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
- Core block flow mind-list（可折疊階層、父子連線）
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
- `gui/poc/mock-data/hlapi-context.json`

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

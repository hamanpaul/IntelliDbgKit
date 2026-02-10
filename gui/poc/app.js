import { MockDebugApi } from "./mock-api.js";

const api = new MockDebugApi();

const timelineEl = document.getElementById("timeline");
const detailsEl = document.getElementById("details");
const graphEl = document.getElementById("graph");
const hintEl = document.getElementById("graphHint");
const statsEl = document.getElementById("timelineStats");
const tpl = document.getElementById("timelineItemTpl");

const runSelect = document.getElementById("runSelect");
const phaseSelect = document.getElementById("phaseSelect");
const toolSelect = document.getElementById("toolSelect");
const searchInput = document.getElementById("searchInput");
const applyFilterBtn = document.getElementById("applyFilterBtn");

const playBtn = document.getElementById("playBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const speedSelect = document.getElementById("speedSelect");

const pathSelect = document.getElementById("pathSelect");
const pathMetaEl = document.getElementById("pathMeta");
const siblingListEl = document.getElementById("siblingList");
const odlContextEl = document.getElementById("odlContext");
const sourceOutlineEl = document.getElementById("sourceOutline");

const state = {
  runs: [],
  runId: "",
  runMeta: null,
  graph: { nodes: [], edges: [] },
  timeline: [],
  activeIndex: 0,
  activeEventId: "",
  filters: {
    phase: "ALL",
    tool: "ALL",
    keyword: ""
  },
  timerId: null,
  hlapiContext: null,
  selectedPath: ""
};

function statusBadge(status) {
  if (status === "ok") return '<span class="badge b-ok">OK</span>';
  if (status === "warn") return '<span class="badge b-warn">WARN</span>';
  return '<span class="badge b-danger">ERR</span>';
}

function consensusBadge(consensus) {
  if (consensus === "pass") return '<span class="badge b-ok">CONSENSUS:PASS</span>';
  if (consensus === "veto") return '<span class="badge b-danger">CONSENSUS:VETO</span>';
  return '<span class="badge b-info">CONSENSUS:PENDING</span>';
}

function runBadge(status) {
  if (status === "pass") return '<span class="badge b-ok">RUN:PASS</span>';
  if (status === "warn") return '<span class="badge b-warn">RUN:WARN</span>';
  return '<span class="badge b-info">RUN:UNKNOWN</span>';
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function selectedEvent() {
  return state.timeline[state.activeIndex] || null;
}

function edgeKey(from, to) {
  return `${from}::${to}`;
}

function activeEdgeSet() {
  const event = selectedEvent();
  if (!event) return new Set();
  const edges = new Set();
  for (let index = 0; index < event.flow.length - 1; index += 1) {
    edges.add(edgeKey(event.flow[index], event.flow[index + 1]));
  }
  return edges;
}

function renderRunOptions() {
  runSelect.innerHTML = "";
  state.runs.forEach((run) => {
    const option = document.createElement("option");
    option.value = run.run_id;
    option.textContent = `${run.run_id} / ${run.target_id}`;
    runSelect.appendChild(option);
  });
  runSelect.value = state.runId;
}

function renderFilterOptions() {
  const phaseSet = new Set(["ALL"]);
  const toolSet = new Set(["ALL"]);
  state.timeline.forEach((event) => {
    phaseSet.add(event.phase);
    toolSet.add(event.tool);
  });

  phaseSelect.innerHTML = "";
  Array.from(phaseSet).forEach((phase) => {
    const option = document.createElement("option");
    option.value = phase;
    option.textContent = phase;
    phaseSelect.appendChild(option);
  });
  phaseSelect.value = state.filters.phase;

  toolSelect.innerHTML = "";
  Array.from(toolSet).forEach((tool) => {
    const option = document.createElement("option");
    option.value = tool;
    option.textContent = tool;
    toolSelect.appendChild(option);
  });
  toolSelect.value = state.filters.tool;
}

function renderTimeline() {
  timelineEl.innerHTML = "";
  state.timeline.forEach((event, index) => {
    const node = tpl.content.firstElementChild.cloneNode(true);
    const button = node.querySelector(".timeline-btn");
    node.querySelector(".time").textContent = `${event.time} / ${event.phase}`;
    node.querySelector(".title").textContent = event.title;
    node.querySelector(".meta").textContent = `${event.tool} • ${event.id}`;
    button.addEventListener("click", () => setActive(index));
    if (index === state.activeIndex) button.classList.add("active");
    timelineEl.appendChild(node);
  });
}

function drawGraph() {
  const event = selectedEvent();
  const activeFlow = new Set(event ? event.flow : []);
  const edges = activeEdgeSet();
  graphEl.innerHTML = "";

  state.graph.edges.forEach(([from, to]) => {
    const src = state.graph.nodes.find((node) => node.id === from);
    const dst = state.graph.nodes.find((node) => node.id === to);
    if (!src || !dst) return;

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", src.x);
    line.setAttribute("y1", src.y);
    line.setAttribute("x2", dst.x);
    line.setAttribute("y2", dst.y);
    line.setAttribute("stroke", edges.has(edgeKey(from, to)) ? "#44c2ff" : "#495d75");
    line.setAttribute("stroke-width", edges.has(edgeKey(from, to)) ? "3" : "1.8");
    line.setAttribute("opacity", edges.has(edgeKey(from, to)) ? "1" : "0.7");
    graphEl.appendChild(line);
  });

  state.graph.nodes.forEach((node) => {
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", String(node.x - 56));
    rect.setAttribute("y", String(node.y - 22));
    rect.setAttribute("width", "112");
    rect.setAttribute("height", "44");
    rect.setAttribute("rx", "10");
    rect.setAttribute("fill", activeFlow.has(node.id) ? "#24425f" : "#1f2a38");
    rect.setAttribute("stroke", activeFlow.has(node.id) ? "#5ec3ff" : "#4b6078");
    rect.setAttribute("stroke-width", activeFlow.has(node.id) ? "2.3" : "1");
    group.appendChild(rect);

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", String(node.x));
    text.setAttribute("y", String(node.y + 5));
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", "#dce6f0");
    text.setAttribute("font-size", "12");
    text.textContent = node.label;
    group.appendChild(text);

    group.style.cursor = "pointer";
    group.addEventListener("click", () => renderNodeDetails(node.id));
    graphEl.appendChild(group);
  });
}

function renderPathOptions() {
  if (!state.hlapiContext) return;
  const paths = state.hlapiContext.path_contexts || [];
  pathSelect.innerHTML = "";
  paths.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.path;
    option.textContent = item.path;
    pathSelect.appendChild(option);
  });
  if (!state.selectedPath && paths.length) {
    state.selectedPath = paths[0].path;
  }
  pathSelect.value = state.selectedPath;
}

function renderContextChips(siblings) {
  siblingListEl.innerHTML = "";
  (siblings || []).forEach((name) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = name;
    siblingListEl.appendChild(chip);
  });
}

function renderSourceOutlineLines(lines) {
  sourceOutlineEl.innerHTML = "";
  (lines || []).forEach((line) => {
    if (line.kind === "loop") {
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = line.text;
      details.appendChild(summary);
      (line.children || []).forEach((child) => {
        const childNode = document.createElement("div");
        childNode.className = "outline-child mono";
        childNode.textContent = child;
        details.appendChild(childNode);
      });
      sourceOutlineEl.appendChild(details);
      return;
    }
    const div = document.createElement("div");
    div.className = "outline-line mono";
    div.textContent = line.text;
    sourceOutlineEl.appendChild(div);
  });
}

function renderHlapiContext() {
  if (!state.hlapiContext) return;
  const context = (state.hlapiContext.path_contexts || []).find((item) => item.path === state.selectedPath);
  if (!context) return;

  const compile = state.hlapiContext.compile_context || {};
  pathMetaEl.innerHTML = [
    `<div><b>Path</b> <span class="mono">${escapeHtml(context.path)}</span></div>`,
    `<div><b>Compile DB</b> <span class="mono">${escapeHtml(compile.compile_commands_ref || "")}</span></div>`,
    `<div><b>Compile Entries</b> ${escapeHtml(compile.entries_total || 0)} (wld/radio=${escapeHtml(compile.wld_or_radio_entries || 0)})</div>`
  ].join("");

  renderContextChips(context.siblings || []);

  if (context.path.includes("Security")) {
    odlContextEl.innerHTML = [
      `<div><b>ODL File</b> <span class="mono">${escapeHtml(context.odl_file || "")}</span></div>`,
      `<div><b>ODL Line</b> ${escapeHtml(context.odl_line || "-")}</div>`,
      `<div><b>Object Scope</b> ${escapeHtml(context.object_scope || "")}</div>`,
      `<div><b>Hint</b> 同階欄位由 Security object 直接展開</div>`
    ].join("");
    renderSourceOutlineLines([
      {
        kind: "statement",
        text: "Security 同階參數已展開（KeyPassPhrase/MFPConfig/ModesAvailable ...）"
      }
    ]);
    return;
  }

  const sourceMapping = context.source_mapping || {};
  const legacy = context.legacy_sample || {};
  const legacySnippet = (legacy.snippet || []).map((line) => `<div class=\"mono\">${escapeHtml(line)}</div>`).join("");
  odlContextEl.innerHTML = [
    `<div><b>ODL File</b> <span class="mono">${escapeHtml(context.odl_file || "")}</span></div>`,
    `<div><b>Entry</b> ${escapeHtml(context.entry_function || "")} @ line ${escapeHtml(context.odl_entry_line || "-")}</div>`,
    `<div><b>Stats Field</b> BytesReceived @ line ${escapeHtml(context.odl_stats_line || "-")}</div>`,
    `<div><b>Source File</b> <span class="mono">${escapeHtml(sourceMapping.source_file || "")}</span></div>`,
    `<div><b>Source Function</b> ${escapeHtml(sourceMapping.source_function || "")} @ line ${escapeHtml(sourceMapping.source_entry_line || "-")}</div>`,
    `<hr>`,
    `<div><b>Legacy Snippet</b> ${escapeHtml(legacy.odl_entry || "")}</div>`,
    legacySnippet
  ].join("");

  const outline = [...(context.source_outline || [])];
  (context.sibling_functions || []).forEach((fn) => {
    outline.push({
      kind: "loop",
      text: `function ${fn.name}() @ line ${fn.line} (expand)`,
      children: (fn.outline || []).map((item) => {
        if (item.kind === "loop") {
          return `${item.text} => ${item.children.join(" ; ")}`;
        }
        return item.text;
      })
    });
  });
  renderSourceOutlineLines(outline);
}

async function renderEventDetails() {
  const event = selectedEvent();
  if (!event) {
    detailsEl.innerHTML = '<div class="badge b-warn">NO EVENT</div>';
    return;
  }

  const detail = await api.getEventDetail(state.runId, event.id);
  detailsEl.innerHTML = `
    <div>${statusBadge(detail.status)}${consensusBadge(detail.consensus)}</div>
    <div>${runBadge(state.runs.find((run) => run.run_id === state.runId)?.status || "unknown")}</div>
    <div><b>Run</b> <span class="mono">${escapeHtml(state.runMeta.run_id)}</span></div>
    <div><b>Target</b> <span class="mono">${escapeHtml(state.runMeta.target_id)}</span></div>
    <div><b>Summary</b> ${escapeHtml(state.runMeta.summary || "")}</div>
    <hr>
    <div><b>Event</b> <span class="mono">${escapeHtml(detail.id)}</span></div>
    <div><b>Time</b> ${escapeHtml(detail.time)}</div>
    <div><b>Tool</b> ${escapeHtml(detail.tool)}</div>
    <div><b>Title</b> ${escapeHtml(detail.title)}</div>
    <div><b>Symbol</b> <span class="mono">${escapeHtml(detail.symbol)}</span></div>
    <div><b>Address</b> <span class="mono">${escapeHtml(detail.address)}</span></div>
    <div><b>Evidence</b> <span class="mono">${escapeHtml((detail.evidence || []).join(", "))}</span></div>
    <div><b>Flow</b> <span class="mono">${escapeHtml((detail.flow || []).join(" -> "))}</span></div>
  `;
}

async function renderNodeDetails(nodeId) {
  const detail = await api.getNodeDetail(state.runId, nodeId);
  if (!detail) return;

  detailsEl.innerHTML = `
    <div><span class="badge b-info">NODE DRILLDOWN</span></div>
    <div><b>Node</b> <span class="mono">${escapeHtml(detail.id)}</span></div>
    <div><b>Label</b> ${escapeHtml(detail.label)}</div>
    <div><b>Type</b> ${escapeHtml(detail.type)}</div>
    <div><b>Related Events</b> ${detail.relatedEvents.length}</div>
    <hr>
    <div class="mono">
      ${detail.relatedEvents
        .map((event) => `${escapeHtml(event.time)} ${escapeHtml(event.id)} ${escapeHtml(event.tool)} ${escapeHtml(event.consensus)}`)
        .join("<br>")}
    </div>
  `;
}

function updateStats() {
  statsEl.textContent = `${state.timeline.length} events`;
}

function updateHint() {
  const event = selectedEvent();
  if (!event) {
    hintEl.textContent = "Current replay: no data";
    return;
  }
  hintEl.textContent = `Current replay: ${event.id} / ${event.phase} / ${event.tool}`;
}

async function setActive(index) {
  if (!state.timeline.length) {
    state.activeIndex = 0;
    renderTimeline();
    drawGraph();
    updateStats();
    updateHint();
    await renderEventDetails();
    return;
  }

  state.activeIndex = Math.max(0, Math.min(index, state.timeline.length - 1));
  state.activeEventId = state.timeline[state.activeIndex].id;
  renderTimeline();
  drawGraph();
  updateStats();
  updateHint();
  await renderEventDetails();
}

function tickNext() {
  if (!state.timeline.length) return;
  const next = (state.activeIndex + 1) % state.timeline.length;
  setActive(next);
}

function startPlay() {
  if (state.timerId) return;
  const interval = Number(speedSelect.value);
  playBtn.textContent = "Pause";
  state.timerId = setInterval(tickNext, interval);
}

function stopPlay() {
  if (!state.timerId) return;
  clearInterval(state.timerId);
  state.timerId = null;
  playBtn.textContent = "Play";
}

async function refreshTimeline() {
  const payload = await api.getTimeline(state.runId, state.filters);
  state.timeline = payload.events;
  renderFilterOptions();

  let index = 0;
  if (state.activeEventId) {
    const found = state.timeline.findIndex((event) => event.id === state.activeEventId);
    if (found >= 0) index = found;
  }
  await setActive(index);
}

async function loadRun(runId) {
  stopPlay();
  state.runId = runId;
  state.runMeta = await api.getRun(runId);
  state.graph = await api.getGraph(runId);
  state.activeIndex = 0;
  state.activeEventId = "";
  await refreshTimeline();
}

function bindEvents() {
  playBtn.addEventListener("click", () => {
    if (state.timerId) {
      stopPlay();
      return;
    }
    startPlay();
  });

  prevBtn.addEventListener("click", () => {
    stopPlay();
    if (!state.timeline.length) return;
    const prev = state.activeIndex === 0 ? state.timeline.length - 1 : state.activeIndex - 1;
    setActive(prev);
  });

  nextBtn.addEventListener("click", () => {
    stopPlay();
    tickNext();
  });

  speedSelect.addEventListener("change", () => {
    if (!state.timerId) return;
    stopPlay();
    startPlay();
  });

  runSelect.addEventListener("change", () => loadRun(runSelect.value));

  applyFilterBtn.addEventListener("click", async () => {
    state.filters.phase = phaseSelect.value;
    state.filters.tool = toolSelect.value;
    state.filters.keyword = searchInput.value.trim();
    await refreshTimeline();
  });

  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      applyFilterBtn.click();
    }
  });

  pathSelect.addEventListener("change", async () => {
    state.selectedPath = pathSelect.value;
    const context = await api.getPathContext(state.selectedPath);
    if (context) {
      renderHlapiContext();
    }
  });
}

async function bootstrap() {
  bindEvents();

  state.hlapiContext = await api.getHlapiContext();
  const firstPath = state.hlapiContext?.path_contexts?.[0]?.path || "";
  state.selectedPath = firstPath;
  renderPathOptions();
  renderHlapiContext();

  state.runs = await api.listRuns();
  if (!state.runs.length) {
    detailsEl.innerHTML = '<div class="badge b-danger">NO MOCK RUNS</div>';
    return;
  }
  state.runId = state.runs[0].run_id;
  renderRunOptions();
  await loadRun(state.runId);
}

bootstrap();

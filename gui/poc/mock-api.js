const MOCK_DELAY_MS = 120;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`mock api load failed: ${path}`);
  }
  return response.json();
}

function containsKeyword(event, keyword) {
  const text = [
    event.id,
    event.phase,
    event.tool,
    event.title,
    event.symbol,
    event.address,
    ...(event.evidence || [])
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return text.includes(keyword.toLowerCase());
}

export class MockDebugApi {
  constructor(basePath = "./mock-data") {
    this.basePath = basePath;
    this.runCache = new Map();
    this.contextCache = null;
  }

  async listRuns() {
    await delay(MOCK_DELAY_MS);
    const data = await loadJson(`${this.basePath}/runs.json`);
    return data.runs || [];
  }

  async getRunBundle(runId) {
    if (!this.runCache.has(runId)) {
      const bundle = await loadJson(`${this.basePath}/${runId}.json`);
      this.runCache.set(runId, bundle);
    }
    await delay(MOCK_DELAY_MS);
    return this.runCache.get(runId);
  }

  async getRun(runId) {
    const bundle = await this.getRunBundle(runId);
    return bundle.run;
  }

  async getGraph(runId) {
    const bundle = await this.getRunBundle(runId);
    return { nodes: bundle.nodes, edges: bundle.edges };
  }

  async getTimeline(runId, filters = {}) {
    const bundle = await this.getRunBundle(runId);
    const phase = filters.phase || "ALL";
    const tool = filters.tool || "ALL";
    const keyword = (filters.keyword || "").trim();

    const events = bundle.events.filter((event) => {
      if (phase !== "ALL" && event.phase !== phase) return false;
      if (tool !== "ALL" && event.tool !== tool) return false;
      if (keyword && !containsKeyword(event, keyword)) return false;
      return true;
    });

    return {
      run_id: runId,
      count: events.length,
      events
    };
  }

  async getEventDetail(runId, eventId) {
    const bundle = await this.getRunBundle(runId);
    return bundle.events.find((event) => event.id === eventId) || null;
  }

  async getNodeDetail(runId, nodeId) {
    const bundle = await this.getRunBundle(runId);
    const node = bundle.nodes.find((item) => item.id === nodeId) || null;
    if (!node) return null;
    const relatedEvents = bundle.events.filter((event) => event.flow.includes(nodeId));
    return {
      ...node,
      relatedEvents
    };
  }

  async getHlapiContext() {
    if (!this.contextCache) {
      this.contextCache = await loadJson(`${this.basePath}/hlapi-context.json`);
    }
    await delay(MOCK_DELAY_MS);
    return this.contextCache;
  }

  async getPathContext(path) {
    const context = await this.getHlapiContext();
    const item = (context.path_contexts || []).find((entry) => entry.path === path);
    await delay(MOCK_DELAY_MS);
    return item || null;
  }
}

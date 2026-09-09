import assert from "node:assert/strict";
import test from "node:test";

import {
  MODERN_PROTOCOL_VERSION,
  SERVER_INFO,
  SUPPORTED_PROTOCOL_VERSIONS,
  TOOL_DEFINITIONS,
  createRequestHandler,
} from "../src/server.mjs";

const TOOL_NAMES = [
  "base120_get",
  "base120_list",
  "base120_prompt",
  "base120_search",
];

test("server advertises a bounded read-only identity", () => {
  assert.deepEqual(SERVER_INFO, {
    name: "hummbl-mcp-base120",
    version: "0.1.0-canary.0",
  });
  assert.deepEqual(
    TOOL_DEFINITIONS.map(({ name }) => name).sort(),
    TOOL_NAMES,
  );
  for (const tool of TOOL_DEFINITIONS) {
    assert.equal(tool.annotations.readOnlyHint, true);
    assert.equal(tool.annotations.destructiveHint, false);
  }
});

test("initialize and discovery expose tools but no resources or prompts", async () => {
  const handleRequest = createRequestHandler();
  const initialized = await handleRequest({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2025-06-18",
      capabilities: {},
      clientInfo: { name: "test", version: "1" },
    },
  });
  assert.equal(initialized.result.protocolVersion, "2025-06-18");
  assert.deepEqual(initialized.result.serverInfo, SERVER_INFO);
  assert.deepEqual(initialized.result.capabilities, { tools: {} });

  const latestLegacyHandler = createRequestHandler();
  const latestLegacy = await latestLegacyHandler({
    jsonrpc: "2.0",
    id: "legacy-latest",
    method: "initialize",
    params: {
      protocolVersion: MODERN_PROTOCOL_VERSION,
      capabilities: {},
      clientInfo: { name: "test", version: "1" },
    },
  });
  assert.equal(latestLegacy.result.protocolVersion, "2025-11-25");

  const tools = await handleRequest({ jsonrpc: "2.0", id: 2, method: "tools/list" });
  assert.deepEqual(
    tools.result.tools.map(({ name }) => name).sort(),
    TOOL_NAMES,
  );
  assert.deepEqual(
    await handleRequest({ jsonrpc: "2.0", id: 3, method: "resources/list" }),
    { jsonrpc: "2.0", id: 3, result: { resources: [] } },
  );
  assert.deepEqual(
    await handleRequest({ jsonrpc: "2.0", id: 4, method: "prompts/list" }),
    { jsonrpc: "2.0", id: 4, result: { prompts: [] } },
  );
});

test("modern discovery and requests use per-request metadata", async () => {
  const handleRequest = createRequestHandler();
  const metadata = {
    "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL_VERSION,
    "io.modelcontextprotocol/clientCapabilities": {},
    "io.modelcontextprotocol/clientInfo": { name: "test", version: "1" },
  };
  const discovered = await handleRequest({
    jsonrpc: "2.0",
    id: "discover",
    method: "server/discover",
    params: { _meta: metadata },
  });
  assert.deepEqual(discovered.result.supportedVersions, SUPPORTED_PROTOCOL_VERSIONS);
  assert.equal(discovered.result.resultType, "complete");
  assert.deepEqual(discovered.result._meta["io.modelcontextprotocol/serverInfo"], SERVER_INFO);

  const tools = await handleRequest({
    jsonrpc: "2.0",
    id: "modern-tools",
    method: "tools/list",
    params: { _meta: metadata },
  });
  assert.equal(tools.result.resultType, "complete");
  assert.deepEqual(tools.result._meta["io.modelcontextprotocol/serverInfo"], SERVER_INFO);
  assert.deepEqual(tools.result.tools.map(({ name }) => name).sort(), TOOL_NAMES);
});

test("modern requests reject unsupported protocol versions", async () => {
  const handleRequest = createRequestHandler();
  const response = await handleRequest({
    jsonrpc: "2.0",
    id: "unsupported",
    method: "server/discover",
    params: {
      _meta: {
        "io.modelcontextprotocol/protocolVersion": "2099-01-01",
        "io.modelcontextprotocol/clientCapabilities": {},
      },
    },
  });
  assert.equal(response.error.code, -32022);
  assert.deepEqual(response.error.data, {
    supported: SUPPORTED_PROTOCOL_VERSIONS,
    requested: "2099-01-01",
  });
});

test("tool calls return structured content with stable errors", async () => {
  const handleRequest = createRequestHandler();
  await handleRequest({
    jsonrpc: "2.0",
    id: "initialize-tools",
    method: "initialize",
    params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "test", version: "1" } },
  });
  const found = await handleRequest({
    jsonrpc: "2.0",
    id: 5,
    method: "tools/call",
    params: { name: "base120_get", arguments: { code: "IN6" } },
  });
  assert.equal(found.result.structuredContent.model.code, "IN6");
  assert.equal(found.result.isError, false);
  assert.equal(found.result.content[0].type, "text");

  const missing = await handleRequest({
    jsonrpc: "2.0",
    id: 6,
    method: "tools/call",
    params: { name: "base120_get", arguments: { code: "BAD" } },
  });
  assert.equal(missing.result.isError, true);
  assert.match(missing.result.content[0].text, /code must be a Base120 code/i);

  const unknownTool = await handleRequest({
    jsonrpc: "2.0",
    id: 7,
    method: "tools/call",
    params: { name: "kill_switch", arguments: { action: "reset" } },
  });
  assert.equal(unknownTool.error.code, -32602);
  assert.match(unknownTool.error.message, /unknown tool/i);
});

test("all four tools and protocol ping execute through the request handler", async () => {
  const handleRequest = createRequestHandler();
  await handleRequest({
    jsonrpc: "2.0",
    id: "initialize-all-tools",
    method: "initialize",
    params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "test", version: "1" } },
  });
  const listed = await handleRequest({
    jsonrpc: "2.0",
    id: 9,
    method: "tools/call",
    params: { name: "base120_list", arguments: { transformation: "SY" } },
  });
  assert.equal(listed.result.structuredContent.count, 20);

  const searched = await handleRequest({
    jsonrpc: "2.0",
    id: 10,
    method: "tools/call",
    params: { name: "base120_search", arguments: { query: "foundational truths", limit: 1 } },
  });
  assert.equal(searched.result.structuredContent.models[0].code, "P1");

  const prompted = await handleRequest({
    jsonrpc: "2.0",
    id: 11,
    method: "tools/call",
    params: { name: "base120_prompt", arguments: { code: "P1", question: "Why?" } },
  });
  assert.match(prompted.result.structuredContent.prompt, /Question: Why\?/);

  assert.deepEqual(await handleRequest({ jsonrpc: "2.0", id: 12, method: "ping" }), {
    jsonrpc: "2.0",
    id: 12,
    result: {},
  });
});

test("malformed requests and tool arguments fail closed", async () => {
  const handleRequest = createRequestHandler();
  assert.deepEqual(await handleRequest(undefined), {
    jsonrpc: "2.0",
    id: null,
    error: { code: -32600, message: "Invalid Request" },
  });
  await handleRequest({
    jsonrpc: "2.0",
    id: "initialize-validation",
    method: "initialize",
    params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "test", version: "1" } },
  });
  const malformed = await handleRequest({
    jsonrpc: "2.0",
    id: 13,
    method: "tools/call",
    params: { name: "base120_list", arguments: [] },
  });
  assert.equal(malformed.result.isError, true);
  assert.match(malformed.result.content[0].text, /arguments must be an object/i);

  for (const [name, args, expected] of [
    ["base120_get", { code: 1 }, /code must be a Base120 code/i],
    ["base120_list", { transformation: "BAD" }, /transformation must be one of/i],
    ["base120_search", { query: "" }, /query must be a non-empty string/i],
    ["base120_search", { query: "truth", limit: 51 }, /limit must be an integer between 1 and 50/i],
    ["base120_prompt", { code: "P1", question: "" }, /question must be a non-empty string/i],
    ["base120_list", { extra: true }, /unexpected argument: extra/i],
  ]) {
    const invalid = await handleRequest({
      jsonrpc: "2.0",
      id: `invalid-${name}-${String(args.limit ?? "args")}`,
      method: "tools/call",
      params: { name, arguments: args },
    });
    assert.equal(invalid.result.isError, true);
    assert.match(invalid.result.content[0].text, expected);
  }
});

test("notifications do not emit JSON-RPC responses", async () => {
  const handleRequest = createRequestHandler();
  assert.equal(
    await handleRequest({ jsonrpc: "2.0", method: "notifications/initialized" }),
    undefined,
  );
});

test("unknown methods return JSON-RPC method-not-found", async () => {
  const handleRequest = createRequestHandler();
  await handleRequest({
    jsonrpc: "2.0",
    id: "initialize-unknown-method",
    method: "initialize",
    params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "test", version: "1" } },
  });
  assert.deepEqual(
    await handleRequest({ jsonrpc: "2.0", id: 8, method: "governance/reset" }),
    {
      jsonrpc: "2.0",
      id: 8,
      error: { code: -32601, message: "Method not found: governance/reset" },
    },
  );
});

import { catalogMetadata, formatPrompt, getModel, listModels, searchModels } from "./catalog.mjs";

export const MODERN_PROTOCOL_VERSION = "2026-07-28";
export const LEGACY_PROTOCOL_VERSIONS = Object.freeze(["2025-11-25", "2025-06-18"]);
export const SUPPORTED_PROTOCOL_VERSIONS = Object.freeze([
  MODERN_PROTOCOL_VERSION,
  ...LEGACY_PROTOCOL_VERSIONS,
]);

export const SERVER_INFO = Object.freeze({
  name: "hummbl-mcp-base120",
  version: "0.1.0-canary.0",
});

const SERVER_INSTRUCTIONS = "Read-only, deterministic Base120 catalog. No network egress or telemetry.";
const SERVER_CAPABILITIES = Object.freeze({ tools: {} });
const PROTOCOL_VERSION_META_KEY = "io.modelcontextprotocol/protocolVersion";
const CLIENT_CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities";
const SERVER_INFO_META_KEY = "io.modelcontextprotocol/serverInfo";
const BASE120_CODE_PATTERN = /^(P|IN|CO|DE|RE|SY)([1-9]|1[0-9]|20)$/;
const TRANSFORMATIONS = Object.freeze(["P", "IN", "CO", "DE", "RE", "SY"]);

const READ_ONLY_ANNOTATIONS = Object.freeze({
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
});

export const TOOL_DEFINITIONS = Object.freeze([
  {
    name: "base120_get",
    description: "Return one Base120 model by code.",
    inputSchema: {
      type: "object",
      properties: { code: { type: "string", pattern: BASE120_CODE_PATTERN.source } },
      required: ["code"],
      additionalProperties: false,
    },
    annotations: READ_ONLY_ANNOTATIONS,
  },
  {
    name: "base120_list",
    description: "List Base120 models, optionally filtered by transformation code.",
    inputSchema: {
      type: "object",
      properties: { transformation: { type: "string", enum: TRANSFORMATIONS } },
      additionalProperties: false,
    },
    annotations: READ_ONLY_ANNOTATIONS,
  },
  {
    name: "base120_search",
    description: "Search Base120 model codes, names, and definitions.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", minLength: 1 },
        limit: { type: "integer", minimum: 1, maximum: 50, default: 10 },
      },
      required: ["query"],
      additionalProperties: false,
    },
    annotations: READ_ONLY_ANNOTATIONS,
  },
  {
    name: "base120_prompt",
    description: "Format a deterministic local prompt for a Base120 model and question.",
    inputSchema: {
      type: "object",
      properties: {
        code: { type: "string", pattern: BASE120_CODE_PATTERN.source },
        question: { type: "string", minLength: 1 },
      },
      required: ["code", "question"],
      additionalProperties: false,
    },
    annotations: READ_ONLY_ANNOTATIONS,
  },
]);

const TOOL_NAMES = new Set(TOOL_DEFINITIONS.map(({ name }) => name));

function toolSuccess(structuredContent) {
  return {
    content: [{ type: "text", text: JSON.stringify(structuredContent) }],
    structuredContent,
    isError: false,
  };
}

function toolError(message) {
  return {
    content: [{ type: "text", text: message }],
    structuredContent: { error: message },
    isError: true,
  };
}

function errorResponse(id, code, message, data) {
  const error = { code, message };
  if (data !== undefined) error.data = data;
  return { jsonrpc: "2.0", id, error };
}

function requireArguments(value) {
  if (value === undefined) return {};
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Tool arguments must be an object");
  }
  return value;
}

function validateKeys(args, allowed, required = []) {
  for (const key of Object.keys(args)) {
    if (!allowed.includes(key)) throw new Error(`Unexpected argument: ${key}`);
  }
  for (const key of required) {
    if (!(key in args)) throw new Error(`Missing required argument: ${key}`);
  }
}

function validateCode(code) {
  if (typeof code !== "string" || !BASE120_CODE_PATTERN.test(code)) {
    throw new Error("Code must be a Base120 code such as P1, IN6, or SY20");
  }
}

function callTool(name, rawArguments) {
  const args = requireArguments(rawArguments);
  if (name === "base120_get") {
    validateKeys(args, ["code"], ["code"]);
    validateCode(args.code);
    const model = getModel(args.code);
    if (!model) throw new Error(`Unknown Base120 code: ${args.code}`);
    return { model, catalog: catalogMetadata };
  }
  if (name === "base120_list") {
    validateKeys(args, ["transformation"]);
    if (args.transformation !== undefined && !TRANSFORMATIONS.includes(args.transformation)) {
      throw new Error(`Transformation must be one of: ${TRANSFORMATIONS.join(", ")}`);
    }
    const models = listModels({ transformation: args.transformation });
    return { models, count: models.length, catalog: catalogMetadata };
  }
  if (name === "base120_search") {
    validateKeys(args, ["query", "limit"], ["query"]);
    if (typeof args.query !== "string" || !args.query.trim()) {
      throw new Error("Query must be a non-empty string");
    }
    if (args.limit !== undefined && (!Number.isInteger(args.limit) || args.limit < 1 || args.limit > 50)) {
      throw new Error("Limit must be an integer between 1 and 50");
    }
    const models = searchModels(args.query, { limit: args.limit });
    return { query: args.query, models, count: models.length, catalog: catalogMetadata };
  }
  if (name === "base120_prompt") {
    validateKeys(args, ["code", "question"], ["code", "question"]);
    validateCode(args.code);
    if (typeof args.question !== "string" || !args.question.trim()) {
      throw new Error("Question must be a non-empty string");
    }
    return { code: args.code, prompt: formatPrompt(args.code, args.question), catalog: catalogMetadata };
  }
  throw new Error(`Unknown tool: ${String(name ?? "(empty)")}`);
}

function modernProtocolVersion(request) {
  return request.params?._meta?.[PROTOCOL_VERSION_META_KEY];
}

function resultResponse(id, result, modern) {
  if (!modern) return { jsonrpc: "2.0", id, result };
  return {
    jsonrpc: "2.0",
    id,
    result: {
      resultType: "complete",
      ...result,
      _meta: {
        ...(result._meta ?? {}),
        [SERVER_INFO_META_KEY]: SERVER_INFO,
      },
    },
  };
}

function validateModernMetadata(request, requestedVersion) {
  if (requestedVersion !== MODERN_PROTOCOL_VERSION) {
    return errorResponse(request.id, -32022, "Unsupported protocol version", {
      supported: SUPPORTED_PROTOCOL_VERSIONS,
      requested: requestedVersion,
    });
  }
  const clientCapabilities = request.params?._meta?.[CLIENT_CAPABILITIES_META_KEY];
  if (!clientCapabilities || typeof clientCapabilities !== "object" || Array.isArray(clientCapabilities)) {
    return errorResponse(request.id, -32602, `Missing or invalid ${CLIENT_CAPABILITIES_META_KEY}`);
  }
  return undefined;
}

export function createRequestHandler() {
  let legacyProtocolVersion;

  return async function handleRequest(request) {
    if (!request || request.jsonrpc !== "2.0" || typeof request.method !== "string") {
      return errorResponse(request?.id ?? null, -32600, "Invalid Request");
    }
    if (request.id === undefined) return undefined;

    if (request.method === "initialize") {
      const requestedVersion = request.params?.protocolVersion;
      if (typeof requestedVersion !== "string") {
        return errorResponse(request.id, -32602, "initialize requires a protocolVersion");
      }
      legacyProtocolVersion = LEGACY_PROTOCOL_VERSIONS.includes(requestedVersion)
        ? requestedVersion
        : LEGACY_PROTOCOL_VERSIONS[0];
      return resultResponse(request.id, {
        protocolVersion: legacyProtocolVersion,
        capabilities: SERVER_CAPABILITIES,
        serverInfo: SERVER_INFO,
        instructions: SERVER_INSTRUCTIONS,
      }, false);
    }

    const requestedVersion = modernProtocolVersion(request);
    const modern = requestedVersion !== undefined || request.method === "server/discover";
    if (modern) {
      const metadataError = validateModernMetadata(request, requestedVersion);
      if (metadataError) return metadataError;
    } else if (!legacyProtocolVersion) {
      return errorResponse(request.id, -32600, "Initialize the legacy session or provide modern request metadata");
    }

    if (request.method === "server/discover") {
      return resultResponse(request.id, {
        supportedVersions: SUPPORTED_PROTOCOL_VERSIONS,
        capabilities: SERVER_CAPABILITIES,
        instructions: SERVER_INSTRUCTIONS,
        ttlMs: 3600000,
        cacheScope: "public",
      }, true);
    }
    if (request.method === "ping") {
      return resultResponse(request.id, {}, modern);
    }
    if (request.method === "tools/list") {
      return resultResponse(request.id, { tools: TOOL_DEFINITIONS }, modern);
    }
    if (request.method === "resources/list") {
      return resultResponse(request.id, { resources: [] }, modern);
    }
    if (request.method === "prompts/list") {
      return resultResponse(request.id, { prompts: [] }, modern);
    }
    if (request.method === "tools/call") {
      const toolName = request.params?.name;
      if (!TOOL_NAMES.has(toolName)) {
        return errorResponse(request.id, -32602, `Unknown tool: ${String(toolName ?? "(empty)")}`);
      }
      let result;
      try {
        result = toolSuccess(callTool(toolName, request.params?.arguments));
      } catch (error) {
        result = toolError(error instanceof Error ? error.message : "Tool call failed");
      }
      return resultResponse(request.id, result, modern);
    }
    return errorResponse(request.id, -32601, `Method not found: ${request.method}`);
  };
}

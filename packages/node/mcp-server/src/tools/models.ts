/**
 * HUMMBL Mental Models Tools
 * MCP tool registrations for Base120 framework operations
 * Hybrid architecture: Local data for fast lookups, REST API for recommendations
 */

// fetch is a global in Cloudflare Workers environment

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import {
  TRANSFORMATIONS,
  PROBLEM_PATTERNS,
  PATTERN_BM25_INDEX,
  getAllModels,
  getModelByCode,
  searchModels,
  getModelsByTransformation,
  getTransformationByKey,
} from "../framework/base120.js";
import { isOk } from "../types/domain.js";
import { MCP_CONFIG } from "../config/mcp.js";

// REST API Configuration (from centralized config)
const API_CONFIG = {
  baseUrl: MCP_CONFIG.HUMMBL_API_URL,
  apiKey: MCP_CONFIG.HUMMBL_API_KEY,
} as const;

/**
 * Register public read-only model tools with the MCP server.
 * These 7 tools are safe for unauthenticated / public / free-tier access.
 * No write tools, no internal graph traversal, no user-data tools.
 */
export function registerPublicModelTools(server: McpServer): void {
  // Tool: Get specific model by code
  server.registerTool(
    "get_model",
    {
      title: "Get Mental Model by Code",
      description:
        "Retrieve detailed information about a specific HUMMBL mental model using its code (e.g., P1, IN3, CO5).",
      annotations: { readOnlyHint: true },
      inputSchema: z.object({
        code: z
          .string()
          .regex(/^(P|IN|CO|DE|RE|SY)\d{1,2}$/i)
          .describe("Model code (e.g., P1, IN3, CO5)"),
      }),
      outputSchema: z.object({
        code: z.string(),
        name: z.string(),
        definition: z.string(),
        priority: z.number(),
        transformation: z.string().nullable(),
      }),
    },
    async ({ code }) => {
      const normalizedCode = code.toUpperCase();
      const result = getModelByCode(normalizedCode);

      if (!isOk(result)) {
        return {
          content: [
            {
              type: "text",
              text: `Model code '${code}' not found in HUMMBL Base120 framework. Valid codes follow the pattern [P|IN|CO|DE|RE|SY][1-20].`,
            },
          ],
          isError: true,
        } as const;
      }

      const model = result.value;

      const transformation = Object.values(TRANSFORMATIONS).find((t) =>
        t.models.some((m) => m.code === model.code)
      );

      const payload = {
        code: model.code,
        name: model.name,
        definition: model.definition,
        priority: model.priority,
        transformation: transformation?.key ?? null,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ model: payload }, null, 2),
          },
        ],
        structuredContent: payload,
      } as const;
    }
  );

  // Tool: List all models
  server.registerTool(
    "list_all_models",
    {
      title: "List All Mental Models",
      description: "Retrieve complete list of all 120 HUMMBL mental models with basic information.",
      annotations: { readOnlyHint: true },
      inputSchema: z.object({
        transformation_filter: z
          .enum(["P", "IN", "CO", "DE", "RE", "SY"])
          .optional()
          .describe("Optional filter by transformation type"),
      }),
      outputSchema: z.object({
        total: z.number(),
        models: z.array(
          z.object({
            code: z.string(),
            name: z.string(),
            definition: z.string(),
            priority: z.number(),
            transformation: z.string(),
          })
        ),
      }),
    },
    async ({ transformation_filter }) => {
      let models = getAllModels();

      if (transformation_filter) {
        const result = getModelsByTransformation(transformation_filter);
        if (!isOk(result)) {
          return {
            content: [
              {
                type: "text",
                text: `Unable to list models for transformation '${transformation_filter}'.`,
              },
            ],
            isError: true,
          } as const;
        }
        models = result.value;
      }

      const enriched = models.map((m) => {
        const trans = Object.values(TRANSFORMATIONS).find((t) =>
          t.models.some((model) => model.code === m.code)
        );

        return {
          code: m.code,
          name: m.name,
          definition: m.definition,
          priority: m.priority,
          transformation: trans?.key ?? "UNKNOWN",
        };
      });

      const payload = {
        total: enriched.length,
        models: enriched,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(payload, null, 2),
          },
        ],
        structuredContent: payload,
      } as const;
    }
  );

  // Tool: Search models
  server.registerTool(
    "search_models",
    {
      title: "Search Mental Models",
      description: "Search HUMMBL mental models by keyword across codes, names, and definitions.",
      annotations: { readOnlyHint: true },
      inputSchema: z.object({
        query: z.string().min(2).describe("Search query (minimum 2 characters)"),
      }),
      outputSchema: z.object({
        query: z.string(),
        resultCount: z.number(),
        results: z.array(
          z.object({
            code: z.string(),
            name: z.string(),
            definition: z.string(),
            priority: z.number(),
            transformation: z.string(),
          })
        ),
      }),
    },
    async ({ query }) => {
      const result = searchModels(query);

      if (!isOk(result)) {
        return {
          content: [
            {
              type: "text",
              text: `Unable to search models: ${result.error.type}`,
            },
          ],
          isError: true,
        } as const;
      }

      const enriched = result.value.map((m) => {
        const trans = Object.values(TRANSFORMATIONS).find((t) =>
          t.models.some((model) => model.code === m.code)
        );
        return {
          code: m.code,
          name: m.name,
          definition: m.definition,
          priority: m.priority,
          transformation: trans?.key ?? "UNKNOWN",
        };
      });

      const payload = {
        query,
        resultCount: enriched.length,
        results: enriched,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(payload, null, 2),
          },
        ],
        structuredContent: payload,
      } as const;
    }
  );

  // Tool: Get transformation
  server.registerTool(
    "get_transformation",
    {
      title: "Get Transformation Details",
      description:
        "Retrieve information about a specific transformation type and all its models (P, IN, CO, DE, RE, SY).",
      annotations: { readOnlyHint: true },
      inputSchema: z.object({
        key: z
          .enum(["P", "IN", "CO", "DE", "RE", "SY"])
          .describe("Transformation key (P, IN, CO, DE, RE, or SY)"),
      }),
      outputSchema: z.object({
        key: z.string(),
        name: z.string(),
        description: z.string(),
        modelCount: z.number(),
        models: z.array(
          z.object({
            code: z.string(),
            name: z.string(),
            definition: z.string(),
            priority: z.number(),
          })
        ),
      }),
    },
    async ({ key }) => {
      const result = getTransformationByKey(key);

      if (!isOk(result)) {
        return {
          content: [
            {
              type: "text",
              text: `Transformation '${key}' not found. Valid keys are: P, IN, CO, DE, RE, SY.`,
            },
          ],
          isError: true,
        } as const;
      }

      const transformation = result.value;

      const payload = {
        key: transformation.key,
        name: transformation.name,
        description: transformation.description,
        modelCount: transformation.models.length,
        models: transformation.models,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(payload, null, 2),
          },
        ],
        structuredContent: payload,
      } as const;
    }
  );

  // Tool: Search problem patterns
  server.registerTool(
    "search_problem_patterns",
    {
      title: "Search Problem Patterns",
      description:
        "Find pre-defined problem patterns with recommended transformations and top models based on a search query.",
      annotations: { readOnlyHint: true },
      inputSchema: z.object({
        query: z.string().min(2).describe("Search query (minimum 2 characters)"),
      }),
      outputSchema: z.object({
        query: z.string(),
        patternCount: z.number(),
        patterns: z.array(
          z.object({
            pattern: z.string(),
            transformations: z.array(z.string()),
            topModels: z.array(z.string()),
            score: z.number(),
          })
        ),
      }),
    },
    async ({ query }) => {
      // BM25-ranked search: patterns are ordered by relevance score.
      // Only patterns with score > 0 are returned.
      const ranked = PATTERN_BM25_INDEX.score(query);
      const matchingPatterns = ranked
        .filter((r) => r.score > 0)
        .map((r) => ({
          ...PROBLEM_PATTERNS[r.index]!,
          score: Math.round(r.score * 1000) / 1000,
        }));

      const payload = {
        query,
        patternCount: matchingPatterns.length,
        patterns: matchingPatterns,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(payload, null, 2),
          },
        ],
        structuredContent: payload,
      } as const;
    }
  );

  // Tool: Recommend models based on problem description (USES REST API)
  server.registerTool(
    "recommend_models",
    {
      title: "Recommend Models for Problem",
      description:
        "Get recommended mental models based on a natural language problem description using HUMMBL REST API.",
      annotations: { readOnlyHint: true, openWorldHint: true },
      inputSchema: z.object({
        problem: z.string().min(10).describe("Detailed description of the problem or challenge"),
      }),
      outputSchema: z.object({
        problem: z.string(),
        recommendationCount: z.number(),
        recommendations: z.array(
          z.object({
            pattern: z.string(),
            transformations: z.array(
              z.object({
                key: z.string(),
                name: z.string(),
                description: z.string(),
              })
            ),
            topModels: z.array(
              z.object({
                code: z.string(),
                name: z.string(),
                definition: z.string(),
                priority: z.number(),
              })
            ),
          })
        ),
      }),
    },
    async ({ problem }) => {
      try {
        if (!API_CONFIG.apiKey) {
          return {
            content: [
              {
                type: "text",
                text: "HUMMBL API key not configured. Please set HUMMBL_API_KEY environment variable.",
              },
            ],
            isError: true,
            structuredContent: undefined,
          } as const;
        }

        const response = await fetch(`${API_CONFIG.baseUrl}/v1/recommend`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${API_CONFIG.apiKey}`,
          },
          body: JSON.stringify({ problem }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          return {
            content: [
              {
                type: "text",
                text: `API request failed: ${response.status} ${response.statusText}\n${errorText}`,
              },
            ],
            isError: true,
            structuredContent: undefined,
          } as const;
        }

        const payload = await response.json();

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(payload, null, 2),
            },
          ],
          structuredContent: payload as {
            problem: string;
            recommendationCount: number;
            recommendations: Array<{
              pattern: string;
              transformations: Array<{
                key: string;
                name: string;
                description: string;
              }>;
              topModels: Array<{
                code: string;
                name: string;
                definition: string;
                priority: number;
              }>;
            }>;
          },
        } as const;
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Failed to call HUMMBL API: ${error instanceof Error ? error.message : "Unknown error"}`,
            },
          ],
          isError: true,
          structuredContent: undefined,
        } as const;
      }
    }
  );

  // Tool: Get related models
  server.registerTool(
    "get_related_models",
    {
      title: "Get Related Mental Models",
      description: "Get all models related to a specific model with relationship details",
      inputSchema: z.object({
        code: z.string().describe("Model code (e.g., P1, DE7)"),
      }),
    },
    async ({ code }) => {
      try {
        const response = await fetch(
          `${API_CONFIG.baseUrl}/v1/models/${code.toUpperCase()}/relationships`,
          {
            headers: {
              Authorization: `Bearer ${API_CONFIG.apiKey}`,
            },
          }
        );

        if (!response.ok) {
          return {
            content: [
              {
                type: "text",
                text: `API request failed: ${response.status} ${response.statusText}`,
              },
            ],
            isError: true,
          };
        }

        const payload = (await response.json()) as Record<string, unknown>;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(payload, null, 2),
            },
          ],
          structuredContent: payload,
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Failed to get related models: ${error instanceof Error ? error.message : "Unknown error"}`,
            },
          ],
          isError: true,
        };
      }
    }
  );
}

/**
 * Register all model-related tools with the MCP server.
 * Includes public read-only tools PLUS internal-only tools
 * (add_relationship, get_recommendation_history).
 * Use this for the internal/admin MCP server only.
 */
export function registerModelTools(server: McpServer): void {
  // Register all public read-only tools first
  registerPublicModelTools(server);

  // Tool: Find relationship path (BFS)

  // Tool: Add relationship
  server.registerTool(
    "add_relationship",
    {
      title: "Add Model Relationship",
      description: "Add a relationship between two mental models with evidence.",
      inputSchema: z.object({
        source_code: z
          .string()
          .regex(/^(P|IN|CO|DE|RE|SY)\d{1,2}$/i)
          .describe("Source model code"),
        target_code: z
          .string()
          .regex(/^(P|IN|CO|DE|RE|SY)\d{1,2}$/i)
          .describe("Target model code"),
        relationship_type: z
          .string()
          .describe("Type of relationship (e.g., 'enables', 'reinforces')"),
        confidence: z
          .enum(["A", "B", "C"])
          .describe("Confidence level: A=High, B=Moderate, C=Hypothesis"),
        evidence: z.string().optional().describe("Evidence supporting this relationship"),
      }),
      outputSchema: z.object({
        success: z.boolean(),
        relationship: z.object({
          source_code: z.string(),
          target_code: z.string(),
          relationship_type: z.string(),
          confidence: z.string(),
          evidence: z.string().optional(),
        }),
      }),
    },
    async ({ source_code, target_code, relationship_type, confidence, evidence }) => {
      try {
        const response = await fetch(`${API_CONFIG.baseUrl}/v1/relationships`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${API_CONFIG.apiKey}`,
          },
          body: JSON.stringify({
            model_a: source_code,
            model_b: target_code,
            relationship_type,
            direction: "a→b",
            confidence,
            logical_derivation: evidence || "No evidence provided",
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          return {
            content: [
              {
                type: "text",
                text: `API request failed: ${response.status} ${response.statusText}\n${errorText}`,
              },
            ],
            isError: true,
          };
        }

        const payload = (await response.json()) as Record<string, unknown>;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(payload, null, 2),
            },
          ],
          structuredContent: payload,
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Failed to add relationship: ${error instanceof Error ? error.message : "Unknown error"}`,
            },
          ],
          isError: true,
        };
      }
    }
  );

  // Tool: Retrieve past recommendations for the authenticated caller
  server.registerTool(
    "get_recommendation_history",
    {
      title: "Get Recommendation History",
      description:
        "Fetch the caller's past recommendation calls (problems submitted and the model codes that were returned), newest first. Useful for 'what did we explore last time?' and for avoiding re-recommending the same models.",
      inputSchema: z.object({
        limit: z
          .number()
          .int()
          .min(1)
          .max(100)
          .optional()
          .describe("Max rows to return (default 20, max 100)"),
        offset: z.number().int().min(0).optional().describe("Pagination offset (default 0)"),
      }),
      outputSchema: z.object({
        count: z.number(),
        limit: z.number(),
        offset: z.number(),
        recommendations: z.array(
          z.object({
            id: z.string(),
            problem: z.string(),
            model_codes: z.array(z.string()),
            top_pattern: z.string().nullable(),
            created_at: z.string(),
          })
        ),
      }),
    },
    async ({ limit, offset }) => {
      if (!API_CONFIG.apiKey) {
        return {
          content: [
            {
              type: "text",
              text: "HUMMBL API key not configured. Set HUMMBL_API_KEY to retrieve recommendation history.",
            },
          ],
          isError: true,
          structuredContent: undefined,
        } as const;
      }

      const params = new URLSearchParams();
      if (limit !== undefined) params.set("limit", String(limit));
      if (offset !== undefined) params.set("offset", String(offset));
      const qs = params.toString();
      const url = `${API_CONFIG.baseUrl}/v1/recommendations${qs ? `?${qs}` : ""}`;

      try {
        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${API_CONFIG.apiKey}` },
        });

        if (!response.ok) {
          const errorText = await response.text();
          return {
            content: [
              {
                type: "text",
                text: `API request failed: ${response.status} ${response.statusText}\n${errorText}`,
              },
            ],
            isError: true,
            structuredContent: undefined,
          } as const;
        }

        const payload = (await response.json()) as {
          count: number;
          limit: number;
          offset: number;
          recommendations: Array<{
            id: string;
            problem: string;
            model_codes: string[];
            top_pattern: string | null;
            created_at: string;
          }>;
        };

        return {
          content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
          structuredContent: payload,
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Failed to fetch recommendation history: ${error instanceof Error ? error.message : "Unknown error"}`,
            },
          ],
          isError: true,
          structuredContent: undefined,
        } as const;
      }
    }
  );
}

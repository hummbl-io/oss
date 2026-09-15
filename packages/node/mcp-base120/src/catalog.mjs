import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const catalogText = readFileSync(new URL("../data/catalog.json", import.meta.url), "utf8");
const provenance = JSON.parse(
  readFileSync(new URL("../data/provenance.json", import.meta.url), "utf8"),
);
const parsedCatalog = JSON.parse(catalogText);

const actualCatalogHash = createHash("sha256").update(catalogText).digest("hex");
if (actualCatalogHash !== provenance.catalog.sha256) {
  throw new Error("Base120 catalog integrity check failed");
}
if (parsedCatalog.length !== provenance.catalog.model_count) {
  throw new Error("Base120 catalog count does not match provenance");
}

export const catalog = Object.freeze(
  parsedCatalog.map((model) => Object.freeze({ ...model })),
);
export const catalogMetadata = Object.freeze({
  schemaVersion: provenance.catalog.schema_version,
  modelCount: provenance.catalog.model_count,
  source: Object.freeze({ ...provenance.source }),
  catalog: Object.freeze({ ...provenance.catalog }),
});

const byCode = new Map(catalog.map((model) => [model.code, model]));

function normalizedText(value) {
  return typeof value === "string" ? value.trim() : "";
}

export function getModel(code) {
  return byCode.get(normalizedText(code).toUpperCase());
}

export function listModels({ transformation } = {}) {
  const family = normalizedText(transformation).toUpperCase();
  return family ? catalog.filter((model) => model.transformation === family) : [...catalog];
}

export function searchModels(query, { limit = 10 } = {}) {
  const needle = normalizedText(query).toLowerCase();
  if (!needle) return [];
  const boundedLimit = Number.isInteger(limit) ? Math.min(Math.max(limit, 1), 50) : 10;
  return catalog
    .filter((model) =>
      [model.code, model.name, model.definition, model.transformation]
        .join(" ")
        .toLowerCase()
        .includes(needle),
    )
    .slice(0, boundedLimit);
}

export function formatPrompt(code, question) {
  const model = getModel(code);
  if (!model) throw new Error(`Unknown Base120 code: ${normalizedText(code) || "(empty)"}`);
  const normalizedQuestion = normalizedText(question);
  if (!normalizedQuestion) throw new Error("Question must be non-empty");
  return [
    `Apply Base120 operator ${model.code} — ${model.name}.`,
    `Definition: ${model.definition}`,
    `Question: ${normalizedQuestion}`,
    "Respond with assumptions, analysis, and a bounded conclusion.",
  ].join("\n");
}

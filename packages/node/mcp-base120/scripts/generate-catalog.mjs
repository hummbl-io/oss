#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SOURCE_PATH = "packages/python/base120/Base120_Canonical_Model_Registry.yaml";
const SOURCE_URL = new URL("../../../python/base120/Base120_Canonical_Model_Registry.yaml", import.meta.url);
const CATALOG_URL = new URL("../data/catalog.json", import.meta.url);
const PROVENANCE_URL = new URL("../data/provenance.json", import.meta.url);
const CHECK = process.argv.includes("--check");
const CODE_RE = /^(P|IN|CO|DE|RE|SY)([1-9]|1[0-9]|20)$/;

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function scalar(raw) {
  const value = raw.trim();
  if (value.startsWith('"') && value.endsWith('"')) {
    return JSON.parse(value);
  }
  if (value.startsWith("'") && value.endsWith("'")) {
    return value.slice(1, -1).replaceAll("''", "'");
  }
  return value;
}

function parseRegistry(source) {
  const models = [];
  let current;

  for (const line of source.split("\n")) {
    const idMatch = line.match(/^\s*-\s+id:\s*(.+?)\s*$/);
    if (idMatch) {
      if (current) models.push(current);
      current = { code: scalar(idMatch[1]) };
      continue;
    }
    if (!current) continue;

    const nameMatch = line.match(/^\s+name:\s*(.+?)\s*$/);
    if (nameMatch) {
      current.name = scalar(nameMatch[1]);
      continue;
    }
    const definitionMatch = line.match(/^\s+definition:\s*(.+?)\s*$/);
    if (definitionMatch) current.definition = scalar(definitionMatch[1]);
  }
  if (current) models.push(current);

  for (const model of models) {
    if (!CODE_RE.test(model.code) || !model.name || !model.definition) {
      throw new Error(`invalid model in canonical registry: ${JSON.stringify(model)}`);
    }
    model.transformation = model.code.match(CODE_RE)[1];
  }

  if (models.length !== 120 || new Set(models.map(({ code }) => code)).size !== 120) {
    throw new Error(`canonical registry must contain 120 unique models; found ${models.length}`);
  }
  return models;
}

function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

async function expectedOutputs() {
  const raw = await readFile(SOURCE_URL, "utf8");
  const normalizedSource = raw.replaceAll("\r\n", "\n").replaceAll("\r", "\n");
  const catalogText = stableJson(parseRegistry(normalizedSource));
  const provenanceText = stableJson({
    schema_version: "hummbl.base120.catalog.provenance.v1",
    source: {
      repository: "https://github.com/hummbl-io/oss",
      path: SOURCE_PATH,
      normalization: "UTF-8 with CRLF and CR normalized to LF",
      sha256: sha256(normalizedSource),
    },
    catalog: {
      path: "packages/node/mcp-base120/data/catalog.json",
      schema_version: "hummbl.base120.catalog.v1",
      model_count: 120,
      sha256: sha256(catalogText),
    },
  });
  return { catalogText, provenanceText };
}

async function checkFile(url, expected) {
  let actual;
  try {
    actual = await readFile(url, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
  return actual === expected;
}

async function main() {
  const { catalogText, provenanceText } = await expectedOutputs();
  if (CHECK) {
    const catalogCurrent = await checkFile(CATALOG_URL, catalogText);
    const provenanceCurrent = await checkFile(PROVENANCE_URL, provenanceText);
    if (!catalogCurrent || !provenanceCurrent) {
      process.stderr.write("generated Base120 catalog or provenance is stale; run npm run generate\n");
      process.exitCode = 1;
    }
    return;
  }

  await mkdir(dirname(fileURLToPath(CATALOG_URL)), { recursive: true });
  await writeFile(CATALOG_URL, catalogText, "utf8");
  await writeFile(PROVENANCE_URL, provenanceText, "utf8");
}

await main();

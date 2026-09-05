import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdtemp, rm } from "node:fs/promises";
import test from "node:test";

import {
  catalog,
  catalogMetadata,
  formatPrompt,
  getModel,
  listModels,
  searchModels,
} from "../src/catalog.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));

test("catalog contains the frozen 6 x 20 Base120 set", () => {
  assert.equal(catalog.length, 120);
  assert.equal(new Set(catalog.map(({ code }) => code)).size, 120);

  const expected = { P: 20, IN: 20, CO: 20, DE: 20, RE: 20, SY: 20 };
  assert.deepEqual(
    Object.fromEntries(
      Object.keys(expected).map((transformation) => [
        transformation,
        catalog.filter((model) => model.transformation === transformation).length,
      ]),
    ),
    expected,
  );
});

test("catalog records expose only the v1 public fields", () => {
  for (const model of catalog) {
    assert.deepEqual(Object.keys(model).sort(), [
      "code",
      "definition",
      "name",
      "transformation",
    ]);
  }
});

test("get, list, and search are deterministic and case-insensitive", () => {
  assert.equal(getModel("in6")?.name, "Inverse/Proof by Contradiction");
  assert.equal(getModel("unknown"), undefined);
  assert.equal(listModels({ transformation: "sy" }).length, 20);
  assert.equal(listModels({ transformation: "bad" }).length, 0);

  const first = searchModels("foundational truths", { limit: 3 });
  const second = searchModels("FOUNDATIONAL TRUTHS", { limit: 3 });
  assert.deepEqual(first, second);
  assert.equal(first[0]?.code, "P1");
  assert.deepEqual(searchModels("", { limit: 3 }), []);
});

test("prompt formatting is local and stable", () => {
  assert.equal(
    formatPrompt("P1", "How should we validate this canary?"),
    [
      "Apply Base120 operator P1 — First Principles Framing.",
      "Definition: Reduce complex problems to foundational truths that cannot be further simplified",
      "Question: How should we validate this canary?",
      "Respond with assumptions, analysis, and a bounded conclusion.",
    ].join("\n"),
  );
  assert.throws(() => formatPrompt("bad", "question"), /unknown Base120 code/i);
  assert.throws(() => formatPrompt("P1", "   "), /question must be non-empty/i);
});

test("provenance binds the generated catalog to the canonical registry", () => {
  assert.equal(catalogMetadata.schemaVersion, "hummbl.base120.catalog.v1");
  assert.equal(catalogMetadata.modelCount, 120);
  assert.equal(
    catalogMetadata.source.path,
    "packages/python/base120/Base120_Canonical_Model_Registry.yaml",
  );
  assert.match(catalogMetadata.source.sha256, /^[a-f0-9]{64}$/);
  assert.match(catalogMetadata.catalog.sha256, /^[a-f0-9]{64}$/);
});

test("generated catalog matches the existing Python SDK representation", async () => {
  const pythonCatalog = JSON.parse(
    await readFile(
      join(HERE, "../../../python/base120/base120/data/operators.json"),
      "utf8",
    ),
  );
  assert.deepEqual(catalog, pythonCatalog);

  const registry = (
    await readFile(
      join(HERE, "../../../python/base120/Base120_Canonical_Model_Registry.yaml"),
      "utf8",
    )
  )
    .replaceAll("\r\n", "\n")
    .replaceAll("\r", "\n");
  assert.equal(
    createHash("sha256").update(registry).digest("hex"),
    catalogMetadata.source.sha256,
  );
});

test("local catalog use creates no files and imports no network modules", async () => {
  const emptyHome = await mkdtemp(join(tmpdir(), "mcp-base120-home-"));
  try {
    getModel("P1");
    listModels({ transformation: "P" });
    searchModels("systems");
    formatPrompt("P1", "test");
    assert.deepEqual(await readdir(emptyHome), []);

    for (const relative of ["../src/catalog.mjs", "../src/server.mjs", "../bin/mcp-base120.mjs"]) {
      const source = await readFile(join(HERE, relative), "utf8");
      assert.doesNotMatch(source, /node:(?:http|https|net|dgram)|\bfetch\s*\(/);
    }
  } finally {
    await rm(emptyHome, { recursive: true, force: true });
  }
});

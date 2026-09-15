import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  validateManifest,
  validateRepository,
} from "./validate_product_manifests.mjs";

const REPOSITORY_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

function validManifest() {
  return {
    $schema:
      "https://raw.githubusercontent.com/hummbl-io/oss/main/schemas/public/product-admission-v1.schema.json",
    schema_version: "hummbl.product.v1",
    product_id: "example-product",
    display_name: "Example Product",
    distribution: "@hummbl/example-product",
    lifecycle: "technical-canary",
    public_launch: false,
    admission: {
      decision: "hold",
      blockers: ["release-provenance"],
    },
    canonical_source: {
      repository: "hummbl-io/oss",
      path: "packages/node/example-product",
    },
    content_authorities: [
      {
        content_id: "example-corpus",
        repository: "hummbl-io/oss",
        path: "packages/python/example-corpus/catalog.yaml",
      },
    ],
    rights: {
      package_license: "UNLICENSED",
      software_license: "Apache-2.0",
      embedded_content: [
        {
          content_id: "example-corpus",
          license: "Proprietary",
          distribution_policy: "no-new-public-redistribution",
          decision_record: "docs/product/example-distribution-decision.md",
        },
      ],
    },
    contract: {
      version: "example.contract.v1",
      protocol_versions: ["2026-07-28"],
      tools: ["example_get"],
      mutations: false,
    },
    local_mode: {
      network_egress: false,
      telemetry: false,
      durable_writes: false,
    },
    excluded: ["customer data"],
  };
}

test("accepts a valid held technical canary", () => {
  assert.deepEqual(
    validateManifest(validManifest(), {
      packageManifest: { name: "@hummbl/example-product", private: true, license: "UNLICENSED" },
      decisionRecordExists: () => true,
    }),
    [],
  );
});

test("publishes a parseable v1 JSON Schema", async () => {
  const schema = JSON.parse(
    await readFile(join(REPOSITORY_ROOT, "schemas", "public", "product-admission-v1.schema.json")),
  );
  assert.equal(schema.$schema, "https://json-schema.org/draft/2020-12/schema");
  assert.equal(schema.$id, validManifest().$schema);
  assert.equal(schema.additionalProperties, false);
});

test("fails closed on unknown fields", () => {
  const manifest = validManifest();
  manifest.unreviewed = true;
  assert.match(
    validateManifest(manifest, {
      packageManifest: { name: "@hummbl/example-product", private: true, license: "UNLICENSED" },
      decisionRecordExists: () => true,
    }).join("\n"),
    /unknown field.*unreviewed/i,
  );
});

test("enforces admission and public-release invariants", () => {
  const manifest = validManifest();
  manifest.public_launch = true;
  manifest.admission = { decision: "admit", blockers: ["still-blocked"] };
  const issues = validateManifest(manifest, {
    packageManifest: { name: "@hummbl/example-product", private: true, license: "UNLICENSED" },
    decisionRecordExists: () => true,
  }).join("\n");
  assert.match(issues, /admit.*blockers/i);
  assert.match(issues, /private package/i);
  assert.match(issues, /no-new-public-redistribution/i);
});

test("requires restricted-content packages to remain private", () => {
  const issues = validateManifest(validManifest(), {
    packageManifest: { name: "@hummbl/example-product", private: false, license: "UNLICENSED" },
    decisionRecordExists: () => true,
  });
  assert.match(issues.join("\n"), /restricted content requires a private package/i);
});

test("requires rights decision evidence", () => {
  const issues = validateManifest(validManifest(), {
    packageManifest: { name: "@hummbl/example-product", private: true, license: "UNLICENSED" },
    decisionRecordExists: () => false,
  });
  assert.match(issues.join("\n"), /decision record.*does not exist/i);
});

test("repository scan validates every Node product manifest", async () => {
  const root = await mkdtemp(join(tmpdir(), "product-admission-"));
  try {
    const packageRoot = join(root, "packages", "node", "example-product");
    const decisionRoot = join(root, "docs", "product");
    await mkdir(packageRoot, { recursive: true });
    await mkdir(decisionRoot, { recursive: true });
    await writeFile(join(packageRoot, "product.json"), JSON.stringify(validManifest()));
    await writeFile(
      join(packageRoot, "package.json"),
      JSON.stringify({ name: "@hummbl/example-product", private: true, license: "UNLICENSED" }),
    );
    await writeFile(join(decisionRoot, "example-distribution-decision.md"), "# Decision\n");

    const result = await validateRepository(root);
    assert.equal(result.manifests.length, 1);
    assert.deepEqual(result.issues, []);

    await rm(join(decisionRoot, "example-distribution-decision.md"));
    const missingEvidence = await validateRepository(root);
    assert.match(missingEvidence.issues.join("\n"), /decision record.*does not exist/i);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdtemp, rm } from "node:fs/promises";
import { spawn, spawnSync } from "node:child_process";
import test from "node:test";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

test("product manifest keeps the technical canary non-public and no-egress", async () => {
  const product = JSON.parse(await readFile(join(ROOT, "product.json"), "utf8"));
  const packageManifest = JSON.parse(await readFile(join(ROOT, "package.json"), "utf8"));
  assert.equal(product.schema_version, "hummbl.product.v1");
  assert.equal(product.product_id, "mcp-base120");
  assert.equal(product.lifecycle, "technical-canary");
  assert.equal(product.public_launch, false);
  assert.equal(product.local_mode.network_egress, false);
  assert.equal(product.local_mode.telemetry, false);
  assert.equal(packageManifest.private, true);
  assert.equal(packageManifest.license, "UNLICENSED");
  assert.ok(product.admission.blockers.includes("corpus-rights-reconciliation"));
  assert.equal(product.rights.package_license, "UNLICENSED");
  assert.equal(product.rights.software_license, "Apache-2.0");
  assert.equal(
    product.rights.embedded_content[0].distribution_policy,
    "no-new-public-redistribution",
  );
  assert.deepEqual(product.contract.tools.sort(), [
    "base120_get",
    "base120_list",
    "base120_prompt",
    "base120_search",
  ]);
  assert.deepEqual(product.contract.protocol_versions, [
    "2026-07-28",
    "2025-11-25",
    "2025-06-18",
  ]);
});

test("generated catalog is current", () => {
  const checked = spawnSync(process.execPath, ["scripts/generate-catalog.mjs", "--check"], {
    cwd: ROOT,
    encoding: "utf8",
  });
  assert.equal(checked.status, 0, checked.stderr || checked.stdout);
});

test("packed artifact passes the public-boundary gate", () => {
  const checked = spawnSync(process.execPath, ["scripts/check-package-boundary.mjs"], {
    cwd: ROOT,
    encoding: "utf8",
  });
  assert.equal(checked.status, 0, checked.stderr || checked.stdout);
});

test("stdio server returns one JSON-RPC response per request without home writes", async () => {
  const emptyHome = await mkdtemp(join(tmpdir(), "mcp-base120-cli-home-"));
  try {
    const child = spawn(process.execPath, ["bin/mcp-base120.mjs"], {
      cwd: ROOT,
      env: { ...process.env, HOME: emptyHome, USERPROFILE: emptyHome },
      stdio: ["pipe", "pipe", "pipe"],
    });

    const stdout = [];
    const stderr = [];
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => stdout.push(chunk));
    child.stderr.on("data", (chunk) => stderr.push(chunk));

    child.stdin.end(
      [
        JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: {
            protocolVersion: "2025-06-18",
            capabilities: {},
            clientInfo: { name: "test", version: "1" },
          },
        }),
        JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list" }),
        "",
      ].join("\n"),
    );

    const exitCode = await new Promise((resolve, reject) => {
      child.once("error", reject);
      child.once("close", resolve);
    });
    assert.equal(exitCode, 0, stderr.join(""));

    const messages = stdout
      .join("")
      .trim()
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line));
    assert.equal(messages.length, 2);
    assert.equal(messages[0].result.serverInfo.name, "hummbl-mcp-base120");
    assert.equal(messages[1].result.tools.length, 4);
    assert.deepEqual(await readdir(emptyHome), []);
  } finally {
    await rm(emptyHome, { recursive: true, force: true });
  }
});

test("stdio server reports malformed JSON without crashing", async () => {
  const child = spawn(process.execPath, ["bin/mcp-base120.mjs"], {
    cwd: ROOT,
    stdio: ["pipe", "pipe", "pipe"],
  });
  const stdout = [];
  child.stdout.setEncoding("utf8");
  child.stdout.on("data", (chunk) => stdout.push(chunk));
  child.stdin.end("{not-json}\n");
  const exitCode = await new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("close", resolve);
  });
  assert.equal(exitCode, 0);
  const response = JSON.parse(stdout.join("").trim());
  assert.equal(response.error.code, -32700);
  assert.equal(response.error.message, "Parse error");
  assert.equal(response.id, null);
});

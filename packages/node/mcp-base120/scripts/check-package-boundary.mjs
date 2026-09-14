#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const FORBIDDEN_PATH = /(^|\/)(?:test|scripts|node_modules|_internal|receipts?|\.git|\.env)(?:\/|$)/i;
const TEXT_EXTENSIONS = new Set([".json", ".md", ".mjs"]);
const FORBIDDEN_TEXT = [
  { label: "Windows user path", pattern: /[A-Z]:\\Users\\[^\\]+\\/i },
  { label: "macOS user path", pattern: /\/Users\/[^/]+\/PROJECTS\//i },
  { label: "machine binding", pattern: /\b(?:host|machine)=[a-z0-9][a-z0-9-]{2,}\b/i },
  { label: "credential-manager key", pattern: /\b[A-Z][A-Z0-9_-]{2,}:[A-Z][A-Z0-9_]{2,}\b/ },
  { label: "long-lived npm token", pattern: /\bNPM_TOKEN\b/ },
];

function extension(path) {
  const match = path.match(/\.[^.\/]+$/);
  return match?.[0].toLowerCase() ?? "";
}

function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
}

const packed = spawnSync("npm", ["pack", "--json", "--dry-run", "--ignore-scripts"], {
  cwd: ROOT,
  encoding: "utf8",
  shell: process.platform === "win32",
});
if (packed.status !== 0) {
  fail(packed.stderr || packed.stdout || "npm pack inspection failed");
} else {
  let manifest;
  try {
    [manifest] = JSON.parse(packed.stdout);
  } catch {
    fail("npm pack did not return a parseable JSON manifest");
  }

  for (const entry of manifest?.files ?? []) {
    const relative = entry.path.replaceAll("\\", "/");
    if (FORBIDDEN_PATH.test(relative)) {
      fail(`forbidden path in npm artifact: ${relative}`);
      continue;
    }
    if (!TEXT_EXTENSIONS.has(extension(relative))) {
      fail(`unreviewed file type in npm artifact: ${relative}`);
      continue;
    }
    const content = await readFile(join(ROOT, relative), "utf8");
    for (const { label, pattern } of FORBIDDEN_TEXT) {
      if (pattern.test(content)) fail(`${label} found in npm artifact: ${relative}`);
    }
  }

  if (!manifest?.files?.some(({ path }) => path === "data/provenance.json")) {
    fail("npm artifact is missing data/provenance.json");
  }
  if (!manifest?.files?.some(({ path }) => path === "product.json")) {
    fail("npm artifact is missing product.json");
  }
}

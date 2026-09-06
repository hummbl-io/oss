#!/usr/bin/env node

import { existsSync } from "node:fs";
import { access, readFile, readdir } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCHEMA_URL =
  "https://raw.githubusercontent.com/hummbl-io/oss/main/schemas/public/product-admission-v1.schema.json";
const ROOT_FIELDS = new Set([
  "$schema",
  "schema_version",
  "product_id",
  "display_name",
  "distribution",
  "lifecycle",
  "public_launch",
  "admission",
  "canonical_source",
  "content_authorities",
  "rights",
  "contract",
  "local_mode",
  "excluded",
]);
const LIFECYCLES = new Set([
  "technical-canary",
  "private-preview",
  "public-preview",
  "general-availability",
  "retired",
]);
const DECISIONS = new Set(["hold", "admit", "retire"]);
const DISTRIBUTION_POLICIES = new Set([
  "private-only",
  "no-new-public-redistribution",
  "public-redistribution-approved",
]);
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const TOOL_NAME = /^[a-z][a-z0-9_]*$/;
const REPOSITORY = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function checkObject(value, path, allowed, required, issues) {
  if (!isObject(value)) {
    issues.push(`${path} must be an object`);
    return false;
  }
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) issues.push(`${path} has unknown field: ${key}`);
  }
  for (const key of required) {
    if (!(key in value)) issues.push(`${path} is missing required field: ${key}`);
  }
  return true;
}

function checkString(value, path, issues, pattern) {
  if (typeof value !== "string" || value.length === 0) {
    issues.push(`${path} must be a non-empty string`);
  } else if (pattern && !pattern.test(value)) {
    issues.push(`${path} has an invalid format`);
  }
}

function checkUniqueStrings(value, path, issues, { min = 0, pattern } = {}) {
  if (!Array.isArray(value)) {
    issues.push(`${path} must be an array`);
    return;
  }
  if (value.length < min) issues.push(`${path} must contain at least ${min} item(s)`);
  const seen = new Set();
  for (const [index, item] of value.entries()) {
    checkString(item, `${path}[${index}]`, issues, pattern);
    if (seen.has(item)) issues.push(`${path} contains duplicate item: ${item}`);
    seen.add(item);
  }
}

function checkRepositoryPath(value, path, issues) {
  checkString(value, path, issues);
  if (
    typeof value === "string" &&
    (/^[A-Za-z]:/.test(value) || value.startsWith("/") || value.split(/[\\/]/).includes(".."))
  ) {
    issues.push(`${path} must be a repository-relative path without parent traversal`);
  }
}

export function validateManifest(manifest, context = {}) {
  const issues = [];
  if (!checkObject(manifest, "manifest", ROOT_FIELDS, ROOT_FIELDS, issues)) return issues;

  if (manifest.$schema !== SCHEMA_URL) issues.push(`manifest.$schema must equal ${SCHEMA_URL}`);
  if (manifest.schema_version !== "hummbl.product.v1") {
    issues.push("manifest.schema_version must equal hummbl.product.v1");
  }
  checkString(manifest.product_id, "manifest.product_id", issues, SLUG);
  checkString(manifest.display_name, "manifest.display_name", issues);
  checkString(manifest.distribution, "manifest.distribution", issues);
  if (!LIFECYCLES.has(manifest.lifecycle)) issues.push("manifest.lifecycle is not supported");
  if (typeof manifest.public_launch !== "boolean") {
    issues.push("manifest.public_launch must be a boolean");
  }

  const admissionFields = new Set(["decision", "blockers"]);
  if (
    checkObject(
      manifest.admission,
      "manifest.admission",
      admissionFields,
      admissionFields,
      issues,
    )
  ) {
    if (!DECISIONS.has(manifest.admission.decision)) {
      issues.push("manifest.admission.decision is not supported");
    }
    checkUniqueStrings(manifest.admission.blockers, "manifest.admission.blockers", issues, {
      pattern: SLUG,
    });
    if (manifest.admission.decision === "hold" && manifest.admission.blockers?.length === 0) {
      issues.push("hold admission requires at least one blocker");
    }
    if (manifest.admission.decision === "admit" && manifest.admission.blockers?.length > 0) {
      issues.push("admit admission cannot retain blockers");
    }
  }

  const sourceFields = new Set(["repository", "path"]);
  if (
    checkObject(
      manifest.canonical_source,
      "manifest.canonical_source",
      sourceFields,
      sourceFields,
      issues,
    )
  ) {
    checkString(manifest.canonical_source.repository, "manifest.canonical_source.repository", issues, REPOSITORY);
    checkRepositoryPath(manifest.canonical_source.path, "manifest.canonical_source.path", issues);
  }

  const authorityIds = new Set();
  if (!Array.isArray(manifest.content_authorities)) {
    issues.push("manifest.content_authorities must be an array");
  } else {
    const authorityFields = new Set(["content_id", "repository", "path"]);
    for (const [index, authority] of manifest.content_authorities.entries()) {
      const path = `manifest.content_authorities[${index}]`;
      if (!checkObject(authority, path, authorityFields, authorityFields, issues)) continue;
      checkString(authority.content_id, `${path}.content_id`, issues, SLUG);
      checkString(authority.repository, `${path}.repository`, issues, REPOSITORY);
      checkRepositoryPath(authority.path, `${path}.path`, issues);
      if (authorityIds.has(authority.content_id)) {
        issues.push(`manifest.content_authorities contains duplicate content_id: ${authority.content_id}`);
      }
      authorityIds.add(authority.content_id);
    }
  }

  const restrictivePolicies = [];
  const embeddedContentIds = new Set();
  const rightsFields = new Set(["package_license", "software_license", "embedded_content"]);
  if (checkObject(manifest.rights, "manifest.rights", rightsFields, rightsFields, issues)) {
    checkString(manifest.rights.package_license, "manifest.rights.package_license", issues);
    checkString(manifest.rights.software_license, "manifest.rights.software_license", issues);
    if (!Array.isArray(manifest.rights.embedded_content)) {
      issues.push("manifest.rights.embedded_content must be an array");
    } else {
      const contentIds = new Set();
      const contentFields = new Set([
        "content_id",
        "license",
        "distribution_policy",
        "decision_record",
      ]);
      for (const [index, content] of manifest.rights.embedded_content.entries()) {
        const path = `manifest.rights.embedded_content[${index}]`;
        if (!checkObject(content, path, contentFields, contentFields, issues)) continue;
        checkString(content.content_id, `${path}.content_id`, issues, SLUG);
        checkString(content.license, `${path}.license`, issues);
        if (contentIds.has(content.content_id)) {
          issues.push(`manifest.rights.embedded_content contains duplicate content_id: ${content.content_id}`);
        }
        contentIds.add(content.content_id);
        embeddedContentIds.add(content.content_id);
        if (!DISTRIBUTION_POLICIES.has(content.distribution_policy)) {
          issues.push(`${path}.distribution_policy is not supported`);
        } else if (content.distribution_policy !== "public-redistribution-approved") {
          restrictivePolicies.push(content.distribution_policy);
        }
        checkRepositoryPath(content.decision_record, `${path}.decision_record`, issues);
        if (
          typeof context.decisionRecordExists === "function" &&
          typeof content.decision_record === "string" &&
          !context.decisionRecordExists(content.decision_record)
        ) {
          issues.push(`${path}.decision record does not exist: ${content.decision_record}`);
        }
      }
    }
  }

  for (const contentId of embeddedContentIds) {
    if (!authorityIds.has(contentId)) {
      issues.push(`embedded content has no matching content authority: ${contentId}`);
    }
  }
  for (const contentId of authorityIds) {
    if (!embeddedContentIds.has(contentId)) {
      issues.push(`content authority has no matching embedded content: ${contentId}`);
    }
  }

  const contractFields = new Set(["version", "protocol_versions", "tools", "mutations"]);
  if (
    checkObject(manifest.contract, "manifest.contract", contractFields, contractFields, issues)
  ) {
    checkString(manifest.contract.version, "manifest.contract.version", issues);
    checkUniqueStrings(manifest.contract.protocol_versions, "manifest.contract.protocol_versions", issues, {
      min: 1,
    });
    checkUniqueStrings(manifest.contract.tools, "manifest.contract.tools", issues, {
      min: 1,
      pattern: TOOL_NAME,
    });
    if (typeof manifest.contract.mutations !== "boolean") {
      issues.push("manifest.contract.mutations must be a boolean");
    }
  }

  const localFields = new Set(["network_egress", "telemetry", "durable_writes"]);
  if (checkObject(manifest.local_mode, "manifest.local_mode", localFields, localFields, issues)) {
    for (const field of localFields) {
      if (typeof manifest.local_mode[field] !== "boolean") {
        issues.push(`manifest.local_mode.${field} must be a boolean`);
      }
    }
  }
  checkUniqueStrings(manifest.excluded, "manifest.excluded", issues, { min: 1 });

  if (manifest.public_launch === true) {
    if (manifest.admission?.decision !== "admit") {
      issues.push("public launch requires an admit admission decision");
    }
    if (context.packageManifest?.private === true) {
      issues.push("public launch cannot use a private package");
    }
    for (const policy of restrictivePolicies) {
      issues.push(`public launch conflicts with ${policy} content`);
    }
  }

  if (restrictivePolicies.length > 0 && context.packageManifest?.private !== true) {
    issues.push("restricted content requires a private package");
  }

  if (context.packageManifest) {
    if (manifest.distribution !== context.packageManifest.name) {
      issues.push("manifest.distribution must match package.json name");
    }
    if (manifest.rights?.package_license !== context.packageManifest.license) {
      issues.push("manifest.rights.package_license must match package.json license");
    }
  }

  return issues;
}

async function pathExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

export async function validateRepository(repositoryRoot) {
  const root = resolve(repositoryRoot);
  const nodeRoot = join(root, "packages", "node");
  const manifests = [];
  const issues = [];
  let packages = [];
  try {
    packages = await readdir(nodeRoot, { withFileTypes: true });
  } catch (error) {
    if (error.code === "ENOENT") return { manifests, issues };
    throw error;
  }

  for (const entry of packages.filter((candidate) => candidate.isDirectory())) {
    const packageRoot = join(nodeRoot, entry.name);
    const productPath = join(packageRoot, "product.json");
    if (!(await pathExists(productPath))) continue;
    const displayPath = relative(root, productPath).replaceAll("\\", "/");
    manifests.push(displayPath);
    try {
      const manifest = JSON.parse(await readFile(productPath, "utf8"));
      const packageManifest = JSON.parse(await readFile(join(packageRoot, "package.json"), "utf8"));
      const manifestIssues = validateManifest(manifest, {
        packageManifest,
        decisionRecordExists: (path) => existsSync(join(root, path)),
      });
      issues.push(...manifestIssues.map((issue) => `${displayPath}: ${issue}`));
    } catch (error) {
      issues.push(`${displayPath}: ${error.message}`);
    }
  }

  return { manifests, issues };
}

async function main() {
  const scriptDirectory = dirname(fileURLToPath(import.meta.url));
  const defaultRoot = resolve(scriptDirectory, "..", "..");
  const { manifests, issues } = await validateRepository(process.argv[2] ?? defaultRoot);
  for (const issue of issues) process.stderr.write(`${issue}\n`);
  if (issues.length > 0) process.exitCode = 1;
  else process.stdout.write(`Validated ${manifests.length} product manifest(s).\n`);
}

if (import.meta.url === pathToFileURL(resolve(process.argv[1] ?? "")).href) await main();

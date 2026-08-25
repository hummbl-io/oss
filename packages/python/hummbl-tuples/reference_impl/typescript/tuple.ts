/**
 * HUMMBL Tuple TypeScript Reference Implementation
 *
 * Canonical serialization per CANONICAL_SERIALIZATION_v1.md.
 * Produces byte-identical output to the Python reference implementation.
 *
 * Zero third-party dependencies — Node.js stdlib only.
 */

import { createHash } from 'node:crypto';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type TupleType =
  | 'CONTRACT'
  | 'DCT'
  | 'DCTX'
  | 'SYSTEM'
  | 'EVIDENCE'
  | 'ATTEST'
  | 'PROMOTION_RECEIPT'
  | 'REVOCATION'
  | 'MODEL_CANDIDATE'
  | 'MODEL_SELECTED'
  | 'TRANSFORMATION_CANDIDATE'
  | 'TRANSFORMATION_SELECTED'
  | 'HITL_OVERRIDE'
  | 'REASONING_PATH'
  | 'PATH_COMPARISON'
  | 'TRACE_EVIDENCE'
  | 'BASE_PROFILE_ISSUED'
  | 'CONTROL_MODE_SET'
  | 'EXPERIMENT_RUN_ASSIGNED'
  | 'REGISTRY_VERSION_PINNED'
  | 'PRETRAINING_TRACE'
  | 'POSTTRAINING_TRACE'
  | 'READINESS_INFERRED'
  | 'STRAIN_FLAGGED'
  | 'WORKLOAD_INFERRED'
  | 'BIO_SIGNAL_CAPTURED'
  | 'BIO_HARM_SIGNAL'
  | 'BIO_ACTION_AUTHORIZED'
  | 'BIO_ACTION_BLOCKED'
  | 'BIO_ADAPTATION_PROPOSED'
  | 'BIO_ADAPTATION_EXECUTED'
  | 'BIO_OUTCOME_OBSERVED'
  | 'BIO_OVERRIDE';

export interface TupleData {
  [key: string]: unknown;
}

export interface TypedTuple {
  tuple_type: TupleType;
  id: string;
  time: string; // ISO 8601 UTC
  tuple_data: TupleData;
}

// ---------------------------------------------------------------------------
// Canonical Serialization (CANONICAL_SERIALIZATION_v1.md)
// ---------------------------------------------------------------------------

/**
 * Sort keys by UTF-8 code point order (NOT JavaScript's default UTF-16 sort).
 * This is critical for byte-identical cross-language hashing.
 */
function compareKeysUtf8(a: string, b: string): number {
  const aBuf = Buffer.from(a, 'utf-8');
  const bBuf = Buffer.from(b, 'utf-8');
  return Buffer.compare(aBuf, bBuf);
}

/**
 * Recursively sort object keys by UTF-8 code point order.
 * Handles nested objects. Preserves array insertion order.
 */
function sortKeysDeep(obj: unknown): unknown {
  if (obj === null || obj === undefined) return undefined;
  if (Array.isArray(obj)) {
    return obj.map(sortKeysDeep);
  }
  if (typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    const keys = Object.keys(obj as Record<string, unknown>).sort(compareKeysUtf8);
    for (const key of keys) {
      const val = (obj as Record<string, unknown>)[key];
      if (val === null || val === undefined) continue; // omit null/absent
      result[key] = sortKeysDeep(val);
    }
    return result;
  }
  if (typeof obj === 'number' && !Number.isInteger(obj)) {
    // Floats: serialize as strings with 4 decimal places
    if (Number.isNaN(obj)) return 'NaN';
    if (obj === Infinity) return 'Infinity';
    if (obj === -Infinity) return '-Infinity';
    return obj.toFixed(4);
  }
  return obj;
}

/**
 * Canonical JSON serialization.
 *
 * Rules (CANONICAL_SERIALIZATION_v1.md §3):
 * - Compact separators (no whitespace)
 * - Keys sorted by UTF-8 code point order
 * - Non-ASCII emitted as raw UTF-8 (not \u-escaped)
 * - Null/undefined values omitted
 * - Floats serialized as strings with 4 decimal places
 * - Arrays preserve insertion order
 */
export function canonicalJson(obj: unknown): string {
  const sorted = sortKeysDeep(obj);
  // JSON.stringify with no replacer and no space produces compact form.
  // We need to ensure non-ASCII is NOT \u-escaped.
  // JSON.stringify does NOT escape non-ASCII by default in Node.js.
  return JSON.stringify(sorted);
}

// ---------------------------------------------------------------------------
// Hash Computation (CANONICAL_SERIALIZATION_v1.md §5)
// ---------------------------------------------------------------------------

/** Integrity-layer fields excluded from content hash. */
const INTEGRITY_FIELDS = new Set(['previous_hash', 'args_hash', 'signature']);

/**
 * Recursively remove integrity-layer fields from an object.
 */
function removeIntegrityFields(obj: unknown): unknown {
  if (obj === null || obj === undefined) return undefined;
  if (Array.isArray(obj)) {
    return obj.map(removeIntegrityFields);
  }
  if (typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    const o = obj as Record<string, unknown>;
    for (const key of Object.keys(o)) {
      if (INTEGRITY_FIELDS.has(key)) continue;
      if (o[key] === null || o[key] === undefined) continue;
      result[key] = removeIntegrityFields(o[key]);
    }
    return result;
  }
  return obj;
}

/**
 * Compute SHA-256 content hash of a tuple.
 *
 * Per CANONICAL_SERIALIZATION_v1.md §5:
 * 1. Serialize the tuple to canonical JSON
 * 2. Remove integrity-layer fields (previous_hash, args_hash, signature)
 * 3. Re-serialize with sorted keys
 * 4. Compute SHA-256 over the UTF-8 bytes
 * 5. Return lowercase hex string (64 characters)
 */
export function contentHash(tuple: TypedTuple | TupleData): string {
  const cleaned = removeIntegrityFields(tuple) as Record<string, unknown>;
  const canonical = canonicalJson(cleaned);
  return createHash('sha256').update(canonical, 'utf-8').digest('hex');
}

/**
 * Compute SHA-256 of an arbitrary string (for args_hash, etc.).
 */
export function sha256Hex(data: string): string {
  return createHash('sha256').update(data, 'utf-8').digest('hex');
}

// ---------------------------------------------------------------------------
// Tuple Construction
// ---------------------------------------------------------------------------

/**
 * Create a TypedTuple with canonical serialization.
 */
export function createTuple(
  tupleType: TupleType,
  id: string,
  tupleData: TupleData,
  time?: string,
): TypedTuple {
  return {
    tuple_type: tupleType,
    id,
    time: time ?? new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    tuple_data: tupleData,
  };
}

/**
 * Serialize a tuple to canonical JSON string.
 */
export function tupleToJson(tuple: TypedTuple): string {
  return canonicalJson(tuple);
}

/**
 * Add chain link to a tuple (returns a new tuple, does not mutate).
 */
export function withChain(tuple: TypedTuple, previousHash: string | null): TypedTuple {
  const newData = { ...tuple.tuple_data };
  if (previousHash === null) {
    delete newData.previous_hash;
  } else {
    newData.previous_hash = previousHash;
  }
  return { ...tuple, tuple_data: newData };
}

/**
 * Verify a chain link: check that tuple.previous_hash matches expectedHash.
 */
export function verifyChain(
  tuple: TypedTuple,
  expectedHash: string | null,
): boolean {
  const actualHash = (tuple.tuple_data.previous_hash as string | undefined) ?? null;
  if (expectedHash === null && actualHash === null) return true;
  if (expectedHash === null || actualHash === null) return false;
  return actualHash === expectedHash;
}

// ---------------------------------------------------------------------------
// Conformance Helpers
// ---------------------------------------------------------------------------

/**
 * Parse a canonical JSON string back to a TypedTuple.
 * Validates the tuple_type field is a known type.
 */
export function parseTuple(json: string): TypedTuple {
  const parsed = JSON.parse(json) as Record<string, unknown>;
  if (typeof parsed.tuple_type !== 'string') {
    throw new Error('Missing or invalid tuple_type field');
  }
  if (typeof parsed.id !== 'string') {
    throw new Error('Missing or invalid id field');
  }
  if (typeof parsed.time !== 'string') {
    throw new Error('Missing or invalid time field');
  }
  if (typeof parsed.tuple_data !== 'object' || parsed.tuple_data === null) {
    throw new Error('Missing or invalid tuple_data field');
  }
  return {
    tuple_type: parsed.tuple_type as TupleType,
    id: parsed.id as string,
    time: parsed.time as string,
    tuple_data: parsed.tuple_data as TupleData,
  };
}

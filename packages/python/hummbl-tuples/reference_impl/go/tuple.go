// Package hummbl provides HUMMBL Typed Tuple canonical serialization and hashing.
//
// Canonical serialization per CANONICAL_SERIALIZATION_v1.md.
// Produces byte-identical output to the Python, TypeScript, and Rust reference implementations.
//
// Zero third-party dependencies — Go stdlib only.
package hummbl

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"
)

// IntegrityFields are excluded from content hash computation.
var IntegrityFields = map[string]bool{
	"previous_hash": true,
	"args_hash":     true,
	"signature":     true,
}

// TupleType is a known tuple type constant.
type TupleType string

const (
	TypeContract       TupleType = "CONTRACT"
	TypeDCT            TupleType = "DCT"
	TypeDCTX           TupleType = "DCTX"
	TypeSystem         TupleType = "SYSTEM"
	TypeEvidence       TupleType = "EVIDENCE"
	TypeAttest         TupleType = "ATTEST"
	TypePromotionRcpt  TupleType = "PROMOTION_RECEIPT"
	TypeRevocation     TupleType = "REVOCATION"
	TypeModelCandidate TupleType = "MODEL_CANDIDATE"
	TypeModelSelected  TupleType = "MODEL_SELECTED"
	TypeTransCandidate TupleType = "TRANSFORMATION_CANDIDATE"
	TypeTransSelected  TupleType = "TRANSFORMATION_SELECTED"
	TypeHitlOverride   TupleType = "HITL_OVERRIDE"
	TypeReasoningPath  TupleType = "REASONING_PATH"
	TypePathComparison TupleType = "PATH_COMPARISON"
	TypeTraceEvidence  TupleType = "TRACE_EVIDENCE"
)

// TypedTuple is a HUMMBL Typed Tuple (Layer 1 envelope).
type TypedTuple struct {
	TupleType string                 `json:"tuple_type"`
	ID        string                 `json:"id"`
	Time      string                 `json:"time"`
	TupleData map[string]interface{} `json:"tuple_data"`
}

// NewTuple creates a tuple with the current UTC time.
func NewTuple(tupleType string, id string, data map[string]interface{}) *TypedTuple {
	return &TypedTuple{
		TupleType: tupleType,
		ID:        id,
		Time:      utcNow(),
		TupleData: data,
	}
}

// NewTupleWithTime creates a tuple with an explicit timestamp.
func NewTupleWithTime(tupleType, id, time string, data map[string]interface{}) *TypedTuple {
	return &TypedTuple{
		TupleType: tupleType,
		ID:        id,
		Time:      time,
		TupleData: data,
	}
}

// ToJSON returns the canonical JSON serialization.
func (t *TypedTuple) ToJSON() string {
	m := t.toMap()
	return CanonicalJSON(m)
}

// Hash returns the SHA-256 content hash (excludes integrity-layer fields).
func (t *TypedTuple) Hash() string {
	m := t.toMap()
	removeIntegrityFields(m)
	canonical := CanonicalJSON(m)
	return SHA256Hex(canonical)
}

// WithChain returns a new tuple with previous_hash set (does not mutate).
func (t *TypedTuple) WithChain(previousHash *string) *TypedTuple {
	data := make(map[string]interface{})
	for k, v := range t.TupleData {
		data[k] = v
	}
	if previousHash == nil {
		delete(data, "previous_hash")
	} else {
		data["previous_hash"] = *previousHash
	}
	return &TypedTuple{
		TupleType: t.TupleType,
		ID:        t.ID,
		Time:      t.Time,
		TupleData: data,
	}
}

// VerifyChain checks that the tuple's previous_hash matches the expected value.
func (t *TypedTuple) VerifyChain(expected *string) bool {
	actual, ok := t.TupleData["previous_hash"].(string)
	if !ok {
		return expected == nil
	}
	if expected == nil {
		return false
	}
	return actual == *expected
}

func (t *TypedTuple) toMap() map[string]interface{} {
	return map[string]interface{}{
		"tuple_type": t.TupleType,
		"id":         t.ID,
		"time":       t.Time,
		"tuple_data": t.TupleData,
	}
}

// ParseTuple parses a canonical JSON string into a TypedTuple.
func ParseTuple(jsonStr string) (*TypedTuple, error) {
	var raw map[string]interface{}
	if err := json.Unmarshal([]byte(jsonStr), &raw); err != nil {
		return nil, fmt.Errorf("JSON parse error: %w", err)
	}

	tt, ok := raw["tuple_type"].(string)
	if !ok {
		return nil, fmt.Errorf("missing tuple_type")
	}
	id, ok := raw["id"].(string)
	if !ok {
		return nil, fmt.Errorf("missing id")
	}
	tm, ok := raw["time"].(string)
	if !ok {
		return nil, fmt.Errorf("missing time")
	}
	data, ok := raw["tuple_data"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("missing tuple_data")
	}

	return &TypedTuple{
		TupleType: tt,
		ID:        id,
		Time:      tm,
		TupleData: data,
	}, nil
}

// ---------------------------------------------------------------------------
// Canonical Serialization (CANONICAL_SERIALIZATION_v1.md)
// ---------------------------------------------------------------------------

// CanonicalJSON produces canonical JSON: compact, sorted keys, raw UTF-8, nulls omitted.
func CanonicalJSON(v interface{}) string {
	sorted := sortKeysDeep(v)
	return encodeCompact(sorted)
}

// sortKeysDeep recursively sorts object keys by UTF-8 byte order and omits null values.
func sortKeysDeep(v interface{}) interface{} {
	switch val := v.(type) {
	case map[string]interface{}:
		keys := make([]string, 0, len(val))
		for k := range val {
			if val[k] != nil {
				keys = append(keys, k)
			}
		}
		sort.Strings(keys) // Go sort.Strings = byte order = UTF-8 code point order for BMP

		result := make(map[string]interface{}, len(keys))
		for _, k := range keys {
			result[k] = sortKeysDeep(val[k])
		}
		return result

	case []interface{}:
		result := make([]interface{}, len(val))
		for i, item := range val {
			result[i] = sortKeysDeep(item)
		}
		return result

	case float64:
		// Floats: serialize as strings with 4 decimal places
		if val != float64(int64(val)) {
			return fmt.Sprintf("%.4f", val)
		}
		return v

	default:
		return v
	}
}

// encodeCompact encodes a value as compact JSON with no whitespace.
// We use a custom encoder to ensure no HTML escaping and raw UTF-8.
func encodeCompact(v interface{}) string {
	var buf strings.Builder
	encodeValue(&buf, v)
	return buf.String()
}

func encodeValue(buf *strings.Builder, v interface{}) {
	if v == nil {
		return // omit nulls
	}
	switch val := v.(type) {
	case bool:
		if val {
			buf.WriteString("true")
		} else {
			buf.WriteString("false")
		}

	case int:
		fmt.Fprintf(buf, "%d", val)
	case int64:
		fmt.Fprintf(buf, "%d", val)
	case float64:
		if val == float64(int64(val)) {
			fmt.Fprintf(buf, "%d", int64(val))
		} else {
			// Already string-serialized by sortKeysDeep
			fmt.Fprintf(buf, "%.4f", val)
		}

	case string:
		encodeString(buf, val)

	case map[string]interface{}:
		keys := make([]string, 0, len(val))
		for k := range val {
			if val[k] != nil {
				keys = append(keys, k)
			}
		}
		sort.Strings(keys)

		buf.WriteByte('{')
		first := true
		for _, k := range keys {
			if val[k] == nil {
				continue
			}
			if !first {
				buf.WriteByte(',')
			}
			first = false
			encodeString(buf, k)
			buf.WriteByte(':')
			encodeValue(buf, val[k])
		}
		buf.WriteByte('}')

	case []interface{}:
		buf.WriteByte('[')
		for i, item := range val {
			if i > 0 {
				buf.WriteByte(',')
			}
			encodeValue(buf, item)
		}
		buf.WriteByte(']')

	default:
		// Fallback to json.Marshal for unknown types
		b, _ := json.Marshal(val)
		buf.Write(b)
	}
}

// encodeString writes a JSON-escaped string to the buffer.
// Escapes control characters per RFC 8259, keeps non-ASCII as raw UTF-8.
func encodeString(buf *strings.Builder, s string) {
	buf.WriteByte('"')
	for _, r := range s {
		switch r {
		case '"':
			buf.WriteString(`\"`)
		case '\\':
			buf.WriteString(`\\`)
		case '\n':
			buf.WriteString(`\n`)
		case '\r':
			buf.WriteString(`\r`)
		case '\t':
			buf.WriteString(`\t`)
		case '\b':
			buf.WriteString(`\b`)
		case '\f':
			buf.WriteString(`\f`)
		default:
			if r < 0x20 {
				fmt.Fprintf(buf, `\u%04x`, r)
			} else {
				// Raw UTF-8 — do NOT \u-escape non-ASCII
				buf.WriteRune(r)
			}
		}
	}
	buf.WriteByte('"')
}

// removeIntegrityFields recursively removes integrity-layer fields.
func removeIntegrityFields(m map[string]interface{}) {
	for _, field := range []string{"previous_hash", "args_hash", "signature"} {
		delete(m, field)
	}
	if data, ok := m["tuple_data"].(map[string]interface{}); ok {
		for _, field := range []string{"previous_hash", "args_hash", "signature"} {
			delete(data, field)
		}
	}
}

// SHA256Hex computes the SHA-256 hash of a string and returns lowercase hex.
func SHA256Hex(data string) string {
	h := sha256.Sum256([]byte(data))
	return hex.EncodeToString(h[:])
}

// utcNow returns the current UTC time in ISO-8601 format (YYYY-MM-DDTHH:MM:SSZ).
func utcNow() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05Z")
}

//! HUMMBL Typed Tuple Rust Reference Implementation
//!
//! Canonical serialization per CANONICAL_SERIALIZATION_v1.md.
//! Produces byte-identical output to the Python and TypeScript reference implementations.
//!
//! Zero third-party dependencies beyond serde_json (for JSON) and sha2 (for SHA-256).

use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

/// Integrity-layer fields excluded from content hash computation.
const INTEGRITY_FIELDS: &[&str] = &["previous_hash", "args_hash", "signature"];

/// A HUMMBL Typed Tuple (Layer 1 envelope).
#[derive(Debug, Clone)]
pub struct TypedTuple {
    pub tuple_type: String,
    pub id: String,
    pub time: String,
    pub tuple_data: Map<String, Value>,
}

impl TypedTuple {
    /// Create a new tuple with the given type, id, and data.
    /// Time defaults to current UTC in ISO-8601 format.
    pub fn new(tuple_type: &str, id: &str, tuple_data: Map<String, Value>) -> Self {
        Self {
            tuple_type: tuple_type.to_string(),
            id: id.to_string(),
            time: utc_now(),
            tuple_data,
        }
    }

    /// Create a tuple with an explicit timestamp.
    pub fn with_time(
        tuple_type: &str,
        id: &str,
        time: &str,
        tuple_data: Map<String, Value>,
    ) -> Self {
        Self {
            tuple_type: tuple_type.to_string(),
            id: id.to_string(),
            time: time.to_string(),
            tuple_data,
        }
    }

    /// Convert to a JSON object (Map) with envelope structure.
    pub fn to_map(&self) -> Map<String, Value> {
        let mut map = Map::new();
        map.insert("tuple_type".to_string(), Value::String(self.tuple_type.clone()));
        map.insert("id".to_string(), Value::String(self.id.clone()));
        map.insert("time".to_string(), Value::String(self.time.clone()));
        map.insert("tuple_data".to_string(), Value::Object(self.tuple_data.clone()));
        map
    }

    /// Canonical JSON serialization (compact, sorted keys, raw UTF-8).
    pub fn to_json(&self) -> String {
        canonical_json(&Value::Object(self.to_map()))
    }

    /// SHA-256 content hash (excludes integrity-layer fields).
    pub fn hash(&self) -> String {
        let mut map = self.to_map();
        remove_integrity_fields(&mut map);
        let canonical = canonical_json(&Value::Object(map));
        let digest = Sha256::digest(canonical.as_bytes());
        format!("{:x}", digest)
    }

    /// Add chain link (returns a new tuple, does not mutate).
    pub fn with_chain(&self, previous_hash: Option<&str>) -> Self {
        let mut data = self.tuple_data.clone();
        match previous_hash {
            Some(h) => {
                data.insert("previous_hash".to_string(), Value::String(h.to_string()));
            }
            None => {
                data.remove("previous_hash");
            }
        }
        Self {
            tuple_type: self.tuple_type.clone(),
            id: self.id.clone(),
            time: self.time.clone(),
            tuple_data: data,
        }
    }

    /// Verify chain link against an expected predecessor hash.
    pub fn verify_chain(&self, expected: Option<&str>) -> bool {
        match self.tuple_data.get("previous_hash") {
            Some(Value::String(actual)) => expected == Some(actual.as_str()),
            _ => expected.is_none(),
        }
    }
}

/// Parse a tuple from a JSON string.
pub fn parse_tuple(json: &str) -> Result<TypedTuple, String> {
    let value: Value = serde_json::from_str(json).map_err(|e| format!("JSON parse error: {}", e))?;
    let obj = value.as_object().ok_or("Expected JSON object")?;

    let tuple_type = obj
        .get("tuple_type")
        .and_then(|v| v.as_str())
        .ok_or("Missing tuple_type")?
        .to_string();
    let id = obj
        .get("id")
        .and_then(|v| v.as_str())
        .ok_or("Missing id")?
        .to_string();
    let time = obj
        .get("time")
        .and_then(|v| v.as_str())
        .ok_or("Missing time")?
        .to_string();
    let tuple_data = obj
        .get("tuple_data")
        .and_then(|v| v.as_object())
        .ok_or("Missing tuple_data")?
        .clone();

    Ok(TypedTuple {
        tuple_type,
        id,
        time,
        tuple_data,
    })
}

// ---------------------------------------------------------------------------
// Canonical Serialization (CANONICAL_SERIALIZATION_v1.md)
// ---------------------------------------------------------------------------

/// Canonical JSON: compact, keys sorted by UTF-8 byte order, raw UTF-8, nulls omitted.
pub fn canonical_json(value: &Value) -> String {
    let sorted = sort_keys_deep(value);
    // serde_json with compact form (no whitespace)
    serde_json::to_string(&sorted).unwrap_or_default()
}

/// Recursively sort object keys by UTF-8 byte order and omit null values.
fn sort_keys_deep(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            // Sort by UTF-8 byte order (Rust String comparison is byte order for UTF-8)
            keys.sort();
            let mut result = Map::new();
            for key in keys {
                let val = &map[key];
                if val.is_null() {
                    continue; // omit nulls
                }
                result.insert(key.clone(), sort_keys_deep(val));
            }
            Value::Object(result)
        }
        Value::Array(arr) => {
            Value::Array(arr.iter().map(sort_keys_deep).collect())
        }
        // Floats: serialize as strings with 4 decimal places
        Value::Number(n) => {
            if let Some(f) = n.as_f64() {
                if !f.is_nan() && !f.is_infinite() && f.fract() != 0.0 {
                    return Value::String(format!("{:.4}", f));
                }
            }
            value.clone()
        }
        _ => value.clone(),
    }
}

/// Recursively remove integrity-layer fields from a JSON value.
fn remove_integrity_fields(value: &mut Map<String, Value>) {
    for field in INTEGRITY_FIELDS {
        value.remove(*field);
    }
    // Also remove from nested objects in tuple_data
    if let Some(Value::Object(data)) = value.get_mut("tuple_data") {
        for field in INTEGRITY_FIELDS {
            data.remove(*field);
        }
    }
}

/// Compute SHA-256 hex digest of a string.
pub fn sha256_hex(data: &str) -> String {
    let digest = Sha256::digest(data.as_bytes());
    format!("{:x}", digest)
}

/// Current UTC time in ISO-8601 format (YYYY-MM-DDTHH:MM:SSZ).
fn utc_now() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    // Simple UTC formatting without chrono dependency
    let (year, month, day, hour, min, sec) = unix_to_utc(secs);
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        year, month, day, hour, min, sec
    )
}

/// Convert Unix timestamp to UTC date-time components.
/// Uses the civil-from-days algorithm by Howard Hinnant.
fn unix_to_utc(secs: u64) -> (u32, u32, u32, u32, u32, u32) {
    let days = (secs / 86400) as i64;
    let remainder = secs % 86400;
    let hour = (remainder / 3600) as u32;
    let min = ((remainder % 3600) / 60) as u32;
    let sec = (remainder % 60) as u32;

    // Days since 1970-01-01 → calendar date
    let z = days + 719468;
    let era = if z >= 0 { z } else { z - 146096 } / 146097;
    let doe = (z - era * 146097) as u64;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe as i64 + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32;
    let year = (y + if m <= 2 { 1 } else { 0 }) as u32;

    (year, m, d, hour, min, sec)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_canonical_json_basic() {
        let input = json!({
            "tuple_type": "CONTRACT",
            "id": "test-001",
            "time": "2026-01-01T00:00:00Z",
            "tuple_data": {
                "objective": "Test",
                "agent": "test-agent"
            }
        });
        let canonical = canonical_json(&input);
        // Keys should be sorted: agent, id, objective, time, tuple_data, tuple_type
        assert!(canonical.contains("\"agent\":\"test-agent\""));
        assert!(!canonical.contains(" "));
    }

    #[test]
    fn test_canonical_json_sorted_keys() {
        let input = json!({"z": 1, "a": 2, "m": 3});
        let canonical = canonical_json(&input);
        assert_eq!(canonical, r#"{"a":2,"m":3,"z":1}"#);
    }

    #[test]
    fn test_canonical_json_omits_null() {
        let input = json!({"a": null, "b": 1});
        let canonical = canonical_json(&input);
        assert_eq!(canonical, r#"{"b":1}"#);
    }

    #[test]
    fn test_canonical_json_float() {
        let input = json!({"confidence": 0.75});
        let canonical = canonical_json(&input);
        assert_eq!(canonical, r#"{"confidence":"0.7500"}"#);
    }

    #[test]
    fn test_tuple_hash_excludes_integrity() {
        let mut data = Map::new();
        data.insert("previous_hash".to_string(), Value::String("abc123".to_string()));
        data.insert("objective".to_string(), Value::String("test".to_string()));

        let tuple = TypedTuple::with_time("CONTRACT", "t1", "2026-01-01T00:00:00Z", data);
        let hash = tuple.hash();
        assert_eq!(hash.len(), 64); // SHA-256 hex

        // Hash should be the same without previous_hash
        let mut data2 = Map::new();
        data2.insert("objective".to_string(), Value::String("test".to_string()));
        let tuple2 = TypedTuple::with_time("CONTRACT", "t1", "2026-01-01T00:00:00Z", data2);
        assert_eq!(hash, tuple2.hash());
    }

    #[test]
    fn test_chain_linking() {
        let data = Map::new();
        let tuple = TypedTuple::with_time("EVIDENCE", "e1", "2026-01-01T00:00:00Z", data);
        let chained = tuple.with_chain(Some("prev-hash-123"));
        assert!(chained.verify_chain(Some("prev-hash-123")));
        assert!(!chained.verify_chain(Some("wrong-hash")));
        assert!(!chained.verify_chain(None));
    }

    #[test]
    fn test_parse_tuple() {
        let json = r#"{"tuple_type":"CONTRACT","id":"c1","time":"2026-01-01T00:00:00Z","tuple_data":{"objective":"test"}}"#;
        let tuple = parse_tuple(json).unwrap();
        assert_eq!(tuple.tuple_type, "CONTRACT");
        assert_eq!(tuple.id, "c1");
        assert_eq!(tuple.time, "2026-01-01T00:00:00Z");
        assert_eq!(tuple.tuple_data.get("objective").unwrap(), "test");
    }

    #[test]
    fn test_sha256() {
        let hash = sha256_hex("hello");
        assert_eq!(hash, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824");
    }
}

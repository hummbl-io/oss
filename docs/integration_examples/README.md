# Integration Examples

This directory contains production-ready examples for integrating with the hardened hummbl-production API, demonstrating the new safety features and best practices.

## Overview

The hummbl-production API now includes enterprise-grade safety features:
- **Edge Safety Middleware**: CAES validation and kill switch integration
- **Error Sanitization Layer**: Prevents data leakage from internal errors
- **Governance Proof Generation**: Audit trail for all requests
- **Fail-Closed Behavior**: Safety engine errors block requests

## Examples

### Python Client (`python_client.py`)

**Demonstrates:**
- Kill switch state checking with caching
- Error handling with sanitized error codes
- Retry logic for retryable errors
- Graceful degradation when kill switch is engaged
- Governance proof retrieval
- All major API endpoints

**Key Features:**
- Type-safe error handling with `ErrorCode` enum
- Automatic retry with exponential backoff
- Kill switch state caching (60s TTL)
- Fail-open behavior for kill switch check errors
- Comprehensive error code mapping

**Usage:**
```bash
python python_client.py
```

**Error Codes:**
- `INTERNAL_ERROR`: Internal system errors (not retryable)
- `EXTERNAL_SERVICE_ERROR`: External API failures (retryable)
- `REQUEST_ERROR`: Invalid requests (not retryable)
- `CAES_VALIDATION_FAILED`: Safety validation failed (not retryable)
- `KILL_SWITCH_ENGAGED`: Kill switch is active (not retryable)
- `SAFETY_ENGINE_ERROR`: Safety engine unavailable (not retryable)

### TypeScript Client (`typescript_client.ts`)

**Demonstrates:**
- Type-safe API calls using OpenAPI schema
- Error code handling with TypeScript enums
- Safety middleware integration
- Governance proof parsing
- Async/await patterns

**Usage:**
```bash
npm install
npm run example
```

### Error Handling Patterns (`error_handling_patterns.md`)

**Documents:**
- How to handle different error codes
- When to retry vs. when to alert
- Proper logging of sanitized errors
- Graceful degradation strategies
- Kill switch response patterns

### Kill Switch Integration (`kill_switch_integration.md`)

**Documents:**
- Kill switch state transitions
- Emergency procedures
- Graceful degradation patterns
- Monitoring and alerting
- Testing kill switch behavior

## Best Practices

### 1. Always Check Kill Switch State
Before making API calls, check the kill switch state to avoid unnecessary requests when the API is unavailable.

### 2. Handle Error Codes Programmatically
Use the error codes to determine appropriate action:
- Retry on `EXTERNAL_SERVICE_ERROR`
- Alert on `INTERNAL_ERROR`
- Block on `KILL_SWITCH_ENGAGED`
- Log all errors with context

### 3. Implement Retry Logic
Use exponential backoff for retryable errors, but respect the `is_retryable` flag to avoid infinite loops.

### 4. Cache Kill Switch State
Kill switch state changes infrequently; cache it for 60 seconds to reduce API calls.

### 5. Log Sanitized Errors
Log the sanitized error messages and codes, but never log the original error (it may contain sensitive information).

### 6. Use Governance Proofs
Retrieve governance proofs for audit trails and compliance verification.

## Error Handling Decision Tree

```
Error received
├── KILL_SWITCH_ENGAGED
│   └── Block requests, alert operators, wait for manual intervention
├── CAES_VALIDATION_FAILED
│   └── Block request, log details, notify user of safety violation
├── INTERNAL_ERROR
│   └── Alert operators, do not retry, investigate logs
├── EXTERNAL_SERVICE_ERROR
│   └── Retry with exponential backoff (up to max_retries)
├── REQUEST_ERROR
│   └── Do not retry, notify user of invalid input
└── SAFETY_ENGINE_ERROR
    └── Block requests, alert operators, investigate safety infrastructure
```

## Testing

### Test Kill Switch Behavior
```python
# Set kill switch to HALT_ALL
client.set_kill_switch_state("HALT_ALL", "Testing kill switch")

# Verify requests are blocked
try:
    client.get_models()
except SanitizedError as e:
    assert e.code == ErrorCode.KILL_SWITCH_ENGAGED

# Restore normal operation
client.set_kill_switch_state("DISENGAGED", "Test complete")
```

### Test Error Sanitization
```python
# Trigger an error (e.g., invalid model code)
try:
    client.get_model("INVALID_CODE")
except SanitizedError as e:
    # Verify error is sanitized (no internal details)
    assert "internal" not in e.message.lower()
    assert "stack" not in e.message.lower()
```

### Test Retry Logic
```python
# Mock external service failure
# Verify retry with exponential backoff
# Verify max_retries is respected
```

## Monitoring

### Key Metrics to Track
- Kill switch state changes
- Error code distribution
- Retry success rate
- Governance proof generation rate
- API latency by error code

### Alerting Rules
- Alert on `KILL_SWITCH_ENGAGED` state changes
- Alert on high `INTERNAL_ERROR` rate
- Alert on `SAFETY_ENGINE_ERROR` occurrences
- Alert on retry exhaustion

## Support

For issues or questions:
- Check the main API documentation: `https://github.com/hummbl-io/oss`
- Review kill switch integration guide: `./kill_switch_integration.md`
- Contact: contact@hummbl.io

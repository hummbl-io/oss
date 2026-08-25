# Error Handling Patterns

This guide documents the recommended patterns for handling errors from the hardened hummbl-production API, including the new error sanitization layer.

## Error Codes

The API returns standardized error codes that indicate the type of error and whether it's retryable:

| Error Code | Description | Retryable | Action |
|------------|-------------|-----------|--------|
| `INTERNAL_ERROR` | Internal system error | No | Alert operators, investigate logs |
| `EXTERNAL_SERVICE_ERROR` | External API failure | Yes | Retry with exponential backoff |
| `REQUEST_ERROR` | Invalid request | No | Notify user, do not retry |
| `CAES_VALIDATION_FAILED` | Safety validation failed | No | Block request, log details |
| `KILL_SWITCH_ENGAGED` | Kill switch is active | No | Block requests, alert operators |
| `SAFETY_ENGINE_ERROR` | Safety engine unavailable | No | Block requests, investigate infrastructure |

## Error Handling Decision Tree

```
Error received
├── KILL_SWITCH_ENGAGED
│   └── Action: Block all requests, alert operators immediately, wait for manual intervention
│   └── Log: CRITICAL - Kill switch engaged, reason from API
│   └── User Message: "Service temporarily unavailable due to safety measures"
│
├── CAES_VALIDATION_FAILED
│   └── Action: Block request, log details for security review
│   └── Log: WARNING - CAES validation failed, endpoint, user context
│   └── User Message: "Request failed safety validation"
│
├── INTERNAL_ERROR
│   └── Action: Alert operators, do not retry, investigate logs
│   └── Log: ERROR - Internal error, endpoint, error code, sanitized message
│   └── User Message: "An internal error occurred. Please try again later."
│
├── EXTERNAL_SERVICE_ERROR
│   └── Action: Retry with exponential backoff (up to max_retries)
│   └── Log: INFO - External service error, retry attempt, backoff duration
│   └── User Message: "External service error. Retrying..."
│
├── REQUEST_ERROR
│   └── Action: Do not retry, notify user of invalid input
│   └── Log: INFO - Request error, validation details
│   └── User Message: "Invalid request: [specific validation error]"
│
└── SAFETY_ENGINE_ERROR
    └── Action: Block requests, alert operators, investigate safety infrastructure
    └── Log: CRITICAL - Safety engine error, infrastructure status
    └── User Message: "Service temporarily unavailable due to safety system error"
```

## Pattern 1: Basic Error Handling

### Python
```python
from hummbl_client import HummblClient, ErrorCode

client = HummblClient(api_key="your-api-key")

try:
    models = client.get_models()
    print(f"Found {models['count']} models")
except SanitizedError as e:
    if e.code == ErrorCode.KILL_SWITCH_ENGAGED:
        print("Service unavailable: Kill switch engaged")
        # Alert operators
    elif e.code == ErrorCode.INTERNAL_ERROR:
        print("Internal error occurred")
        # Log and alert
    elif e.code == ErrorCode.EXTERNAL_SERVICE_ERROR:
        print("External service error")
        # Client handles retry automatically
    else:
        print(f"Error: {e.message}")
```

### TypeScript
```typescript
import { HummblClient, ErrorCode } from './hummbl-client';

const client = new HummblClient({ apiKey: 'your-api-key' });

try {
  const models = await client.getModels();
  console.log(`Found ${models.count} models`);
} catch (error) {
  const err = error as SanitizedError;
  
  switch (err.code) {
    case ErrorCode.KILL_SWITCH_ENGAGED:
      console.log('Service unavailable: Kill switch engaged');
      // Alert operators
      break;
    case ErrorCode.INTERNAL_ERROR:
      console.log('Internal error occurred');
      // Log and alert
      break;
    case ErrorCode.EXTERNAL_SERVICE_ERROR:
      console.log('External service error');
      // Client handles retry automatically
      break;
    default:
      console.log(`Error: ${err.message}`);
  }
}
```

## Pattern 2: Retry with Exponential Backoff

### Python
```python
import time
from hummbl_client import HummblClient, ErrorCode, SanitizedError

client = HummblClient(api_key="your-api-key", max_retries=3)

# The client handles retry automatically for retryable errors
# But you can implement custom retry logic:

def custom_retry_with_backoff(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except SanitizedError as e:
            if not e.is_retryable or attempt >= max_retries - 1:
                raise
            
            backoff = 2 ** attempt
            print(f"Retry {attempt + 1}/{max_retries} in {backoff}s...")
            time.sleep(backoff)
    
    raise SanitizedError("Max retries exceeded", ErrorCode.INTERNAL_ERROR, False)

# Usage
try:
    models = custom_retry_with_backoff(client.get_models)
except SanitizedError as e:
    print(f"Failed after retries: {e.message}")
```

### TypeScript
```typescript
import { HummblClient, ErrorCode, SanitizedError } from './hummbl-client';

const client = new HummblClient({ apiKey: 'your-api-key', maxRetries: 3 });

// The client handles retry automatically for retryable errors
// But you can implement custom retry logic:

async function customRetryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const err = error as SanitizedError;
      
      if (!err.isRetryable || attempt >= maxRetries - 1) {
        throw err;
      }
      
      const backoff = Math.pow(2, attempt) * 1000;
      console.log(`Retry ${attempt + 1}/${maxRetries} in ${backoff}ms...`);
      await new Promise(resolve => setTimeout(resolve, backoff));
    }
  }
  
  throw {
    message: 'Max retries exceeded',
    code: ErrorCode.INTERNAL_ERROR,
    isRetryable: false,
  } as SanitizedError;
}

// Usage
try {
  const models = await customRetryWithBackoff(() => client.getModels());
} catch (error) {
  const err = error as SanitizedError;
  console.log(`Failed after retries: ${err.message}`);
}
```

## Pattern 3: Kill Switch Awareness

### Python
```python
from hummbl_client import HummblClient, ErrorCode, KillSwitchState

client = HummblClient(admin_api_key="your-admin-api-key")

def check_and_wait_for_kill_switch():
    """Check kill switch and wait if engaged."""
    state = client.get_kill_switch_state()
    
    if state['state'] in [KillSwitchState.HALT_ALL, KillSwitchState.EMERGENCY]:
        print(f"Kill switch is {state['state']}. Waiting...")
        # Implement wait logic or alert operators
        return False
    
    return True

# Usage
if check_and_wait_for_kill_switch():
    try:
        models = client.get_models()
        print(f"Found {models['count']} models")
    except SanitizedError as e:
        if e.code == ErrorCode.KILL_SWITCH_ENGAGED:
            print("Kill switch engaged during request")
        else:
            print(f"Error: {e.message}")
```

### TypeScript
```typescript
import { HummblClient, ErrorCode, KillSwitchState } from './hummbl-client';

const client = new HummblClient({ adminApiKey: 'your-admin-api-key' });

async function checkAndWaitForKillSwitch(): Promise<boolean> {
  const state = await client.getKillSwitchState();
  
  if (state.state === KillSwitchState.HALT_ALL || state.state === KillSwitchState.EMERGENCY) {
    console.log(`Kill switch is ${state.state}. Waiting...`);
    // Implement wait logic or alert operators
    return false;
  }
  
  return true;
}

// Usage
if (await checkAndWaitForKillSwitch()) {
  try {
    const models = await client.getModels();
    console.log(`Found ${models.count} models`);
  } catch (error) {
    const err = error as SanitizedError;
    if (err.code === ErrorCode.KILL_SWITCH_ENGAGED) {
      console.log('Kill switch engaged during request');
    } else {
      console.log(`Error: ${err.message}`);
    }
  }
}
```

## Pattern 4: Graceful Degradation

### Python
```python
from hummbl_client import HummblClient, ErrorCode

client = HummblClient(api_key="your-api-key")

def get_models_with_fallback():
    """Get models with graceful fallback on errors."""
    try:
        models = client.get_models()
        return models['data']
    except SanitizedError as e:
        if e.code == ErrorCode.KILL_SWITCH_ENGAGED:
            # Return cached data or empty list
            print("Using cached data (kill switch engaged)")
            return get_cached_models()
        elif e.code == ErrorCode.EXTERNAL_SERVICE_ERROR:
            # Return partial data or degraded mode
            print("Degraded mode: returning limited data")
            return get_limited_models()
        else:
            # Return empty list with error message
            print(f"Error: {e.message}")
            return []
```

### TypeScript
```typescript
import { HummblClient, ErrorCode } from './hummbl-client';

const client = new HummblClient({ apiKey: 'your-api-key' });

async function getModelsWithFallback(): Promise<Model[]> {
  try {
    const models = await client.getModels();
    return models.data;
  } catch (error) {
    const err = error as SanitizedError;
    
    if (err.code === ErrorCode.KILL_SWITCH_ENGAGED) {
      // Return cached data or empty list
      console.log('Using cached data (kill switch engaged)');
      return getCachedModels();
    } else if (err.code === ErrorCode.EXTERNAL_SERVICE_ERROR) {
      // Return partial data or degraded mode
      console.log('Degraded mode: returning limited data');
      return getLimitedModels();
    } else {
      // Return empty list with error message
      console.log(`Error: ${err.message}`);
      return [];
    }
  }
}
```

## Pattern 5: Logging and Monitoring

### Python
```python
import logging
from hummbl_client import HummblClient, ErrorCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = HummblClient(api_key="your-api-key")

try:
    models = client.get_models()
    logger.info(f"Successfully retrieved {models['count']} models")
except SanitizedError as e:
    if e.code == ErrorCode.KILL_SWITCH_ENGAGED:
        logger.critical(f"Kill switch engaged: {e.message}")
        # Send alert to operators
    elif e.code == ErrorCode.INTERNAL_ERROR:
        logger.error(f"Internal error: {e.message}")
        # Send alert to operators
    elif e.code == ErrorCode.SAFETY_ENGINE_ERROR:
        logger.critical(f"Safety engine error: {e.message}")
        # Send alert to operators
    else:
        logger.warning(f"Error: {e.message} (code: {e.code.value})")
```

### TypeScript
```typescript
import { HummblClient, ErrorCode } from './hummbl-client';

const client = new HummblClient({ apiKey: 'your-api-key' });

try {
  const models = await client.getModels();
  console.log(`Successfully retrieved ${models.count} models`);
} catch (error) {
  const err = error as SanitizedError;
  
  switch (err.code) {
    case ErrorCode.KILL_SWITCH_ENGAGED:
      console.error(`CRITICAL: Kill switch engaged: ${err.message}`);
      // Send alert to operators
      break;
    case ErrorCode.INTERNAL_ERROR:
      console.error(`ERROR: Internal error: ${err.message}`);
      // Send alert to operators
      break;
    case ErrorCode.SAFETY_ENGINE_ERROR:
      console.error(`CRITICAL: Safety engine error: ${err.message}`);
      // Send alert to operators
      break;
    default:
      console.warn(`WARNING: Error: ${err.message} (code: ${err.code})`);
  }
}
```

## Best Practices

1. **Never log original error messages** - They may contain sensitive information. Only log sanitized messages and codes.

2. **Always check error codes** - Use the error code to determine appropriate action, not just the message.

3. **Respect the `is_retryable` flag** - Don't retry non-retryable errors; it can cause infinite loops or cascading failures.

4. **Implement exponential backoff** - For retryable errors, use exponential backoff to avoid overwhelming the system.

5. **Alert on critical errors** - Kill switch engagement, internal errors, and safety engine errors should trigger alerts.

6. **Provide user-friendly messages** - Don't expose technical details to end users. Use generic messages for internal errors.

7. **Cache kill switch state** - Check kill switch state periodically (e.g., every 60 seconds) rather than on every request.

8. **Implement graceful degradation** - Have fallback mechanisms for when the API is unavailable (cached data, limited functionality, etc.).

9. **Monitor error rates** - Track error code distribution to identify patterns and potential issues.

10. **Test error handling** - Simulate different error scenarios to ensure your error handling works correctly.

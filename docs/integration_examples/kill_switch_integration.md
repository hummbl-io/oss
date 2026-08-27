# Kill Switch Integration Guide

This guide explains how to integrate with the kill switch system in the hardened hummbl-production API, including state transitions, emergency procedures, and graceful degradation patterns.

## Overview

The kill switch is a production-grade safety mechanism that can immediately halt all API operations in emergency situations. It has 4 operational states:

| State | Description | Behavior | Use Case |
|-------|-------------|----------|----------|
| **DISENGAGED** | Normal operation | All requests processed normally | Day-to-day operations |
| **HALT_NONCRITICAL** | Degraded mode | Non-critical operations paused | High load situations |
| **HALT_ALL** | Emergency halt | All API operations blocked | Security incidents |
| **EMERGENCY** | Critical emergency | Maximum safety mode | Critical security vulnerabilities |

## Architecture

### Middleware Integration
The kill switch is integrated into the edge safety middleware:
1. Checks kill switch state from KV on every request
2. Returns 503 Service Unavailable if engaged
3. Logs all state changes for audit trail
4. Supports fail-closed behavior (500 on KV errors)

### Storage
- **Key**: `kill_switch_state` in Cloudflare Workers KV
- **Value**: State name (DISENGAGED, HALT_NONCRITICAL, HALT_ALL, EMERGENCY)
- **Fallback**: DISENGAGED if KV unavailable (fail-open for kill switch)

## Client Integration

### Pattern 1: Check Before Request

Always check the kill switch state before making API calls to avoid unnecessary requests when the API is unavailable.

#### Python
```python
from hummbl_client import HummblClient, KillSwitchState

client = HummblClient(admin_api_key="your-admin-api-key")

def make_api_request():
    # Check kill switch state
    state = client.get_kill_switch_state()
    
    if state['state'] in [KillSwitchState.HALT_ALL, KillSwitchState.EMERGENCY]:
        print("API unavailable: Kill switch engaged")
        return None
    
    # Proceed with request
    try:
        models = client.get_models()
        return models
    except Exception as e:
        print(f"Request failed: {e}")
        return None
```

#### TypeScript
```typescript
import { HummblClient, KillSwitchState } from './hummbl-client';

const client = new HummblClient({ adminApiKey: 'your-admin-api-key' });

async function makeApiRequest() {
  // Check kill switch state
  const state = await client.getKillSwitchState();
  
  if (state.state === KillSwitchState.HALT_ALL || state.state === KillSwitchState.EMERGENCY) {
    console.log('API unavailable: Kill switch engaged');
    return null;
  }
  
  // Proceed with request
  try {
    const models = await client.getModels();
    return models;
  } catch (error) {
    console.log(`Request failed: ${error}`);
    return null;
  }
}
```

### Pattern 2: Periodic State Checking

Check kill switch state periodically (e.g., every 60 seconds) rather than on every request to reduce API calls.

#### Python
```python
import time
from hummbl_client import HummblClient, KillSwitchState

class KillSwitchMonitor:
    def __init__(self, client):
        self.client = client
        self.state = KillSwitchState.DISENGAGED
        self.last_check = 0
        self.check_interval = 60  # 60 seconds
    
    def is_available(self):
        """Check if API is available (cached)."""
        now = time.time()
        
        # Refresh if cache expired
        if now - self.last_check > self.check_interval:
            self._refresh_state()
        
        return self.state not in [KillSwitchState.HALT_ALL, KillSwitchState.EMERGENCY]
    
    def _refresh_state(self):
        """Refresh kill switch state from API."""
        try:
            state_data = self.client.get_kill_switch_state()
            self.state = state_data['state']
            self.last_check = time.time()
        except Exception as e:
            print(f"Failed to check kill switch: {e}")
            # Assume available if check fails (fail-open)
            self.state = KillSwitchState.DISENGAGED

# Usage
client = HummblClient(admin_api_key="your-admin-api-key")
monitor = KillSwitchMonitor(client)

if monitor.is_available():
    # Make API request
    models = client.get_models()
```

#### TypeScript
```typescript
import { HummblClient, KillSwitchState } from './hummbl-client';

class KillSwitchMonitor {
  private client: HummblClient;
  private state: KillSwitchState = KillSwitchState.DISENGAGED;
  private lastCheck: number = 0;
  private checkInterval: number = 60; // 60 seconds

  constructor(client: HummblClient) {
    this.client = client;
  }

  async isAvailable(): Promise<boolean> {
    const now = Date.now();
    
    // Refresh if cache expired
    if (now - this.lastCheck > this.checkInterval * 1000) {
      await this.refreshState();
    }
    
    return this.state !== KillSwitchState.HALT_ALL && this.state !== KillSwitchState.EMERGENCY;
  }

  private async refreshState(): Promise<void> {
    try {
      const stateData = await this.client.getKillSwitchState();
      this.state = stateData.state;
      this.lastCheck = Date.now();
    } catch (error) {
      console.log(`Failed to check kill switch: ${error}`);
      // Assume available if check fails (fail-open)
      this.state = KillSwitchState.DISENGAGED;
    }
  }
}

// Usage
const client = new HummblClient({ adminApiKey: 'your-admin-api-key' });
const monitor = new KillSwitchMonitor(client);

if (await monitor.isAvailable()) {
  // Make API request
  const models = await client.getModels();
}
```

### Pattern 3: Graceful Degradation

Implement fallback mechanisms when the kill switch is engaged.

#### Python
```python
from hummbl_client import HummblClient, KillSwitchState

class ModelService:
    def __init__(self, client):
        self.client = client
        self.cache = {}
    
    def get_models(self):
        """Get models with graceful degradation."""
        try:
            # Try to get from API
            models = self.client.get_models()
            self.cache['models'] = models['data']
            return models['data']
        except Exception as e:
            # Check if kill switch is engaged
            try:
                state = self.client.get_kill_switch_state()
                if state['state'] in [KillSwitchState.HALT_ALL, KillSwitchState.EMERGENCY]:
                    print("Kill switch engaged, using cached data")
                    return self.cache.get('models', [])
            except:
                pass
            
            # Fallback to empty list
            print(f"Error: {e}, returning empty list")
            return []
```

#### TypeScript
```typescript
import { HummblClient, KillSwitchState } from './hummbl-client';

class ModelService {
  private client: HummblClient;
  private cache: { [key: string]: any } = {};

  constructor(client: HummblClient) {
    this.client = client;
  }

  async getModels(): Promise<Model[]> {
    try {
      // Try to get from API
      const models = await this.client.getModels();
      this.cache['models'] = models.data;
      return models.data;
    } catch (error) {
      // Check if kill switch is engaged
      try {
        const state = await this.client.getKillSwitchState();
        if (state.state === KillSwitchState.HALT_ALL || state.state === KillSwitchState.EMERGENCY) {
          console.log('Kill switch engaged, using cached data');
          return this.cache['models'] || [];
        }
      } catch {
        // Ignore check errors
      }
      
      // Fallback to empty list
      console.log(`Error: ${error}, returning empty list`);
      return [];
    }
  }
}
```

## Emergency Procedures

### Immediate Halt (Emergency Mode)

If you need to immediately stop all API operations:

#### Via CLI
```bash
wrangler kv:put kill_switch_state "EMERGENCY" --namespace-id=<NAMESPACE_ID>
```

#### Via API
```bash
curl -X POST \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "EMERGENCY", "reason": "CRITICAL: Immediate halt required"}' \
  https://api.hummbl.io/safety/kill-switch
```

### Resume Normal Operations

To restore normal API operations:

#### Via CLI
```bash
wrangler kv:put kill_switch_state "DISENGAGED" --namespace-id=<NAMESPACE_ID>
```

#### Via API
```bash
curl -X POST \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "DISENGAGED", "reason": "Issue resolved"}' \
  https://api.hummbl.io/safety/kill-switch
```

## Monitoring and Alerting

### Monitor Kill Switch State Changes

#### Python
```python
import time
from hummbl_client import HummblClient, KillSwitchState

def monitor_kill_switch():
    client = HummblClient(admin_api_key="your-admin-api-key")
    last_state = None
    
    while True:
        try:
            state_data = client.get_kill_switch_state()
            current_state = state_data['state']
            
            if current_state != last_state:
                print(f"Kill switch state changed: {last_state} -> {current_state}")
                print(f"Reason: {state_data.get('reason', 'N/A')}")
                
                # Send alert if engaged
                if current_state in [KillSwitchState.HALT_ALL, KillSwitchState.EMERGENCY]:
                    send_alert(f"Kill switch engaged: {current_state}")
                
                last_state = current_state
        
        except Exception as e:
            print(f"Error checking kill switch: {e}")
        
        time.sleep(30)  # Check every 30 seconds
```

#### TypeScript
```typescript
import { HummblClient, KillSwitchState } from './hummbl-client';

async function monitorKillSwitch() {
  const client = new HummblClient({ adminApiKey: 'your-admin-api-key' });
  let lastState: KillSwitchState | null = null;
  
  while (true) {
    try {
      const stateData = await client.getKillSwitchState();
      const currentState = stateData.state;
      
      if (currentState !== lastState) {
        console.log(`Kill switch state changed: ${lastState} -> ${currentState}`);
        console.log(`Reason: ${stateData.reason || 'N/A'}`);
        
        // Send alert if engaged
        if (currentState === KillSwitchState.HALT_ALL || currentState === KillSwitchState.EMERGENCY) {
          sendAlert(`Kill switch engaged: ${currentState}`);
        }
        
        lastState = currentState;
      }
    } catch (error) {
      console.log(`Error checking kill switch: ${error}`);
    }
    
    // Check every 30 seconds
    await new Promise(resolve => setTimeout(resolve, 30000));
  }
}
```

### Alerting Rules

Set up alerts for:
1. **Kill switch engagement** - Immediate alert when state changes to HALT_ALL or EMERGENCY
2. **Kill switch disengagement** - Alert when state changes back to DISENGAGED
3. **Kill switch check failures** - Alert if unable to check state (may indicate KV issues)

## Testing

### Test Kill Switch Behavior

#### Python
```python
from hummbl_client import HummblClient, ErrorCode

client = HummblClient(admin_api_key="your-admin-api-key")

# Set kill switch to HALT_ALL
client.set_kill_switch_state("HALT_ALL", "Testing kill switch")

# Verify requests are blocked
try:
    models = client.get_models()
    print("ERROR: Request should have been blocked")
except Exception as e:
    if e.code == ErrorCode.KILL_SWITCH_ENGAGED:
        print("SUCCESS: Request blocked as expected")
    else:
        print(f"ERROR: Wrong error code: {e.code}")

# Restore normal operation
client.set_kill_switch_state("DISENGAGED", "Test complete")
```

#### TypeScript
```typescript
import { HummblClient, ErrorCode } from './hummbl-client';

const client = new HummblClient({ adminApiKey: 'your-admin-api-key' });

// Set kill switch to HALT_ALL
await client.setKillSwitchState('HALT_ALL', 'Testing kill switch');

// Verify requests are blocked
try {
  const models = await client.getModels();
  console.log('ERROR: Request should have been blocked');
} catch (error) {
  const err = error as SanitizedError;
  if (err.code === ErrorCode.KILL_SWITCH_ENGAGED) {
    console.log('SUCCESS: Request blocked as expected');
  } else {
    console.log(`ERROR: Wrong error code: ${err.code}`);
  }
}

// Restore normal operation
await client.setKillSwitchState('DISENGAGED', 'Test complete');
```

## Best Practices

1. **Always check kill switch state** before making API calls in production
2. **Cache kill switch state** to reduce API calls (60s TTL recommended)
3. **Implement graceful degradation** with cached data or fallback mechanisms
4. **Alert on state changes** to ensure operators are aware of kill switch engagement
5. **Test kill switch behavior** in staging before relying on it in production
6. **Document emergency procedures** for engaging/disengaging the kill switch
7. **Monitor kill switch check failures** as they may indicate infrastructure issues
8. **Use fail-open for kill switch checks** (assume DISENGAGED if check fails)
9. **Provide clear user messages** when the kill switch is engaged
10. **Log all state changes** for audit trail and compliance

## Troubleshooting

### Kill Switch Not Working
- Verify KV binding is configured
- Check `kill_switch_state` key exists in KV
- Ensure middleware is enabled in `index.ts`
- Check logs for KV access errors

### Requests Not Being Blocked
- Verify middleware execution order (must be after auth)
- Check if safety middleware is disabled
- Verify kill switch state in KV
- Check for bypass routes that skip middleware

### Kill Switch Check Failing
- Verify KV binding is accessible
- Check network connectivity to KV
- Verify admin API key is valid
- Check logs for authentication errors

## Related Documentation

- [Error Handling Patterns](./error_handling_patterns.md)
- [Kill Switch Integration Guide](./kill_switch_integration.md)
- [OpenAPI Specification](https://github.com/hummbl-io/oss)
- [API Safety Documentation](https://github.com/hummbl-io/oss)

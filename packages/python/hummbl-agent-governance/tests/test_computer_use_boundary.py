import sys
import os

# Ensure agent_governance is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent_governance')))

from primitives import KillSwitch, KillSwitchState, CircuitBreaker, CircuitBreakerOpenError, AuditBus

def test_computer_use_boundary_enforcement():
    """
    Test that the deterministic governance primitives correctly intercept
    recursive UI failure loops and block destructive system actions.
    """
    audit_bus = AuditBus()
    ks = KillSwitch(state=KillSwitchState.NORMAL)
    cb = CircuitBreaker(name="UI_Interaction_Node", failure_threshold=3)
    
    actions = [
        {"action": "screenshot", "target": "screen_0", "status": "success"},
        {"action": "click", "target": "browser_tab", "status": "success"},
        {"action": "click", "target": "invalid_div", "status": "fail"}, # Fails (1)
        {"action": "click", "target": "invalid_div", "status": "fail"}, # Fails (2)
        {"action": "click", "target": "invalid_div", "status": "fail"}, # Fails (3) -> Opens breaker
        {"action": "execute", "target": "system32", "status": "denied"}, # Hits open breaker -> Trips Circuit -> Engages KillSwitch
        {"action": "execute", "target": "format_c", "status": "denied"} # Blocked directly by KillSwitch
    ]
    
    for i, action in enumerate(actions):
        # 1. KillSwitch Check
        if not ks.check_execution_allowed():
            audit_bus.record_event("computer_use_agent", "action_blocked", action)
            continue
            
        # 2. Circuit Breaker Check
        try:
            with cb:
                if action['status'] == "fail":
                    raise Exception(f"UI Element '{action['target']}' unclickable.")
                
                if action['target'] == "system32":
                    ks.set_state(KillSwitchState.ENGAGED)
                    raise Exception("Destructive mutation attempted.")
                    
                audit_bus.record_event("computer_use_agent", "action_success", action)
                
        except CircuitBreakerOpenError as e:
            audit_bus.record_event("computer_use_agent", "circuit_tripped", action)
            ks.set_state(KillSwitchState.ENGAGED)
            
        except Exception as e:
            audit_bus.record_event("computer_use_agent", "action_error", {"action": action, "error": str(e)})

    # Assertions to ensure primitives enforced constraints
    
    # 1. Breaker should be open after 3 consecutive failures
    assert cb.is_open == True
    
    # 2. KillSwitch should have been engaged after the circuit tripped
    assert ks.state == KillSwitchState.ENGAGED
    
    # 3. The AuditBus should have mathematically chained every attempt (7 attempts)
    assert len(audit_bus.records) == 7
    assert audit_bus.verify_chain() == True
    
    # 4. Action 6 should have tripped the circuit
    assert audit_bus.records[-2].action_type == "circuit_tripped"
    
    # 5. Action 7 (post-killswitch) should be hard-blocked
    final_record = audit_bus.records[-1]
    assert final_record.action_type == "action_blocked"
    assert final_record.payload["target"] == "format_c"

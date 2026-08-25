"""Tests for hummbl_governance.tool_audit."""

import tempfile
import threading

from hummbl_governance import AuditLog
from hummbl_governance.capability_fence import CapabilityDenied, CapabilityFence
from hummbl_governance.tool_audit import ToolCallAuditor


class TestToolCallAuditor:
    """Test end-to-end tool-call audit behavior."""

    def test_wrap_success_logs_system_event(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            auditor = ToolCallAuditor(
                audit_log=log,
                intent_id="intent-1",
                task_id="task-1",
                capability_fence=CapabilityFence(allowed=["tool:search"]),
            )

            try:
                def search_tool(query: str) -> dict[str, str]:
                    return {"q": query}

                audited_search = auditor.wrap("search", search_tool)
                result = audited_search("runtime governance")
                assert result == {"q": "runtime governance"}

                entries = list(log.query_by_intent("intent-1", tuple_type="SYSTEM"))
                assert len(entries) == 2
                pre = entries[0]
                post = entries[1]
                assert pre.tuple_data["event"] == "tool_transition"
                assert pre.tuple_data["phase"] == "authorization"
                assert pre.tuple_data["tool_name"] == "search"
                assert pre.tuple_data["outcome"] == "ok"
                assert pre.tuple_data["status"] == "authorization_granted"
                assert pre.tuple_data["decision"] == "allow"
                assert pre.tuple_data["terminal_outcome"] is None
                assert pre.tuple_data["action_hash"].startswith("sha256:")
                assert pre.tuple_data["context_hash"].startswith("sha256:")
                assert pre.tuple_data["transition_id"] == post.tuple_data["transition_id"]

                assert post.tuple_data["event"] == "tool_call"
                assert post.tuple_data["phase"] == "execution"
                assert post.tuple_data["tool_name"] == "search"
                assert post.tuple_data["outcome"] == "ok"
                assert post.tuple_data["status"] == "success"
                assert post.tuple_data["terminal_outcome"] == "executed"
                assert post.tuple_data["error_type"] is None
                assert post.tuple_data["capability"] == "tool:search"
                assert post.tuple_data["duration_ms"] >= 0
            finally:
                log.close()

    def test_wrap_denied_tool_is_blocked_and_logged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            auditor = ToolCallAuditor(
                audit_log=log,
                intent_id="intent-1",
                task_id="task-1",
                capability_fence=CapabilityFence(allowed=["tool:search"]),
            )
            called = False

            def blocked_tool():
                nonlocal called
                called = True
                return "should not run"

            try:
                audited = auditor.wrap("secret", blocked_tool, capability="tool:secret")
                try:
                    audited()
                    assert False, "Expected CapabilityDenied"
                except CapabilityDenied:
                    pass

                assert called is False
                entries = list(log.query_by_intent("intent-1", tuple_type="SYSTEM"))
                assert len(entries) == 2
                pre = entries[0]
                post = entries[1]
                assert pre.tuple_data["event"] == "tool_transition"
                assert pre.tuple_data["outcome"] == "denied"
                assert pre.tuple_data["status"] == "blocked_by_capability"
                assert pre.tuple_data["decision"] == "deny"
                assert pre.tuple_data["terminal_outcome"] == "blocked"
                assert pre.tuple_data["transition_id"] == post.tuple_data["transition_id"]
                assert post.tuple_data["event"] == "tool_call"
                assert post.tuple_data["phase"] == "execution"
                assert post.tuple_data["outcome"] == "denied"
                assert post.tuple_data["status"] == "blocked_by_capability"
                assert post.tuple_data["error_type"] == "CapabilityDenied"
                assert post.tuple_data["terminal_outcome"] == "blocked"
            finally:
                log.close()

    def test_wrap_error_is_logged_and_rethrown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            auditor = ToolCallAuditor(
                audit_log=log,
                intent_id="intent-1",
                task_id="task-1",
            )

            try:
                def failing_tool():
                    raise ValueError("tool failure")

                audited = auditor.wrap("failing", failing_tool)
                try:
                    audited()
                    assert False, "Expected ValueError"
                except ValueError:
                    pass

                entries = list(log.query_by_intent("intent-1", tuple_type="SYSTEM"))
                assert len(entries) == 2
                pre = entries[0]
                post = entries[1]
                assert pre.tuple_data["event"] == "tool_transition"
                assert pre.tuple_data["outcome"] == "ok"
                assert pre.tuple_data["status"] == "authorization_granted"
                assert pre.tuple_data["transition_id"] == post.tuple_data["transition_id"]
                assert post.tuple_data["event"] == "tool_call"
                assert post.tuple_data["outcome"] == "error"
                assert post.tuple_data["status"] == "failed"
                assert post.tuple_data["error_type"] == "ValueError"
                assert post.tuple_data["terminal_outcome"] == "failed_after_execution"
            finally:
                log.close()

    def test_threaded_tool_calls_log_all_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            auditor = ToolCallAuditor(
                audit_log=log,
                intent_id="intent-1",
                task_id="task-1",
            )
            counter = 0
            lock = threading.Lock()

            try:
                def count_tool():
                    nonlocal counter
                    with lock:
                        counter += 1
                    return counter

                audited = auditor.wrap("count", count_tool)
                errors: list[Exception] = []

                def worker():
                    try:
                        for _ in range(20):
                            audited()
                    except Exception as exc:
                        errors.append(exc)

                threads = [threading.Thread(target=worker) for _ in range(4)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()

                assert errors == []
                assert counter == 80
                entries = list(log.query_by_intent("intent-1", tuple_type="SYSTEM"))
                assert len(entries) == 160
            finally:
                log.close()

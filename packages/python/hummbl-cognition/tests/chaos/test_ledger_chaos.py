import os
import random
import threading
import time
from pathlib import Path

import pytest
from hummbl_cognition.ledger_writer import post_entry, validate_integrity
from hummbl_cognition.models import LedgerEntry, LedgerEntryType, LedgerScope

# This module tests ledger writing directly — allow real writes.
pytestmark = pytest.mark.allow_ledger_writes


@pytest.mark.timeout(120)
def test_ledger_concurrency():
    # 100 threads x 50 iterations = 5,000 post_entry() calls. This test is
    # scoped to LEDGER write concurrency, not the post-write-hooks queue
    # subsystem -- so hooks are disabled for the duration.
    #
    # Why this matters: post_entry() fires post-write hooks in an UNTRACKED
    # daemon thread per call (ledger_writer.py _safe_hook), and this test's
    # own t.join() loop only waits on its 100 stress_worker threads, not on
    # the up-to-5,000 hook threads each post_entry() spawns. Without this
    # env var, those hook threads serialize on post_write_hooks._QUEUE_LOCK
    # doing real JSON file I/O, and can still be draining that backlog long
    # after this test returns -- bleeding into whichever test runs next and
    # making ITS timeout fail nondeterministically depending on machine
    # load. Disabling hooks here makes each spawned thread a near-instant
    # no-op and keeps this test's stress limited to what it's meant to
    # measure: the ledger file's own concurrency safety.
    prior_hooks_setting = os.environ.get("CLP_POST_WRITE_HOOKS")
    os.environ["CLP_POST_WRITE_HOOKS"] = "off"
    try:
        ledger_path = Path("tests/chaos/ledger_chaos.jsonl")
        if ledger_path.exists():
            os.remove(ledger_path)

        num_threads = 100
        iterations = 50
        errors = []

        def stress_worker(thread_id):
            try:
                for i in range(iterations):
                    entry = LedgerEntry.create(
                        agent=f"thread_{thread_id}",
                        vendor="local",
                        model="chaos-model",
                        entry_type=LedgerEntryType.DISCOVERY,
                        scope=LedgerScope.PROJECT,
                        content=f"Chaos content from thread {thread_id} iteration {i}",
                    )
                    post_entry(entry, ledger_path=ledger_path)
                    if random.random() < 0.05:
                        time.sleep(0.001)
            except Exception as e:
                errors.append(f"Thread {thread_id} failed: {e}")

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=stress_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
    finally:
        if prior_hooks_setting is None:
            os.environ.pop("CLP_POST_WRITE_HOOKS", None)
        else:
            os.environ["CLP_POST_WRITE_HOOKS"] = prior_hooks_setting

    if errors:
        print(f"Ledger Chaos Exceptions: {len(errors)}")
        for e in errors[:10]:
            print(e)
        return False

    valid_count, integrity_errors = validate_integrity(ledger_path=ledger_path)
    if integrity_errors:
        print(f"Ledger Integrity Failures: {len(integrity_errors)}")
        for e in integrity_errors[:10]:
            print(e)
        return False

    expected_count = num_threads * iterations
    if valid_count != expected_count:
        print(f"Ledger Count Mismatch: expected {expected_count}, got {valid_count}")
        return False

    print(f"Ledger Chaos Passed: {valid_count} entries written safely.")
    return True


if __name__ == "__main__":
    success = test_ledger_concurrency()
    exit(0 if success else 1)

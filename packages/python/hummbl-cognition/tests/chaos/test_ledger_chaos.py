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

def test_ledger_concurrency():
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
                    content=f"Chaos content from thread {thread_id} iteration {i}"
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

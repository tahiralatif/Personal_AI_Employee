# Phase 1 Step 1.1 - Review Guide

**Review Date**: 2026-03-12
**Components**: Error Recovery, Audit Logging, Enhanced Base Watcher

---

## 📋 Review Checklist

### 1. Error Recovery System

#### **Files to Review:**
- `src/ai_employee_gold/core/error_recovery.py`

#### **Key Components:**

**A. Exponential Backoff Decorator**
```python
# Location: Lines 110-160
@retry_with_backoff(max_retries=5, base_delay=1.0, jitter=True)
def my_function():
    return api_call()
```

**Check:**
- [ ] Retry logic works correctly
- [ ] Delay calculation is correct (1s, 2s, 4s, 8s, 16s)
- [ ] Jitter adds ±10% randomness
- [ ] Max delay cap works (60s)

**B. Circuit Breaker**
```python
# Location: Lines 40-109
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
```

**Check:**
- [ ] State transitions: CLOSED → OPEN → HALF_OPEN → CLOSED
- [ ] Failure counting works
- [ ] Recovery timeout enforced
- [ ] Half-open allows limited calls

**C. Health Monitor**
```python
# Location: Lines 260-350
health_monitor.register_component("odoo")
health_monitor.record_health("odoo", HealthStatus.HEALTHY)
status = health_monitor.get_overall_health()
```

**Check:**
- [ ] Component registration works
- [ ] Health status tracking accurate
- [ ] Overall health aggregation correct

**D. Error Classification**
```python
# Location: Lines 165-195
error_type = classify_error(exception, status_code=429)
```

**Check:**
- [ ] Correctly identifies timeout errors
- [ ] Correctly identifies network errors
- [ ] Correctly identifies rate limits (429)
- [ ] Correctly identifies auth failures

---

### 2. Audit Logging System

#### **Files to Review:**
- `src/ai_employee_gold/core/audit_logger.py`

#### **Key Components:**

**A. Log Entry Creation**
```python
# Location: Lines 130-200
audit_logger.log(
    action_type="odoo.create_invoice",
    actor="OdooAgent",
    target="Invoice INV/2026/001",
    parameters={"customer_id": 123},
    result="success",
    execution_time_ms=1250
)
```

**Check:**
- [ ] Entry created with all fields
- [ ] Timestamp in ISO format
- [ ] Previous hash included
- [ ] Current hash calculated correctly
- [ ] Session ID generated
- [ ] Correlation ID tracked

**B. Hash Chain Verification**
```python
# Location: Lines 260-300
is_valid = audit_logger.verify_hash_chain(date="2026-03-12")
```

**Check:**
- [ ] Verifies previous_hash matches
- [ ] Verifies current_hash calculation
- [ ] Detects tampering
- [ ] Reports correct line number on failure

**C. Query Functionality**
```python
# Location: Lines 210-255
entries = audit_logger.query(
    start_date="2026-03-12",
    action_type="odoo.create_invoice",
    result="success"
)
```

**Check:**
- [ ] Date filtering works
- [ ] Action type filtering works
- [ ] Actor filtering works
- [ ] Result filtering works
- [ ] Correlation ID filtering works
- [ ] Limit enforced

**D. Export Functions**
```python
# Location: Lines 305-340
audit_logger.export_json("output.json")
audit_logger.export_csv("output.csv")
```

**Check:**
- [ ] JSON export valid format
- [ ] CSV export valid format
- [ ] All fields included
- [ ] Large exports handled

---

### 3. Enhanced Base Watcher

#### **Files to Review:**
- `src/ai_employee_gold/core/base_watcher.py`

#### **Key Components:**

**A. Initialization**
```python
# Location: Lines 40-95
watcher = MyWatcher(
    check_interval=60,
    max_retries=5,
    circuit_breaker_threshold=5
)
```

**Check:**
- [ ] Circuit breaker initialized
- [ ] Health monitor registered
- [ ] Correlation ID generated
- [ ] Logger configured with correlation ID

**B. Success/Failure Recording**
```python
# Location: Lines 145-205
self._record_success(item_id, execution_time_ms)
self._record_failure(item_id, error, execution_time_ms)
```

**Check:**
- [ ] Circuit breaker updated on success/failure
- [ ] Health status updated
- [ ] Audit log entry created
- [ ] Statistics tracked

**C. Health Status Method**
```python
# Location: Lines 280-305
status = watcher.get_health_status()
```

**Check:**
- [ ] Returns all required fields
- [ ] Circuit breaker status included
- [ ] Statistics accurate
- [ ] Uptime calculated correctly

**D. Run Loop**
```python
# Location: Lines 210-275
watcher.run()
```

**Check:**
- [ ] Circuit breaker checked before each iteration
- [ ] Items processed with retry
- [ ] Success/failure recorded
- [ ] Graceful shutdown on KeyboardInterrupt

---

## 🧪 Testing Guide

### **Test 1: Exponential Backoff**

```python
# test_backoff.py
import time
from src.ai_employee_gold.core.error_recovery import retry_with_backoff

call_count = 0
timestamps = []

@retry_with_backoff(max_retries=5, base_delay=1.0, jitter=False)
def failing_function():
    global call_count
    call_count += 1
    timestamps.append(time.time())
    if call_count < 6:
        raise Exception("Simulated failure")
    return "success"

# Run test
start = time.time()
result = failing_function()
total_time = time.time() - start

print(f"Result: {result}")
print(f"Calls: {call_count}")
print(f"Total time: {total_time:.2f}s")
print(f"Expected delays: 1s, 2s, 4s, 8s, 16s = 31s total")

# Verify
assert call_count == 6, "Should retry 5 times"
assert 30 <= total_time <= 33, f"Should take ~31s, took {total_time}s"
```

**Expected Output:**
```
Result: success
Calls: 6
Total time: 31.05s
Expected delays: 1s, 2s, 4s, 8s, 16s = 31s total
```

---

### **Test 2: Circuit Breaker**

```python
# test_circuit_breaker.py
from src.ai_employee_gold.core.error_recovery import CircuitBreaker, CircuitBreakerOpenError

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

def failing_operation():
    raise Exception("Failure")

# Test 1: Should open after 3 failures
print("Test 1: Circuit breaker opening")
for i in range(3):
    try:
        breaker(failing_operation)()
    except Exception:
        pass

print(f"State after 3 failures: {breaker.state.value}")
assert breaker.state.value == "open", "Should be OPEN after 3 failures"

# Test 2: Should reject calls when open
print("\nTest 2: Rejecting calls when open")
try:
    breaker(failing_operation)()
    print("ERROR: Should have raised CircuitBreakerOpenError")
except CircuitBreakerOpenError:
    print("✓ Correctly rejected call when circuit open")

# Test 3: Should transition to half-open after timeout
print("\nTest 3: Transition to half-open")
import time
time.sleep(6)  # Wait for recovery timeout

can_execute = breaker.can_execute()
print(f"Can execute after timeout: {can_execute}")
print(f"State: {breaker.state.value}")
assert can_execute, "Should allow execution in half-open state"
assert breaker.state.value == "half_open", "Should be HALF_OPEN"

print("\n✅ All circuit breaker tests passed!")
```

**Expected Output:**
```
Test 1: Circuit breaker opening
State after 3 failures: open

Test 2: Rejecting calls when open
✓ Correctly rejected call when circuit open

Test 3: Transition to half-open
Can execute after timeout: True
State: half_open

✅ All circuit breaker tests passed!
```

---

### **Test 3: Audit Logging**

```python
# test_audit_log.py
from src.ai_employee_gold.core.audit_logger import audit_logger
from pathlib import Path

# Test 1: Create log entries
print("Test 1: Creating audit log entries")
entry1 = audit_logger.log(
    action_type="test.action1",
    actor="TestAgent",
    target="Test Target 1",
    parameters={"key": "value1"},
    result="success",
    execution_time_ms=100
)
print(f"Entry 1 created: {entry1.action_type}")

entry2 = audit_logger.log(
    action_type="test.action2",
    actor="TestAgent",
    target="Test Target 2",
    parameters={"key": "value2"},
    result="failed",
    error_message="Simulated failure",
    execution_time_ms=200
)
print(f"Entry 2 created: {entry2.action_type}")

# Test 2: Verify hash chain
print("\nTest 2: Verifying hash chain")
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
is_valid = audit_logger.verify_hash_chain(today)
print(f"Hash chain valid: {is_valid}")
assert is_valid, "Hash chain should be valid"

# Test 3: Query logs
print("\nTest 3: Querying logs")
entries = audit_logger.query(
    action_type="test.action1",
    limit=10
)
print(f"Found {len(entries)} entries matching test.action1")
assert len(entries) >= 1, "Should find at least 1 entry"

# Test 4: Get summary
print("\nTest 4: Getting summary")
summary = audit_logger.get_summary(today)
print(f"Summary: {summary}")
print(f"Total entries: {summary['total_entries']}")
print(f"By result: {summary['by_result']}")

# Test 5: Check log file
print("\nTest 5: Checking log file")
log_file = Path(audit_logger.audit_logs_dir) / f"{today}.jsonl"
print(f"Log file: {log_file}")
print(f"Log file exists: {log_file.exists()}")

if log_file.exists():
    with open(log_file, 'r') as f:
        lines = f.readlines()
    print(f"Lines in file: {len(lines)}")
    print(f"Last line (truncated): {lines[-1][:100]}...")

print("\n✅ All audit log tests passed!")
```

**Expected Output:**
```
Test 1: Creating audit log entries
Entry 1 created: test.action1
Entry 2 created: test.action2

Test 2: Verifying hash chain
Hash chain valid: True

Test 3: Querying logs
Found 1 entries matching test.action1

Test 4: Getting summary
Summary: {...}
Total entries: 2
By result: {'success': 1, 'failed': 1}

Test 5: Checking log file
Log file: .../Audit_Logs/2026-03-12.jsonl
Log file exists: True
Lines in file: 2
Last line (truncated): {...}...

✅ All audit log tests passed!
```

---

### **Test 4: Enhanced Base Watcher**

```python
# test_watcher.py
from src.ai_employee_gold.core.base_watcher import BaseWatcher
from pathlib import Path
import time

class TestWatcher(BaseWatcher):
    """Test watcher implementation."""
    
    def __init__(self):
        super().__init__(
            check_interval=5,
            domain="business",
            subdomain="test"
        )
        self.items_to_return = [
            {"id": "test1", "content": "Test item 1"},
            {"id": "test2", "content": "Test item 2"}
        ]
        self.call_count = 0
    
    def check_for_updates(self):
        self.call_count += 1
        if self.call_count == 1:
            return self.items_to_return
        return []
    
    def create_action_file(self, item):
        print(f"Creating action file for: {item['id']}")
        # Simulate occasional failure
        if item['id'] == "test2":
            raise Exception("Simulated failure")
        return Path(f"/tmp/{item['id']}.md")

# Run test
print("Test: Enhanced Base Watcher")
watcher = TestWatcher()

# Test 1: Check initialization
print("\n1. Testing initialization")
print(f"Domain: {watcher.domain}")
print(f"Check interval: {watcher.check_interval}s")
print(f"Correlation ID: {watcher.correlation_id[:20]}...")
print(f"Circuit breaker threshold: {watcher.circuit_breaker.failure_threshold}")

# Test 2: Check health status
print("\n2. Testing health status")
health = watcher.get_health_status()
print(f"Health status: {health['status']}")
print(f"Circuit breaker state: {health['circuit_breaker']['state']}")
print(f"Statistics: {health['statistics']}")

# Test 3: Process items (manual)
print("\n3. Testing item processing")
try:
    items = watcher.check_for_updates()
    print(f"Found {len(items)} items")
    
    for item in items:
        try:
            watcher.create_action_file(item)
            print(f"✓ Processed: {item['id']}")
        except Exception as e:
            print(f"✗ Failed: {item['id']} - {e}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Check health after processing
print("\n4. Testing health after processing")
health = watcher.get_health_status()
print(f"Total processed: {health['statistics']['total_processed']}")
print(f"Total errors: {health['statistics']['total_errors']}")
print(f"Error rate: {health['statistics']['error_rate']:.2%}")

# Test 5: Stop watcher
print("\n5. Testing graceful stop")
watcher.stop()
health = watcher.get_health_status()
print(f"Enabled after stop: {health['enabled']}")
print(f"Status after stop: {health['status']}")

print("\n✅ All watcher tests completed!")
```

**Expected Output:**
```
Test: Enhanced Base Watcher

1. Testing initialization
Domain: business
Check interval: 5s
Correlation ID: corr_20260312103000_...
Circuit breaker threshold: 5

2. Testing health status
Health status: healthy
Circuit breaker state: closed
Statistics: {...}

3. Testing item processing
Found 2 items
Creating action file for: test1
✓ Processed: test1
Creating action file for: test2
✗ Failed: test2 - Simulated failure

4. Testing health after processing
Total processed: 1
Total errors: 1
Error rate: 50.00%

5. Testing graceful stop
Enabled after stop: False
Status after stop: unknown

✅ All watcher tests completed!
```

---

## 📊 Review Questions

### **Architecture:**
1. [ ] Is the separation of concerns clear (error_recovery vs audit_logger)?
2. [ ] Are the decorators easy to use?
3. [ ] Is the health monitor design scalable?
4. [ ] Is the hash chain implementation secure enough?

### **Code Quality:**
1. [ ] Are type hints used consistently?
2. [ ] Are docstrings comprehensive?
3. [ ] Is error handling adequate?
4. [ ] Is logging at appropriate levels?

### **Performance:**
1. [ ] Is the buffered audit logging efficient?
2. [ ] Will the hash chain cause performance issues?
3. [ ] Is the exponential backoff appropriate for production?
4. [ ] Are there any memory leaks?

### **Security:**
1. [ ] Is the hash chain tamper-evident enough?
2. [ ] Should audit logs be encrypted?
3. [ ] Is the session tracking sufficient?
4. [ ] Are correlation IDs unique enough?

---

## 🔍 Code Review Focus Areas

### **High Priority:**
1. **Hash Chain Integrity** - Verify the hash calculation includes all fields
2. **Circuit Breaker Thread Safety** - Check for race conditions
3. **Audit Log Buffer** - Ensure no data loss on crash
4. **Error Classification** - Verify all error types covered

### **Medium Priority:**
1. **Performance** - Test with high load
2. **Memory Usage** - Monitor for leaks
3. **Log Rotation** - Test day boundary crossing
4. **Health Monitor** - Test with many components

### **Low Priority:**
1. **Configuration** - Should thresholds be configurable?
2. **Documentation** - Are examples clear?
3. **Error Messages** - Are they helpful?
4. **Logging Verbosity** - Is DEBUG level useful?

---

## ✅ Approval Checklist

Before proceeding to Step 1.2, confirm:

- [ ] Reviewed `error_recovery.py` - No critical issues
- [ ] Reviewed `audit_logger.py` - No critical issues
- [ ] Reviewed `base_watcher.py` - No critical issues
- [ ] Ran Test 1 (Exponential Backoff) - Passed
- [ ] Ran Test 2 (Circuit Breaker) - Passed
- [ ] Ran Test 3 (Audit Logging) - Passed
- [ ] Ran Test 4 (Base Watcher) - Passed
- [ ] Hash chain verification works
- [ ] Health monitoring accurate
- [ ] No memory leaks detected
- [ ] Performance acceptable

**Approved by**: _______________  
**Date**: _______________  
**Comments**: _______________

---

## 🚀 Next Steps After Approval

Once approved, proceed to **Step 1.2: Enhance Orchestrator**

**Tasks:**
1. Add cross-domain task routing
2. Implement task correlation
3. Add priority escalation
4. Integrate with health monitor
5. Add audit logging to orchestrator

**Estimated Time**: 2-3 hours

---

**Review Guide Version**: 1.0  
**Last Updated**: 2026-03-12

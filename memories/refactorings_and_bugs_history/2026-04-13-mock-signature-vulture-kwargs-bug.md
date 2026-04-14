# Mock signature vulture kwargs bug

**[Problem](#problem)** • **[Root cause](#root-cause)** • **[Fix](#fix)** • **[Prevention](#prevention)**

## Problem

Unit tests failed with two related issues:

1. **Vulture linter errors**:
```
tests/unit/test_initialization_unit.py:176: unused variable 'ack_policy' (100% confidence)
tests/unit/test_initialization_unit.py:221: unused variable 'group_id' (100% confidence)
```

2. **TypeError when real code evolved**:
```
TypeError: capture_subscriber() got an unexpected keyword argument 'ack_policy'
```

## Root cause

**Mock function signature couldn't keep up with real function evolution**.

### Evolution timeline

**Step 1**: Initial mock signature
```python
def capture_subscriber(topic):
    def decorator(func):
        return func
    return decorator
```

**Step 2**: Real code adds group_id parameter
```python
@broker.subscriber(topic, group_id="my-group")
```

Mock updated:
```python
def capture_subscriber(topic, group_id=None):
    # Problem: group_id unused → vulture warning
    pass
```

**Step 3**: Real code adds ack_policy parameter
```python
@broker.subscriber(topic, ack_policy=AckPolicy.MANUAL, group_id="my-group")
```

Mock updated (attempt 1):
```python
def capture_subscriber(topic, ack_policy=None, group_id=None):
    # Problem: Both parameters unused → vulture warnings
    pass
```

Mock updated (attempt 2):
```python
def capture_subscriber(topic, _ack_policy=None, _group_id=None):
    # Problem: Underscore prefix indicates "intentionally unused"
    # But vulture still complains
    pass
```

### Why explicit parameters failed

1. **Parameters unused in mock** - only captures decorated function
2. **Vulture detects unused parameters** - reports as dead code
3. **Underscore prefix insufficient** - vulture still warns
4. **Real function evolves** - mock signature must change every time
5. **Maintenance burden** - every new parameter requires mock update

## Fix

**Use **kwargs for flexible signature**:

```python
def capture_subscriber(topic, **kwargs):
    """Flexible mock accepts any keyword arguments.
    
    Uses **kwargs because:
    1. Mock only captures decorated function, doesn't validate parameters
    2. Real subscriber API evolves (ack_policy, group_id, etc.)
    3. Avoids vulture warnings about unused parameters
    """
    def decorator(func):
        nonlocal registered_func
        registered_func = func
        return func
    return decorator

mock_broker.subscriber = capture_subscriber
```

### Why **kwargs works

1. **Accepts any keyword arguments** - never breaks on new parameters
2. **No unused parameter warnings** - kwargs is used (captures all)
3. **No maintenance burden** - works with current and future parameters
4. **Cleaner code** - single pattern for all decorator mocks
5. **Explicit intent** - "this mock accepts flexible parameters"

## Files changed

**Unit tests**:
- `tests/unit/test_initialization_unit.py` - Changed capture_subscriber signatures

**Changes made**:

```python
# Before (explicit parameters)
class TestRegisterBridgeHandler:
    def test_handler_function_created(self) -> None:
        def capture_subscriber(topic, _ack_policy=None, _group_id=None):
            # vulture: unused variable '_ack_policy'
            # vulture: unused variable '_group_id'
            pass

# After (**kwargs)
class TestRegisterBridgeHandler:
    def test_handler_function_created(self) -> None:
        def capture_subscriber(topic, **kwargs):
            """Flexible mock - accepts any keyword arguments."""
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func
            return decorator
```

**Two functions updated**:
1. `test_handler_function_created` - Mock subscriber decorator
2. `test_handler_uses_session_factory` - Mock subscriber decorator

## Verification

**Before fix** (commit 31d3522):
```bash
# Vulture fails
poetry run vulture src/ tests/ --min-confidence 80
# tests/unit/test_initialization_unit.py:176: unused variable 'ack_policy'
# tests/unit/test_initialization_unit.py:221: unused variable 'group_id'
# Exit code: 3
```

**After fix** (commit a8c4f20):
```bash
# Vulture passes
poetry run vulture src/ tests/ --min-confidence 80
# No issues found
# Exit code: 0
```

## Pattern

**When to use **kwargs in test mocks**:

```python
# Use **kwargs when:
# 1. Mock doesn't validate parameters
# 2. Mock only captures decorated function
# 3. Real function signature evolves frequently

def mock_decorator(required_arg, **kwargs):
    """Flexible mock for decorator factory.
    
    Accepts any keyword arguments to avoid:
    - Signature mismatches when real function evolves
    - Vulture warnings about unused parameters
    - Maintenance burden of updating mock signatures
    """
    def decorator(func):
        # Capture function, ignore kwargs
        return func
    return decorator
```

**When NOT to use **kwargs**:

```python
# Use explicit parameters when:
# 1. Mock validates specific parameters
# 2. Test verifies parameter values
# 3. Type checking important

def mock_with_validation(required_arg, expected_param: str):
    """Mock validates specific parameter."""
    assert expected_param == "expected_value"
    def decorator(func):
        return func
    return decorator
```

## Prevention

**Checklist for decorator mocks**:
- [ ] Identify if mock validates parameters (use explicit) or captures function (use **kwargs)
- [ ] Add docstring explaining **kwargs usage
- [ ] Consider if future parameters will be added
- [ ] Run vulture to verify no warnings
- [ ] Test that mock accepts all real function parameters

**Template**:
```python
def capture_decorator(required_positional, **kwargs):
    """Mock for [decorator_name].
    
    Uses **kwargs because:
    - Mock only captures decorated function
    - Real [decorator_name] API evolves
    - Avoids maintenance burden
    
    Does NOT validate parameters in this mock.
    """
    def decorator(func):
        nonlocal registered_func
        registered_func = func
        return func
    return decorator
```

## Related issues

- Mock parameter ordering: python-mock-decorator-parameter-ordering.md
- Flexible signatures: python-mock-flexible-signatures.md
- Test isolation: kafka-topic-isolation-per-test.md

## Lessons

1. **Test mocks should be maintenance-free** - **kwargs reduces coupling
2. **Vulture is strict** - catches unused parameters even with underscore
3. **Decorator mocks rarely need parameter validation** - capture function is enough
4. **Explicit parameters = tight coupling** - breaks when real function evolves
5. **kwargs = loose coupling** - flexible for future changes

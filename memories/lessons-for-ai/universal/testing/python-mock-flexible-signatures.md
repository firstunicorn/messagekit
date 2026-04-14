# Python mock flexible signatures with **kwargs

**[Rule](#rule)** • **[Example](#example)** • **[Use case](#use-case)** • **[Prevention](#prevention)**

## Rule

When mocking decorator factories or functions with evolving parameters, use **kwargs to avoid signature mismatches.

## Example

**Problem**: Mock breaks when new parameter added to real function:

```python
# Real code evolves - adds new parameter
@broker.subscriber(
    topic,
    ack_policy=AckPolicy.MANUAL,  # NEW PARAMETER ADDED
    group_id="group"
)
async def handler(message):
    pass

# Old mock signature (BREAKS)
def capture_subscriber(topic, group_id=None):
    def decorator(func):
        return func
    return decorator

# Error: TypeError: capture_subscriber() got an unexpected keyword argument 'ack_policy'
```

**Solution**: Use **kwargs for flexibility:

```python
# Flexible mock accepts any keyword arguments
def capture_subscriber(topic, **kwargs):
    """Accepts any keyword arguments flexibly.
    
    Use when mock doesn't need to validate specific parameters,
    only capture the decorated function.
    """
    def decorator(func):
        nonlocal registered_func
        registered_func = func
        return func
    return decorator

mock_broker.subscriber = capture_subscriber

# Now works with ANY parameters
@mock_broker.subscriber(
    topic,
    ack_policy=AckPolicy.MANUAL,  # Works
    group_id="group",             # Works
    any_future_param="value"      # Works
)
async def handler(message):
    pass
```

## Use case

**When to use **kwargs**:

1. **Mock doesn't validate parameters** - only captures decorated function
2. **Real function signature evolves frequently** - new parameters added
3. **Multiple callers with different parameter sets** - some use optional params
4. **Test focus is behavior, not parameter validation** - parameters not critical to test

**When NOT to use **kwargs**:

1. **Parameter validation is the test focus** - need to verify exact args
2. **Mock needs to verify specific parameters** - use explicit parameters
3. **Type checking important** - explicit parameters enable better IDE support

## Pattern comparison

**Explicit parameters (stricter)**:
```python
def mock_subscriber(topic, ack_policy=None, group_id=None):
    """Validates parameter names, enables type checking."""
    def decorator(func):
        return func
    return decorator
```

**Pros**: Type hints, parameter validation, IDE autocomplete
**Cons**: Breaks when real function adds new parameters

**kwargs parameters (flexible)**:
```python
def mock_subscriber(topic, **kwargs):
    """Accepts any keyword arguments."""
    def decorator(func):
        return func
    return decorator
```

**Pros**: Never breaks on signature changes, works with any parameters
**Cons**: No parameter validation, no type checking

## Vulture compatibility

**kwargs avoids vulture "unused parameter" warnings**:

```python
# BAD - Vulture complains about unused parameters
def mock_subscriber(topic, ack_policy=None, group_id=None):
    # vulture: unused variable 'ack_policy' (100% confidence)
    # vulture: unused variable 'group_id' (100% confidence)
    pass

# Option 1: Prefix with underscore (indicates intentionally unused)
def mock_subscriber(topic, _ack_policy=None, _group_id=None):
    pass

# Option 2: Use **kwargs (cleaner, more flexible)
def mock_subscriber(topic, **kwargs):
    pass
```

## Prevention

**Before creating test mock**:

1. **Identify mock purpose**: Capture function or validate parameters?
2. **If capturing only**: Use **kwargs pattern
3. **If validating**: Use explicit parameters with underscores
4. **Document decision**: Add comment explaining why

```python
def capture_subscriber(topic, **kwargs):
    """Flexible mock for subscriber decorator.
    
    Uses **kwargs because:
    1. Test validates handler behavior, not subscriber parameters
    2. Real subscriber API evolves (ack_policy, group_id, etc.)
    3. Mock only needs to capture decorated function
    
    Not validating parameters in this mock.
    """
    def decorator(func):
        nonlocal registered_func
        registered_func = func
        return func
    return decorator
```

## Related

- Mock parameter ordering: python-mock-decorator-parameter-ordering.md
- Bug fix example: 2026-04-13-mock-signature-vulture-kwargs-bug.md

# Python Idioms

## Data Structure Selection

Choose the right data structure for the job — don't default to `list` for everything:

- **`set`**: membership tests (`if x in items`), deduplication, set operations (union, intersection)
- **`tuple`**: fixed-size immutable sequences, function return values, dict keys, named records (`NamedTuple`)
- **`dict`**: key-value lookups, replacing long if/elif chains with mapping tables
- **`frozenset`**: immutable sets for use as dict keys or in other sets
- **`list`**: only when you need ordered, mutable, indexed access

```python
# Bad: list for membership test
allowed = ["admin", "editor", "viewer"]
if role in allowed: ...

# Good: set for membership test
ALLOWED_ROLES = {"admin", "editor", "viewer"}
if role in ALLOWED_ROLES: ...
```

## Generators and Lazy Evaluation

Use generators when you don't need the full collection in memory:

- **Generator expressions** over list comprehensions when the result is iterated once: `sum(x**2 for x in values)` not `sum([x**2 for x in values])`
- **`yield`** in functions that produce sequences consumed incrementally
- **`itertools`** for composing lazy pipelines: `islice`, `chain`, `groupby`, `batched`
- Keep `list()` only when you need random access, `len()`, or multiple iterations

## Pattern Matching

Use `match/case` instead of long `if/elif` chains when dispatching on type or value:

```python
# Bad: if/elif chain
if status == 200:
    handle_ok(response)
elif status == 404:
    handle_not_found(response)
elif status == 500:
    handle_error(response)
else:
    handle_unknown(response)

# Good: match/case
match status:
    case 200:
        handle_ok(response)
    case 404:
        handle_not_found(response)
    case 500:
        handle_error(response)
    case _:
        handle_unknown(response)
```

Especially effective for structural pattern matching on types, dataclasses, and nested structures.

## Explicit Keyword Arguments

Always use keyword arguments when calling functions, methods, and constructors — unless the parameter is strictly positional or the variable name already matches the parameter name:

```python
# Bad: positional arguments obscure meaning
response = make_request("https://api.example.com", "POST", True, 30)

# Good: explicit keyword arguments
response = make_request(
    url="https://api.example.com",
    method="POST",
    verify_ssl=True,
    timeout=30,
)

# OK: variable name matches parameter name
timeout = 30
response = make_request(url, method, verify_ssl=True, timeout=timeout)

# OK: strictly positional (single obvious argument)
len(items)
print(message)
Path(filepath)
int(value)
```

This applies to all code including standard library calls:

```python
# Bad
json.dumps(data, False, True, None, None, 2)

# Good
json.dumps(data, indent=2, sort_keys=True)

# Bad
subprocess.run(["ls", "-la"], True, None, None, None, None, None, True)

# Good
subprocess.run(["ls", "-la"], capture_output=True, check=True)
```

## Other Idioms

- **Unpacking** over indexing: `name, age = get_user()` not `result = get_user(); name = result[0]`
- **`any()`/`all()`** over manual loops for boolean checks
- **`dict.get(key, default)`** over `if key in dict: ... else: ...` for simple lookups
- **Context managers** (`with`) for all resource management — files, locks, connections, transactions
- **`enumerate()`** over manual counter: `for i, item in enumerate(items)` not `i = 0; for item in items: ... i += 1`
- **`zip()`** for parallel iteration, `zip(strict=True)` when lengths must match (Python 3.10+)

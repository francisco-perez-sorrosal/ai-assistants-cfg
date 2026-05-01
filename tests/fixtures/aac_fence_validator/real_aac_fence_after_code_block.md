# Mixed: Code Block Then Real Fence

A Python code example that happens to appear before a real AaC fence.

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

After the code block ends, a real aac:authored region follows.

<!-- aac:authored owner=carol -->
This is real authored content. The validator must detect it
because it appears OUTSIDE the Python code block above.
<!-- aac:end -->

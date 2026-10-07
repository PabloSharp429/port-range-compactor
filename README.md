# Port Range Compactor

Compress a list of individual TCP/UDP port numbers into the shortest possible
comma-and-dash range specification.

```python
from port_range_compactor import compact_ports, compact_ports_from_list

# From an iterable of individual ports:
compact_ports_from_list([22, 80, 81, 82, 443])
# -> '22,80-82,443'

# From an already-messy spec string (expands then re-compacts):
compact_ports("80,81,82,80")
# -> '80-82'
```

## Why

Generating firewall or proxy rules from a pile of discovered ports tends to
produce specs like `80,81,82,80,443,444` — long, redundant, and noisy. This
library collapses that into the minimal `80-82,443-444` form. The trade-off
is memory: it builds the full port set in memory rather than streaming. That
is fine here because the input is bounded by the 0-65535 port space.

## Edge cases

- Ports are validated against the IANA range 0-65535. Anything outside raises
  `ValueError`.
- Booleans are rejected explicitly. Because `bool` subclasses `int` in Python,
  `True` would otherwise silently become `1`.
- `compact_ports_from_list` accepts numeric strings (e.g. `"22"`) for
  convenience; non-numeric strings raise.
- `compact_ports` parses dash ranges. A backwards range like `"82-80"` raises
  rather than being silently reversed — one clear interpretation.
- Empty input (empty list or empty string) returns an empty string.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.


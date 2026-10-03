"""Core implementation of port-range compaction.

The compactor turns a sequence of individual TCP/UDP port numbers into the
shortest possible comma-and-dash specification (e.g. 22,80-82,443). Input may
arrive as a list of integers, or as a string in a relaxed human form.

Design decision: the input is ALWAYS reduced to a de-duplicated sorted set of
integers first. By making normalisation an explicit phase we get one place
that owns validation, ordering, and de-duplication; the range-splitting phase
then operates on a clean invariant. This is simpler and easier to test than
streaming parsers that try to do all three at once.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple, Union


# Valid TCP/UDP port range per IANA. We chose to enforce it so nonsense like
# 70000 or negative numbers fails loudly rather than producing a spec that no
# firewall can actually consume.
_MIN_PORT = 0
_MAX_PORT = 65535


def _normalize_ports(ports: Iterable[Union[int, str]]) -> List[int]:
    """Validate and normalize arbitrary port-like input.

    Accepts integers or numeric strings. Returns a sorted list of unique port
    ints in the valid range.
    """
    seen: List[int] = []
    seen_set = set()
    for raw in ports:
        if isinstance(raw, bool):
            # bool is a subclass of int; reject explicitly so True/False do
            # not silently become 1/0.
            raise TypeError(f"port values must be int or str, got bool: {raw!r}")
        if isinstance(raw, str):
            s = raw.strip()
            if not s:
                raise ValueError("empty port value")
            try:
                value = int(s)
            except ValueError:
                raise ValueError(f"invalid port value: {raw!r}")
        elif isinstance(raw, int):
            value = raw
        else:
            raise TypeError(f"port values must be int or str, got {type(raw).__name__}")
        if value < _MIN_PORT or value > _MAX_PORT:
            raise ValueError(f"port {value} out of range {_MIN_PORT}-{_MAX_PORT}")
        if value not in seen_set:
            seen_set.add(value)
            seen.append(value)
    seen.sort()
    return seen


def _group_into_runs(ports: List[int]) -> List[Tuple[int, int]]:
    """Split a sorted unique port list into inclusive (start, end) runs.

    Two ports are joined into a run when they are consecutive integers; gaps
    start a new run.
    """
    runs: List[Tuple[int, int]] = []
    if not ports:
        return runs
    start = prev = ports[0]
    for p in ports[1:]:
        if p == prev + 1:
            prev = p
            continue
        runs.append((start, prev))
        start = prev = p
    runs.append((start, prev))
    return runs


def _render_runs(runs: List[Tuple[int, int]]) -> str:
    """Render runs into comma-and-dash notation.

    A single-port run is rendered as a bare number; multi-port runs as
    'start-end'. This keeps the output as short as possible, which is the
    whole point of the library.
    """
    parts: List[str] = []
    for start, end in runs:
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")
    return ",".join(parts)


def compact_ports_from_list(ports: Iterable[Union[int, str]]) -> str:
    """Compact an iterable of individual ports into a range spec.

    >>> compact_ports_from_list([22, 80, 81, 82, 443])
    '22,80-82,443'

    Works on any iterable of ints or numeric strings. Throws TypeError on
    non-numeric types and ValueError on out-of-range or malformed values.
    """
    normalized = _normalize_ports(ports)
    runs = _group_into_runs(normalized)
    return _render_runs(runs)


def compact_ports(port_spec: str) -> str:
    """Compact a (possibly already messy) port specification.

    Parses a comma-separated list where each item is either a single port or
    a dash range, expands everything to individual ports, then re-compacts.

    >>> compact_ports("80,81,82,80")
    '80-82'
    >>> compact_ports("22,80-82,443")
    '22,80-82,443'

    Whitespace around items is ignored. Out-of-range or non-numeric tokens
    raise ValueError.
    """
    if not isinstance(port_spec, str):
        raise TypeError("port_spec must be a str")
    spec = port_spec.strip()
    if spec == "":
        return ""
    expanded: List[int] = []
    for item in spec.split(","):
        token = item.strip()
        if token == "":
            raise ValueError(f"empty token in spec near {item!r}")
        if "-" in token:
            start_s, _, end_s = token.partition("-")
            if start_s == "" or end_s == "":
                raise ValueError(f"malformed range token: {token!r}")
            try:
                start = int(start_s)
                end = int(end_s)
            except ValueError:
                raise ValueError(f"malformed range token: {token!r}")
            if start < _MIN_PORT or end < _MIN_PORT or start > _MAX_PORT or end > _MAX_PORT:
                raise ValueError(f"port out of range in token: {token!r}")
            if start > end:
                raise ValueError(f"range start greater than end: {token!r}")
            expanded.extend(range(start, end + 1))
        else:
            try:
                value = int(token)
            except ValueError:
                raise ValueError(f"invalid port value: {token!r}")
            if value < _MIN_PORT or value > _MAX_PORT:
                raise ValueError(f"port {value} out of range {_MIN_PORT}-{_MAX_PORT}")
            expanded.append(value)
    return compact_ports_from_list(expanded)

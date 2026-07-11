#!/usr/bin/env python3
"""Shared utilities for i18n tools — unified source.txt parser and helpers."""

import os
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Entry:
    """A single source.txt entry (one %%%% block).

    Represents a key-value pair from a source.txt-format file. The key is
    the English lookup text; the value is the Chinese translation. Both
    may contain literal control characters (\\n, \\t, \\r).

    Attributes:
        key: The English lookup key (original case, no lowercase).
        value: The Chinese translation. Multi-line values are joined with \\n.
            Empty translations are represented as '' (not None).
        key_line: 1-indexed line number of the EN key in the source file.
        value_line: 1-indexed line number of the first ZH value line.
        source_file: Path to the source file.
    """
    key: str
    value: str
    key_line: int
    value_line: int
    source_file: Path = field(default=Path('.'))

    @property
    def is_empty(self) -> bool:
        """True if the translation value is empty or whitespace-only."""
        return not self.value.strip()


def _unescape_hash(s: str) -> str:
    """Convert source.txt \\# escape back to literal #.

    In source.txt, EN keys that start with '#' are written as '\\#' so
    they are not mistaken for comment lines. This converts them back.
    """
    if s.startswith('\\#'):
        return '#' + s[2:]
    return s


def parse_entries(filepath, lowercase_keys=True, unescape_hash=True,
                  require_zh=True) -> list:
    """Parse a %%%%-separated text database file into Entry objects.

    Handles:
        - %%%% block separators (leading/trailing whitespace stripped)
        - Multi-line values (physical newlines joined as \\n)
        - # comment lines (skipped when encountered before a key)
        - \\# escape for key lines starting with literal #
        - Empty blocks (skipped)
        - Blocks with only a key but no value (value is '')

    Args:
        filepath: Path to the source file.
        lowercase_keys: If True, lowercase the key (matching C++ GDBM behavior).
        unescape_hash: If True, convert \\# back to # on key lines.
        require_zh: If True, blocks with no ZH value are still included.

    Returns:
        List of Entry objects in file order.
    """
    entries = []
    if not os.path.exists(filepath):
        return entries

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    key = None
    key_line = 0
    value_line = 0
    value_lines = []
    in_entry = False
    source_path = Path(filepath)

    for line_num, line in enumerate(lines, start=1):
        stripped = line.rstrip('\n').rstrip('\r')

        # Comments are always metadata, never part of entry data
        if stripped.startswith('#'):
            continue

        # %%%% separator — flush current entry
        if stripped.strip() == '%%%%':
            if key is not None:
                value = '\n'.join(value_lines).rstrip('\n')
                entries.append(Entry(
                    key=key,
                    value=value,
                    key_line=key_line,
                    value_line=value_line or key_line + 1,
                    source_file=source_path,
                ))
            key = None
            value_lines = []
            in_entry = True
            continue

        if not in_entry:
            continue

        # First non-empty, non-comment line after %%%% is the key
        if key is None:
            if stripped:
                # Handle \# escape
                if unescape_hash:
                    stripped = _unescape_hash(stripped)
                if lowercase_keys:
                    key = stripped.lower()
                else:
                    key = stripped
                key_line = line_num
        else:
            # Subsequent lines are part of the value
            value_lines.append(stripped)
            if value_line == 0:
                value_line = line_num

    # Flush the last entry
    if key is not None:
        value = '\n'.join(value_lines).rstrip('\n')
        entries.append(Entry(
            key=key,
            value=value,
            key_line=key_line,
            value_line=value_line or key_line + 1,
            source_file=source_path,
        ))

    return entries


# ═══════════════════════════════════════════════════════════════════════
# Backward-compatible interface
# ═══════════════════════════════════════════════════════════════════════


def parse_source_txt(filepath: str) -> OrderedDict:
    """Parse source.txt and return OrderedDict of key -> translation.

    Backward-compatible wrapper around parse_entries(). Keys are lowercased
    to match C++ runtime behavior (case-insensitive lookups via GDBM).

    Use parse_entries() for new code that needs line numbers or per-entry
    metadata.

    Returns:
        OrderedDict with keys in file insertion order.
    """
    entries = parse_entries(filepath, lowercase_keys=True, unescape_hash=True)
    result = OrderedDict()
    for entry in entries:
        result[entry.key] = entry.value
    return result

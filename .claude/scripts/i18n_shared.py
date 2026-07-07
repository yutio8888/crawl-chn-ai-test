#!/usr/bin/env python3
"""Shared utilities for i18n tools — source.txt parser and helpers."""

import os
import re
from collections import OrderedDict


def parse_source_txt(filepath: str) -> OrderedDict:
    """Parse source.txt and return OrderedDict of key -> translation.

    The source.txt format uses %%%% as block separators:
        KEY
        VALUE (multiline with \\n)
        %%%%

    Keys are lowercased to match C++ runtime behavior (case-insensitive
    lookups via GDBM/database.cc).

    Returns:
        OrderedDict with keys in file insertion order.
    """
    entries = OrderedDict()
    if not os.path.exists(filepath):
        return entries

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    key = None
    value_lines = []
    in_entry = False

    for line in lines:
        stripped = line.rstrip("\n").rstrip("\r")
        if stripped.startswith("#") and key is None:
            continue
        if stripped.startswith("%%%%"):
            if key is not None:
                entries[key] = "\n".join(value_lines).rstrip()
            key = None
            value_lines = []
            in_entry = True
            continue
        if not in_entry:
            continue
        if key is None:
            if stripped:
                key = stripped.lower()
        else:
            value_lines.append(stripped)

    if key is not None:
        entries[key] = "\n".join(value_lines).rstrip()

    return entries

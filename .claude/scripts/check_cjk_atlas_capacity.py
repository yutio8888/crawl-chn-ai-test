#!/usr/bin/env python3
"""Check zh codepoint count and regress the runtime font-atlas model."""

import glob
import os
import sys

CJK_START = 0x4E00
CJK_END = 0x9FFF
CJK_EXT_A_START = 0x3400
CJK_EXT_A_END = 0x4DBF
CJK_COMPAT_START = 0xF900
CJK_COMPAT_END = 0xFAFF

CJK_RANGES = [(CJK_START, CJK_END), (CJK_EXT_A_START, CJK_EXT_A_END),
              (CJK_COMPAT_START, CJK_COMPAT_END)]

# Non-CJK but common in Chinese text: fullwidth, CJK symbols, etc.
EXTRA_RANGES = [(0x3000, 0x303F), (0xFF00, 0xFFEF), (0x2000, 0x206F),
                (0x2100, 0x214F), (0x2200, 0x22FF), (0x2500, 0x257F)]

THRESHOLD_WARN = 3900
MAX_GRID_SIDE = 64
ATLAS_BYTE_BUDGET = 16 * 1024 * 1024
RESERVED_GLYPHS = 2 + (0x7F - 0x20)
ZH_DIR = os.path.join(os.path.dirname(__file__),
                      '../../crawl-ref/source/dat/**/zh/*.txt')


def choose_atlas_grid(cell_width, cell_height, max_texture_size):
    """Mirror FTFontWrapper's power-of-two rectangular grid selection."""
    best = (0, 0)
    best_score = (0, 0, 0)
    columns = 1
    while columns <= MAX_GRID_SIDE:
        width = columns * cell_width
        rows = 1
        while rows <= MAX_GRID_SIDE:
            height = rows * cell_height
            byte_count = width * height * 4
            if (width <= max_texture_size
                    and height <= max_texture_size
                    and byte_count <= ATLAS_BYTE_BUDGET):
                capacity = columns * rows
                score = (capacity, -max(width, height), -abs(width - height))
                if score > best_score:
                    best = (columns, rows)
                    best_score = score
            rows *= 2
        columns *= 2
    return (*best, best[0] * best[1])


def check_atlas_model():
    cases = [
        ('cell32', (32, 32, 16384), (64, 64, 4096)),
        ('cell64', (64, 64, 16384), (32, 32, 1024)),
        ('cell128', (128, 128, 16384), (16, 16, 256)),
        ('rectangular', (64, 32, 16384), (32, 64, 2048)),
        ('low-max-texture', (32, 32, 1024), (32, 32, 1024)),
        ('insufficient', (128, 128, 1024), (8, 8, 64)),
    ]
    for name, args, expected in cases:
        actual = choose_atlas_grid(*args)
        if actual != expected:
            print(f'ERROR: atlas model {name}: expected {expected}, got {actual}')
            return False
    if choose_atlas_grid(128, 128, 1024)[2] >= RESERVED_GLYPHS:
        print('ERROR: insufficient-capacity model must fail reserved slots')
        return False
    print('check_cjk_atlas_capacity: atlas model regressions OK')
    return True


if not check_atlas_model():
    sys.exit(1)

unique = set()
for fpath in glob.glob(ZH_DIR, recursive=True):
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        for ch in f.read():
            cp = ord(ch)
            for lo, hi in CJK_RANGES:
                if lo <= cp <= hi:
                    unique.add(cp)
                    break

total = len(unique)
print(f"check_cjk_atlas_capacity: {total} unique CJK codepoints in zh text")

if total >= 4096:
    print(f"ERROR: {total} CJK codepoints >= 4096 atlas slots!"
          f" Font atlas capacity EXCEEDED.")
    sys.exit(1)
elif total >= THRESHOLD_WARN:
    print(f"WARNING: {total} CJK codepoints >= {THRESHOLD_WARN} threshold."
          f" Evaluate atlas capacity.")
else:
    print(f"OK: {total} < {THRESHOLD_WARN} threshold.")

sys.exit(0)

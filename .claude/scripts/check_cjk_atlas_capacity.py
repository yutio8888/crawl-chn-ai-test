#!/usr/bin/env python3
"""Build-time check: count unique CJK codepoints across zh translation files.
Warns if total exceeds the 3900 threshold for the 4096-slot font atlas."""

import os, sys, glob

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
ZH_DIR = os.path.join(os.path.dirname(__file__),
                      '../../crawl-ref/source/dat/**/zh/*.txt')

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

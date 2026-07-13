#!/usr/bin/env python3
"""Static regression gate for the cached FontBuffer/atlas contract (Issue 54)."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


checks = [
    ("font generation API",
     "virtual uint64_t atlas_generation() const" in read("crawl-ref/source/tilefont.h")),
    ("configure invalidates cached UVs",
     re.search(r"configure_font\(\).*?\+\+m_atlas_generation;",
               read("crawl-ref/source/fontwrapper-ft.cc"), re.S) is not None),
    ("slot reuse invalidates cached UVs",
     re.search(r"m_atlas\[evict\]\.uchar != 0.*?\+\+m_atlas_generation;",
               read("crawl-ref/source/fontwrapper-ft.cc"), re.S) is not None),
    ("all-pinned path uses missing glyph",
     re.search(r"if \(evict == m_atlas_capacity\)\s*\{\s*.*?return "
               r"m_glyph_to_slot\.at\(MISSING_CHAR\);\s*\}",
               read("crawl-ref/source/fontwrapper-ft.cc"), re.S) is not None),
    ("textblock starts a fresh pin batch",
     re.search(r"render_textblock\(.*?\{.*?clear_pins\(\);",
               read("crawl-ref/source/fontwrapper-ft.cc"), re.S) is not None),
    ("stale FontBuffer rebuilds before draw",
     re.search(r"FontBuffer::draw\(\) const\s*\{\s*.*?if \(!atlas_valid\(\)\)\s*"
               r"const_cast<FontBuffer \*>\(this\)->rebuild\(\);\s*"
               r"VertBuffer::draw\(\);",
               read("crawl-ref/source/tilebuf.cc"), re.S) is not None),
    ("FontBuffer retains replay operations",
     "m_replay.emplace_back" in read("crawl-ref/source/tilebuf.cc") and
     re.search(r"FontBuffer::rebuild\(\).*?for \(const auto &replay : m_replay\)\s*"
               r"replay\(\*this\);",
               read("crawl-ref/source/tilebuf.cc"), re.S) is not None),
    ("generation changes during add trigger full replay",
     re.search(r"FontBuffer::finish_add\(uint64_t generation_before\).*?"
               r"generation_before != m_font->atlas_generation\(\).*?rebuild\(\);",
               read("crawl-ref/source/tilebuf.cc"), re.S) is not None and
     read("crawl-ref/source/tilebuf.cc").count("finish_add(generation_before);") == 4),
    ("direct glyph stores use replayable add",
     "get_font_wrapper().store(m_buf_glyphs" not in
     read("crawl-ref/source/tiledgnbuf.cc") and
     "get_font_wrapper().store(m_font_buf" not in
     read("crawl-ref/source/cio.cc")),
    ("UIMenu rebuilds stale text buffer",
     re.search(r"UIMenu::_render\(\).*?if \(!m_text_buf\.atlas_valid\(\)\)\s*"
               r"mark_buffers_dirty\(\);",
               read("crawl-ref/source/menu.cc"), re.S) is not None),
]

failures = [name for name, passed in checks if not passed]
for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name}")

if failures:
    print(f"check_font_atlas_generation: {len(failures)} failure(s)")
    sys.exit(1)

print("check_font_atlas_generation: all checks passed")

# CJK Tiles Text Architecture

## Grid Width

`tilereg-text.cc:addstr_aux()` uses the project's locale-independent
`wcwidth(char32_t)` overload to count terminal-style grid cells. A wide CJK
character occupies two cells; the continuation cell uses a `0x200B` marker so
cursor movement, selection, and layout remain aligned with the grid. All
platforms use this implementation so Finder-launched macOS apps do not depend
on `LANG` or `LC_CTYPE` for CJK layout.

## Rendering

`fontwrapper-ft.cc:render_textblock()` skips continuation markers and sizes the
background/advance from the character's display width. Glyph advances are
quantized against the grid metrics so CJK text does not drift from logical
cells.

## Fonts

The compiled Chinese defaults use the versioned Maple Mono NF CN file as the
primary font for every tile text role. Because the primary font already
contains CJK glyphs, normal Chinese deployment does not depend on a DejaVu-
primary/Sarasa-secondary pairing.

The renderer still supports a secondary CJK face for configurations whose
primary font lacks a glyph. Candidate fallback fonts are resolved by the
current `fontwrapper-ft.cc` implementation; documentation should not describe a
particular fallback as mandatory unless deployment scripts enforce it.

Runtime fonts are deployed to `dat/tiles/`. This localization repository does
not change the upstream `contrib/fonts` submodule; the default CJK font is
versioned directly in `dat/tiles/`. See `docs/build-workflow.md` for optional
`init.txt` overrides and the deployment process.

## Change Verification

CJK width, font, atlas, or rendering changes require focused tests plus the
risk-routed code verification profile. Use the dedicated Windows tiles
worktree for the actual tiles build. Do not infer rendering correctness from a
console-only compile.

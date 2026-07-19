# CJK Tiles Text Architecture

## Grid Width

`tilereg-text.cc:addstr_aux()` uses `wcwidth()` to count terminal-style grid
cells. A wide CJK character occupies two cells; the continuation cell uses a
`0x200B` marker so cursor movement, selection, and layout remain aligned with
the grid.

## Rendering

`fontwrapper-ft.cc:render_textblock()` skips continuation markers and sizes the
background/advance from the character's display width. Glyph advances are
quantized against the grid metrics so CJK text does not drift from logical
cells.

## Fonts

The supported Chinese deployment config uses Maple Mono NF CN as the primary
font for every tile text role. Because the primary font already contains CJK
glyphs, normal Chinese deployment does not depend on a DejaVu-primary/Sarasa-
secondary pairing.

The renderer still supports a secondary CJK face for configurations whose
primary font lacks a glyph. Candidate fallback fonts are resolved by the
current `fontwrapper-ft.cc` implementation; documentation should not describe a
particular fallback as mandatory unless deployment scripts enforce it.

Runtime fonts are deployed to `dat/tiles/`. This localization repository does
not change the upstream `contrib/fonts` submodule; CJK source fonts belong in
the ignored local `dat/tiles/` directory. See `docs/build-workflow.md` for the
supported `init.txt`, font placement, and deployment process.

## Change Verification

CJK width, font, atlas, or rendering changes require focused tests plus the
risk-routed code verification profile. Use the dedicated Windows tiles
worktree for the actual tiles build. Do not infer rendering correctness from a
console-only compile.

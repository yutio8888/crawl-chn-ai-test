# CJK Tiles Text Architecture

## Grid Width

`tilereg-text.cc:addstr_aux()` uses `wcwidth()` to count terminal-style grid
cells. A wide CJK character occupies two cells; the continuation cell uses a
`0x200B` marker so cursor movement, selection, and layout remain aligned with
the grid. Unix builds retain the platform's current Unicode width tables. At
startup, non-Android local tiles launched with the `C` or `POSIX` character
locale fall back to an installed UTF-8 `LC_CTYPE`, which keeps Finder-launched
macOS apps aligned without replacing the platform's width data. Explicit
non-UTF-8 locales, Android, and non-tiles Unix builds are left unchanged.
Non-Unix builds use the bundled width table.

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

## Windows Text Encoding

MinGW builds decode files without a byte-order mark through the system ANSI
code page (for example CP936), which corrupts UTF-8 CJK text. Any file the
game writes and later reads back through `FileLineInput` with non-ASCII
content must therefore start with a UTF-8 BOM; `FileLineInput` then takes the
`BOM_UTF8` path (`utf8_validate()`) instead of `mb_to_utf8()`. The prefs file
written by `initfile.cc` follows this rule; the clua persist file written by
`clua.cc` does not yet, so non-ASCII persisted Lua data is not protected on
MinGW.

`lowercase_string()` preserves U+2E80–U+9FFF byte-for-byte instead of calling
`towlower()`, because `iswupper()`/`towlower()` misbehave for these ranges on
MinGW/msvcrt. Chinese names looked up through lowercase comparisons rely on
this guard.

## Change Verification

CJK width, font, atlas, or rendering changes require focused tests plus the
risk-routed code verification profile. Use the dedicated Windows tiles
worktree for the actual tiles build. Do not infer rendering correctness from a
console-only compile.

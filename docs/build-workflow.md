# Build Workflow — Dual Worktree + ccache

## Overview

Two worktrees keep console and tiles `.o` files isolated, avoiding full
rebuilds when switching build targets. ccache caches compiled objects so even
within a worktree, switching branches with similar flags is faster.

| Worktree | Build target | Purpose |
|----------|-------------|---------|
| **Main** (`/home/yutio888/projects/crawl`) | WSL Console | `make -j8` |
| `.worktrees/mingw-tiles` | Windows Tiles | `CROSSHOST=x86_64-w64-mingw32 TILES=y` |

## Prerequisites

- ccache: `sudo apt install ccache` (already at `/usr/bin/ccache`)

## Quick Start

### WSL Console (main worktree)

```bash
cd crawl-ref/source
bash util/build-console.sh          # with ccache
# or manually:
make -j8
```

### Windows Tiles (mingw-tiles worktree)

```bash
cd crawl-ref/source
bash util/build-tiles.sh            # auto-syncs + builds with ccache
```

## Worktree Sync

Worktrees are **detached** — they stay at the commit they were created on.
Sync them to the latest code before building:

```bash
# Sync mingw-tiles worktree to main worktree HEAD (local only)
cd /home/yutio888/projects/crawl
TARGET=$(git rev-parse HEAD)
cd .worktrees/mingw-tiles
git reset --hard $TARGET
```

**Caveat**: `git reset --hard` discards uncommitted changes in the worktree.
Commit or stash first if you have local modifications there.

## Deploy to Windows

```bash
bash .claude/scripts/deploy.sh                  # default: /mnt/d/crawl-release
bash .claude/scripts/deploy.sh /custom/path     # custom target
```

The deploy script auto-syncs `.worktrees/mingw-tiles` before building.

## ccache

When `ccache` is installed, the project Makefile automatically wraps its `GCC`
and `GXX` commands. No environment or `PATH` override is required. Cache stats:

```bash
ccache -s
```

Default cache size: 5 GB (`ccache -M 5G`). To increase:

```bash
ccache -M 10G
```

## Architecture

```
repo/
├── crawl-ref/source/           ← Main worktree (WSL Console)
│   ├── *.o, *.d, .cflags       ← Console-specific build artifacts
│   ├── util/build-console.sh
│   └── util/build-tiles.sh     ← Syncs & builds in mingw-tiles worktree
│
└── .worktrees/mingw-tiles/     ← Detached worktree (Windows Tiles)
    └── crawl-ref/source/
        ├── *.o, *.d, .cflags   ← Tiles-specific build artifacts
        └── crawl.exe           ← Cross-compiled binary
```

Contrib libraries go to `contrib/install/$(ARCH)/` — different compilers
(linux-gnu vs w64-mingw32) use different `ARCH` paths, so they never conflict.

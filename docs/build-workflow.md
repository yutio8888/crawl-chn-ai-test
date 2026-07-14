# Build Workflow — Target Worktrees + Persistent ccache

## Overview

Dedicated worktrees keep target-specific `.o` files isolated. ccache stores
compiled objects persistently under the main repository and separates them by
toolchain, so switching branches with similar flags remains fast without
mixing console, MinGW, and Android results.

| Worktree | Build target | Purpose |
|----------|-------------|---------|
| **Main** (`/home/yutio888/projects/crawl`) | WSL Console | `make -j8` |
| `.worktrees/mingw-tiles` | Windows Tiles | `CROSSHOST=x86_64-w64-mingw32 TILES=y` |
| `.worktrees/android-tiles` | Android APK | NDK/Gradle build |

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
and `GXX` commands. Caches live under the ignored `.ccache/` directory:

| Profile | Cache directory |
|---------|-----------------|
| WSL console | `.ccache/console` |
| Windows tiles | `.ccache/mingw-tiles` |
| Android | `.ccache/android-tiles` |

The main worktree plus `.worktrees/mingw-tiles` and
`.worktrees/android-tiles` use read-write mode. All other worktrees use the
matching profile cache with `CCACHE_READONLY=1` and `CCACHE_NOSTATS=1`; they
can get hits but cannot store results, update statistics, or trigger cleanup.
Their temporary files go under `/tmp/crawl-ccache-<uid>/<profile>`, never into
the persistent cache. The Android helper exports `NDK_CCACHE=ccache`, so native
NDK compilation uses `.ccache/android-tiles` as well.

Inspect the policy selected for the current worktree and target:

```bash
make ccache-config
make CROSSHOST=x86_64-w64-mingw32 ccache-config
make ANDROID=1 ccache-config
```

Cache stats for a particular profile:

```bash
# Run this command from the main worktree.
CCACHE_DIR="$(git rev-parse --show-toplevel)/.ccache/console" ccache -s
```

Default cache size: 5 GB (`ccache -M 5G`). To increase:

```bash
# Run this command from the main worktree.
CCACHE_DIR="$(git rev-parse --show-toplevel)/.ccache/console" ccache -M 10G
```

## Architecture

```
repo/
├── crawl-ref/source/           ← Main worktree (WSL Console)
│   ├── *.o, *.d, .cflags       ← Console-specific build artifacts
│   ├── util/build-console.sh
│   └── util/build-tiles.sh     ← Syncs & builds in mingw-tiles worktree
│
├── .ccache/                    ← Persistent and gitignored
│   ├── console/
│   ├── mingw-tiles/
│   └── android-tiles/
└── .worktrees/
    ├── mingw-tiles/            ← Detached Windows Tiles build worktree
    └── android-tiles/          ← Detached Android build worktree
```

Contrib libraries go to `contrib/install/$(ARCH)/` — different compilers
(linux-gnu vs w64-mingw32) use different `ARCH` paths, so they never conflict.

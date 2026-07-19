# Build and Deployment Workflow

Dedicated detached worktrees isolate target-specific object files. Persistent
ccache profiles improve rebuilds without allowing arbitrary development
worktrees to mutate shared caches.

## Targets

| Worktree | Target | Helper |
|---|---|---|
| Main repository | WSL console | `crawl-ref/source/util/build-console.sh` |
| `.worktrees/mingw-tiles` | Windows tiles | `crawl-ref/source/util/build-tiles.sh` |
| `.worktrees/android-tiles` | Android APK | `crawl-ref/source/util/build-android.sh` |

Use at most eight parallel build jobs. Agents compiling while other work is in
progress should use four jobs and avoid concurrent compile storms.

## Console

From the main worktree:

```bash
cd crawl-ref/source
bash util/build-console.sh
```

The helper configures the console ccache profile and builds the `crawl` binary.

## Windows Tiles

Create the dedicated detached worktree once from the main repository root:

```bash
git worktree add .worktrees/mingw-tiles --detach HEAD
git -C .worktrees/mingw-tiles submodule update --init --recursive
```

The submodule initialization is required before the first build. A newly
created worktree contains empty contrib submodule directories; without this
step, the MinGW build stops when a required contrib Makefile is missing. The
initialized submodules and their target-specific build products remain in the
persistent build worktree for later incremental deployments.

Then build from the main worktree:

```bash
cd crawl-ref/source
bash util/build-tiles.sh
```

The helper refuses a dirty `.worktrees/mingw-tiles`, synchronizes the detached
worktree to the main checkout's exact HEAD, and runs the MinGW tiles build.

Manual synchronization is discouraged. If diagnosis requires it, reproduce the
same guard exactly:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
MAIN_HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
cd "$REPO_ROOT/.worktrees/mingw-tiles"
test -z "$(git status --porcelain --untracked-files=all)" || {
  echo "refusing destructive sync: build worktree is dirty" >&2
  exit 1
}
git reset --hard "$MAIN_HEAD"
cd crawl-ref/source
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8
```

This exception applies only to the dedicated detached build worktree. Never use
the reset pattern in the main checkout or a development worktree.

## Android

The Android helper requires the Android SDK and NDK described by
`crawl-ref/docs/develop/android.txt`.

```bash
cd crawl-ref/source
bash util/build-android.sh            # buildTest, arm64-v8a
bash util/build-android.sh --release  # release/all configured ABIs
```

Release builds require the signing environment validated by the helper. The
helper refuses success if the resulting APK remains unsigned. Do not document
or deploy an `*-unsigned.apk` as a successful artifact.

## Windows Deployment

### Deployment path configuration

The deployment root can be configured once for a different mount or artifact
location:

```bash
cp .dcss-paths.conf.example .dcss-paths.conf
# Edit DCSS_DEPLOY_ROOT in the ignored local copy.
```

The local file is a non-executable `key=value` format. It accepts only
`DCSS_DEPLOY_ROOT`, `DCSS_WINDOWS_DEPLOY_DIR`, and
`DCSS_ANDROID_DEPLOY_DIR`; relative values are anchored at the repository root.
Set `DCSS_PATH_CONFIG` to use a different config file. An explicitly selected
but missing file is an error.

Resolution precedence is command-line target, matching per-target environment
variable, `DCSS_DEPLOY_ROOT`, then `.artifacts`. Existing environment variables
override the local config file. The shared root produces `windows-tiles/` and
`android/` subdirectories unless a per-target destination is configured.

Use the guarded deployment helper from the repository root:

```bash
bash .claude/scripts/deploy.sh
DCSS_WINDOWS_DEPLOY_DIR=../crawl-game bash .claude/scripts/deploy.sh
```

It first requires a valid Chinese configuration and the configured Maple font,
then synchronizes and builds the MinGW worktree, copies `crawl.exe`, `dat/`, the
exact font, and `init.txt`, verifies the deployed copies, and clears the target
`saves/db/` cache so TextDB changes are reloaded. It fails before building when
either required asset is absent or invalid. Close the running game before
deployment.

Without a path configuration, deployment goes to the ignored
repository-relative `.artifacts/windows-tiles/` directory. Relative values are
resolved from the repository root before the script enters a build worktree;
absolute values remain accepted when an external destination is required.

When a local `crawl-ref/source/init.txt` exists, the helper preserves its user
preferences but appends `init.zh.txt` to the deployed copy. The canonical
template first resets aliases for the six required option names, then assigns
the language and five fonts. Those values are therefore last and remain
effective even if the local file contains duplicates, `include` directives, or
`option := alias` rules.

## Android Deployment

```bash
bash .claude/scripts/deploy-android.sh
DCSS_ANDROID_DEPLOY_DIR=../crawl-apks \
  bash .claude/scripts/deploy-android.sh --release
```

The deployment helper invokes the Android build helper and refuses to copy an
unsigned APK. Its default destination is the ignored repository-relative
`.artifacts/android/` directory; relative overrides are resolved from the
repository root.

## Local `init.txt` and Fonts

`crawl-ref/source/init.txt` is intentionally gitignored. The version-controlled
`crawl-ref/source/init.zh.txt` is the supported Chinese configuration template:

```bash
cd crawl-ref/source
test -e init.txt || cp init.zh.txt init.txt
```

This localization repository does not modify or extend the upstream
`crawl-ref/source/contrib/fonts` submodule. Obtain
`MapleMono-NF-CN-Regular.ttf` separately and place it in the ignored local
`crawl-ref/source/dat/tiles/` directory. The deployment helper copies that
local font to the target's `dat/tiles/` directory.

The configured Maple font is CJK-capable and is the default primary font for
all tile text roles. Renderer fallback support remains available for other
configurations; see `docs/cjk-tiles-architecture.md`. Do not commit font files
or change the font submodule pointer. Font licensing references are listed in
the root `README.md`.

## ccache

Persistent caches live in the ignored root `.ccache/` directory:

| Profile | Directory |
|---|---|
| Console | `.ccache/console` |
| Windows tiles | `.ccache/mingw-tiles` |
| Android | `.ccache/android-tiles` |

Only the main worktree and the two dedicated build worktrees write their
matching cache. Other worktrees use it read-only with statistics disabled and
temporary files outside the persistent cache.

Inspect the selected policy with:

```bash
cd crawl-ref/source
make ccache-config
make CROSSHOST=x86_64-w64-mingw32 ccache-config
make ANDROID=1 ccache-config
```

Contrib libraries remain isolated by toolchain under
`contrib/install/$(ARCH)/`.

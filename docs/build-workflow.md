# Build and Deployment Workflow

Dedicated detached worktrees isolate target-specific object files. Persistent
ccache profiles improve rebuilds without allowing arbitrary development
worktrees to mutate shared caches.

## Targets

| Worktree | Target | Helper |
|---|---|---|
| Main repository | WSL console | `crawl-ref/source/util/build-console.sh` |
| Main repository (macOS) | macOS Tiles DMG | `make TILES=y mac-app-tiles-dmg -j4` |
| `.worktrees/mingw-tiles` | Windows tiles | `crawl-ref/source/util/build-tiles.sh` |
| `.worktrees/android-tiles` | Android APK | `crawl-ref/source/util/build-android.sh` |

Formal version tags, closed-world artifact validation, checksums, draft
Releases, and the manual publication gate are defined in
[release-workflow.md](release-workflow.md).

Use at most eight parallel build jobs. Agents compiling while other work is in
progress should use four jobs and avoid concurrent compile storms.

## Console

From the main worktree:

```bash
cd crawl-ref/source
bash util/build-console.sh
```

The helper configures the console ccache profile and builds the `crawl` binary.

## macOS Tiles DMG

From the main worktree on macOS:

```bash
cd crawl-ref/source
make TILES=y mac-app-tiles-dmg -j4
```

The build produces an ad-hoc-signed Apple application DMG under
`mac-app-zips/`. The signature seals the final assembled bundle so macOS can
launch it, but it is not an Apple Developer signature and does not provide
notarization.
GitHub Actions uploads the versioned DMG as the `macos-tiles-app` artifact and
includes it in tagged draft Releases after closed-world artifact validation.
Because this release profile has no Apple Developer signing or notarization,
macOS Gatekeeper may require the user to choose “Open” from the app's
Control-click menu or “Open Anyway” in System Settings → Privacy & Security.
The release notes must also provide the SHA-256 check and the quarantine-removal
command for users who need the explicit command-line override.

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

GitHub Actions builds the distributable archive with
`make CROSSHOST=x86_64-w64-mingw32 package-windows-tiles -j4` and uploads the
versioned ZIP as the `windows-tiles` artifact. The package contains the binary,
runtime data, settings directory, documentation, and versioned Maple font.

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

GitHub Actions keeps the four-ABI debug APK from ordinary branch, scheduled,
and manual runs as the `android-debug-apk` test artifact. It replaces Gradle's
ephemeral debug signature with a dedicated stable test certificate, verifies
the pinned public certificate digest, and only then uploads the APK. This lets
testers install later branch artifacts as updates without exposing or reusing
the production release key. Pull requests cannot access the test signing
secrets; their ephemeral artifact is named `android-pr-debug-apk` so it cannot
be mistaken for the update channel.

On a valid three-part release tag the workflow also builds `assembleRelease`,
zipaligns and signs the APK, verifies the signature and four-ABI PCRE contract,
and uploads the versioned file as `android-release-apk`:

```text
stone_soup-0.34.1-zhA-B-CCC-android.apk
```

Configure dedicated test-signing Actions secrets
`ANDROID_TEST_KEYSTORE_BASE64`, `ANDROID_TEST_KEYSTORE_PASS`, and
`ANDROID_TEST_KEY_ALIAS`. The test key password is also used as its private-key
password. Configure the separate production secrets `ANDROID_KEYSTORE_BASE64`,
`ANDROID_KEYSTORE_PASS`, and `ANDROID_KEY_ALIAS`; `ANDROID_KEY_PASS` is optional
and falls back to the production store password. The workflow passes passwords
to `apksigner` through environment-variable references, never as literal
command-line values. The Android `versionCode` comes from the positive,
monotonically increasing `GITHUB_RUN_NUMBER`; the player-visible `versionName`
remains the release tag. Missing required secrets, invalid Base64, an empty
decoded keystore, a wrong password or alias, or a test certificate that differs
from the pinned digest fails before its artifact is uploaded. An unsigned or
unverifiable APK is never uploaded as a test or release asset.

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

It first requires the versioned Maple font, then synchronizes and builds the
MinGW worktree, copies `crawl.exe`, `dat/`, the exact font, and any non-empty
local `init.txt` override, verifies the deployed copies, and clears the target
`saves/db/` cache so TextDB changes are reloaded. It fails before building when
the required font is absent or invalid. Close the running game before
deployment.

Without a path configuration, deployment goes to the ignored
repository-relative `.artifacts/windows-tiles/` directory. Relative values are
resolved from the repository root before the script enters a build worktree;
absolute values remain accepted when an external destination is required.

The Chinese language, Maple font roles, and local Tiles window geometry are C++
defaults. A non-empty local `crawl-ref/source/init.txt` is copied unchanged as
an optional user override; when it is empty or absent, deployment removes any
stale target `init.txt` so it cannot override the compiled defaults.

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

`crawl-ref/source/init.txt` remains intentionally gitignored and is needed only
for user overrides. This localization repository does not modify or extend the
upstream `crawl-ref/source/contrib/fonts` submodule. Instead, the OFL-licensed
`MapleMono-NF-CN-Regular.ttf` is versioned directly under
`crawl-ref/source/dat/tiles/`, so normal builds and CI packages contain it.

The configured Maple font is CJK-capable and is the default primary font for
all tile text roles. Renderer fallback support remains available for other
configurations; see `docs/cjk-tiles-architecture.md`. Do not change the font
submodule pointer. Font licensing references are listed in the root `README.md`.

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

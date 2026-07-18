# path-portability-v1

Repository documentation and configuration use repository-root-relative paths.
They must not assume a clone directory, user name, home-directory layout,
Windows drive letter, or WSL mount point.

## Repository paths

- Write tracked-file references relative to the repository root, such as
  `docs/glossary.md` or `.claude/scripts/verify_zh.sh`.
- A script may resolve its own location to an absolute path at runtime. This is
  the preferred way to remain independent of the caller's current directory.
- When a runtime path is inside the repository, logs and generated context use
  its repository-relative identifier whenever that identifier is sufficient.
- Relative command-line paths are interpreted from the repository root, not
  from whichever build directory the script later enters.
- Bash deployment helpers share `.claude/scripts/lib/path_utils.sh` for this
  resolution contract instead of maintaining independent path rules.

## External paths

- External repositories and deployment directories use a documented
  environment variable or command-line argument.
- Portable defaults are relative to the repository root. Build and deployment
  artifacts default under the ignored `.artifacts/` directory.
- A local `.dcss-paths.conf` may define the shared deployment root or
  per-target destinations. It is ignored by Git; the versioned
  `.dcss-paths.conf.example` documents the accepted non-executable keys.
- Home-scoped tool installations, temporary directories, device paths, and
  operating-system files are not repository references. They may use the
  relevant environment variable or system convention, but must not contain a
  project author's user name or clone layout.

## Enforcement

Run:

```bash
python3 .claude/scripts/check_path_portability.py
```

The checker scans maintained project documentation, agent configuration, and
project-specific scripts for clone-specific home paths, drive-letter paths,
WSL mount paths, and obsolete home-relative project layouts. Test fixtures,
historical metrics, third-party/upstream documentation, and server deployment
scripts with intentional system paths are outside this policy's scope. A
line-level `path-portability: allow-*` marker is reserved for a literal regular
expression or test example that would otherwise be a false positive; it is not
an exemption for a real filesystem reference.

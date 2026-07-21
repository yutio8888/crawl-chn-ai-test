# Security Policy for the DCSS Chinese Fork

Last reviewed: 2026-07-21.

## Supported Versions

This repository is a downstream Chinese-localization fork based on the upstream
DCSS `0.34.1` tag. Security fixes are maintained only on the current default
branch:

| Version | Supported |
|---|---|
| Current default branch based on `0.34.1` | Yes |
| Older fork branches, commits, and build artifacts | No guaranteed support |
| Upstream DCSS releases and online servers | Maintained by the upstream project |

The default branch contains localization and platform changes after the tag; it
is not a byte-for-byte copy of upstream `0.34.1`. A report against an older
revision should be reproduced on the current default branch when possible.

## Reporting a Vulnerability

For an ordinary bug without sensitive exploit details, open a
[GitHub Issue](https://github.com/yutio8888/crawl-chn-ai-test/issues) and include
the affected commit, platform, build type, reproduction steps, and impact.

Do **not** publish credentials, private server data, a working exploit, or other
details that would make active abuse easier. For a vulnerability inherited from
upstream DCSS, or one that affects upstream code or public online servers, use
the [upstream DCSS security policy](https://github.com/crawl/crawl/security/policy).
GitHub private vulnerability reporting is not currently enabled for this fork.
For a sensitive fork-specific problem, open only a minimal issue asking the
repository owner to establish a private channel; do not include exploit details
in that issue.

Security remediation and disclosure timing are tracked privately while details
remain sensitive. A public GitHub Issue may be created after a fix is available
and disclosure no longer increases risk.

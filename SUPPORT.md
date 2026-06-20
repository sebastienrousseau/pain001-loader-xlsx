<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting support

Thanks for using `pain001-loader-xlsx`. Here's the fastest way to
get help, by need.

## Read first

- **[README.md](README.md)** — install, quick start, the IBAN
  safety guard explained, the streaming variant.
- **[`examples/`](examples/)** — two runnable, self-checking
  scripts exercised in CI.
- **[pain001 plugin contract](https://github.com/sebastienrousseau/pain001/blob/main/docs/plugins.md)**
  — the structural Protocol this loader satisfies.

## Questions & how-to

Open a [GitHub Discussion](https://github.com/sebastienrousseau/pain001-loader-xlsx/discussions)
with:

- Python version + OS
- `pain001-loader-xlsx` version + `pain001` version
- A minimal reproducer (CLI invocation or short Python snippet)
- The full error output

Cross-package questions (e.g. how does the loader interact with
pain001's REST API?) are also welcome on the parent's
[Discussions](https://github.com/sebastienrousseau/pain001/discussions).

## Bugs

Open an [issue](https://github.com/sebastienrousseau/pain001-loader-xlsx/issues/new)
with:

- The same triage data as above
- A failing `.xlsx` (any sensitive values redacted; the IBAN guard
  often fires *because* of redaction patterns, so include real
  context where possible)
- Expected vs. actual behaviour

## Feature requests

Likely categories:

- **Multi-sheet support** — currently out of scope; consolidate
  before invocation.
- **`.xls` (legacy binary)** — out of scope; convert to `.xlsx`
  first.
- **Encrypted workbooks** — out of scope; pre-decrypt with
  `msoffcrypto-tool`.

Anything else? Open an issue. Plugin-contract changes in the parent
pain001 may unlock new options.

## Security

**Do not** open public issues for vulnerabilities. Follow the
private disclosure process in [SECURITY.md](SECURITY.md).

## Support tiers

This package is open source under Apache-2.0. There is no paid
support tier.

- **Community support** (issues / discussions / PRs): best effort.
- **Commercial support**: not available today. Contact
  `support@pain001.com` so the maintainer can gauge demand.

## The pain001 suite

This package is one of four:

- [`pain001`](https://github.com/sebastienrousseau/pain001) — core
  library, CLI, REST API
- [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp)
  — MCP server (AI agents)
- [`pain001-lsp`](https://github.com/sebastienrousseau/pain001-lsp)
  — Language Server (editors)
- [`pain001-loader-xlsx`](https://github.com/sebastienrousseau/pain001-loader-xlsx)
  — **Excel loader plugin (this package)**

Issues spanning multiple packages can be filed against `pain001`
(the core); the maintainer will route them.

## Supported versions

| Version | Supported? |
| :--- | :--- |
| 0.0.53 (latest) | ✅ |
| ≤ 0.0.52 | ❌ (no such release; this package debuted at 0.0.53) |

Requires Python 3.10+ and `pain001 >= 0.0.54`.

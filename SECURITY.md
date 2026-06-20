<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Policy

## Supported versions

This package follows the [`pain001`](https://github.com/sebastienrousseau/pain001)
suite cadence. Security patches are issued for the latest minor of
the latest major. While pre-`1.0`, that means **the latest released
0.0.x and the immediately prior 0.0.x** receive security fixes; older
0.0.x versions do not.

| Version | Status | Receives security fixes? |
| :--- | :--- | :--- |
| `0.0.53` (latest) | Current | ✅ Yes |
| `≤ 0.0.52` | Old | ❌ No — upgrade |

## Reporting a vulnerability

**Do not open a public issue for security reports.**

Use one of the following private channels:

1. **GitHub Private Vulnerability Reporting (preferred)**
   <https://github.com/sebastienrousseau/pain001-loader-xlsx/security/advisories/new>
2. **Email**: `security@pain001.com`

**Acknowledgement**: within 48 hours. **Triage**: within 7 days.
**Fix windows**: critical 7 days, high 30 days, medium 60 days, low
best-effort.

## Security posture

### Scope

This package is a single class — `XlsxLoader` — that reads an Excel
`.xlsx` / `.xlsm` file and hands the rows back to pain001. It does
**not** parse XML, render templates, or write files. The pain001
core enforces every downstream security control; this package is a
thin input adapter.

### Threat model

| Surface | How it's handled |
| :--- | :--- |
| **Excel macros (VBA)** | Not executed. `openpyxl` is opened with `read_only=True` — the workbook reader doesn't initialise the macro engine. |
| **Excel formulas** | Cached value only (`data_only=True`). The formula engine never runs; we read what the user last saw + saved. |
| **External references** | `openpyxl` does not follow external `[Workbook]Sheet!Cell` links in read-only mode. |
| **IBAN data corruption** | The loader **refuses** rows whose IBAN cells are numeric (Excel's "General" format silently strips leading zeros — a known SAP/Oracle/Workday export bug). Caught at load time, not at the bank. |
| **Path traversal** | Defers entirely to pain001's `pain001.security.path_validator`. The loader receives an already-validated path. |
| **Dependency CVEs** | `openpyxl >= 3.1, < 4` is the only direct dep. Pinned via PyPI and audited by GitHub Dependabot. |

### Cryptography status

This package implements **no** cryptographic functionality. The
underlying `openpyxl` parses the OOXML zip envelope without
performing any cryptographic verification of the workbook contents.
If you need encrypted-Excel support, that is out of scope —
pre-decrypt the file with `msoffcrypto-tool` or similar and feed
pain001 the plaintext.

### Supply chain

- **PyPI Trusted Publishing** (OIDC, no long-lived tokens).
- **Sigstore attestations** for sdist + wheel via
  `pypa/gh-action-pypi-publish`.
- **Signed git tags**: every release tag is signed with the
  maintainer's SSH key (`git tag --verify v0.0.53`).
- **No `--no-verify` or `--allow-unverified` shortcuts** in any
  release workflow.

## Contact

- **GitHub Private Vulnerability Reporting (preferred):**
  <https://github.com/sebastienrousseau/pain001-loader-xlsx/security/advisories/new>
- **Email:** `security@pain001.com`

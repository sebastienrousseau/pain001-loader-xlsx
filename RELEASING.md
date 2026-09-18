<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Releasing pain001-loader-xlsx

What merits a release, and how to cut one, so versions are deliberate.

## Versioning scheme

Every member of the pain001 suite ships the **same version number** as the
core: when `pain001` ships `0.0.X`, pain001-loader-xlsx ships `0.0.X`, even when nothing
in this repository changed. Versions advance in `0.0.1` steps along the
`0.0.x` line. The maintainer decides when the next number opens.

The `pain001` floor in `pyproject.toml` is the oldest core whose plugin
contract this loader needs. It is recorded in the core's `pain001.suite`
table; a floor that moves in one place but not the other fails the daily
suite-consistency check. Raise it there first, deliberately.

## What merits a release

The suite releases together, so a release of pain001-loader-xlsx is usually the suite
release. Between suite releases, an out-of-band fix is cut only for a
security or correctness defect in this loader, as `0.0.X.postN`.

## Pre-flight checklist

A release is ready only when all of the following hold on `main`:

1. CI is green: tests with the 100% coverage gate, docstring gate, ruff,
   mypy, CodeQL, the suite conformance test.
2. Every Dependabot and CodeQL alert is resolved or has a documented,
   expiring suppression.
3. `CHANGELOG.md` has a dated section for the new version, newest first.
4. Release notes exist at `releases/v0.0.X.md`; CI's "Release Notes Present" check and the release workflow both fail without them.
5. The version is identical in `pyproject.toml` and `pain001_loader_xlsx/__init__.py`.

## Cutting the release

1. Bump the version and add the changelog section in one PR, titled
   `chore(release): align pain001-loader-xlsx on 0.0.X`.
2. Merge it once CI is green.
3. Push a signed tag:

   ```bash
   git tag -s v0.0.X -m "pain001-loader-xlsx v0.0.X" <merge-commit>
   git push origin v0.0.X
   ```

4. The tag runs `release.yml`: it fails fast if the tag does not match the
   package version, builds the sdist and wheel, runs `twine check`,
   attests build provenance, signs each distribution keylessly with
   sigstore, creates the GitHub release with the files and their
   `.sig`/`.pem`, publishes to PyPI through trusted publishing with PEP 740
   attestations, and attaches CycloneDX and SPDX SBOMs of the installed
   package.

## After releasing

- Confirm the version on [PyPI](https://pypi.org/project/pain001-loader-xlsx/) and that
  the GitHub release is published, with the SBOMs attached.
- Verify a clean install: `pip install pain001-loader-xlsx==0.0.X`.
- The core's daily `check_suite_consistency` must report the suite
  consistent; if it does not, a member was left behind.

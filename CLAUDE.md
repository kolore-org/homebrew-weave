# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the public-facing **distribution repo** for the `weave` family of tools (v1:
`weave-viewer-cli`). It ships the released binary, Homebrew formula, examples, docs, and a
scaffold skill — but **no engine source** (that lives in a private upstream monorepo). See
`README.md` for the user-facing CLI surface and `.weave` project model. Today the repo ships
`README.md`, `LICENSE`, `EULA.txt`, this file, `Formula/weave-viewer.rb`,
`scripts/update-formula.sh`, `docs/feature-support.md`, and `.github/workflows/bump-formula.yml`;
the `examples/` and the `weave-scaffold` skill referenced below are still planned.

## Commands

| Action | Command |
| :--- | :--- |
| **Install** | `brew tap kolore-org/weave && brew install kolore-org/weave/weave-viewer` (qualified name — bare `weave` collides with homebrew-core) |
| **Preview** | `weave-viewer-cli PATH` |
| **Render MP4** | `weave-viewer-cli PATH --record out.mp4 [--width W --height H --duration S --fps N]` |
| **Validate (no GPU)** | `weave-viewer-cli PATH --validate` |

## Workflow Constraints

- **Do not compile:** This is a distribution repo. There is no build system, engine code, or `cmake`. `weave-viewer-cli` is an external release artifact downloaded via Homebrew.
- **Do not invent specifications:** The `.weave` format, `id="template-*-N"` matchers, supported CSS subset, and `overrides.json` schema are defined upstream. Pull exact rules from the upstream monorepo or ask for them.
- **Do not fabricate release targets:** `Formula/weave-viewer.rb` is owned by this repo and its `version`/`url`/`sha256` must strictly track an existing `weave-v*` release. Don't hand-edit them — `.github/workflows/bump-formula.yml` (on `release: published`) or `scripts/update-formula.sh` sync them from the release's `.sha256` asset.
- **Scaffold limitation:** `.claude/skills/weave-scaffold/SKILL.md` is for generating new projects only. Do not use it to edit existing projects or trigger renders.

## Licensing Rules

- **Repo content (docs, examples, formula, skill):** Apache License 2.0 (`LICENSE`, copyright kolore-org).
- **Binary (`weave-viewer-cli`):** Proprietary EULA. The binding copy ships inside each release tarball; `EULA.txt` here is an informational placeholder (terms TBD, review with counsel).
- **Formula requirement:** `Formula/weave-viewer.rb`'s `license` field must reflect the proprietary binary (e.g. `:cannot_represent`), not the repo's Apache license.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the public-facing **distribution repo** for the `weave` family of tools (v1:
`weave-viewer-cli`). It ships the released binary, Homebrew formula, examples, docs, and a
scaffold skill — but **no engine source** (that lives in a private upstream monorepo). See
`README.md` for the user-facing CLI surface and `.weave` project model. Only `README.md`,
`LICENSE`, `EULA.txt`, and this file exist today; everything else referenced below is planned.

## Commands

| Action | Command |
| :--- | :--- |
| **Install** | `brew tap USER/weave && brew install weave` (confirm `USER` org before running) |
| **Preview** | `weave-viewer-cli PATH` |
| **Render MP4** | `weave-viewer-cli PATH --record out.mp4 [--width W --height H --duration S --fps N]` |
| **Validate (no GPU)** | `weave-viewer-cli PATH --validate` |

## Workflow Constraints

- **Do not compile:** This is a distribution repo. There is no build system, engine code, or `cmake`. `weave-viewer-cli` is an external release artifact downloaded via Homebrew.
- **Do not invent specifications:** The `.weave` format, `id="template-*-N"` matchers, supported CSS subset, and `overrides.json` schema are defined upstream. Pull exact rules from the upstream monorepo or ask for them.
- **Do not fabricate release targets:** The Homebrew formula's `url` and `sha256` must strictly track existing upstream `weave-v*` release tags.
- **Scaffold limitation:** `.claude/skills/weave-scaffold/SKILL.md` is for generating new projects only. Do not use it to edit existing projects or trigger renders.

## Licensing Rules

- **Repo content (docs, examples, formula, skill):** Apache License 2.0 (`LICENSE`, copyright kolore-org).
- **Binary (`weave-viewer-cli`):** Proprietary EULA. The binding copy ships inside each release tarball; `EULA.txt` here is an informational placeholder (terms TBD, review with counsel).
- **Formula requirement:** `Formula/weave.rb`'s `license` field must reflect the proprietary binary (e.g. `:cannot_represent`), not the repo's Apache license.

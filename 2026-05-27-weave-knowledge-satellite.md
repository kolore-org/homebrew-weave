# Weave Knowledge — Satellite (`kolore-org/weave`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author the human-owned, designer-facing knowledge in the public satellite repo — runnable examples, worded authoring guide, agent skill wrappers, and an `llms.txt` entry point — that together with the machine-generated `docs/feature-support.md` let an LLM reliably author weave projects.

**Architecture:** All files here are **human-owned** except `docs/feature-support.md`, which is machine-generated and pushed by the monorepo on release (this plan only commits a placeholder so links never dangle). The skill **scaffolds + validates** (GPU-free `--validate`); per the satellite's existing `CLAUDE.md`, it **never auto-triggers renders** — screenshotting is a user-run step. `llms.txt` is **reference-only** (links the other files; no assembly/marker-merge), keeping the generator footprint to one file.

**Tech Stack:** HTML/CSS (`template.weave`), JSON (`manifest.json`/`overrides.json`), markdown, GitHub Actions, `weave-viewer-cli`.

> **Working directory:** the satellite checkout `../weave` (a.k.a. `kolore-org/weave`). All paths below are relative to that repo root.
>
> **Binary for local validation:** set `WEAVE_CLI` to a built `weave-viewer-cli`. Default assumed: `../hexer-clone-1/cmake-build-debug/apps/weave-viewer-cli/weave-viewer-cli` (build it in the monorepo first). `--validate` is GPU-free.
>
> **Reference:** design spec at `hexer-clone-1/docs/superpowers/specs/2026-05-27-weave-agentic-knowledge-design.md` (cross-repo contract §3, usage loop §5). Examples use **only ✅ verified features**; avoid CSS Grid and reactive Noiser scripting (v1 out-of-scope).

---

## File Structure

| File | Responsibility | Owner |
|---|---|---|
| `examples/hello-title/{template.weave,manifest.json,overrides.json}` | Canonical minimal example (block + text-align + fade-up keyframes) | Human |
| `examples/lower-third/{template.weave,manifest.json,overrides.json}` | Richer example (absolute-positioned flex bar + slide-in transform) | Human |
| `docs/authoring.md` | Worded guide: project structure, CLI usage, the scaffold→validate loop, gotchas | Human |
| `docs/feature-support.md` | Machine-generated index (placeholder committed here; overwritten on release) | **Machine** |
| `llms.txt` | Reference-only agent entry point linking the above | Human |
| `.claude/skills/weave-scaffold/SKILL.md` | Claude skill (scaffold + validate; no auto-render) | Human |
| `AGENTS.md` | Codex pointer → `llms.txt` + loop | Human |
| `GEMINI.md` | Gemini pointer → `llms.txt` + loop | Human |
| `.github/workflows/validate-examples.yml` | CI: download released binary, `--validate` every example | Human |
| `scripts/check-llms-links.sh` | Link-checker: every path referenced in `llms.txt` resolves | Human |

---

## Task 1: Canonical example — `hello-title`

**Files:**
- Create: `examples/hello-title/template.weave`
- Create: `examples/hello-title/manifest.json`
- Create: `examples/hello-title/overrides.json`

- [ ] **Step 1: Verify validation FAILS before the example exists**

Run: `"${WEAVE_CLI:-../hexer-clone-1/cmake-build-debug/apps/weave-viewer-cli/weave-viewer-cli}" examples/hello-title --validate; echo "exit=$?"`
Expected: non-zero exit (folder/`template.weave` not found).

- [ ] **Step 2: Create `examples/hello-title/template.weave`**

```html
<!DOCTYPE html><html><head><style>
html, body { margin: 0; padding: 0; }
body { background: #888888; width: 1280px; height: 720px;
       font-family: 'Inter', sans-serif; color: #ffffff; }
.title { font-size: 96px; text-align: center; padding-top: 280px;
         animation: fade-up 5s ease-out infinite both; }
@keyframes fade-up {
  0%   { opacity: 0; transform: translateY(40px); }
  20%  { opacity: 1; transform: translateY(0); }
  85%  { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-20px); }
}
</style></head><body>
  <div class="title">Hello, World</div>
</body></html>
```

- [ ] **Step 3: Create `examples/hello-title/manifest.json`**

```json
{
  "name": "hello-title",
  "description": "Centered title that fades up over 5s and loops.",
  "render": { "width": 1280, "height": 720, "duration": 5, "fps": 60 }
}
```

- [ ] **Step 4: Create `examples/hello-title/overrides.json`**

```json
{ "colors": {}, "text": {}, "images": {} }
```

- [ ] **Step 5: Verify validation PASSES**

Run: `"${WEAVE_CLI:-../hexer-clone-1/cmake-build-debug/apps/weave-viewer-cli/weave-viewer-cli}" examples/hello-title --validate; echo "exit=$?"`
Expected: `exit=0`.

- [ ] **Step 6: (User-run, optional) eyeball the render** — NOT part of the skill loop

Run: `"$WEAVE_CLI" examples/hello-title --headless --exit-screenshot /tmp/hello.png --frame-num-until-exit 90`
Expected: a PNG showing the white centered "Hello, World" on grey. (Requires a GPU.)

- [ ] **Step 7: Commit**

```bash
git add examples/hello-title/
git commit -m "examples: hello-title (block + text-align + fade-up keyframes)"
```

---

## Task 2: Richer example — `lower-third`

**Files:**
- Create: `examples/lower-third/template.weave`
- Create: `examples/lower-third/manifest.json`
- Create: `examples/lower-third/overrides.json`

> Uses only ✅ features: absolute positioning, flexbox column, color, font, `@keyframes` with **px** `translateX` (avoid `%` transforms — a known engine bug affects `%`-transform absolute-rect computation). No `border-radius` (its Chrome pixel parity is known-failing).

- [ ] **Step 1: Verify validation FAILS before the example exists**

Run: `"${WEAVE_CLI:-../hexer-clone-1/cmake-build-debug/apps/weave-viewer-cli/weave-viewer-cli}" examples/lower-third --validate; echo "exit=$?"`
Expected: non-zero exit.

- [ ] **Step 2: Create `examples/lower-third/template.weave`**

```html
<!DOCTYPE html><html><head><style>
html, body { margin: 0; padding: 0; }
body { background: #1a1a1a; width: 1920px; height: 1080px;
       font-family: 'Inter', sans-serif; }
.bar { position: absolute; left: 96px; bottom: 120px;
       display: flex; flex-direction: column; justify-content: center;
       width: 720px; height: 160px; padding: 0 40px;
       background: #2563eb; color: #ffffff;
       animation: slide-in 0.8s ease-out both; }
.name     { font-size: 56px; }
.subtitle { font-size: 28px; color: #cbd5e1; }
@keyframes slide-in {
  0%   { opacity: 0; transform: translateX(-80px); }
  100% { opacity: 1; transform: translateX(0); }
}
</style></head><body>
  <div class="bar">
    <div class="name">Ada Lovelace</div>
    <div class="subtitle">Mathematician &amp; first programmer</div>
  </div>
</body></html>
```

- [ ] **Step 3: Create `examples/lower-third/manifest.json`**

```json
{
  "name": "lower-third",
  "description": "Bottom-left name/title bar that slides in from the left.",
  "render": { "width": 1920, "height": 1080, "duration": 4, "fps": 60 }
}
```

- [ ] **Step 4: Create `examples/lower-third/overrides.json`**

```json
{ "colors": {}, "text": {}, "images": {} }
```

- [ ] **Step 5: Verify validation PASSES**

Run: `"${WEAVE_CLI:-../hexer-clone-1/cmake-build-debug/apps/weave-viewer-cli/weave-viewer-cli}" examples/lower-third --validate; echo "exit=$?"`
Expected: `exit=0`.

- [ ] **Step 6: Commit**

```bash
git add examples/lower-third/
git commit -m "examples: lower-third (absolute flex bar + px slide-in)"
```

---

## Task 3: `docs/feature-support.md` placeholder (machine-owned slot)

**Files:**
- Create: `docs/feature-support.md`

> This file is **generated by the monorepo and overwritten on every release**. Commit a placeholder now so `llms.txt` links resolve before the first generated push. The DO-NOT-EDIT header matches the generator's header (spec §3) so humans don't hand-edit it.

- [ ] **Step 1: Create the placeholder**

`docs/feature-support.md`:

```markdown
<!-- GENERATED by weave gen-knowledge — DO NOT EDIT BY HAND.
     engine_version: (placeholder — populated on first release)
     source_commit:  (placeholder)
     generated_at:   (placeholder)
     Source of truth: hexer-clone-1 css_fixtures + known_failing_fixtures.txt -->

# weave-viewer-cli — Supported CSS & HTML

> **Placeholder.** This index is auto-generated from the engine's fixture suite
> and replaced on the next `weave-v*` release. Until then, rely on the examples
> in `examples/` and the guidance in `docs/authoring.md`. Use only features you
> can confirm against an example; treat anything else as unverified.

## Verified-working features

_(populated on release)_

## Known limitations

Not supported (do not use): **CSS Grid**; reactive Noiser `<script type="noiser">` scripting.
```

- [ ] **Step 2: Verify the header guard is present**

Run: `grep -q "DO NOT EDIT BY HAND" docs/feature-support.md && echo ok`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add docs/feature-support.md
git commit -m "docs: feature-support.md placeholder (machine-owned slot)"
```

---

## Task 4: `docs/authoring.md` (worded knowledge)

**Files:**
- Create: `docs/authoring.md`

- [ ] **Step 1: Create the guide**

`docs/authoring.md`:

```markdown
# Authoring weave projects

A weave project is a **folder**. `weave-viewer-cli` discovers these files by name:

| File | Required | Purpose |
|---|---|---|
| `template.weave` (or `template.html`) | yes | HTML + CSS document (with optional `@keyframes` animations) |
| `manifest.json` | no | Default render `width`/`height`/`duration`/`fps` |
| `overrides.json` | no | Variable overrides: `{ "colors": {}, "text": {}, "images": {} }` |

## CLI quick reference

```
weave-viewer-cli PATH                          # preview window (loops animations)
weave-viewer-cli PATH --validate               # GPU-free parse + id/image checks; exit!=0 on error
weave-viewer-cli PATH --record out.mp4         # render MP4 (defaults from manifest.json)
weave-viewer-cli PATH --exit-screenshot p.png --frame-num-until-exit N   # single frame
weave-viewer-cli --template FILE [--overrides O --manifest M]            # single-file input
```

Common flags: `--width --height --duration --fps` (override manifest), `--headless`, `--watch` (live-reload preview).

## The authoring loop

1. Read `feature-support.md` — **use only ✅-listed features.** No CSS Grid; no `<script type="noiser">`.
2. Write `template.weave` (+ `manifest.json`). Size the `body` to your canvas (e.g. `width: 1280px; height: 720px`).
3. Run `weave-viewer-cli <folder> --validate` until it exits 0.
4. *(local, optional)* render a frame with `--exit-screenshot` to eyeball it.

## What works well (start here)

- **Layout:** flexbox (`display: flex`, `flex-direction`, `justify-content`, `align-items`, `gap`), block flow, absolute positioning (`position: absolute` + `top/right/bottom/left`).
- **Animation:** `@keyframes` + `animation` (duration/easing/iteration/fill-mode), `transition`. Prefer **px** translates over `%`.
- **Visual:** `color`, `background-color`, linear gradients, `opacity`, `box-shadow`/`text-shadow`, `clip-path: polygon(...)`, `filter`.
- **Text:** `font-family` (Google Fonts fetched lazily), `font-size/weight`, `text-align`, `letter-spacing`, `line-height`.

## Gotchas

- **No audio** in recorded video (v1).
- **`border-radius`** parses but its pixel parity is on the roadmap — verify visually before relying on rounded corners.
- **`%` transforms** on absolutely-positioned elements have a known bug — prefer px.
- Fonts load lazily over the network; offline renders fall back. Declare `font-family` explicitly.
- See `feature-support.md` for the authoritative, release-matched ✅/❌ list.
```

- [ ] **Step 2: Verify it references the index**

Run: `grep -q "feature-support.md" docs/authoring.md && echo ok`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add docs/authoring.md
git commit -m "docs: authoring guide (project structure, CLI, loop, gotchas)"
```

---

## Task 5: `llms.txt` entry point + skill wrappers + link-check

**Files:**
- Create: `llms.txt`
- Create: `.claude/skills/weave-scaffold/SKILL.md`
- Create: `AGENTS.md`
- Create: `GEMINI.md`
- Create: `scripts/check-llms-links.sh`

- [ ] **Step 1: Write the link-checker test FIRST**

`scripts/check-llms-links.sh`:

```bash
#!/usr/bin/env bash
# Assert every repo-relative path mentioned in llms.txt exists. Exit!=0 on any miss.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
miss=0
# Process substitution keeps the loop in THIS shell so `miss` survives.
while IFS= read -r p; do
  # Only validate path-like tokens (contain '/'). Bare filenames mentioned in
  # prose (e.g. `manifest.json`, `template.weave`) are NOT repo paths — skip them.
  case "$p" in
    */*) [ -e "$p" ] || { echo "MISSING: $p"; miss=1; };;
  esac
done < <(grep -oE '`[^`]+`' llms.txt | tr -d '`' | sort -u)
if [ "$miss" -eq 0 ]; then
  echo "all llms.txt paths resolve"
else
  echo "llms.txt has dangling path(s)"; exit 1
fi
```

```bash
chmod +x scripts/check-llms-links.sh
```

- [ ] **Step 2: Run it — verify it FAILS (no llms.txt yet)**

Run: `bash scripts/check-llms-links.sh; echo "exit=$?"`
Expected: non-zero (`llms.txt` absent).

- [ ] **Step 3: Create `llms.txt` (reference-only)**

```text
# weave-viewer-cli — agent guide

weave-viewer-cli renders a project FOLDER (HTML+CSS) to a preview window, a
screenshot, or an MP4. Your job: turn a user's request into a valid project
folder, then validate it.

## Read these, in order
1. `docs/feature-support.md` — the authoritative, release-matched list of
   supported CSS/HTML features. USE ONLY ✅-listed features.
2. `docs/authoring.md` — project structure, CLI usage, the authoring loop, gotchas.
3. `examples/hello-title/` and `examples/lower-third/` — copy these as starting points.

## A project folder contains
- `template.weave`  (required) — HTML + CSS, with optional @keyframes.
- `manifest.json`   (optional) — render defaults: width/height/duration/fps.
- `overrides.json`  (optional) — { "colors": {}, "text": {}, "images": {} }.

## Loop
1. Write the folder using only ✅ features (no CSS Grid; no <script type="noiser">).
2. `weave-viewer-cli <folder> --validate`  → must exit 0.
3. (The user renders/inspects with --exit-screenshot or --record; you do not auto-render.)

## Hard rules
- Do not use features absent from `docs/feature-support.md`.
- Prefer px over % in transforms. Avoid relying on border-radius pixel parity.
- Size body to the canvas (e.g. width:1280px; height:720px).
```

- [ ] **Step 4: Create `.claude/skills/weave-scaffold/SKILL.md`**

```markdown
---
name: weave-scaffold
description: Use when a user wants to create a new weave-viewer-cli project (motion graphic, title card, lower-third, animated HTML/CSS scene) from a description. Scaffolds a project folder and validates it. Generates NEW projects only — does not edit existing projects or trigger renders.
---

# weave-scaffold

Turn a user's description into a valid weave project folder, then validate it.

## Steps
1. **Read the knowledge** (in this repo): `docs/feature-support.md` (authoritative ✅/❌ feature list — use only ✅), then `docs/authoring.md` (structure, CLI, gotchas).
2. **Copy a starting point** from `examples/hello-title/` (simple) or `examples/lower-third/` (positioned bar + animation).
3. **Write the folder:** `template.weave` (+ `manifest.json`; `overrides.json` if variables are needed). Use only ✅ features. Prefer px transforms; avoid CSS Grid and `<script type="noiser">`.
4. **Validate:** run `weave-viewer-cli <folder> --validate` and fix until it exits 0.
5. **Hand off:** tell the user how to preview/render themselves (`weave-viewer-cli <folder>` or `--record out.mp4`). **Do not auto-render** (see repo CLAUDE.md).

## Constraints
- New projects only — do not edit existing projects or run renders from this skill.
- If a requested effect needs an unsupported feature (e.g. CSS Grid), say so and offer a flexbox alternative.
```

- [ ] **Step 5: Create `AGENTS.md` (Codex)**

```markdown
# Agent guide (Codex)

You are authoring **weave-viewer-cli** projects. Start by reading `llms.txt`, then
`docs/feature-support.md` (use only ✅ features) and `docs/authoring.md`.

Produce a project folder (`template.weave` [+ `manifest.json`, `overrides.json`]),
then run `weave-viewer-cli <folder> --validate` until it exits 0. Do not auto-render;
the user previews/records themselves. Copy `examples/hello-title/` or
`examples/lower-third/` as a starting point.
```

- [ ] **Step 6: Create `GEMINI.md` (Gemini)**

```markdown
# Agent guide (Gemini)

You are authoring **weave-viewer-cli** projects. Start by reading `llms.txt`, then
`docs/feature-support.md` (use only ✅ features) and `docs/authoring.md`.

Produce a project folder (`template.weave` [+ `manifest.json`, `overrides.json`]),
then run `weave-viewer-cli <folder> --validate` until it exits 0. Do not auto-render;
the user previews/records themselves. Copy `examples/hello-title/` or
`examples/lower-third/` as a starting point.
```

- [ ] **Step 7: Run the link-checker — verify it PASSES**

Run: `bash scripts/check-llms-links.sh; echo "exit=$?"`
Expected: `all llms.txt paths resolve` and `exit=0`. (All of `docs/feature-support.md`, `docs/authoring.md`, `examples/hello-title/`, `examples/lower-third/` now exist.)

- [ ] **Step 8: Commit**

```bash
git add llms.txt .claude/skills/weave-scaffold/SKILL.md AGENTS.md GEMINI.md scripts/check-llms-links.sh
git commit -m "knowledge: llms.txt entry point + claude/codex/gemini skill wrappers + link-check"
```

---

## Task 6: CI — validate every example against the released binary

**Files:**
- Create: `.github/workflows/validate-examples.yml`

> The satellite is a distribution repo (no engine source, no compilation). CI downloads the **released** macOS arm64 binary tarball and runs the GPU-free `--validate` on each example. Skips gracefully if no release exists yet.

- [ ] **Step 1: Create the workflow**

`.github/workflows/validate-examples.yml`:

```yaml
name: Validate examples

on:
  push:
    paths: ['examples/**', '.github/workflows/validate-examples.yml']
  pull_request:
    paths: ['examples/**']
  workflow_dispatch:

jobs:
  validate:
    runs-on: macos-14   # Apple Silicon / arm64 (v1 is arm64-only)
    steps:
      - uses: actions/checkout@v4

      - name: Download latest released binary
        id: dl
        env:
          GH_TOKEN: ${{ github.token }}
        shell: bash
        run: |
          set -euo pipefail
          if ! gh release list --limit 1 | grep -q .; then
            echo "no_release=true" >> "$GITHUB_OUTPUT"; echo "No release yet — skipping."; exit 0
          fi
          gh release download --pattern 'weave-viewer-cli-macos-arm64.tar.gz' --dir /tmp/wv
          tar -xzf /tmp/wv/weave-viewer-cli-macos-arm64.tar.gz -C /tmp/wv
          CLI="$(find /tmp/wv -type f -name weave-viewer-cli | head -1)"
          chmod +x "$CLI"
          echo "cli=$CLI" >> "$GITHUB_OUTPUT"
          echo "no_release=false" >> "$GITHUB_OUTPUT"

      - name: Validate all examples
        if: steps.dl.outputs.no_release == 'false'
        shell: bash
        run: |
          set -euo pipefail
          CLI='${{ steps.dl.outputs.cli }}'
          fail=0
          for d in examples/*/; do
            echo "::group::validate $d"
            if "$CLI" "$d" --validate; then echo "PASS $d"; else echo "FAIL $d"; fail=1; fi
            echo "::endgroup::"
          done
          [ "$fail" -eq 0 ]
```

- [ ] **Step 2: Validate the workflow YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/validate-examples.yml')); print('yaml ok')"`
Expected: `yaml ok`.

- [ ] **Step 3: Locally simulate the validation loop**

Run:
```bash
CLI="${WEAVE_CLI:-../hexer-clone-1/cmake-build-debug/apps/weave-viewer-cli/weave-viewer-cli}"
for d in examples/*/; do "$CLI" "$d" --validate && echo "PASS $d" || echo "FAIL $d"; done
```
Expected: `PASS examples/hello-title/` and `PASS examples/lower-third/`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/validate-examples.yml
git commit -m "ci: validate every example against the released binary (--validate, GPU-free)"
```

---

## Task 7: Reconcile `CLAUDE.md` references (surgical)

**Files:**
- Modify: `CLAUDE.md`

> The satellite `CLAUDE.md` already names `.claude/skills/weave-scaffold/SKILL.md` and the no-render constraint — both now satisfied. Only add pointers to the new knowledge files if they are not already referenced. Do not restructure the file.

- [ ] **Step 1: Check what's already referenced**

Run: `grep -n "llms.txt\|feature-support\|authoring.md\|examples/" CLAUDE.md || echo "none referenced"`

- [ ] **Step 2: If missing, add a single pointer line** under the existing commands/knowledge section (match surrounding style). Example:

```markdown
- **Knowledge for agents:** `llms.txt` (entry point) → `docs/feature-support.md` (✅/❌ features, auto-generated) + `docs/authoring.md` + `examples/`.
```

- [ ] **Step 3: Commit (only if changed)**

```bash
git add CLAUDE.md
git commit -m "docs: point CLAUDE.md at the new agent knowledge (llms.txt/feature-support/examples)"
```

---

## Self-Review

- **Spec coverage:** §2 ownership (human vs machine) → every file tagged in File Structure; only `docs/feature-support.md` machine-owned (Task 3 placeholder). §3 contract (single generated file + DO-NOT-EDIT header) → Task 3. §5 usage loop + skill wrappers (scaffold + validate, no auto-render) → Tasks 4–5. Examples (✅ features only) → Tasks 1–2. ✅
- **Decision B (reference-only `llms.txt`):** Task 5 — `llms.txt` links files, no assembly/markers; link-checker enforces resolution. ✅
- **Satellite CLAUDE.md contract:** skill named `weave-scaffold`, "new projects only", "no renders" — honored in Task 5 SKILL.md and Task 7 reconcile. ✅
- **Honesty (M4 contract conformance):** examples avoid known-failing surfaces (`%` transforms, reliance on `border-radius` parity) and out-of-scope features (Grid, Noiser scripting); gotchas documented in `authoring.md`. ✅
- **Name/path consistency:** `weave-viewer-cli --validate` invocation, `WEAVE_CLI` default path, and the four referenced knowledge paths (`docs/feature-support.md`, `docs/authoring.md`, `examples/hello-title/`, `examples/lower-third/`) are identical across Tasks 1–6. ✅
- **Cross-repo:** `docs/feature-support.md` placeholder here is overwritten by the monorepo plan's Task 7 push — paths match (`/tmp/sat/docs/feature-support.md` ↔ `docs/feature-support.md`). ✅
```

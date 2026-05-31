# weave — public release surface

This repo is the public-facing distribution point for the `weave` family of tools (v1: `weave-viewer-cli`). It carries no engine code — that lives in a private upstream monorepo and is published here as binary releases.

```
[ Upstream Monorepo ]       [ This Distribution Repo ]
┌───────────────────┐       ┌────────────────────────┐
│ - Engine Source   │──────▶│ - weave-viewer-cli bin │
│ - Build System    │ CI    │ - Homebrew Formula     │
│ - .weave Specs    │ Cuts  │ - Examples & Docs      │
│ - CSS Subsets     │ Tag   │ - Scaffold Skill       │
└───────────────────┘       └────────────────────────┘
  (Source of Truth)           (Deployment & Usage)
```

## What's in this repo

- `Formula/weave-viewer.rb` — Homebrew formula that installs the `weave-viewer-cli` binary + its runtime data dir. **Owned by this repo**; `version`/`sha256` are bumped on each release by `.github/workflows/bump-formula.yml` (or `scripts/update-formula.sh`).
- `examples/` — designer-facing curated `.weave` projects. Each subfolder is a self-contained project. `git clone` this repo, copy or edit examples, point `weave-viewer-cli` at the folder.
- `docs/` — install, authoring guide, CSS subset reference, gotchas.
- `.claude/skills/weave-subtitle/SKILL.md` — Claude Code skill that assists in creating, styling, and recording subtitles, and automatically manages the rendering pipeline.
- `.claude/skills/weave-scaffold/SKILL.md` — Claude Code skill that scaffolds a new `.weave` project from a user description.
- `.github/workflows/test-formula.yml` — CI that installs the formula in a clean environment and renders `examples/basic` to verify the release works.

## Install (macOS Only)

Weave is currently experimental and supports **macOS (Apple Silicon / M-series ARM64)** only.

To install the CLI and all of its required runtime dependencies, run the following Homebrew commands:

```bash
# 1. Tap the official Weave repository
brew tap kolore-org/weave

# 2. Install the weave-viewer package (use the qualified name to avoid collisions)
brew install kolore-org/weave/weave-viewer
```

### Known Apple Silicon & Git LFS Sandbox Caveat

If you are on an M-series Mac and have **Git LFS** globally configured on your system, the `brew tap` command may fail with an error similar to:
```
git-lfs filter-process: git-lfs: command not found
fatal: the remote end hung up unexpectedly
error: Failure while executing; `git clone ...` exited with 128.
```

**Why this happens:** On Apple Silicon, Homebrew is installed under `/opt/homebrew`. When executing a tap clone, Homebrew sanitizes the environment `PATH` for isolation and security, stripping `/opt/homebrew/bin` (where `git-lfs` resides). Because this repository uses Git LFS to track and store examples/assets, the git checkout triggers your global Git LFS filter. Since the sanitized PATH doesn't include `/opt/homebrew/bin`, the checkout fails with `git-lfs: command not found`.

**The Workaround:** Bypassing your global Git config (including LFS filters) during the tap is highly recommended. You can do this elegantly by setting `HOME=/dev/null` during the command execution:
```bash
# Run tap with clean HOME to bypass global LFS filters
HOME=/dev/null brew tap kolore-org/weave
```
Or for local testing:
```bash
HOME=/dev/null brew tap kolore-org/weave-local ./homebrew-weave
```

### Dependency Resolution
- **`weave-viewer-cli`**: This command is added directly to your system PATH.
- **`ffmpeg`**: Homebrew will **automatically detect and install `ffmpeg`** as a dependency if it's not already installed. `ffmpeg` is strictly required for encoding and saving recorded MP4 videos (`--record`).
- **Dawn/WebGPU Shaders**: All WebGPU runtime shaders and required dylibs are automatically bundled and placed in the formula's Cellar prefix.

> [!IMPORTANT]
> **Avoid naming collisions:** Do NOT run `brew install weave`. Homebrew's default core contains an unrelated Git merge-driver called `weave` which will conflict. Always use the qualified name `kolore-org/weave/weave-viewer` or `kolore-org/weave/weave` to install the correct package.

### Install from a local clone (testing the formula)

Modern Homebrew rejects `brew install --formula ./path.rb`, so install through a throwaway tap that
points at your clone:

```
git clone https://github.com/kolore-org/homebrew-weave
HOME=/dev/null brew tap kolore-org/weave-local ./homebrew-weave   # tap name is arbitrary; points at the clone
brew install kolore-org/weave-local/weave-viewer
# cleanup: brew uninstall weave-viewer && brew untap kolore-org/weave-local
```

## First use

```
git clone https://github.com/kolore-org/homebrew-weave
cd homebrew-weave/examples/basic
weave-viewer-cli .                        # opens preview window
weave-viewer-cli . --record out.mp4       # renders to MP4
```

A project is a **folder**. Inside, `weave-viewer-cli` looks for:

- `template.weave` (required) — HTML+CSS document describing the scene and any animations.
- `overrides.json` (optional) — variable overrides for text, images, colors.
- `manifest.json` (optional) — default render dimensions / duration / fps + (later) a variable schema.
- Assets at any relative subpath, resolved against the project folder.

## CLI surface (v1)

| Invocation | Effect |
|---|---|
| `weave-viewer-cli PATH` | Open a preview **window** that plays the template; animations loop until user closes. |
| `weave-viewer-cli PATH --record OUT.mp4 [--width W --height H --duration S --fps N]` | Render to MP4. Defaults come from `manifest.json` if present, else `1280×720 / 5s / 60fps`. |
| `weave-viewer-cli PATH --validate` | Static check (no GPU): parse `template.weave`, parse `overrides.json`, verify `id="template-*-N"` references match manifest keys, verify every image path under `overrides.images` resolves on disk. Exit non-zero on errors. |

Video output is **silent** in v1 (audio dropped). Audio mixing is on the roadmap.

## Automated Transcription & Alignment Tool

This repository includes a powerful local utility script, `scripts/transcribe_to_weave.py`, to help users and agents automatically transcribe any video file and generate a fully-compliant `.weave` project with precise, word-level synchronized Karaoke-Highlight subtitle animations.

### Prerequisites

The script runs locally and requires **OpenAI Whisper** and `ffmpeg` (installed by the Homebrew formula):

```bash
pip install openai-whisper
```

### Usage

Run the script pointing to your video file. It will automatically probe your video's dimensions/duration and generate the styled `template.weave` and `manifest.json`:

```bash
python3 scripts/transcribe_to_weave.py path/to/your/video.mp4 [output_dir]
```

By default, the output project is created at `outputs/<video_name>/`. Once generated, you can immediately render it:

```bash
# 1. Render visual tracks to silent MP4
weave-viewer-cli outputs/video_name --record outputs/video_name/silent.mp4

# 2. Re-mux the original audio instantly
ffmpeg -y -i outputs/video_name/silent.mp4 -i path/to/your/video.mp4 -map 0:v -map 1:a -c:v copy -c:a copy -shortest outputs/video_name/final_subtitled.mp4
```

## How releases work

`Formula/weave-viewer.rb`'s URL points at a tarball hosted on this repo's GitHub Releases. The
tarballs are produced by the upstream private monorepo's CI pipeline (GitHub Actions on tag push)
and uploaded here as a `weave-v*` release (binary + `.sha256` + `feature-support.md`). The monorepo
**does not** edit the formula — this repo owns it: `.github/workflows/bump-formula.yml` reacts to
each published release and bumps `version`/`sha256` from the `.sha256` asset (and refreshes
`docs/feature-support.md`). Source code is **not** distributed via this repo.

## Claude Skills

If you use **Claude Code**, this repository ships specialized **Agent Skills** located in `.claude/skills/` to automate your video creation and motion-design workflow:

### 1. Subtitle & Recording Skill (`/weave-subtitle`)
Designed specifically for kinetic motion graphics and subtitle design. To trigger the skill:
```bash
/weave-subtitle
```
This skill helps you:
- Suggest interactive browser-based subtitle styling workflows (using the Claude `frontend-design` plugin or Chrome DevTools).
- Map transcripts into contiguous word-by-word or phrase-based subtitle components in `template.weave`.
- Proactively avoid engine rendering limitations (e.g. text clipping, layout spacing gaps).
- Execute the rendering and audio-re-muxing pipelines using `weave-viewer-cli` and `ffmpeg` to produce a finalized video.

### 2. Scaffolding Skill (`/weave-scaffold`)
Helps you bootstrap new projects from a high-level description:
```bash
/weave-scaffold
```
Claude asks about your creative goal (intro, lower-third, greeting card), dimensions, and writes starting templates (`template.weave`, `overrides.json`, `manifest.json`) in your working directory.

## Examples

| Folder | What it shows | Window | Duration |
|---|---|---|---|
| `examples/basic` | Smoke test: gray bg, three muted SVG squares in a flexbox row, Ahem-font label. | 400×200 | 3s |

Additional examples added during v1: `lower-third`, `social-square`, `greeting-with-sun`, `video-with-overlay`.

## Authoring a template

See `docs/authoring.md` for the full guide. Quick version:

```html
<!DOCTYPE html><html><head><style>
html, body { margin: 0; padding: 0; }
body { background: #888; width: 1280px; height: 720px;
       font-family: 'Inter', sans-serif; color: #fff; }
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

Save as `template.weave` in a fresh folder, add a `manifest.json` with `"render": {"duration": 5}`, and `weave-viewer-cli FOLDER` opens it. `weave-viewer-cli FOLDER --record out.mp4` produces an MP4. Google Fonts are fetched lazily on first use; no font setup required.

## Known limitations (v1)

- **No audio** in output. Video files included as content (`<video>` tags) render visually but their audio track is dropped. Roadmap.
- **macOS only.** Linux and Windows binaries are planned but not in v1.
- **No live reload.** Edit → re-render. `weave watch` (file-change reload) is in the roadmap.
- **No GUI** for filling out variables. The CLI + Claude scaffold skill are the authoring surface.

## License

This repository contains two kinds of material under two different licenses:

- **Repository content** — the documentation, example `.weave` projects, the Homebrew
  formula, and the `weave-scaffold` Claude skill — is licensed under the **Apache
  License 2.0**. See [`LICENSE`](LICENSE).
- **The `weave-viewer-cli` binary**, distributed via this repo's GitHub Releases, is
  **proprietary and closed-source**. Its use is governed by an end-user license
  agreement bundled inside each release archive. See [`EULA.txt`](EULA.txt) for the
  current (placeholder) terms.

Bundled third-party assets in `examples/` and fonts fetched at runtime retain their own
respective licenses.

# Subtitle Scene Builder — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce one kinetic word-by-word subtitled clip over a portrait video, gated behind a minimal sync-test fixture, and record engine behavior in a findings log for upstream feedback.

**Architecture:** A pregenerated `template.weave` (HTML+CSS) layers a `<video>` background under per-word `<div>`s, each sequenced by `animation-delay`/`animation-duration` derived from `subtitles.json`, with `animation-fill-mode: both` hiding words outside their window. A standalone 3-box `sync-test/` fixture isolates the timeline primitive before the full clip is authored. `weave-viewer-cli --record` renders to MP4; `ffmpeg` re-muxes the source audio.

**Tech Stack:** weave-viewer-cli (Homebrew), ffmpeg (bundled), HTML/CSS subset per `docs/feature-support.md`, Google Fonts (Montserrat).

> **Domain note (read first):** There is no unit-test framework and **`exploration/` is gitignored** — every artifact this plan creates (`sync-test/`, `template.weave`, `manifest.json`, `FINDINGS.md`, all `*.mp4`) is a **local, untracked** investigation product. The skill's "commit" step is therefore replaced by **"record the observation in `FINDINGS.md`."** The only git-tracked artifacts are this plan and the spec, already committed on branch `subtitles-phase1`. Do **not** `git add` anything under `exploration/`.

> **Reference spec:** `docs/superpowers/specs/2026-05-28-subtitle-scene-builder-design.md`

---

## File Structure

| Path | Responsibility | Tracked? |
|---|---|---|
| `exploration/video-subs/FINDINGS.md` | Probe checklist + recorded results for upstream | no (gitignored) |
| `exploration/video-subs/sync-test/sync_bg.mp4` | 4s burned-in-timecode background (ffmpeg-generated) | no |
| `exploration/video-subs/sync-test/template.weave` | 3 boxes at delays 0/1.5/3s — the timeline gate | no |
| `exploration/video-subs/sync-test/manifest.json` | sync-test render config | no |
| `exploration/video-subs/template.weave` | Full 21-word kinetic caption scene | no |
| `exploration/video-subs/manifest.json` | Full-clip render config | no |
| `exploration/video-subs/dude.mp4`, `dude_alpha.mp4`, `subtitles.json` | Provided inputs (already present) | no |

All `weave-viewer-cli`/`ffmpeg` commands below are written to run **from the repo root** `/Users/jakubtyrcha/repos/weave`.

---

## Task 0: Prerequisites & findings scaffold

**Files:**
- Create: `exploration/video-subs/FINDINGS.md`

- [ ] **Step 1: Verify the toolchain is present**

Run:
```sh
weave-viewer-cli --help >/dev/null 2>&1 && echo "weave OK" || echo "weave MISSING"
ffmpeg -version >/dev/null 2>&1 && echo "ffmpeg OK" || echo "ffmpeg MISSING"
ffprobe -version >/dev/null 2>&1 && echo "ffprobe OK" || echo "ffprobe MISSING"
```
Expected: three `... OK` lines. If `weave MISSING`, install: `brew tap kolore-org/weave && brew install kolore-org/weave/weave-viewer` (installs `weave-viewer-cli` + bundled ffmpeg). Do not proceed until all three are OK.

- [ ] **Step 2: Create the findings log**

Create `exploration/video-subs/FINDINGS.md`:
```markdown
# Phase 1 — Findings (weave-viewer-cli subtitle exploration)

engine_version: <fill from `weave-viewer-cli --version`>
date: 2026-05-28

## Gate: sync-test fixture (probes 1–3)

| # | Probe | Expected | Result | Notes |
|---|---|---|---|---|
| 1 | `animation-delay` sequencing | Boxes appear at 0.0s / 1.5s / 3.0s | | |
| 2 | `animation-fill-mode: both` | Each box hidden before its delay and after its 1s window (no flash/stick) | | |
| 3 | `<video>` decode + clock sync | Box becomes visible exactly when burned-in timecode reads its delay | | |

**Gate verdict:** PASS / FAIL (if any of 1–3 FAIL, stop — do not build the full clip; report for replan.)

## Full clip (probes 4–8)

| # | Probe | Expected | Result | Notes |
|---|---|---|---|---|
| 4 | `font-weight` 700/800/900 distinct | Visibly different stroke weights | | |
| 5 | Non-ASCII glyph `ü` (`überhaupt`) | Renders correctly | | |
| 6 | Text overflow (`Sonntagmorgen` @80px in 528px) | wraps / clips / pushes — record which | | |
| 7 | Short-window animation (`das`, ~0.18s) | Pops sanely, no glitch | | |
| 8 | `object-fit: cover` on `<video>` | Fills 576×1024 without distortion | | |

## Bugs / surprises for upstream

- (list as discovered, with the fixture/word that triggered them)
```
Fill `engine_version` from `weave-viewer-cli --version`.

---

## Task 1: Sync-test fixture (GATE — must pass before Task 2)

**Files:**
- Create: `exploration/video-subs/sync-test/sync_bg.mp4`
- Create: `exploration/video-subs/sync-test/template.weave`
- Create: `exploration/video-subs/sync-test/manifest.json`

- [ ] **Step 1: Generate the burned-in-timecode background**

Run (creates the dir and the 4s video):
```sh
mkdir -p exploration/video-subs/sync-test
ffmpeg -y -f lavfi -i color=c=0x202830:s=576x1024:d=4:r=24 \
  -vf "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%{pts\:hms}':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=60" \
  -pix_fmt yuv420p exploration/video-subs/sync-test/sync_bg.mp4
```
Expected: file written, no error. If the font path errors, substitute any present `.ttf` (e.g. `/System/Library/Fonts/Supplemental/Courier New.ttf`).
Verify: `ffprobe -v error -show_entries stream=width,height,duration -of csv exploration/video-subs/sync-test/sync_bg.mp4` → `...,576,1024,4...`.

- [ ] **Step 2: Write the sync-test template**

Create `exploration/video-subs/sync-test/template.weave`:
```html
<!DOCTYPE html><html><head><style>
html,body{margin:0;padding:0}
body{width:576px;height:1024px;background:#000;position:relative;overflow:hidden;font-family:sans-serif}
video{position:absolute;inset:0;width:576px;height:1024px;object-fit:cover}
.box{position:absolute;left:138px;width:300px;height:120px;
  display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:48px;font-weight:700;
  opacity:0;animation-name:show;animation-duration:1s;
  animation-timing-function:linear;animation-fill-mode:both}
.b1{top:140px;background:#ee2233;animation-delay:0s}
.b2{top:452px;background:#22aa77;animation-delay:1.5s}
.b3{top:764px;background:#3366ee;animation-delay:3s}
@keyframes show{0%{opacity:0}10%{opacity:1}90%{opacity:1}100%{opacity:0}}
</style></head><body>
  <video src="sync_bg.mp4" muted></video>
  <div class="box b1">T=0.0</div>
  <div class="box b2">T=1.5</div>
  <div class="box b3">T=3.0</div>
</body></html>
```

- [ ] **Step 3: Write the sync-test manifest**

Create `exploration/video-subs/sync-test/manifest.json`:
```json
{ "render": { "width": 576, "height": 1024, "fps": 24, "duration": 4 } }
```

- [ ] **Step 4: Parse smoke-check**

Run: `weave-viewer-cli exploration/video-subs/sync-test --validate`
Expected: exit 0, no parse errors. (This only confirms the file parses; it does not validate timing.)

- [ ] **Step 5: Render the sync-test**

Run: `weave-viewer-cli exploration/video-subs/sync-test --record exploration/video-subs/sync-test/sync_out.mp4`
Expected: a ~4s MP4 is written. Confirm: `ffprobe -v error -show_entries format=duration -of csv exploration/video-subs/sync-test/sync_out.mp4` → ~`4.0`.

- [ ] **Step 6: Observe & record probes 1–3**

Open `sync_out.mp4` and scrub. Check, then write each result into `FINDINGS.md` (Gate table):
- **Probe 1/3:** the red `T=0.0` box is visible while the burned-in timecode reads ~`0:00:00.1`–`0:00:00.9`; the green `T=1.5` box while timecode reads ~`0:00:01.5`–`0:00:02.4`; the blue `T=3.0` box while ~`0:00:03.0`–`0:00:03.9`. The box label must agree with the on-screen timecode → sequencing + video-clock sync correct.
- **Probe 2:** before its delay and after its 1s window, each box is fully absent (no flash at t=0, no lingering box). → `fill-mode: both` correct.
- Set the **Gate verdict** in `FINDINGS.md`.

- [ ] **Step 7: GATE**

If any of probes 1–3 is FAIL, **stop here.** Do not start Task 2. Summarize the failure (which probe, observed vs expected) for the user — this means the timeline approach needs upstream fixes or a redesign. Only continue to Task 2 if the gate verdict is PASS.

---

## Task 2: Full 21-word kinetic clip

**Files:**
- Create: `exploration/video-subs/template.weave`
- Create: `exploration/video-subs/manifest.json`

Per-word values below are computed from `subtitles.json` (`start = timing[0]`, `dur = timing[1]-timing[0]`, rounded to ms) and the spec's rank table (rank 1–3 → `t-filler` 44px/700/white; 4–6 → `t-mid` 60px/800/white; 7–9 → `t-key` 80px/900 + cycling accent `c0=#FFD400`, `c1=#00E0FF`, `c2=#FF4D8D` advancing only on rank≥7 words — 7 such words → c0,c1,c2,c0,c1,c2,c0).

- [ ] **Step 1: Write the full-clip template**

Create `exploration/video-subs/template.weave`:
```html
<!DOCTYPE html><html><head><style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&display=swap');
html,body{margin:0;padding:0}
body{width:576px;height:1024px;background:#000;position:relative;overflow:hidden;
  font-family:'Montserrat',sans-serif;text-transform:uppercase}
video{position:absolute;inset:0;width:576px;height:1024px;object-fit:cover}
.w{position:absolute;left:24px;width:528px;top:46%;text-align:center;line-height:1.05;
  opacity:0;filter:drop-shadow(0 4px 10px rgba(0,0,0,.9));
  animation-name:wordPop;animation-timing-function:ease-out;animation-fill-mode:both}
.t-filler{font-size:44px;font-weight:700;color:#fff}
.t-mid{font-size:60px;font-weight:800;color:#fff}
.t-key{font-size:80px;font-weight:900}
.c0{color:#FFD400}.c1{color:#00E0FF}.c2{color:#FF4D8D}
@keyframes wordPop{
  0%{opacity:0;transform:translateY(18px) scale(.7)}
  18%{opacity:1;transform:translateY(0) scale(1.12)}
  30%{transform:scale(1)}
  82%{opacity:1;transform:scale(1)}
  100%{opacity:0;transform:scale(.92)}
}
</style></head><body>
  <video src="dude.mp4" muted></video>
  <div class="w t-mid"      style="animation-delay:0.240s;animation-duration:0.340s">Ehrlich</div>
  <div class="w t-mid"      style="animation-delay:0.580s;animation-duration:0.460s">gesagt,</div>
  <div class="w t-key c0"   style="animation-delay:1.041s;animation-duration:0.799s">Sonntagmorgen</div>
  <div class="w t-filler"   style="animation-delay:1.841s;animation-duration:0.186s">sind</div>
  <div class="w t-filler"   style="animation-delay:2.027s;animation-duration:0.180s">das</div>
  <div class="w t-key c1"   style="animation-delay:2.207s;animation-duration:0.353s">Beste</div>
  <div class="w t-key c2"   style="animation-delay:2.561s;animation-duration:1.039s">überhaupt.</div>
  <div class="w t-mid"      style="animation-delay:3.601s;animation-duration:0.440s">Kein</div>
  <div class="w t-key c0"   style="animation-delay:4.041s;animation-duration:0.440s">Handy,</div>
  <div class="w t-filler"   style="animation-delay:4.481s;animation-duration:0.439s">keine</div>
  <div class="w t-mid"      style="animation-delay:4.921s;animation-duration:0.520s">Planen,</div>
  <div class="w t-mid"      style="animation-delay:5.441s;animation-duration:0.520s">einfach</div>
  <div class="w t-filler"   style="animation-delay:5.961s;animation-duration:0.519s">nur</div>
  <div class="w t-key c1"   style="animation-delay:6.481s;animation-duration:0.740s">Ruhe,</div>
  <div class="w t-mid"      style="animation-delay:7.221s;animation-duration:0.739s">langsamer</div>
  <div class="w t-key c2"   style="animation-delay:7.961s;animation-duration:0.733s">Kaffee,</div>
  <div class="w t-mid"      style="animation-delay:8.694s;animation-duration:0.733s">gutes</div>
  <div class="w t-key c0"   style="animation-delay:9.427s;animation-duration:0.733s">Buch</div>
  <div class="w t-filler"   style="animation-delay:10.880s;animation-duration:0.387s">und</div>
  <div class="w t-mid"      style="animation-delay:11.267s;animation-duration:0.387s">los</div>
  <div class="w t-mid"      style="animation-delay:11.654s;animation-duration:0.387s">geht's.</div>
</body></html>
```

- [ ] **Step 2: Write the full-clip manifest**

Create `exploration/video-subs/manifest.json`:
```json
{ "render": { "width": 576, "height": 1024, "fps": 24, "duration": 12.1 } }
```

- [ ] **Step 3: Parse smoke-check**

Run: `weave-viewer-cli exploration/video-subs --validate`
Expected: exit 0, no parse errors.

- [ ] **Step 4: Render the silent clip**

Run: `weave-viewer-cli exploration/video-subs --record exploration/video-subs/out.mp4`
Expected: a ~12.1s MP4. Confirm: `ffprobe -v error -show_entries stream=width,height -of csv exploration/video-subs/out.mp4` → `...,576,1024`.

- [ ] **Step 5: Re-mux the source audio**

Run:
```sh
ffmpeg -y -i exploration/video-subs/out.mp4 -i exploration/video-subs/dude.mp4 \
  -map 0:v -map 1:a -c:v copy -c:a copy -shortest exploration/video-subs/final.mp4
```
Expected: `final.mp4` written. Confirm audio present: `ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv exploration/video-subs/final.mp4` → `...,aac`.

- [ ] **Step 6: Observe & record probes 4–8**

Open `final.mp4` and write each result into `FINDINGS.md` (Full clip table):
- **Probe 4:** filler (`das`, 700), mid (`Kein`, 800), key (`Sonntagmorgen`, 900) show visibly different stroke weights.
- **Probe 5:** `überhaupt.` renders the `ü` correctly (not tofu/missing glyph).
- **Probe 6:** at `Sonntagmorgen` (80px in a 528px box) — record whether it wraps to two centered lines, clips at the box edge, or overflows/pushes. Note which.
- **Probe 7:** `das` (~0.18s window) pops in and out without flicker or skipped frames.
- **Probe 8:** the `dude.mp4` footage fills the full 576×1024 frame via `object-fit: cover` without stretching/letterboxing.
- Spot-check timing: `Sonntagmorgen` should pop at ~1.04s, `geht's.` at ~11.65s, matching the audio.

---

## Task 3: Findings write-up & handoff

**Files:**
- Modify: `exploration/video-subs/FINDINGS.md`

- [ ] **Step 1: Complete the findings log**

Ensure both tables in `FINDINGS.md` have a Result for every probe, and the "Bugs / surprises for upstream" section lists each defect with the triggering fixture/word and observed-vs-expected. This file is the deliverable to relay to the upstream monorepo.

- [ ] **Step 2: Report**

Summarize to the user: gate verdict, which probes passed/failed, the final clip path (`exploration/video-subs/final.mp4`), and the upstream bug list. Nothing under `exploration/` is committed (gitignored by design) — confirm there are no unintended tracked changes with `git status --short`.

---

## Self-Review

**Spec coverage:**
- Timeline mechanism (layers, animation-delay, fill-mode) → Task 1 (gate) + Task 2.
- Single-word relay layout → Task 2 template (`.w` absolute, shared centered slot).
- rank → size/weight/color mapping incl. color cycle → Task 2 per-word classes (computed values shown).
- Canvas 576×1024/24fps/~12.1s → Task 1 & 2 manifests.
- Render + `-c:a copy` audio re-mux → Task 2 Steps 4–5.
- `--validate` as parse smoke-check → Task 1 Step 4, Task 2 Step 3.
- sync-test isolation fixture + probes 1–3 gate → Task 1.
- Bug-hunt checklist (8 probes) → Task 0 scaffold + recorded in Tasks 1 & 2.
- Phase 2 alpha / styles library / generator script → out of scope (not in any task). ✓

**Placeholder scan:** No TBD/TODO in steps; all file contents and commands are literal. (`FINDINGS.md` Result cells are intentionally blank — they are filled by observation, which is this plan's "test output.")

**Type/name consistency:** keyframe `wordPop` defined and used; classes `.w`, `.t-filler/.t-mid/.t-key`, `.c0/.c1/.c2` defined in CSS and used on every word; sync-test uses its own `show`/`.box`/`.b1-3`. Paths consistent and rooted at repo root throughout.

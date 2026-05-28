# Subtitle Scene Builder — Phase 1 design

**Date:** 2026-05-28
**Status:** Approved (brainstorming) — ready for implementation plan
**Scope:** One working subtitled clip that stress-tests the engine and produces upstream feedback.

## Goal

Establish the basics of agent-generated, kinetic HTML/CSS subtitles over a user-supplied
video, **find bugs**, and feed them upstream. The output is *one* pregenerated `template.weave`
plus a findings log — not a reusable styles library or a generator script (yet).

This is an **agent-heavy workflow**: an agent (Claude) reads the video + word-timed transcript
and writes a pregenerated page by hand. No runtime scripting, no `<script type="noiser">`.

## Non-goals (explicitly deferred)

- **Phase 2 — alpha / "text behind subject" depth.** `dude_alpha.mp4` (a grayscale matte)
  is parked. The depth effect stacks two unknowns (does the engine decode alpha video at all;
  straight-vs-premultiplied compositing) and waits until Phase 1 is proven.
- **Styles library.** Only the chosen "word-by-word pop" style (mock B) is built.
- **Generator script / SRT-VTT conversion.** The word-level JSON is kept as the native input.
- **Packaging** into a `weave-subtitle` skill or polished `docs/` guide — revisit later.

## Inputs (in `exploration/video-subs/`)

| File | What it is |
|---|---|
| `dude.mp4` | 576×1024 (9:16 portrait), h264 `yuv420p`, 24fps, 289 frames, 12.041s, **stereo AAC audio**. The footage. |
| `dude_alpha.mp4` | 720×1280, h264 `yuv420p` — a **grayscale matte, not an alpha channel**. Frame-aligned (24fps/289f/12.04s). Phase 2 only. |
| `subtitles.json` | **Word-level** transcript: array of `{ text, rank, timing:[start,end] }`, 21 words, German, spans 0.24s–12.041s. |

`subtitles.json` is richer than SRT/VTT (which are line-level): it carries per-word timing and a
`rank` 1–9 emphasis signal. Converting to SRT would discard both, so it is kept as-is.

## Architecture

### Timeline mechanism (pure HTML + CSS, no JS)

weave renders a fixed-duration timeline; every CSS animation is anchored to render-start (t=0).
- **Layer 0 (back):** `<video src="dude.mp4">` full-frame, `object-fit: cover`, muted, plays from t=0.
- **Layer 1 (front):** 21 word `<div>`s. Each: `animation: wordPop <dur>s <ease> <start>s both`
  with `start = timing[0]`, `dur = timing[1] - timing[0]`. Keyframes hide → pop-in → hold →
  pop-out **within the word's own window**; `animation-fill-mode: both` keeps it hidden before
  its delay and after it ends.
- **Canvas:** 576×1024, 24fps, ≈12.1s, via `manifest.json` `render`. Matches the source exactly.

This deliberately maximizes exercise of the lowest-coverage primitive: **21 sequential
`animation-delay`s + `fill-mode: both`** (zero fixtures today).

### Word display model — single-word relay

Word timings are contiguous (each word's end ≈ next word's start). One word is centered at a
time; it pops in, holds, then pops out as the next arrives. Words share the same centered slot;
because windows are contiguous, overlap at handoff is ≈0. No grouping logic.

*(Accumulating-phrase / CapCut-style line build-up is a deferred refinement — it needs phrase
grouping heuristics.)*

### rank → emphasis mapping (proposed, tweakable)

`rank` meaning is uncertain; this table is a documented default the agent can dial per style/prompt.
The intent is real variation across **size, weight, and color**.

| rank | font-size | font-weight | color |
|---|---|---|---|
| 1–3 (filler) | 44px | 700 | white |
| 4–6 (mid) | 60px | 800 | white |
| 7–9 (key) | 80px | 900 | **cycles** accent palette `["#FFD400","#00E0FF","#FF4D8D"]` as `palette[key_word_index % 3]`, where `key_word_index` increments only on rank≥7 words (8 such words in the data) |

Font: **Montserrat** (700/800/900 loaded as real weights via Google Fonts, fetched lazily by the
engine) — uppercase, centered, `filter: drop-shadow(...)` for legibility over footage.

**Allowed CSS only** (per `docs/feature-support.md`): flex + gap, position, transform
(scale/translate), opacity, `filter: drop-shadow`, color, font-size/weight. **Avoided:**
`border-radius` (failing), `text-shadow` (unlisted), `background-image` (failing), inline `<span>`
text styling (failing — words are flex/block elements, not inline spans).

### Per-word fade caveat

Keyframe in/out as a *percentage* of each word's duration means short words (e.g. `das`, 0.18s ≈
4 frames) fade faster than long words. Accepted for Phase 1; if it reads poorly, switch to
fixed-frame in/out percentages computed per word (the agent has the duration).

## Render + audio pipeline

weave output is **silent** in v1, so source audio is re-muxed as a final step:

```sh
weave-viewer-cli exploration/video-subs --record out.mp4
ffmpeg -i out.mp4 -i exploration/video-subs/dude.mp4 \
  -map 0:v -map 1:a -c:v copy -c:a copy -shortest final.mp4
```

Source audio is already AAC, so `-c:a copy` (no lossy re-encode). Run
`weave-viewer-cli exploration/video-subs --validate` first as a **parse smoke-check** only — with
no `id="template-*-N"` refs or `overrides.json` it validates that the file parses, not the timeline.

## Deliverables

**Built first — the isolation fixture:**

- `exploration/video-subs/sync-test/` — a 4-second, 3-box minimal fixture that isolates the
  timeline primitive *before* any styling exists:
  - `sync_bg.mp4` — a 576×1024 / 24fps / 4s background with a **burned-in timecode** (generated
    with `ffmpeg -f lavfi -i color=c=black:s=576x1024:d=4:r=24 -vf drawtext=...timecode ...`).
  - `template.weave` — three boxes at `animation-delay` 0 / 1.5 / 3s, each visible 1s, `fill: both`.
  - `manifest.json` — `render: { width:576, height:1024, fps:24, duration:4 }`.
  - **Pass test:** box N becomes visible exactly when the burned-in timecode reads its delay.
    Probes 1–3 below are decided **here**, on 3 boxes — not by debugging 21 sequenced words.

**Then the full clip (only if the fixture passes):**

- `exploration/video-subs/template.weave` — the generated scene (video layer + 21 timed words).
- `exploration/video-subs/manifest.json` — `render: { width:576, height:1024, fps:24, duration:12.1 }`.
- `exploration/video-subs/FINDINGS.md` — the real payoff: a probe checklist (below) with results
  recorded for upstream. `dude.mp4` / `dude_alpha.mp4` / `subtitles.json` already present.

## Bug-hunt / must-verify checklist (→ FINDINGS.md)

These are unproven against the fixture set; each is a probe, not an assumption. **Probes 1–3 are
decided on the `sync-test/` fixture first**; 4–8 on the full clip.

1. **`animation-delay` sequencing** — do staggered delays (0/1.5/3s in sync-test) fire on time?
2. **`animation-fill-mode: both`** — boxes hidden before delay and after end (no flash/stick)?
3. **`<video>` decode + clock sync** — does video playback position track the render clock? Read
   directly from the burned-in timecode in `sync-test`. (If it drifts, the whole approach reworks.)
4. **`font-weight`** — do 700/800/900 render as distinct weights? (`font-weight-computed` is failing.)
5. **Non-ASCII glyphs** — does `ü` (`überhaupt`) render correctly?
6. **Text overflow** — long word at large size (`Sonntagmorgen` @80px > 576px): wrap, clip, or push?
7. **Short-window animations** — does a ~0.18s (4-frame) pop animate sanely?
8. **`object-fit: cover`** on `<video>` — does it fill 576×1024 without distortion?

## Risks

- Any of probes 1–3 failing invalidates the timeline approach → replan (this is acceptable; the
  goal is to learn that early and cheaply).
- Render-clock vs video-decode-clock drift is the highest-impact unknown.
- Audio re-mux assumes `final.mp4` duration matches; `-shortest` guards minor mismatch.

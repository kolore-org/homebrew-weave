---
name: weave-broll
description: Generate A/B-roll video footage from a text prompt using the hosted fal MCP, then overlay text + sprinkles and record an MP4 with weave-viewer-cli. Trigger when a user wants to generate a video, create B-roll/footage from a description, or make a captioned clip from scratch on macOS.
---

# Weave B-roll Generation Skill (Experimental)

This skill turns a text idea — *"a video about cats based on 'Cats are mysterious creatures'"* —
into a finished clip: it **generates footage** with a text-to-video model via the **hosted fal
MCP**, then composes the requested on-screen **text + sprinkles** over it and records an MP4 with
`weave-viewer-cli` on macOS.

It is the "make me a video" counterpart to [`/weave-subtitle`](../weave-subtitle/SKILL.md), which
assumes you already have footage. This skill produces the footage first, then reuses
`weave-subtitle`'s overlay patterns for the captions.

> [!IMPORTANT]
> This skill does **not** build or host any MCP server. It integrates the existing **hosted,
> stateless** fal MCP. It is **opt-in and user-keyed**: you bring your own fal API key, you
> approve every paid run.

---

## 🚀 1. Setup & Installation (macOS Only)

### A. The renderer (same chain as `/weave-subtitle`)
```bash
brew tap kolore-org/weave
brew install kolore-org/weave/weave-viewer
```
This installs `weave-viewer-cli` and pulls in `ffmpeg` (required for `--record`). Verify with:
```bash
weave-viewer-cli . --validate
```

### B. The fal MCP (opt-in — request a token first)
Footage generation runs through fal's hosted MCP server. This is a **paid, opt-in** integration —
**do not register it or spend money without explicit user consent.** Follow this protocol:

1. **Explain & ask.** Tell the user generation needs a fal account and API key, that fal's MCP
   server itself is free and stateless (the key is sent per-request in the `Authorization`
   header, never stored or logged), but **each model run costs money** billed by fal.
   Ask: *"Do you have a fal API key, and may I register the fal MCP server? Reply YES to proceed."*
2. **Get a key.** Direct the user to create a key in the fal.ai dashboard (Keys / API Keys).
3. **Register the server** (the user runs this — it carries their secret key):
   ```bash
   claude mcp add --transport http fal-ai \
     https://mcp.fal.ai/mcp \
     --header "Authorization: Bearer <FAL_KEY>"
   ```
4. **Verify** the server is reachable:
   ```bash
   claude mcp list
   ```
   Expect `fal-ai` to appear and connect. The MCP tools (below) then become available in-session.

> [!NOTE]
> The hosted server exposes 9 tools. Discovery: `search_models`, `get_model_schema`,
> `get_pricing`, `search_docs`. Execution: `run_model`, `submit_job`, `check_job`. Utility:
> `upload_file`, `recommend_model`. This skill uses the discovery tools + `submit_job`/`check_job`.

---

## 💸 2. Cost & Consent Protocol

Every `submit_job` spends real money. Treat it like the Whisper opt-in in `/weave-subtitle`:
surface the cost, then wait for an explicit YES.

Before **any** `submit_job`:
1. Identify the chosen model (`endpoint_id`) and call `get_pricing` for it.
2. State plainly: *"Model `<id>` costs ~$X per <unit>; generating <N>s of footage ≈ $Y. Reply
   YES to spend it and generate."*
3. **Stop and wait.** Only call `submit_job` after the user confirms.
4. For A/B-roll (multiple clips), tally the **total** estimate and confirm the total, not each
   clip silently.

Never auto-retry a failed paid job without re-confirming.

---

## 🎥 3. Generating B-roll From Text

The footage step, using the fal MCP tools. Video models are long-running, so always use
**`submit_job` + `check_job`** (not `run_model`) to avoid timeouts.

1. **Pick a model.** Call `recommend_model` describing the need (e.g. *"short cinematic
   text-to-video clip of a cat, vertical 9:16"*), or `search_models` with category
   `"text-to-video"`. Present the user a sensible default and let them override.
2. **Validate the input.** Call `get_model_schema` for the chosen `endpoint_id` and build a valid
   input object — typically `{ "prompt": "...", "aspect_ratio": "9:16", "duration": 5, ... }`.
   **Match `aspect_ratio` to the render target** (9:16 → 576×1024, 16:9 → 1280×720, 1:1 →
   1080×1080).
3. **Confirm cost** per §2.
4. **Submit:** `submit_job(endpoint_id, input)` → returns a `request_id`.
5. **Poll:** call `check_job(request_id)` until it reports complete. On completion it returns the
   **video URL**.
6. **Download** into the (gitignored) outputs tree — never alongside source fixtures:
   ```bash
   mkdir -p outputs/<project>
   curl -L "<video_url>" -o outputs/<project>/broll-01.mp4
   ```

**A/B-roll:** generate the main shot plus one or two cutaways as separate short clips
(`broll-01.mp4`, `broll-02.mp4`, …). You can layer them with `z-index` in the template (see the
`subtitles-depth` example) or sequence them by giving each `<video>` its own visibility window.

> [!NOTE]
> Text-to-video output is **silent** and has **no narration**, so there is no transcript and no
> Whisper step. On-screen text comes from the user (next section), timed by hand.

---

## ✨ 4. Adding Text + Sprinkles

With footage in hand, the overlay is exactly the `/weave-subtitle` workflow — use that skill's
verified patterns. The only difference: there's no transcript, so **the user supplies the on-screen
copy** (e.g. "Cats are mysterious creatures") and you **hand-author the timing cues** across the
clip's duration (the manual-timing fallback from `/weave-subtitle` §3, Option 3).

- **Text:** reuse the Pop (word-by-word), Cue (grouped phrase), or Advanced rank-based patterns.
  Split the copy into words/cues and spread `animation-delay`/`animation-duration` across the clip
  length so captions land while the relevant footage is on screen.
- **Sprinkles:** the inline-SVG **Doodle** pattern from `/weave-subtitle` §4.5 — squiggles, stars,
  arrows that fade in next to emphasized words. Keep SVGs **inline** with **inline presentation
  attributes** (the engine doesn't load external SVGs or cascade CSS into `<svg>`).

Author the project:
```
outputs/<project>/
├── template.weave    # references ../<project>/broll-01.mp4 (relative path), text + sprinkle overlays
└── manifest.json     # { "render": { "width": 576, "height": 1024, "fps": 24, "duration": <clip secs> } }
```
Reference the downloaded clip by **relative path** and set `manifest.json` `width`/`height`/`fps`/
`duration` to match the footage and aspect ratio.

> [!TIP]
> When designing the text/sprinkle styling, enable the `frontend-design@claude-plugins-official`
> plugin and iterate live in Chrome DevTools, just as in `/weave-subtitle` §2.

---

## 🎬 5. Render

The footage is silent, so this is a single step — no audio re-mux needed:
```bash
weave-viewer-cli outputs/<project> --record outputs/<project>/final.mp4 \
  --width 576 --height 1024 --fps 24 --duration <clip secs>
```

> [!TIP]
> Want a music bed? Generate or supply an audio file and mux it in as a follow-up:
> `ffmpeg -y -i outputs/<project>/final.mp4 -i music.mp3 -map 0:v -map 1:a -c:v copy -shortest outputs/<project>/final_music.mp4`.
> This is optional and outside the core path.

---

## ⚠️ 6. Notes & Limits

- **Engine bugs apply.** The overlay obeys the same constraints as `/weave-subtitle` §5: no
  `filter: drop-shadow` on opacity transitions, embed SVGs inline with inline attributes, use
  `display:inline-block` + margin for word spacing, and keep `<video>` simple and full-canvas
  (`position:absolute; inset:0`) to avoid host FFI panics.
- **Output-folder policy.** Generated clips, ffmpeg intermediates, and renders all live under
  `outputs/` (gitignored) or `/tmp/` — never alongside source fixtures, in `assets/`, or in
  `examples/`. Nothing fal produces gets committed.
- **Cost lives with the user.** fal bills per run against the user's key; always confirm spend
  (§2) before submitting.
- **macOS / Apple Silicon only**, same as the rest of the toolchain.

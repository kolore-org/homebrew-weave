---
name: weave-subtitle
description: Create, author, and record video subtitles/captions using weave-viewer-cli. Trigger when a user wants to style subtitles, generate a subtitle template, transcribe audio, or render subtitled videos to MP4 on macOS.
---

# Weave Subtitles Expert Skill (Experimental)

This skill provides expert instructions, templates, and best practices for creating kinetic, beautifully animated HTML/CSS subtitles over background videos, and recording them to MP4 using `weave-viewer-cli` on macOS.

---

## 🚀 1. Setup & Installation (macOS Only)

The `weave-viewer` tool chain is currently experimental and **macOS (Apple Silicon / M-series ARM64) only**.

### Installation from Homebrew
To set up the CLI, use the official qualified formula tap:
```bash
brew tap kolore-org/weave
brew install kolore-org/weave/weave-viewer
```

> [!NOTE]
> This automatically installs `weave-viewer-cli` in your PATH, links all required runtime shaders and dylibs under `/opt/homebrew/Cellar/weave-viewer`, and pulls in **`ffmpeg`** as a required dependency. `ffmpeg` is strictly required to record/save videos (`--record`).

### Verifying the Installation
Run the following command to check if the tool is ready and can validate templates without needing a GPU:
```bash
weave-viewer-cli . --validate
```

---

## 🎨 2. Interactive Browser-Based Design Workflow

Because `weave` supports standard HTML5 and a rich subset of CSS, you do not need to rely on static previews. Designers can live-design and iterate directly in their web browser.

### A. Suggesting the CSS Plugin
When designing or modifying subtitle aesthetics, the agent should recommend enabling the Claude official **frontend-design plugin** (`frontend-design@claude-plugins-official`). This plugin helps the agent generate professional, intentional typography, sophisticated HSL color palettes, and polished spacing, avoiding generic or plain layouts.

### B. Live Brower Iteration
Instruct the designer to follow this workflow to build subtitles:
1. Open the project's `template.weave` file in a desktop browser (like **Google Chrome**).
2. Because it is standard HTML and CSS, the browser will render the static components perfectly.
3. Open the browser's **DevTools (Inspect)** or use live-styling plugins (like **Stylebot** or **CSS Peeper**) to test colors, margins, fonts, and layout parameters interactively.
4. Once the styles look perfect, copy the CSS changes back into `template.weave` and run the recorder.

---

## 🎙️ 3. Transcribing Video-Only Inputs (Soft Suggestions)

If a user provides a video-only input with no subtitle timing data, the agent should softly suggest transcription workflows to generate a compliant word-level `subtitles.json` file.

### Option A: Whisper MCP Server (Automated)
If you have an MCP server like **`whisper-mcp`** or a similar audio-to-text Model Context Protocol server configured, use it to directly transcribe the video. This retrieves word-level timestamps directly into your conversation context.

### Option B: Local ffmpeg + Whisper Workflow
Alternatively, guide the user or perform the following manual steps:
1. **Extract Audio**: Extract a lightweight MP3 file from the video:
   ```bash
   ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 2 output.mp3
   ```
2. **Transcribe**: Run the MP3 through a local OpenAI Whisper CLI or an API-based script to get word-level timestamps.
3. **Format JSON**: Construct a Weave-compliant `subtitles.json` array containing `{ text, rank, timing:[start, end] }`:
   ```json
   [
     { "text": "Ehrlich", "rank": 4, "timing": [0.24, 0.58] },
     { "text": "gesagt,", "rank": 4, "timing": [0.58, 1.04] }
   ]
   ```
   *Note: `rank` is an integer from 1 (lowest) to 9 (highest) representing emphasis.*

---

## 📝 4. Subtitle Design Examples & Effects

Weave supports a wide range of kinetics. Here are five verified patterns drawn from our subtitle examples directory:

### 1. Simple Pop (Word-by-Word)
Best for clean, modern, zero-latency captions. It shows one word at a time by holding opacity 1 for the exact duration of the word, then snapping to 0. This bypasses text shadow and glyph-clipping bugs.

```html
<!DOCTYPE html><html><head><style>
@import url('https://fonts.googleapis.com/css2?family=Cabin+Sketch:wght@700&display=swap');
html,body{margin:0;padding:0}
body{width:576px;height:1024px;background:#000;position:relative;overflow:hidden;
  font-family:'Cabin Sketch',cursive;color:#fff;text-align:center}
video{position:absolute;inset:0;width:576px;height:1024px;object-fit:cover}
.w{position:absolute;left:24px;width:528px;top:74%;
  font-size:64px;font-weight:700;line-height:1.2;opacity:0;
  animation-name:show;animation-timing-function:linear;animation-fill-mode:forwards}
@keyframes show{
  0%, 99.99% { opacity:1 }
  100% { opacity:0 }
}
</style></head><body>
  <video src="dude.mp4" muted></video>
  <div class="w" style="animation-delay:0.24s;animation-duration:0.34s">Ehrlich</div>
  <div class="w" style="animation-delay:0.58s;animation-duration:0.46s">gesagt,</div>
</body></html>
```

### 2. Cue-Based (Grouped Phrases)
Groups 2-5 words along natural punctuation boundaries. This reduces cognitive load on viewers.

```html
<!-- C sits in a center-safe zone. Cues do not overlap because timings are contiguous. -->
<style>
.c{position:absolute;left:24px;width:528px;top:66%;
  font-size:54px;font-weight:700;line-height:1.15;opacity:0;
  animation-name:show;animation-timing-function:linear;animation-fill-mode:forwards}
@keyframes show{
  0%, 99.99% { opacity:1 }
  100% { opacity:0 }
}
</style>
<div class="c" style="animation-delay:0.240s;animation-duration:0.800s">Ehrlich gesagt,</div>
<div class="c" style="animation-delay:1.041s;animation-duration:2.559s">Sonntagmorgen sind das Beste überhaupt.</div>
```

### 3. Karaoke Highlight
The phrase remains visible, but colors transition dynamically through three states as words are spoken: upcoming (subdued) ➔ active (high contrast) ➔ past (black or dark gray).

```html
<style>
.cue{position:absolute;left:15%;width:70%;top:66%;font-size:54px;font-weight:700;
  opacity:0;animation-name:cueshow;animation-timing-function:linear;animation-fill-mode:forwards}
@keyframes cueshow{ 0%, 99.99% { opacity:1 } 100% { opacity:0 } }
.w{color:rgba(255,255,255,.4);display:inline-block;margin:0 6px;
  animation-name:speak;animation-timing-function:step-end;animation-fill-mode:forwards}
@keyframes speak{
  from { color:#00D900 } /* Active State (bright green) */
  to   { color:#111111 } /* Past State (subdued dark gray) */
}
</style>
<div class="cue" style="animation-delay:0.240s;animation-duration:0.800s">
  <span class="w" style="animation-delay:0.240s;animation-duration:0.340s">Ehrlich</span>
  <span class="w" style="animation-delay:0.580s;animation-duration:0.460s">gesagt,</span>
</div>
```

### 4. Advanced Motion & Emphasis (Rank-Based)
Maps Weave transcript `rank` values to font weights, sizes, and colors, animating entry points with elastic spring curves.

```html
<style>
/* Rank tiers */
.r-sm{font-size:32px;color:#f5d97e}                /* Rank 1-3: small dim yellow */
.r-md{font-size:48px;color:#ffffff}                /* Rank 4-6: medium white */
.r-lg{font-size:72px;color:#00d9ff;font-weight:700} /* Rank 7-9: large bold cyan */

/* Entry animations with cubic-bezier */
.w{display:inline-block;margin:0 6px;opacity:0;animation-duration:0.45s;animation-fill-mode:forwards}
.a-pop     { animation-name:pop;     animation-timing-function:cubic-bezier(.34,1.56,.64,1) } /* Spring pop */
.a-slide-l { animation-name:slideL;  animation-timing-function:cubic-bezier(.22,1,.36,1) }
.a-slide-up{ animation-name:slideUp; animation-timing-function:cubic-bezier(.22,1,.36,1) }

@keyframes pop { 0% { opacity:0; transform:scale(.4) } 100% { opacity:1; transform:scale(1) } }
@keyframes slideL { 0% { opacity:0; transform:translateX(-80px) } 100% { opacity:1; transform:translateX(0) } }
@keyframes slideUp { 0% { opacity:0; transform:translateY(40px) } 100% { opacity:1; transform:translateY(0) } }
</style>
<div class="cue" style="animation-delay:1.041s;animation-duration:2.559s">
  <span class="w r-lg a-pop"      style="animation-delay:1.041s">Sonntagmorgen</span>
  <span class="w r-sm a-slide-l"  style="animation-delay:1.841s">sind</span>
  <span class="w r-lg a-slide-up" style="animation-delay:2.207s">Beste</span>
</div>
```

### 5. SVG Doodle Accents
Adds playful hand-drawn SVG shapes directly adjacent to specific emphasized words.

```html
<!-- Absolute positioned SVG doodle fades in on delay -->
<style>
.w{display:inline-block;position:relative;margin:0 5px}
.doodle{position:absolute;pointer-events:none;overflow:visible;opacity:0;
  animation-name:doodlein;animation-duration:0.25s;animation-fill-mode:forwards}
@keyframes doodlein{ to { opacity:1 } }
.dood-squiggle{left:0;right:0;bottom:-12px;height:16px;width:100%}
</style>
<span class="w">gesagt,<svg class="doodle dood-squiggle" viewBox="0 0 100 16" preserveAspectRatio="none" style="animation-delay:0.58s"><path d="M2 8 Q 14 1, 26 8 T 50 8 T 74 8 T 98 8" fill="none" stroke="#ff4d8d" stroke-width="3.5" stroke-linecap="round"/></svg></span>
```

---

## ⚠️ 5. Known Engine Bugs & Workarounds

Avoid designing templates that break the core engine. Always follow these rules:

1. **NO `filter: drop-shadow` on opacity transitions**: Applying standard CSS drop-shadow filters on spans that animate their `opacity` from `0` to `1` causes partial-opacity glyphs to be clipped or truncated by the engine. Switch to solid block backgrounds or step-animations without fading.
2. **NO `<img>` for SVGs**: The engine's image loader does not recognize or render external SVGs in `<img src="doodle.svg">`. Always embed SVGs **inline** in the HTML.
3. **NO CSS Cascade inside `<svg>`**: CSS class rules defined in `<style>` will not cascade to SVG `<path>` children. Always declare presentation attributes (`fill="..."`, `stroke="..."`, `stroke-width="..."`) **inline** directly on the SVG nodes.
4. **Avoid standard `<span>` spacing issues**: A known engine bug drops normal whitespace characters between inline `<span>` elements. Work around this by making subtitle word-wrappers `display: inline-block` and applying an explicit `margin` or layout `gap` between them.
5. **Video Playback Panic**: Refrain from using `<video src="...">` directly in unregistered or layout-complex nodes, as the host FFI may panic (`Host returned no intrinsic dimensions`). Keep background videos simple and full-canvas (`position: absolute; inset:0`).

---

## 🎬 6. Render & Re-muxing Pipeline

Once the `.weave` folder is created and fully authored, use this two-step recording workflow:

### Step 1: Render the Silent MP4
Run the recorder on your project folder. The output MP4 will be silent because the v1 engine discards audio tracks.
```bash
weave-viewer-cli path/to/project --record outputs/silent_render.mp4 --width 576 --height 1024 --fps 24 --duration 12.1
```

### Step 2: Re-mux Audio with ffmpeg
Use `ffmpeg` (which Homebrew installed automatically) to copy the original high-quality audio track back over the visual render:
```bash
ffmpeg -y -i outputs/silent_render.mp4 -i path/to/project/dude.mp4 -map 0:v -map 1:a -c:v copy -c:a copy -shortest outputs/final_subtitled.mp4
```

> [!TIP]
> This command uses `-c:v copy` and `-c:a copy` to instantly merge the audio and video tracks without lossy re-encoding, taking less than a second to complete.

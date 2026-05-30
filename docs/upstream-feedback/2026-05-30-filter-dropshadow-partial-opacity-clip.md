# weave-viewer-cli — `filter:drop-shadow` clips glyphs to upper half when the element's opacity is animating

**Tested:** locally-built `weave-viewer-cli` from `../hexer` branch `fix/graceful-font-fallback`
(today's date). Also reproduces against released v0.1.5.
**Severity:** **blocker** for any kinetic-text template that fades words in/out with a drop-shadow.
**Visible symptom:** "bottom half of every letter is missing while the word fades in or out."

## TL;DR

When an element has `filter:drop-shadow(...)` **and** is being painted at partial opacity
(opacity changing under a CSS animation), the engine clips glyph rendering to roughly the
top half of each letter — every pixel below the baseline-ish line is dropped. At
opacity 1.0 (steady-state between keyframes that hold opacity at 1) the same element
renders correctly.

Remove the `filter:drop-shadow` line and the clip disappears at every opacity value.

## Minimum repro (one paste)

```bash
mkdir -p /tmp/clip && cd /tmp/clip
cat > template.weave <<'HTML'
<!DOCTYPE html><html><head><style>
html,body{margin:0;padding:0}
body{width:576px;height:1024px;background:#000;position:relative;overflow:hidden;
  font-family:sans-serif;text-transform:uppercase}
.w{position:absolute;left:24px;width:528px;top:46%;text-align:center;line-height:1.05;
  opacity:0;filter:drop-shadow(0 4px 10px rgba(0,0,0,.9));
  animation-name:fade;animation-duration:4s;animation-fill-mode:both;
  font-size:60px;font-weight:800;color:#fff}
@keyframes fade{0%{opacity:0}20%{opacity:1}80%{opacity:1}100%{opacity:0}}
</style></head><body>
  <div class="w">PLANEN</div>
</body></html>
HTML
cat > manifest.json <<'JSON'
{"render":{"width":576,"height":1024,"fps":24,"duration":3}}
JSON

weave-viewer-cli . --record out.mp4
# Extract two frames: one mid-fade (clipped), one steady (full)
ffmpeg -ss 0.5 -i out.mp4 -frames:v 1 mid-fade.png   # clipped
ffmpeg -ss 0.9 -i out.mp4 -frames:v 1 steady.png     # full glyphs
```

## Behavior matrix

Using the template above, varying ONE knob at a time:

| Variant | mid-fade frame (t=0.5) | steady frame (t=0.9) |
|---|---|---|
| Buggy (filter present, opacity animation) | **glyph rows y=518..540 → 23px tall (≈ 50% of cap-to-baseline)** | full glyph rows y=484..526 → 43px tall |
| Same template, **no filter** | full 43px | full 43px |
| Filter present, **no animation** (`opacity:1` static) | full 43px | n/a |

So the bug requires the *intersection* of:
1. `filter:drop-shadow(...)` on the element, AND
2. the element's `opacity` currently being interpolated by a running animation (i.e.
   the value is *neither* the initial keyframe value *nor* a hold keyframe value, but
   somewhere mid-transition).

When opacity reaches 1.0 and stays there (between two `opacity:1` keyframes), the same
element renders its glyphs fully. The clip returns the moment the next opacity
transition begins.

## What this looks like in practice (subtitle template)

`examples/subtitles/template.weave` is the Phase 1 kinetic-subtitle template — 21 word
divs, each animated with `wordPop` (a fade in / fade out pop) and each carrying
`filter:drop-shadow(0 4px 10px rgba(0,0,0,.9))`. Every word spends meaningful time in
the fade-in (0–18% of its `animation-duration`) and the fade-out (82–100%) windows. In
those windows the rendering clips the bottom half of every letter. The viewer sees
"text cut at the bottom" for most of each word's appearance.

A frame at t=5.2 s (PLANEN mid-pop), bottom half of each glyph missing — only the top
half ("PL ANEN" with cropped letters) renders:

![clipped](../../outputs/strip-video/weave-PLANEN-t5.2.png) <!-- gitignored; regen with the repro -->

## Diagnosis hypotheses

Without engine source, three plausible mechanisms:

1. **Drop-shadow backdrop sized to the opaque pass.** The drop-shadow filter likely
   rasterizes the element into an offscreen buffer at full opacity, then composites the
   buffer with the requested opacity. If the offscreen buffer's *vertical extent* is
   recomputed from glyph metrics differently when opacity isn't 1 (e.g. the bounding
   box is taken from the line-box height rather than the actual glyph ink extent), the
   buffer would be sized to the line-box (~63px for 60px font / line-height 1.05) and
   then the glyphs (which naturally extend a few px below the line-box for the
   ascender/descender) would be cropped — and the lower half of uppercase letters
   sitting around the line-box bottom edge would be exactly what's lost.
2. **Filter pass + alpha multiplication order.** If the filter's alpha-multiplication
   happens before the glyph rasterization in some shader path and after in another,
   and the engine takes the "partial opacity" branch differently from "opacity = 1",
   the rasterization rect could be inheriting the wrong extents.
3. **Cached glyph atlas reused at the wrong region.** The element's render texture
   might be cached with the line-box dimensions at first paint (when opacity was 0?),
   and reused for all subsequent partial-opacity frames; the steady-state opacity=1
   path might force a re-rasterization that uses the correct ink-extent rect.

The fact that the clip cleanly disappears the moment opacity hits 1.0 and stays
there is the strongest signal: the engine has at least two glyph-render code paths
and they disagree on the y-extent rect.

## Asks for upstream

1. Make `filter:drop-shadow` use the same glyph-ink-extent bounding box at any
   opacity, not just at opacity = 1.
2. Until fixed, consider a render-time warning when an element has both
   `filter:drop-shadow` and an animation that modifies `opacity` — that combo is the
   exact viral-text shorthand template authors reach for first.
3. As a workaround documented in `feature-support.md`: prefer `text-shadow` over
   `filter:drop-shadow` for shadow effects on animated text until the filter path is
   fixed. (Quick sanity test would be to swap our template and re-render — see below.)

## Workaround verification (template author side)

Swapping `filter:drop-shadow(0 4px 10px rgba(0,0,0,.9))` for
`text-shadow: 0 4px 10px rgba(0,0,0,.9)` on the `.w` rule produces an equivalent visual
result (per-letter shadow rather than per-element shadow) and bypasses the bug entirely
because the partial-opacity branch isn't dependent on the filter pass. Not yet
re-rendered as of this report — flagged as the recommended template fix in our notes.

## Status table (engine-side issues this session)

| Issue | Where | Status |
|---|---|---|
| `<video>` FFI panic at `src/layout/mod.rs:2309:35` | layout | ✅ fixed in v0.1.4 |
| `<video>` PathResolver doesn't search project dir | media/host | ✅ fixed in v0.1.5 |
| `<video>` IOSurface feature gate | wgpu adapter | ✅ fixed in v0.1.5 |
| Default-font load failure SIGABRTs `--record` | font subsystem | ✅ fixed on branch `fix/graceful-font-fallback` |
| `font-weight > 400` not applied to glyphs | embedded-fonts faces | ❌ pending (separate report) |
| **`filter:drop-shadow` + animated opacity → glyph clip** | **filter / glyph rasterizer** | **❌ pending (this report)** |

# weave-viewer-cli — `text-align:center` drops to left-aligned on wrapped lines

**Tested:** locally-built `weave-viewer-cli` from `../hexer` branch
`fix/graceful-font-fallback` (today). Also reproduces against released v0.1.5.
**Severity:** any centered text that wraps reads as left-aligned. Visual divergence
from Chrome / CSS spec.

## TL;DR

A block with `text-align:center` correctly centers text that fits on a single line.
The moment the text wraps, the engine **left-aligns every wrapped line** at the box's
content-left edge instead of centering each line independently. Chrome (and the CSS
Text spec) centers each broken line separately.

## Minimum repro (one paste)

```bash
mkdir -p /tmp/center && cd /tmp/center
cat > template.weave <<'HTML'
<!DOCTYPE html><html><head><style>
html,body{margin:0;background:#222;color:#fff;font-family:sans-serif}
.box{width:380px;margin:24px auto;border:2px solid #f0f;text-align:center;font-size:36px;line-height:1.2}
</style></head><body>
  <div class="box">Short text</div>
  <div class="box">This is a much longer sentence that will definitely wrap to multiple lines.</div>
</body></html>
HTML
cat > manifest.json <<'JSON'
{"render":{"width":900,"height":600,"fps":24,"duration":1}}
JSON
weave-viewer-cli . --record out.mp4 --width 900 --height 600 --fps 24 --duration 1
ffmpeg -ss 0.5 -i out.mp4 -frames:v 1 weave.png

# Chrome control:
chrome --headless=new --hide-scrollbars --window-size=900,600 \
  --screenshot=chrome.png "file://$PWD/template.weave"  # or rename to .html
```

## Observed vs expected

In the second box (the longer sentence that wraps):

| Renderer | Line 1 "This is a much longer" | Line 2 "sentence that will" | Line 3 "definitely wrap to" | Line 4 "multiple lines." |
|---|---|---|---|---|
| **Chrome** | centered in box | centered in box (different left margin from line 1) | centered in box | centered in box |
| **weave-viewer-cli** | starts at box's left edge | starts at box's left edge | starts at box's left edge | starts at box's left edge |

All four lines in weave start at exactly the same `x` (the box's content-left position),
which is the visual signature of `text-align:left`. The first/longest line in Chrome
starts roughly where weave puts every line, but each subsequent shorter line is shifted
right to keep it centered.

The single-line cases (`box` containing "Short text", and the same long sentence in a
wider 760 px box where it fits) center identically in both renderers — so the
`text-align:center` rule IS being parsed and applied, just not to individual wrapped
lines.

## Screenshots

Side-by-side, same HTML, magenta box outline = box bounds, cyan line = page horizontal
center:

- `outputs/text-align-bug/chrome.png` — every line of the wrapped box independently centered
- `outputs/text-align-bug/weave.png` — every line of the wrapped box left-aligned

(Both 900×700; gitignored under the output-folder policy; regen with the script above.)

## Why this matters for subtitle / caption use cases

Subtitle templates routinely use a fixed-width centered text container and let cues
wrap when phrases run long. With this bug, any cue longer than one line reads as a
left-aligned block sitting against the left of the caption area, even though the
template asked for centered captions. The viewer can tell something is off but not
why, because *short* cues (and most ad-hoc tests) center correctly.

Repro'd in the kinetic-subtitle example at `examples/subtitles-cues/template.weave` —
cues 2 ("Sonntagmorgen sind das Beste überhaupt."), 3 ("Kein Handy, keine Planen,"),
and 5 ("langsamer Kaffee, gutes Buch") all wrap and all read left-aligned, while
single-line cues 4 ("einfach nur Ruhe,") and 6 ("und los geht's.") are correctly
centered.

## Likely fix surface

CSS Text — the line-box assembly step. Sounds like the engine computes the inline-box
content extent once for the whole paragraph and centers THAT, rather than computing the
horizontal position per line-box after wrapping. Per CSS Text Module Level 3
([§7.1](https://www.w3.org/TR/css-text-3/#text-align-property)), `text-align` applies
to *each* line box independently.

## Asks for upstream

1. Apply `text-align: center | right | justify` per line-box after wrapping, matching
   CSS Text Level 3.
2. Until fixed, document the gap in `docs/feature-support.md` — currently the support
   matrix lists *Text with Ahem* with two verified fixtures, but doesn't call out that
   `text-align:center` works only on non-wrapping content.

## Status table (engine-side issues this session)

| Issue | Status |
|---|---|
| `<video>` FFI panic at `src/layout/mod.rs:2309:35` | ✅ fixed in v0.1.4 |
| `<video>` PathResolver doesn't search project dir | ✅ fixed in v0.1.5 |
| `<video>` IOSurface feature gate | ✅ fixed in v0.1.5 |
| Default-font load failure SIGABRTs `--record` | ✅ fixed on `fix/graceful-font-fallback` |
| `filter:drop-shadow` + animated opacity → glyph clip | ❌ pending |
| `font-weight > 400` not applied to glyphs | ❌ pending |
| **`text-align:center` not applied to wrapped lines** | **❌ pending (this report)** |

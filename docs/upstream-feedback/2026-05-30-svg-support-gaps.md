# weave-viewer-cli — SVG support gaps

**Tested:** locally-built `weave-viewer-cli` from `../hexer` branch
`fix/graceful-font-fallback` (today). Also reproduces against released v0.1.5.
**Severity:** medium. Inline SVG with fully-inline presentation attributes works
fine; the gaps below trip up templates that follow standard CSS-styling patterns
or load SVG via `<img>`.

## TL;DR

Three concrete gaps surfaced while authoring a per-word doodle-accent subtitle
template (`examples/subtitles-doodles/`):

1. **CSS rules do not cascade into SVG child elements.** A rule like
   `.doodle path { fill:none; stroke:#ff4d8d; stroke-width:3.5 }` is silently
   ignored on the child `<path>`. The path renders with the SVG default
   (`fill:black; stroke:none`), which makes line-art doodles invisible.
   Workaround: put every presentation attribute inline on the `<path>` element.

2. **`<img src="*.svg">` is not loaded.** The image loader emits
   `LazyLoadReplacedSource: unknown extension for '...square.svg'` and the
   `<img>` renders as an empty replaced-element box. Chrome loads it fine.

3. **(Stretch) CSS animation of SVG presentation attributes
   (`stroke-dashoffset`, etc.) does not appear to fire.** Animating dashoffset
   to draw a path in over time is the classic CSS hand-drawn-doodle trick.
   In weave the path stays at its initial dashoffset value (invisible if
   dasharray ≥ length) for the whole render. Workaround: animate `opacity` on
   the `<svg>` element instead (CSS animation DOES apply to the SVG container)
   and accept a pop-in rather than a draw-in.

## Minimum repro (one paste — covers gaps 1 and 2)

```bash
mkdir -p /tmp/svg-bug && cd /tmp/svg-bug
cat > template.weave <<'HTML'
<!DOCTYPE html><html><head><style>
html,body{margin:0;background:#222;color:#fff;font-family:sans-serif}
.row{padding:20px;border-bottom:1px solid #444}
.lbl{font-family:monospace;color:#aaa;padding-bottom:8px}
.box{border:2px dashed #f0f;width:300px;height:120px;display:flex;align-items:center;justify-content:center}
/* This rule is what fails in gap 1 — engine renders the path as fill:black */
.via-css path { fill:none; stroke:#ff4d8d; stroke-width:4; stroke-linecap:round }
</style></head><body>
  <div class="row">
    <div class="lbl">A: inline svg, attributes inline on path — works in weave ✓</div>
    <div class="box">
      <svg width="200" height="80" viewBox="0 0 200 80">
        <path d="M10 40 Q 50 10, 100 40 T 190 40" fill="none" stroke="#ff4d8d" stroke-width="4" stroke-linecap="round"/>
      </svg>
    </div>
  </div>
  <div class="row">
    <div class="lbl">B: same path, styled via CSS class — gap 1: invisible in weave</div>
    <div class="box">
      <svg width="200" height="80" viewBox="0 0 200 80" class="via-css">
        <path d="M10 40 Q 50 10, 100 40 T 190 40"/>
      </svg>
    </div>
  </div>
  <div class="row">
    <div class="lbl">C: external svg via &lt;img src&gt; — gap 2: empty replaced-element box in weave</div>
    <div class="box">
      <img src="square.svg" alt="external svg" width="200" height="80"/>
    </div>
  </div>
</body></html>
HTML
cat > square.svg <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="80" viewBox="0 0 200 80">
  <rect x="10" y="10" width="180" height="60" fill="#00d9ff" stroke="#ffd400" stroke-width="4"/>
</svg>
SVG
cat > manifest.json <<'JSON'
{"render":{"width":900,"height":600,"fps":24,"duration":1}}
JSON
weave-viewer-cli . --record out.mp4 --width 900 --height 600 --fps 24 --duration 1
ffmpeg -ss 0.5 -i out.mp4 -frames:v 1 weave.png

# Chrome control
chrome --headless=new --hide-scrollbars --window-size=900,600 \
  --screenshot=chrome.png "file://$PWD/template.weave"
```

Verbatim weave log for the external-svg case:

```
[warning] LazyLoadReplacedSource: unknown extension for '<abs>/square.svg'
```

## Observed vs expected

| Case | Chrome | weave |
|---|---|---|
| A (inline attrs on path) | pink wavy line | pink wavy line ✓ |
| B (CSS-class styled path) | pink wavy line (CSS cascades) | **invisible** (default fill:black, stroke:none) |
| C (external svg via `<img>`) | cyan rect with yellow border | **empty box** (unknown extension) |

## Asks for upstream

1. **Cascade CSS rules into SVG child elements.** SVG 2.0 / CSS Painting both
   specify that CSS properties like `fill`, `stroke`, `stroke-width`, etc.
   apply to SVG elements via the cascade. Without this, every shared style
   has to be duplicated inline per shape, which makes any non-trivial
   SVG-as-iconography pattern unmaintainable.

2. **Recognise the `.svg` extension in the image loader.** Either parse and
   rasterise inline (preferred), or at minimum surface a clearer error than
   "unknown extension" so consumers know SVG-as-image isn't supported.

3. **(Lower priority) Animate SVG presentation attributes via CSS.** Already
   workaroundable with a parent-element opacity animation, but the draw-in
   stroke-dashoffset trick is iconic enough that supporting it would unlock
   a whole class of doodle / handwriting / progress-ring effects.

4. Add a `Replaced elements` / `SVG` row to `docs/feature-support.md`
   explicitly documenting what subset is supported today (inline SVG basic
   shapes with inline attributes works; CSS cascade into children doesn't;
   `<img src=*.svg>` doesn't; SMIL/CSS animation of SVG attrs untested).

## Status table (engine-side issues this session)

| Issue | Status |
|---|---|
| `<video>` panic / path / IOSurface | ✅ fixed v0.1.4/v0.1.5 |
| Default-font SIGABRT | ✅ fixed |
| `filter:drop-shadow` + animated opacity → glyph clip | ✅ fixed (hexer commit `f0c49749`) |
| `font-weight > 400` not applied | ✅ fixed |
| `text-align:center` not applied to wrapped lines | ✅ fixed |
| inter-span whitespace dropped | ❌ pending |
| **SVG support gaps (this report)** | **❌ pending** |

_Re-verified against locally-built `../hexer` binary on 2026-05-31._

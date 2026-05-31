# weave-viewer-cli — whitespace between sibling inline elements is dropped

**Tested:** locally-built `weave-viewer-cli` from `../hexer` branch
`fix/graceful-font-fallback` (today). Also reproduces against released v0.1.5.
**Severity:** breaks any template that splits a sentence into multiple inline
elements (per-word `<span>`s, karaoke highlighting, decorated mark / em / b
runs, etc.). Words run together, line breaks vanish.

## TL;DR

When the HTML contains adjacent inline elements separated by whitespace
(`<span>foo</span> <span>bar</span>`), the engine drops the whitespace entirely
and concatenates the contents (`foobar`). Since the wrap algorithm can only
break at whitespace, this also kills word-wrap on the affected element: a
long sentence built from per-word spans renders as one unbreakable run that
overflows the container.

This is independent of animation, transform, or any other styling — the
whitespace is gone before any of those matter.

## Minimum repro (one paste)

```bash
mkdir -p /tmp/spans && cd /tmp/spans
cat > template.weave <<'HTML'
<!DOCTYPE html><html><head><style>
html,body{margin:0;background:#222;color:#fff;font-family:sans-serif;font-size:32px;line-height:1.3}
.box{width:400px;margin:24px auto;border:2px solid #f0f;text-align:center}
</style></head><body>
  <div class="box">This is a fairly long sentence that should wrap to multiple lines</div>
  <div class="box"><span>This</span> <span>is</span> <span>a</span> <span>fairly</span> <span>long</span> <span>sentence</span> <span>that</span> <span>should</span> <span>wrap</span> <span>to</span> <span>multiple</span> <span>lines</span></div>
</body></html>
HTML
cat > manifest.json <<'JSON'
{"render":{"width":900,"height":500,"fps":24,"duration":1}}
JSON
weave-viewer-cli . --record out.mp4 --width 900 --height 500 --fps 24 --duration 1
ffmpeg -ss 0.5 -i out.mp4 -frames:v 1 weave.png

# Chrome control (rename to .html or pass directly):
chrome --headless=new --hide-scrollbars --window-size=900,500 \
  --screenshot=chrome.png "file://$PWD/template.weave"
```

## Observed vs expected

| Box | Source | Chrome render | weave render |
|---|---|---|---|
| 1 | `<div>This is a fairly long sentence …</div>` | 3 wrapped lines, words space-separated | 3 wrapped lines, words space-separated ✓ |
| 2 | `<div><span>This</span> <span>is</span> …</div>` | **3 wrapped lines, words space-separated** | **single unbreakable line `Thisisafairlylong…` overflowing the box** |

The two `<div>` boxes have the same visible text content; the only difference
is that box 2 wraps each word in a `<span>`. Chrome treats the literal whitespace
between adjacent `<span>` tags as the single space it is (per HTML serialization
rules + the `white-space:normal` default), preserves break opportunities, and wraps.
weave drops the whitespace, concatenates everything, and consequently can't wrap.

## Root cause hypothesis

Inter-element-whitespace collapse during DOM serialization / inline-box assembly.
Either:

1. The HTML parser is stripping whitespace-only text nodes between sibling
   elements as if they were ignorable formatting whitespace, OR
2. The parser keeps them but the inline-box layout pass treats whitespace-only
   text nodes as empty when their parent is an inline element, OR
3. The white-space:normal pass collapses runs of whitespace but is incorrectly
   reducing a single space to empty when one or both adjacent inline boxes are
   element-bounded.

Per HTML5 (§4.6 The text-level semantic elements) and CSS Text Module Level 3
(§4.1 The white-space property), a single ASCII space between two inline
elements MUST be preserved and treated as a wrap opportunity unless
`white-space: nowrap | pre | …` overrides it.

## Knock-on consequences in existing templates

`examples/subtitles-karaoke/template.weave` — every cue is a `<div>` containing
`<span class="w">…</span>` per word. With this bug:
- Within-cue word boundaries vanish ("SonntagmorgensinddasBesteüberhaupt.")
- No wrap occurs even though the cue container is narrowed to a 70% safe zone
- The karaoke per-word colour state still works mechanically (each span's
  animation runs), but visually the spans bleed into one inseparable string

The narrower templates (`examples/subtitles/`, `examples/subtitles-cues/`,
`examples/subtitles-simple/`) don't hit it because they put plain text in each
word/cue div, not nested spans.

## Asks for upstream

1. Preserve the single-space text node between adjacent inline siblings and
   honour it as a wrap opportunity, matching CSS Text L3 default behaviour.
2. Add an explicit fixture exercising
   `<div><span>foo</span> <span>bar</span></div>` to the test suite — it's a
   common decoration pattern (per-word styling, marked phrases, etc.).
3. Note: this likely interacts with the already-filed text-align:center bug —
   once whitespace is preserved, the wrapped lines from box-2 will also need
   per-line centering to land correctly.

## Status table (engine-side issues, re-verified 2026-05-31)

| Issue | Status |
|---|---|
| `<video>` panic / path / IOSurface | ✅ fixed v0.1.4/v0.1.5 |
| Default-font SIGABRT | ✅ fixed |
| `filter:drop-shadow` + animated opacity → glyph clip | ✅ fixed (hexer commit `f0c49749`) |
| `font-weight > 400` not applied | ✅ fixed |
| `text-align:center` not applied to wrapped lines | ✅ fixed |
| **inter-span whitespace dropped (this report)** | **❌ pending** |
| SVG support gaps | ❌ pending |
| Font-cache race silently falls back to embedded font | ❌ pending |

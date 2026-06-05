<!-- Hand-authored companion to the generated, Chrome-fixture-anchored
     feature-support.md (scripts/weave/gen-knowledge.sh → local/knowledge/feature-support.md).
     The features below are WEAVE-UNIQUE CSS extensions with NO Chrome equivalent
     (Chrome cannot trace an image/video alpha channel into a path), so they
     cannot be proven by a Chrome reference and do not appear in that index.
     Each is instead proven by the cited Rust/C++ test or showcase. -->

# Weave CSS Extensions

Weave's renderer accepts the standard CSS subset catalogued in the generated `feature-support.md`
index (every ✅ feature there is Chrome-referenced). This document covers the **Weave-unique**
properties that extend beyond
standard CSS — a small declarative system for **deriving a path from an element and riding it
with strokes and text**. They have no browser equivalent, so they are validated by integration
tests and showcases rather than Chrome fixtures.

The system has one **producer** (publishes a named path) and two **consumers** (an SVG stroke
and text-along-path) that resolve the same published path.

```
  ┌─ producer ──────────────┐      ┌─ consumers ─────────────────────────┐
  <video path-name:--outline> ──▶  <path d="--outline">     (dashed stroke)
        path-source:alpha            <span text-path="--outline">  (glyphs)
```

---

## 1. Path producer

Declare an element as a named path source. Resolution is the same for `<img>`, `<video>`, and
any box (rim). The published path is a closed polyline in **document px space** (the producer's
CSS transform is baked in at resolution).

| Property | Values | Initial | Notes |
|---|---|---|---|
| `path-name` | `--<ident>` (dashed-ident) | none | Registers this element's path under the name. |
| `path-source` | `auto \| alpha \| rim` | `auto` | `auto`: alpha silhouette if the content has alpha (`<img>`/`<video>`), else the rim. `alpha`: force the content's alpha silhouette (`<img>`/`<video>` only). `rim`: force the border box rounded by `border-radius` (any element). |
| `path-image-threshold` | `<number 0..1>` | `1.0` | Alpha-coverage cutoff for the silhouette trace. A cell is "inside" when its non-transparent fraction ≥ threshold. |

Last producer in DOM order under a given `path-name` wins (CSS Anchor-Positioning style).
For `<video>`, the silhouette is re-traced and re-published **per frame**.

```css
#subject {
  position: absolute; inset: 0; width: 576px; height: 1024px; object-fit: cover;
  path-name: --outline;
  path-source: alpha;
  path-image-threshold: 0.5;
}
```

**Proven by:** `apps/weave-showcase/src/showcases/showcase_textpath_image_silhouette.cpp`
(static image), `…/showcase_textpath_video_outline.cpp` (video, per-frame),
`tests/outline_text_image_silhouette_e2e_test.cpp`, `tests/outline_trace_alpha_silhouette_tests.cpp`
(the pure grid→polyline trace), `css-engine/src/draw/path_producer.rs`.

---

## 2. SVG path consumer — `d="--<ident>"`

An SVG `<path>` resolves a published path by name in its `d` attribute (or the CSS `d:`
property — CSS wins per the cascade) and strokes/fills it with standard SVG paint. The geometry
is already document-space, so the SVG's own `viewBox`/box does not re-transform it.

```html
<svg viewBox="0 0 576 1024" width="576" height="1024">
  <path d="--outline" stroke="#99ff99" stroke-width="2" stroke-dasharray="6 4" fill="none"/>
</svg>
```

Standard `stroke`, `stroke-width`, `stroke-dasharray`, `stroke-dashoffset`, `fill` apply.

**Proven by:** `css-engine/tests/path_d_registry.rs`
(`cross_consumer_path_and_text_share_one_published_path`), `emit_registry_d_paths` in
`css-engine/src/draw/mod.rs`.

---

## 3. Text-along-path consumer — `text-path`

A text element lays its glyphs along a published path. Glyphs are placed in document space
along the curve (the element's own box position is irrelevant to placement).

| Property | Values | Initial | Notes |
|---|---|---|---|
| `text-path` | `--<ident>` | none | Reference the producer's `path-name`. |
| `text-path-side` | `top \| right \| bottom \| left \| <angle>deg` | `top` | Where along the closed path the run is anchored. Conic convention, clockwise: `top = 0°`, `right = 90°`, `bottom = 180°`, `left = 270°`. |
| `text-path-offset` | `<length>` (signed px) | `0` | Perpendicular distance from the path; **positive = outward**, negative = inward. |
| `text-path-start` | `<length> \| <percentage>` | `0` | Where along the path the run begins (arc-length / fraction). |

```css
#caption {
  font-family: Anton; font-size: 48px; color: #fff;
  text-path: --outline;
  text-path-side: top;
  text-path-offset: 12px;
}
```

**Proven by:** `css-engine/tests/text_path_consumer_e2e.rs`,
`css-engine/src/svg/text_path.rs` (`place_text_along_resolved_path`),
`text-geometry/src/along_curve.rs` (placement SSOT: arc-length, offset curve, anchor, glyph
matrices), `text-geometry/tests/text_along_path_ffi_parity.rs` (VM↔FFI wire parity).

---

## 4. End-to-end example

A `<video>` alpha silhouette → dashed outline → captions riding the outline top. This is the
shape of `homebrew-weave/examples/subtitles-anchored/`.

```html
<style>
  #subject { position:absolute; inset:0; width:576px; height:1024px; object-fit:cover;
             path-name:--outline; path-source:alpha; path-image-threshold:0.5; z-index:1; }
  svg      { position:absolute; inset:0; z-index:2; }
  .cue     { position:absolute; z-index:3;   /* see Gotchas — paint order */
             font-family:Anton; color:#fff; opacity:0; /* …show window animation… */
             text-path:--outline; text-path-side:top; text-path-offset:12px; }
</style>
<video id="subject" src="clean-footage-with-alpha.mov" muted></video>
<svg viewBox="0 0 576 1024" width="576" height="1024">
  <path d="--outline" stroke="#99ff99" stroke-width="2" stroke-dasharray="6 4" fill="none"/>
</svg>
<span class="cue" style="animation-delay:4.46s;animation-duration:0.76s">video.</span>
```

---

## 5. Gotchas

- **Paint order (CSS 2.1 §9.9) — and the opacity-animation trap.** `z-index` only takes effect
  on an element that is **positioned** or **forms a stacking context**. The engine reads
  `z-index` for any stacking-context former, positioned or not (`classify_paint_tier`,
  `css-engine/src/draw/mod.rs`) — so a `position: static` caption with `opacity: 0.99` + `z-index: 3`
  paints *above* `<video>` layers at `z-index: 0/1`. **But `opacity` forms a stacking context only
  while `opacity < 1`** (`establishes_stacking_context`). So a static caption animating
  `opacity: 0 → 1` is on top at every frame *except* the fully-shown ones where opacity reaches
  exactly `1.0`: there it loses the stacking context, drops to the in-flow tier, and paints
  **under** the positioned videos. (Verified: static `opacity:0.99`+`z-index:3` → caption on top;
  static `opacity:1.0`+`z-index:3` → caption hidden under the videos.) The robust fix for an
  animated caption is **`position: absolute`** (or relative) + a `z-index` above the other layers —
  a positioned element honors `z-index` regardless of its opacity value.
- **Stacking-context layers fit the ink, not the box.** When a `text-path` element forms a
  stacking-context layer (`opacity` / `transform` / `filter`), its layer is sized to the
  **ink-overflow rect** — the union of its box with its painted glyph run (and shadows/outline),
  so path-placed glyphs that fall outside the element's flow box are not clipped. (See
  `compute_layer_ink_rect` in `css-engine/src/draw/mod.rs`; `tests/textpath_opacity_layer_clip_e2e_test.cpp`.)
- **No Chrome reference by construction.** Alpha-silhouette paths have no browser equivalent, so
  these features are intentionally absent from the Chrome-anchored `feature-support.md`; their
  correctness oracle is the cited tests/showcases.

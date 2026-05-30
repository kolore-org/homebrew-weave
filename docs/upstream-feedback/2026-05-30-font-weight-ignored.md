# weave-viewer-cli — `font-weight` values above the fallback's regular weight render at regular weight

**Tested:** locally-built `weave-viewer-cli` from `../hexer` branch `fix/graceful-font-fallback`
(commit `637fde10`, today's date). Also reproduces against the released v0.1.5.
**Severity:** visible regression of viral / kinetic-subtitle templates against Chrome / web baseline.

## TL;DR

When `font-family` falls back through `css_engine::embedded_fonts` to the bundled Roboto
family, `font-weight: 700|800|900` (and the keyword `bold`) is silently ignored. Every
declared weight renders with the same regular-weight glyphs Roboto's "regular" face
provides. The engine emits no warning that the requested weight isn't available.

In Chrome the same CSS picks up heavier system faces (Helvetica/Arial Bold on macOS, or
the weighted variants Google Fonts serves) and renders the glyphs much heavier — which is
how the subtitle templates were authored.

## Side-by-side repro

A single static HTML file rendered identically in Chrome headless and weave-viewer-cli:

```html
<!DOCTYPE html><html><head><style>
html,body{margin:0;padding:0;background:#222;color:#fff;font-family:sans-serif}
.row{padding:8px 12px;border-bottom:1px solid #444}
.lbl{font-family:monospace;font-size:11px;color:#aaa}
.txt{border:1px solid #f0f;font-size:60px}
.A .txt{font-weight:400}
.B .txt{font-weight:800}
.C .txt{font-weight:800;line-height:1.05}
.D .txt{font-weight:800;line-height:1.5}
.E .txt{font-weight:800;text-transform:uppercase}
.F .txt{font-size:80px;font-weight:900;line-height:1.05;text-transform:uppercase}
</style></head><body>
  <div class="row A"><div class="lbl">A: weight 400 (default)</div><div class="txt">Planen</div></div>
  <div class="row B"><div class="lbl">B: weight 800</div><div class="txt">Planen</div></div>
  <div class="row C"><div class="lbl">C: + line-height:1.05</div><div class="txt">Planen</div></div>
  <div class="row D"><div class="lbl">D: + line-height:1.5</div><div class="txt">Planen</div></div>
  <div class="row E"><div class="lbl">E: + uppercase</div><div class="txt">Planen</div></div>
  <div class="row F"><div class="lbl">F: 80px / weight 900 / upper</div><div class="txt">Planen</div></div>
</body></html>
```

**Chrome:** row A is light, rows B–F are distinctly heavier (bold strokes, more ink
coverage); row F overflows the magenta box on the right because bold 80px is wider than
the available horizontal space.

**weave-viewer-cli:** rows A–F all render with **identical regular-weight strokes**. The
box widens for 80px (font-size IS being honored), but the strokes never thicken. Row F
does NOT overflow the box because the regular-weight 80px glyphs are narrower than what
the spec demands.

Screenshots are checked in at:
- `outputs/chrome-vs-weave/matrix/chrome.png`
- `outputs/chrome-vs-weave/matrix/weave.png`
(both 576×1200 PNGs, gitignored under the output-folder policy — regen with the script
at the bottom of this doc).

## Observed vs expected

| Property | Chrome | weave-viewer-cli | Expected per CSS Fonts |
|---|---|---|---|
| `font-size` (60px / 80px) | honored | **honored** (same x-extent) | honored |
| `font-weight: 400` (default) | regular | regular | regular |
| `font-weight: 800` | **bold** | regular | bold |
| `font-weight: 900` | **bold** | regular | bold |
| `font-weight: bold` (keyword) | bold | (untested in this matrix — likely same) | bold |
| Heavy-weight glyph metrics widening | yes | **no** — layout uses regular glyph widths | yes |

The last row is the one that matters for layout: in Chrome, `font-weight:900` makes
"PLANEN" overflow a 528px box at 80px; in weave the same text fits because the strokes
are thin. This means **layout calculations also use regular-weight metrics even when the
template asks for a heavier weight**, which can cascade into wrap / overflow bugs.

## Why the subtitle template "looks cut at the bottom"

The Phase 1 subtitle template (`examples/subtitles/template.weave`) declares
`.t-mid{font-size:60px;font-weight:800}` and `.t-key{font-size:80px;font-weight:900}`.
On Chrome those produce heavy, viral-poster-style letters; on weave they produce
regular-weight letters that look small and thin against the video background — a thin
glyph silhouette + a heavy `filter:drop-shadow` halo reads to the eye as "cut letters
sitting in a fuzzy blob". The visible difference is entirely the missing weight.

## Likely fix surface

`css_engine::embedded_fonts`. The bundled Roboto family in `data/fonts/` either:

1. Doesn't include the heavier weight faces (Roboto Bold, Black) — ship them, register
   `Roboto-Bold.ttf` and `Roboto-Black.ttf` as additional faces for the same family with
   `font-weight: 700` / `900`.
2. Or has them but they're not being matched by the fallback layer when the original
   `@font-face` URL fails — extend the matching to look up the embedded family's heavier
   faces by requested weight rather than always returning regular.

Also worth flagging: warn (once per render) when a requested `font-weight` doesn't have
a matching face in the resolved family, so consumers know the weight is being silently
downgraded. Right now the only warning is the original Google-Fonts miss.

## Knock-on consequence

The Phase 1 spec's rank → font-weight tiers (700 / 800 / 900) are not visually
distinguishable in weave output: every word renders at the same weight regardless of
rank. The size tier (44 / 60 / 80 px) IS distinguishable; the weight tier is not.

## Regeneration script

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HEXER_BIN=/Users/jakubtyrcha/repos/hexer/cmake-build-debug/apps/weave-viewer-cli/weave-viewer-cli

# (HTML body above lives at outputs/chrome-vs-weave/matrix/proj/{template.weave,index.html}
#  and manifest.json with {"render":{"width":576,"height":1200,"fps":24,"duration":1}})

"$HEXER_BIN" outputs/chrome-vs-weave/matrix/proj --record /tmp/m.mp4 \
  --width 576 --height 1200 --fps 24 --duration 1
ffmpeg -ss 0.5 -i /tmp/m.mp4 -frames:v 1 outputs/chrome-vs-weave/matrix/weave.png

"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=576,1200 \
  --screenshot=outputs/chrome-vs-weave/matrix/chrome.png \
  "file://$PWD/outputs/chrome-vs-weave/matrix/proj/index.html"
```

# weave-viewer-cli — concurrent renders race the Google-Fonts cache and silently fall back

**Tested:** locally-built `weave-viewer-cli` from `../hexer` at commit
`f0c49749` (today). Reproduces against released v0.1.5 as well.
**Severity:** silent visual regression. Templates render with the wrong typeface
under concurrent load.

## TL;DR

When two or more `weave-viewer-cli --record` processes start at the same time
and both ask for the same Google Font that isn't yet cached, they race on the
"download to `.tmp`, then rename to final" cache write. The rename step in the
losing process(es) fails with:

```
[warning] [css_engine::google_fonts] google-fonts: write CabinSketch-Bold.ttf:
  rename .../CabinSketch-Bold.ttf.tmp -> .../CabinSketch-Bold.ttf:
  No such file or directory (os error 2)
```

The error is treated as "Google had no source for that family" and the engine
falls through to the embedded font (currently `Google Sans Code`). Even though
the font is actually available — both on the network and (after the race) on
disk — those renders end up using the wrong typeface.

`ENOENT` on the rename target almost certainly means the source `.tmp` is gone
because another process won the race and renamed it first. The font is on disk
under the final name, but this process never checks and never tries again.

## Minimum repro

Wipe the cache, fire two concurrent renders against any template that uses an
uncached Google Font:

```bash
rm -rf ~/Library/Caches/weave/CabinSketch-*.ttf*

cat > /tmp/cabin.weave <<'HTML'
<!DOCTYPE html><html><head><style>
@import url('https://fonts.googleapis.com/css2?family=Cabin+Sketch:wght@400;700&display=swap');
html,body{margin:0;background:#000;color:#fff;font-family:'Cabin Sketch',cursive;font-size:80px;text-align:center}
</style></head><body><div style="padding:200px 0">Cabin Sketch</div></body></html>
HTML
mkdir -p /tmp/race-{a,b}
cp /tmp/cabin.weave /tmp/race-a/template.weave
cp /tmp/cabin.weave /tmp/race-b/template.weave
echo '{"render":{"width":576,"height":400,"fps":24,"duration":1}}' \
  | tee /tmp/race-{a,b}/manifest.json > /dev/null

# Fire two concurrent --record processes
weave-viewer-cli /tmp/race-a --record /tmp/race-a.mp4 --width 576 --height 400 --fps 24 --duration 1 > /tmp/race-a.log 2>&1 &
weave-viewer-cli /tmp/race-b --record /tmp/race-b.mp4 --width 576 --height 400 --fps 24 --duration 1 > /tmp/race-b.log 2>&1 &
wait

# Inspect logs
grep -E "rename|unresolved|embedded" /tmp/race-a.log /tmp/race-b.log
```

At least one of the two logs will contain the `rename` ENOENT followed by:

```
[warning] [css_engine::google_fonts] google-fonts: no source found for 'Cabin Sketch'
[warning] [css_engine::embedded_fonts] embedded-fonts: 'Cabin Sketch' unresolved
  by Google — rendering with embedded variable fallback (Google Sans Code)
```

The render that wins gets Cabin Sketch; the losers get Google Sans Code. Same
template, same inputs, different fonts.

This bit us in the wild this session: a parallel re-render of seven subtitle
examples (six of which declare Cabin Sketch via `@font-face`/`@import`) had
some examples render with Cabin Sketch and others fall back, depending on
which finished the download write first. The font files DID end up in the
cache on disk; the losing processes just didn't notice.

## Observed vs expected

| Aspect | Observed | Expected |
|---|---|---|
| Two concurrent renders with empty cache | losers fall back to embedded font | both render with the Google Font |
| ENOENT on rename of own .tmp | reported as warning, fallback path taken | if final file is now present, treat as success (someone else cached it); otherwise retry / re-fetch into memory |
| Final cache state | font file is correctly on disk (winner cached it) | same |
| Log clarity | message blames "no source found for 'X'" even though source exists | distinguish "couldn't write cache file" from "Google returned no font" |

## Likely fix surface

`css_engine::google_fonts` write path. The simplest robust patterns:

1. **On rename ENOENT, check if the destination exists.** If yes, treat as
   success and load the font from the destination — the other process won the
   race. If not, fall through to in-memory use and retry the download.

2. **Per-process temp filenames.** Write to `CabinSketch-Bold.ttf.<pid>.tmp`
   (or `.tmp.<random>`) so concurrent writers never share a `.tmp` name.
   Combined with an atomic rename, this eliminates the ENOENT path entirely:
   each writer renames its own unique temp; the last one in wins; previous
   final-file overwrites are atomic via `rename(2)`.

3. **In-memory first, cache second.** Decode the font straight from the
   download buffer for this render, then write to disk on a best-effort basis
   for future renders. A failed cache write is purely an optimisation miss,
   never a visible regression.

(1) and (2) are independent and both worth doing — (1) handles the case where
two writers share a tmp name; (2) makes the case impossible.

## Asks for upstream

1. Make a Google-Fonts cache-write failure a non-fatal, non-fallback-trigger
   event — recover the font for this render (in-memory or by re-reading the
   final file) and keep going.
2. Use per-process / per-render unique temp filenames during cache writes.
3. When the engine DOES fall back to the embedded family, surface a clearer
   message: "couldn't write Google Font cache, using embedded fallback" rather
   than "no source found", so users know the network request succeeded and
   the failure is local.

## Status table (engine-side issues, re-verified 2026-05-31)

| Issue | Status |
|---|---|
| `<video>` panic / path / IOSurface | ✅ fixed v0.1.4/v0.1.5 |
| Default-font SIGABRT | ✅ fixed |
| `filter:drop-shadow` + animated opacity → glyph clip | ✅ fixed (hexer commit `f0c49749`) |
| `font-weight > 400` not applied | ✅ fixed |
| `text-align:center` not applied to wrapped lines | ✅ fixed |
| inter-span whitespace dropped | ❌ pending |
| SVG support gaps | ❌ pending |
| **Font-cache race silently falls back to embedded font (this report)** | **❌ pending** |

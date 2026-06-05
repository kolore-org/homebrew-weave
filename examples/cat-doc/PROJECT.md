# PROJECT — "The Midnight Zoomies" (cat-doc)

A 20s (27.5s w/ title) BBC-nature-doc parody about a house cat's "zoomies".
**fal-generated B-roll → weave HUD overlays → per-scene VO mux → concat.**
Built with the `/weave-broll` + `/weave-subtitle` skills.

This example ships **only the inputs that can't be cheaply regenerated** — the
fal B-roll (`scene-0N.mp4`), the fal voiceover (`vo-0N.mp3`), the hand-authored
overlay templates, and the title generator. The **renders, A/V segments, and the
final cut are NOT shipped** — rebuild them with the commands below (`final.mp4`
lands one level up at `../final.mp4`). The `title/` folder is likewise generated
(run `gen_title.py`), so it's absent until you build.

---

## ⚠️ Read this first (traps)

| Trap | Truth |
| :--- | :--- |
| `title/` is missing | It's **generated** by `artifacts/gen_title.py` (writes `title/template.weave` + `title/manifest.json`). Run it first. Edit the *script*, never the generated `.weave`. |
| Magic tpad numbers | `0.530563` etc. = `vo_duration − render_duration`. Re-deriving is mandatory after any re-render or new VO (see Sync rule). |
| The 3 scene clips are 6/8/6s but VO is longer | Video is **freeze-extended** to match VO. That's intentional, not a bug. |
| Binary media is in Git LFS | `*.mp4`/`*.mp3` are LFS-tracked (`.gitattributes`). Clone needs `git lfs` or the media arrives as pointer text. |

---

## Build graph

```
SOURCE (edit these)                     GENERATED (reproducible)
─────────────────────                   ────────────────────────
scene-0N/template.weave  ─ weave ─▶  scene-0N.render.mp4 ┐
scene-0N.mp4 (fal B-roll)                                ├─ ffmpeg tpad+mux ─▶ scene-0N.av.mp4 ┐
vo-0N.mp3   (fal TTS)    ─────────────────────────────────┘                                    │
                                                                                               ├─ concat ─▶ final.mp4
gen_title.py ─ python ─▶ title/template.weave ─ weave ─▶ title.render.mp4 ─ ffmpeg +silence ─▶ title.av.mp4 ┘
                                                                                  (order: concat.txt)
```

## Source-of-truth files (the only things you hand-edit)

- `artifacts/scene-01/template.weave`, `scene-02/…`, `scene-03/…` — HUD overlay HTML+CSS per scene (1280×720). Reference their B-roll as `../scene-0N.mp4`.
- `artifacts/scene-0N/manifest.json` — render dims/fps/**duration** (6/8/6s).
- `artifacts/gen_title.py` — **generator** for the title card → writes `title/template.weave` + `title/manifest.json` (5s).
- `artifacts/scene-0N.mp4` — raw fal B-roll (regenerate via `/weave-broll`; see below).
- `artifacts/vo-0N.mp3` — raw fal TTS narration (regenerate via fal Eleven v3).
- `artifacts/concat.txt` — final assembly order: `title → scene-01 → 02 → 03`.

Everything else in `artifacts/` (`*.render.mp4`, `*.av.mp4`) and `final.mp4` is **derived** — safe to delete and rebuild.

---

## Reproduce the deliverable

All commands run from `outputs/cat-doc/artifacts/`.

### 1. (Title only) regenerate the card
```bash
python3 gen_title.py      # writes title/template.weave + title/manifest.json
```

### 2. Render each weave project → silent .render.mp4
```bash
for s in title scene-01 scene-02 scene-03; do
  weave-viewer-cli "$s" --validate                      # static check, no GPU
  D=$(python3 -c "import json;print(json.load(open('$s/manifest.json'))['render']['duration'])")
  weave-viewer-cli "$s" --record "$s.render.mp4" --width 1280 --height 720 --fps 24 --duration "$D"
done
```

### 3. Mux VO onto each scene (freeze-extend video to VO length)
`build <scene> <pad> <total>` where **pad = vo_dur − render_dur** and **total = vo_dur**:
```bash
build(){ ffmpeg -y -loglevel error -i "$1.render.mp4" -i "vo-${1#scene-}.mp3" \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=$2,fps=24,format=yuv420p[v]" \
  -map "[v]" -map 1:a -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k -ar 44100 -ac 1 \
  -t "$3" -movflags +faststart "$1.av.mp4"; }
build scene-01 0.530563 6.530563
build scene-02 0.124063 8.124063
build scene-03 1.810563 7.810563
```
Title gets 5s of **silence** (no VO) instead:
```bash
ffmpeg -y -i title.render.mp4 -f lavfi -t 5 -i anullsrc=r=44100:cl=mono \
  -map 0:v -map 1:a -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 192k -ar 44100 -ac 1 -t 5 -movflags +faststart title.av.mp4
```

### 4. Concat → final
```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy ../final.mp4
```
All `.av.mp4` share codec/params (h264 + aac mono 44.1k 24fps), so `-c copy` is safe.

### Sync rule (why the magic numbers)
Each scene's on-screen length is driven by its **narration**, not the clip:
```
pad   = vo_duration − render_duration   # tpad stop_duration (freeze last frame)
total = vo_duration                     # -t
```
Current VO: 6.530563 / 8.124063 / 7.810563s. Render durs: 6 / 8 / 6s.
**If you re-record VO or change a scene duration, recompute both** (`ffprobe -show_entries format=duration vo-0N.mp3`).

---

## Regenerating the raw assets (fal — paid, opt-in)

Use `/weave-broll`. fal MCP is user-keyed (`.fal.key.donotcommit`, gitignored) and every paid run needs explicit consent.

- **B-roll** (`scene-0N.mp4`): text→video, 16:9, 1280×720. Prompts = documentary realism, cinematic lighting, shallow DoF, per the 3-scene script (scene 1 tense still cat / scene 2 whip-pan chaos / scene 3 calm atop fridge).
- **VO** (`vo-0N.mp3`): `fal-ai/elevenlabs/tts/eleven-v3`, deep British male, Attenborough delivery, pause tags on the "…" beats. One file per scene so each locks to its scene start.

---

## Known weave engine gotchas (hit during this build)

Honor these when editing templates — each has a filed bug report in this folder:

- `bug-report-backdrop-filter-black-preroll.md` — **`backdrop-filter: blur()` → black-frame preroll.** Use opaque panel bg instead.
- `bug-report-bitcount-font-invisible.md` — Bitcount fonts render invisible (title uses VT323 instead).
- `bug-report-text-shadow-em-units.md` — `text-shadow` ignores `em` units; **use px**.
- `bug-report-text-shadow-no-inherit.md` — `text-shadow` does **not** inherit; declare via `*{}` universal selector, override per-tier by class (current scenes do this).
- Also: CSS does **not** cascade into `<svg>` children (title typewriter = one windowed top-level `<svg>` per glyph); `<br>`/`&nbsp;` unreliable for breaks/spacing; `-webkit-text-stroke` unsupported.

## Known open issue (not yet fixed)
- Scene-02 data tags read `VELOCITYHIGH` / `STATUSAIRBORNE` / `THREATNONE` — the `&nbsp;` spacer between label and value collapsed (inter-span whitespace drop). Fix with an explicit `margin`/`padding` on the value span if desired.

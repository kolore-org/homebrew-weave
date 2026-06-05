#!/usr/bin/env python3
"""Title card v2 — "FIELD PLATE Nº07 / Nocturnal Observation Terminal".
Refined-maximalist dark observation terminal: Danfo title hard-left with an amber
rule, an oscilloscope SIGNAL panel (right) where 'powered by Weave renderer' rides
a sine in VT323 with an amber plotting dot, engraved SVG grid, scan-line sweep,
corner registration crosses, specimen header, 03:00:00 timecode.

Weave constraints honoured: no backdrop-filter (black-preroll bug); no CSS into
<svg> children -> per-glyph typewriter is one windowed top-level <svg> per char;
grid built from SVG lines (not repeating-gradients); literal colours (no var())."""
import html, pathlib

OUT = pathlib.Path(__file__).parent / "title"
OUT.mkdir(exist_ok=True)

INK, BONE, PHOS, AMBER = "#070a0e", "#ece4d2", "#7fe9dc", "#ffb44d"

PHRASE = "powered by Weave renderer"
CARET, T_START, PER_CHAR = "_", 0.55, 0.050
N = len(PHRASE)

# sine inside the SIGNAL panel's svg space (520 x 120, baseline y=62)
SINE_D = "M 26 62 Q 86 30, 146 62 T 266 62 T 386 62 T 506 62"

def tw_svg(text, z, delay, cls):
    return (
        f'<svg class="{cls}" width="520" height="120" viewBox="0 0 520 120" '
        f'style="z-index:{z};animation-delay:{delay:.3f}s">'
        f'<defs><path id="sg{z}" d="{SINE_D}" fill="none"/></defs>'
        f'<text text-anchor="start" font-family="VT323" font-size="32" '
        f'fill="{PHOS}" letter-spacing="1">'
        f'<textPath href="#sg{z}" startOffset="0">{html.escape(text)}</textPath>'
        f'</text></svg>'
    )

steps = [tw_svg(PHRASE[:k] + CARET, k, T_START + PER_CHAR*(k-1), "tw")
         for k in range(1, N+1)]
steps.append(tw_svg(PHRASE, N+1, T_START + PER_CHAR*N, "twf"))
typewriter = "\n      ".join(steps)

# 4 corner registration crosses with tiny coord labels
def reg(pos_css, label, delay):
    return (f'<div class="reg" style="{pos_css};animation-delay:{delay:.2f}s">'
            f'<span class="rl">{label}</span></div>')
regs = "\n  ".join([
    reg("top:42px;left:42px",      "x0 y0",   .05),
    reg("top:42px;right:42px",     "x1 y0",   .12),
    reg("bottom:42px;left:42px",   "x0 y1",   .19),
    reg("bottom:42px;right:42px",  "x1 y1",   .26),
])

# amber plotting dot path along the sine (panel-local px, matches SINE_D apexes)
DOT_KF = ("0%{transform:translate(26px,62px)}"
          "20%{transform:translate(146px,62px)}"
          "30%{transform:translate(206px,92px)}"
          "40%{transform:translate(266px,62px)}"
          "55%{transform:translate(386px,62px)}"
          "70%{transform:translate(446px,92px)}"
          "100%{transform:translate(506px,62px)}")
DOT_DUR = PER_CHAR * N

DOC = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Danfo&family=VT323&display=swap');
html,body{{margin:0;padding:0}}
body{{width:1280px;height:720px;position:relative;overflow:hidden;background:{INK};
  font-family:'VT323',monospace;color:{PHOS}}}
.vig{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(58% 52% at 30% 44%, rgba(22,40,46,.5) 0%, rgba(7,10,14,0) 62%),
             radial-gradient(120% 100% at 50% 50%, rgba(0,0,0,0) 52%, rgba(0,0,0,.72) 100%)}}
.grid{{position:absolute;inset:0;opacity:0;animation:fade 1s ease-out .05s forwards;
  background-image:
    repeating-linear-gradient(0deg, rgba(127,233,220,.05) 0 1px, transparent 1px 80px),
    repeating-linear-gradient(90deg, rgba(127,233,220,.05) 0 1px, transparent 1px 80px),
    repeating-linear-gradient(0deg, rgba(127,233,220,.10) 0 1px, transparent 1px 320px),
    repeating-linear-gradient(90deg, rgba(127,233,220,.10) 0 1px, transparent 1px 320px)}}
.scan{{position:absolute;left:0;width:1280px;height:3px;top:0;pointer-events:none;
  background:linear-gradient(90deg, rgba(127,233,220,0), rgba(127,233,220,.5), rgba(127,233,220,0));
  animation:sweep 2.6s linear .2s infinite}}
@keyframes sweep{{from{{transform:translateY(-10px)}}to{{transform:translateY(720px)}}}}

/* corner registration crosses */
.reg{{position:absolute;width:20px;height:20px;opacity:0;
  animation:pop .4s cubic-bezier(.2,1.4,.3,1) forwards}}
.reg::before{{content:"";position:absolute;left:0;top:9px;width:20px;height:2px;background:{PHOS}}}
.reg::after{{content:"";position:absolute;left:9px;top:0;width:2px;height:20px;background:{PHOS}}}
.rl{{position:absolute;top:24px;left:0;font-size:13px;letter-spacing:.18em;color:rgba(127,233,220,.6);white-space:nowrap}}

/* specimen header (top-left) */
.hdr{{position:absolute;top:64px;left:64px;opacity:0;
  animation:slidein .6s cubic-bezier(.16,1,.3,1) .18s forwards}}
.hdr .h1{{font-size:20px;letter-spacing:.5em;color:{PHOS};margin:0 0 2px}}
.hdr .h2{{font-family:'Danfo',serif;font-size:30px;letter-spacing:.06em;color:{AMBER};margin:0;line-height:1}}
.cls{{position:absolute;top:150px;left:64px;font-size:17px;letter-spacing:.34em;
  color:rgba(127,233,220,.72);opacity:0;animation:fade .6s ease-out .5s forwards}}

/* data cluster (top-right) */
.data{{position:absolute;top:62px;right:64px;text-align:right;font-size:17px;
  letter-spacing:.22em;line-height:1.7;color:rgba(127,233,220,.78);
  opacity:0;animation:fade .6s ease-out .6s forwards}}
.data div b{{color:{AMBER};font-weight:400}}

/* HERO title, hard-left, asymmetric */
.bar{{position:absolute;left:64px;top:262px;width:6px;height:232px;background:{AMBER};
  transform:scaleY(0);transform-origin:top;animation:grow .6s cubic-bezier(.2,.8,.2,1) .3s forwards}}
.title{{position:absolute;left:96px;top:248px;font-family:'Danfo',serif;color:{BONE};
  font-size:150px;line-height:.86;letter-spacing:2px}}
.title .ln{{display:block;opacity:0;transform:translateY(30px)}}
.title .l1{{animation:rise .8s cubic-bezier(.16,1,.3,1) .42s forwards}}
.title .l2{{animation:rise .8s cubic-bezier(.16,1,.3,1) .56s forwards;color:#d9cdb4}}

/* SIGNAL oscilloscope panel (right) */
.sig{{position:absolute;left:700px;top:388px;width:500px;height:176px;
  border:1px solid rgba(127,233,220,.34);
  background:linear-gradient(180deg, rgba(12,20,24,.5), rgba(7,12,16,.5));
  opacity:0;transform:translateY(12px);animation:rise .55s ease-out .42s forwards}}
.sig .br{{position:absolute;width:14px;height:14px;border:2px solid {PHOS}}}
.sig .b1{{left:-1px;top:-1px;border-right:0;border-bottom:0}}
.sig .b2{{right:-1px;top:-1px;border-left:0;border-bottom:0}}
.sig .b3{{left:-1px;bottom:-1px;border-right:0;border-top:0}}
.sig .b4{{right:-1px;bottom:-1px;border-left:0;border-top:0}}
.sig .lab{{position:absolute;top:12px;left:16px;font-size:16px;letter-spacing:.28em;color:{AMBER}}}
.sig .lab2{{position:absolute;top:12px;right:16px;font-size:15px;letter-spacing:.2em;color:rgba(127,233,220,.6)}}
.tw,.twf{{position:absolute;left:710px;top:432px}}
.tw{{opacity:0;animation:win {PER_CHAR:.3f}s linear forwards}}
@keyframes win{{0%,99%{{opacity:1}}100%{{opacity:0}}}}
.twf{{opacity:0;animation:snap .01s steps(1,end) forwards}}
@keyframes snap{{to{{opacity:1}}}}
.dot{{position:absolute;left:710px;top:432px;width:11px;height:11px;border-radius:50%;
  background:{AMBER};margin:-5px 0 0 -5px;opacity:0;
  animation:dotin .2s ease-out {T_START}s forwards, plot {DOT_DUR:.3f}s linear {T_START}s forwards}}
@keyframes dotin{{to{{opacity:1}}}}
@keyframes plot{{{DOT_KF}}}

/* bottom strip */
.base{{position:absolute;left:64px;right:64px;bottom:96px;height:1px;background:rgba(127,233,220,.28);
  transform:scaleX(0);transform-origin:left;animation:growx .9s cubic-bezier(.2,.8,.2,1) .35s forwards}}
.tc{{position:absolute;left:64px;bottom:50px;font-size:40px;letter-spacing:.12em;color:{AMBER};
  opacity:0;animation:fade .5s ease-out .8s forwards}}
.tc .bl{{animation:blink 1s steps(1,end) infinite}}
.obs{{position:absolute;right:64px;bottom:58px;font-size:20px;letter-spacing:.3em;
  color:rgba(127,233,220,.85);opacity:0;animation:fade .5s ease-out .9s forwards}}
.obs .d{{display:inline-block;width:11px;height:11px;border-radius:50%;background:#ff5a4d;
  margin-right:10px;animation:blink 1.1s steps(1,end) infinite}}

@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:.15}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes rise{{to{{opacity:1;transform:translateY(0)}}}}
@keyframes slidein{{from{{opacity:0;transform:translateX(-22px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes pop{{to{{opacity:1}}}}
@keyframes grow{{to{{transform:scaleY(1)}}}}
@keyframes growx{{to{{transform:scaleX(1)}}}}
</style></head><body>
  <div class="vig"></div>
  <div class="grid"></div>
  <div class="scan"></div>

  {regs}

  <div class="hdr"><p class="h1">FIELD PLATE</p><p class="h2">N&ordm; 07</p></div>
  <div class="cls">ORDER CARNIVORA &middot; FAM. FELIDAE &middot; NOCTURNAL</div>
  <div class="data"><div>OBS &mdash; <b>NOCTURNAL</b></div><div>51.51&deg;N &middot; 0.13&deg;W</div><div>SUBJ &mdash; <b>FELIS CATUS</b></div></div>

  <div class="bar"></div>
  <div class="title"><span class="ln l1">FELIS</span><span class="ln l2">CATUS</span></div>

  <div class="sig">
    <span class="br b1"></span><span class="br b2"></span><span class="br b3"></span><span class="br b4"></span>
    <span class="lab">SIGNAL &middot; v/t</span><span class="lab2">PLOT</span>
  </div>
  {typewriter}
  <div class="dot"></div>

  <div class="base"></div>
  <div class="tc">03<span class="bl">:</span>00<span class="bl">:</span>00</div>
  <div class="obs"><span class="d"></span>OBSERVING</div>
</body></html>
"""

(OUT / "template.weave").write_text(DOC)
(OUT / "manifest.json").write_text('{ "render": { "width":1280, "height":720, "fps":24, "duration":5 } }\n')
print(f"wrote {OUT}/template.weave (v2 observation terminal, {N} typing steps)")

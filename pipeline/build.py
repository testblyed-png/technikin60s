"""Technik in 60s – baut ein Short aus einer Topic-JSON.
Aufruf:  python3 pipeline/build.py topics/<slug>.json
Ergebnis: out/<slug>.mp4 + out/<slug>.meta.json
"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE = os.environ.get("VOICE", "/tmp/voice/de-thorsten-low.onnx")
W, H, FPS, SR = 1080, 1920, 30, 44100
FD = "/usr/share/fonts/opentype/inter/InterDisplay-"
_fc = {}
def F(size, w="Bold"):
    if (size, w) not in _fc: _fc[(size, w)] = ImageFont.truetype(FD + w + ".otf", size)
    return _fc[(size, w)]

TOP = (7, 14, 30); BOT = (10, 34, 62)
COL = dict(water=(56, 189, 248), waterd=(14, 116, 178), yel=(250, 204, 21), white=(240, 246, 252),
           grey=(148, 163, 184), red=(248, 113, 113), blue=(96, 165, 250), green=(74, 222, 128),
           orange=(217, 119, 6), card=(22, 40, 70))
def C(c): return COL[c] if isinstance(c, str) else tuple(c)

BASE = Image.new("RGB", (W, H)); _d = ImageDraw.Draw(BASE)
for y in range(H):
    a = y / H; _d.line([(0, y), (W, y)], fill=tuple(int(TOP[i] + (BOT[i] - TOP[i]) * a) for i in range(3)))
def bg(y):
    a = max(0, min(1, y / H)); return tuple(int(TOP[i] + (BOT[i] - TOP[i]) * a) for i in range(3))
def mix(c, a, y):
    b = bg(y); a = max(0, min(1, a)); c = C(c); return tuple(int(b[i] + (c[i] - b[i]) * a) for i in range(3))
def cl(x): return max(0.0, min(1.0, x))
def ease(x): x = cl(x); return x * x * (3 - 2 * x)
def back(x):
    x = cl(x); k = 1.70158; return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2
def ap(t, t0, d=0.45): return ease((t - t0) / d)

def wrap(text, font, maxw, d):
    out = []
    for para in text.split("\n"):
        line = ""
        for w_ in para.split(" "):
            test = (line + " " + w_).strip()
            if d.textlength(test, font=font) <= maxw: line = test
            else: out.append(line); line = w_
        out.append(line)
    return out
def ctext(d, y, text, font, col, a=1.0, maxw=900, x=None):
    for i, ln in enumerate(wrap(text, font, maxw, d)):
        yy = y + i * font.size * 1.18
        d.text((x if x is not None else W / 2, yy), ln, font=font, fill=mix(col, a, yy), anchor="ma")
    return y + len(wrap(text, font, maxw, d)) * font.size * 1.18
def rich(d, y, parts, font, a):
    tot = sum(d.textlength(p, font=font) for p, _ in parts); x = (W - tot) / 2
    for p, c in parts: d.text((x, y), p, font=font, fill=mix(c, a, y)); x += d.textlength(p, font=font)
def card(d, box, a, outline=None):
    d.rounded_rectangle(box, 34, fill=mix("card", a, (box[1] + box[3]) / 2),
                        outline=mix(outline, a, box[1]) if outline else None, width=4)
def header(d, gt, total, title):
    d.rounded_rectangle((260, 130, 820, 196), 33, fill=(20, 52, 88))
    d.text((W / 2, 163), title, font=F(34, "SemiBold"), fill=COL["water"], anchor="mm")
    d.rounded_rectangle((140, 226, 940, 234), 4, fill=(30, 50, 80))
    d.rounded_rectangle((140, 226, 140 + 800 * cl(gt / total), 234), 4, fill=COL["water"])
def caption(d, t, dur, S, texts, y=1330):
    cur = None
    for i in range(min(len(S), len(texts))):
        if t >= S[i] and texts[i]: cur = i
    if cur is None: return
    nxt = S[cur + 1] if cur + 1 < len(S) else dur + 1
    ctext(d, y, texts[cur], F(58, "SemiBold"), "white", min(ap(t, S[cur], 0.3), cl((nxt - t) / 0.2)))
def waves(d, t):
    for (col, y0, amp, sp, k, a) in (("waterd", 1500, 26, 1.6, 0.010, 1), ("water", 1560, 20, 2.2, 0.014, 0.85)):
        pts = [(x, y0 + amp * math.sin(k * x + (t + (1.3 if a < 1 else 0)) * sp)) for x in range(0, W + 20, 20)]
        d.polygon(pts + [(W, H), (0, H)], fill=mix(col, a, y0 + 200))

# ---------------------------------------------------------------- icons (animated)
def icon(d, kind, t, a, cx=540, cy=650):
    if kind == "turbine":
        R = 230; spin = t * 2.5
        d.ellipse((cx - R - 20, cy - R - 20, cx + R + 20, cy + R + 20), outline=mix((60, 80, 110), a, cy), width=10)
        for k in range(9):
            ang = spin + k * 2 * math.pi / 9; pts = []
            for i in range(7):
                s = i / 6; r = 60 + (R - 60) * s; aa = ang + math.radians(28 * s); pts.append((cx + r * math.cos(aa), cy + r * math.sin(aa)))
            for i in range(6, -1, -1):
                s = i / 6; r = 60 + (R - 60) * s; aa = ang + math.radians(28 * s + 18 * (1 - .5 * s)); pts.append((cx + r * math.cos(aa), cy + r * math.sin(aa)))
            d.polygon(pts, fill=mix("water" if k % 2 else (125, 211, 252), a, cy))
        d.ellipse((cx - 60, cy - 60, cx + 60, cy + 60), fill=mix((200, 210, 225), a, cy))
    elif kind == "generator":
        d.ellipse((cx - 250, cy - 250, cx + 250, cy + 250), outline=mix((90, 100, 125), a, cy), width=40)
        for k in range(6):
            x, y = cx + 205 * math.cos(k * math.pi / 3), cy + 205 * math.sin(k * math.pi / 3)
            d.rounded_rectangle((x - 34, y - 34, x + 34, y + 34), 10, fill=mix("orange", a, y))
        ang = t * 3; ca, sa = math.cos(ang), math.sin(ang)
        rot = lambda px, py: (cx + px * ca - py * sa, cy + px * sa + py * ca)
        d.polygon([rot(0, -45), rot(140, -45), rot(140, 45), rot(0, 45)], fill=mix("red", a, cy))
        d.polygon([rot(-140, -45), rot(0, -45), rot(0, 45), rot(-140, 45)], fill=mix("blue", a, cy))
        d.text(rot(80, 0), "N", font=F(52, "Black"), fill=mix("white", a, cy), anchor="mm")
        d.text(rot(-80, 0), "S", font=F(52, "Black"), fill=mix("white", a, cy), anchor="mm")
    elif kind == "trafo":
        d.rectangle((cx - 280, cy - 210, cx + 280, cy + 210), outline=mix((120, 130, 150), a, cy), width=36)
        for x, n in ((cx - 262, 6), (cx + 262, 14)):
            for i in range(n):
                y = cy - 180 + i * (360 / n)
                d.rounded_rectangle((x - 50, y, x + 50, y + 360 / n - 6), 8, fill=mix("orange", a, y))
        for i in range(4):
            s = (t * 1.2 + i / 4) % 1; x = cx - 200 + s * 380
            d.polygon([(x, cy - 30), (x + 30, cy), (x, cy + 30)], fill=mix("yel", a * .9, cy))
    elif kind == "sine":
        pts = [(x, cy - 160 * math.sin((x - 110) / 860 * 4 * math.pi - t * 4)) for x in range(110, 971, 6)]
        d.line([(110, cy), (970, cy)], fill=mix((60, 80, 110), a, cy), width=3)
        d.line(pts, fill=mix("yel", a, cy), width=10)
    elif kind == "bolt":
        s = 1 + 0.05 * math.sin(t * 5)
        pts = [(470, 90), (250, 440), (390, 440), (320, 710), (560, 330), (415, 330), (500, 90)]
        d.polygon([(cx + (x - 400) * 1.1 * s, cy + (y - 400) * 1.1 * s) for x, y in pts], fill=mix("yel", a, cy))
    elif kind == "sun":
        for k in range(12):
            ang = t * 0.6 + k * math.pi / 6
            d.line([(cx + 190 * math.cos(ang), cy + 190 * math.sin(ang)), (cx + 270 * math.cos(ang), cy + 270 * math.sin(ang))], fill=mix("yel", a, cy), width=22)
        d.ellipse((cx - 150, cy - 150, cx + 150, cy + 150), fill=mix("yel", a, cy))
    elif kind == "battery":
        lvl = (t * 0.35) % 1
        d.rounded_rectangle((cx - 150, cy - 260, cx + 150, cy + 260), 30, outline=mix("white", a, cy), width=14)
        d.rounded_rectangle((cx - 60, cy - 300, cx + 60, cy - 260), 10, fill=mix("white", a, cy))
        top = cy + 230 - 460 * lvl
        d.rounded_rectangle((cx - 120, top, cx + 120, cy + 230), 16, fill=mix("green", a, cy))
    elif kind == "bulb":
        glow = 0.6 + 0.4 * math.sin(t * 3)
        d.ellipse((cx - 170, cy - 260, cx + 170, cy + 80), fill=mix("yel", a * glow, cy))
        d.rectangle((cx - 80, cy + 70, cx + 80, cy + 180), fill=mix((160, 170, 185), a, cy))
        for i in range(3): d.line([(cx - 80, cy + 95 + i * 30), (cx + 80, cy + 95 + i * 30)], fill=mix((90, 100, 120), a, cy), width=6)
    elif kind == "plug":
        d.rounded_rectangle((cx - 200, cy - 140, cx + 200, cy + 200), 40, fill=mix((200, 210, 225), a, cy))
        for dx in (-90, 90): d.ellipse((cx + dx - 35, cy - 10, cx + dx + 35, cy + 60), fill=mix(TOP, a, cy))
        p = (math.sin(t * 6) + 1) / 2
        d.line([(cx, cy + 200), (cx, cy + 330)], fill=mix("yel", a * (0.5 + p / 2), cy), width=26)

# ---------------------------------------------------------------- scene renderers
def sc_hook(d, t, dur, S, s):
    waves(d, t)
    a1, a2 = back((t - 0.15) / .5), back((t - 0.6) / .5)
    y = 560
    for i, (txt, col, size) in enumerate(s["lines"]):
        aa = a1 if i == 0 else a2
        f = F(size, "Black" if size > 130 else "Bold")
        y = ctext(d, y - 40 * (1 - aa), txt, f, col, cl(aa)) + 10
    ctext(d, 1190, s.get("sub", "In 60 Sekunden erklärt"), F(56, "Medium"), "grey", ap(t, S[-1]))

def sc_icon(d, t, dur, S, s):
    ctext(d, 300, s["title"], F(84, "Black"), s.get("title_color", "white"), ap(t, 0))
    icon(d, s["icon"], t, ap(t, 0.2), 540, s.get("icon_y", 700))
    caption(d, t, dur, S, s["captions"], y=s.get("cap_y", 1250))

def sc_cards(d, t, dur, S, s):
    ctext(d, 300, s["title"], F(84, "Black"), s.get("title_color", "white"), ap(t, 0))
    n = len(s["cards"]); hgt = 290 if n <= 3 else 220; gap = 40 if n <= 3 else 30
    for i, c in enumerate(s["cards"]):
        t0 = S[min(c.get("at", i + 1), len(S) - 1)] - 0.1
        aa = ap(t, t0); y0 = 450 + i * (hgt + gap) + 40 * (1 - aa)
        oc = c.get("color", "water")
        card(d, (90, y0, 990, y0 + hgt), aa, outline=oc)
        d.text((140, y0 + 34), c["big"], font=F(72 if n <= 3 else 60, "Black"), fill=mix(oc, aa, y0))
        for j, ln in enumerate(wrap(c["small"], F(42, "Medium"), 800, d)[:3]):
            d.text((140, y0 + (140 if n <= 3 else 115) + j * 50), ln, font=F(42, "Medium"), fill=mix("white", aa, y0))

def sc_formula(d, t, dur, S, s):
    ctext(d, 330, s["title"], F(76, "Bold"), "white", ap(t, 0))
    rich(d, 470, s["parts"], F(s.get("size", 118), "Black"), ap(t, 0.4))
    span = (S[1] if len(S) > 1 else dur) - 1.0
    for i, (sym, txt, c) in enumerate(s["rows"]):
        aa = ap(t, 0.8 + i * span / max(1, len(s["rows"]))); y = 680 + i * 92
        d.text((215, y), sym, font=F(64, "Black"), fill=mix(c, aa, y))
        d.text((300, y + 10), txt, font=F(48, "Medium"), fill=mix("white", aa, y))
    if "box" in s:
        b = s["box"]; ab = ap(t, S[min(1, len(S) - 1)] - .1); y0 = 1170 - 30 * (1 - ab)
        card(d, (110, y0, 970, y0 + 390), ab, outline="yel")
        ctext(d, y0 + 35, b.get("label", "Beispiel"), F(44, "SemiBold"), "grey", ab)
        ctext(d, y0 + 105, b["line"], F(56, "Bold"), "white", ab)
        ctext(d, y0 + 185, b["big"], F(92, "Black"), "yel", ab)
        if b.get("foot"): ctext(d, y0 + 300, b["foot"], F(42, "Medium"), "grey", ab)

def sc_compare(d, t, dur, S, s):
    ctext(d, 300, s["title"], F(84, "Black"), "white", ap(t, 0))
    a = ap(t, 0.2); L, R = s["left"], s["right"]
    for x, side, col in ((290, L, "grey"), (790, R, "yel")):
        card(d, (x - 220, 480, x + 220, 900), a, outline=col)
        ctext(d, 520, side["label"], F(44, "SemiBold"), "grey", a, maxw=400, x=x)
        ctext(d, 640, side["value"], F(96, "Black"), col, a, maxw=420, x=x)
    p = ease((t - S[min(1, len(S) - 1)]) / 1.0)
    d.line([(520, 690), (520 + 40 * p, 690)], fill=mix("yel", a, 690), width=10)
    caption(d, t, dur, S, s["captions"], y=1100)

def sc_outro(d, t, dur, S, s):
    waves(d, t); a = back((t - .1) / .5)
    ctext(d, 640, "Folgen für mehr", F(84, "Bold"), "white", cl(a))
    ctext(d, 760, "TECHNIK", F(170, "Black"), "yel", cl(a))
    ctext(d, 950, "in 60 Sekunden", F(84, "Bold"), "white", cl(a))
    if s.get("next"): ctext(d, 1130, "Nächstes Mal: " + s["next"], F(46, "Medium"), "grey", ap(t, 1.0), maxw=860)

R = dict(hook=sc_hook, icon=sc_icon, cards=sc_cards, formula=sc_formula, compare=sc_compare, outro=sc_outro)

# ---------------------------------------------------------------- pipeline
def tts(text, path):
    subprocess.run(["python3", "-m", "piper", "-m", VOICE, "--length-scale", "0.84", "-f", path],
                   input=text.encode(), check=True, capture_output=True)
    with wave.open(path) as w: return w.getnframes() / w.getframerate()

def main(spec_path):
    spec = json.load(open(spec_path)); slug = spec["slug"]
    work = f"/tmp/build_{slug}"; os.makedirs(work, exist_ok=True)
    out = os.path.join(ROOT, "out"); os.makedirs(out, exist_ok=True)
    scenes = [{"type": "hook", **spec["hook"]}] + spec["scenes"] + [{"type": "outro", "say": ["Folg für mehr Technik in sechzig Sekunden!"], "next": spec.get("next")}]
    # narration
    for si, s in enumerate(scenes):
        t = 0.3; s["_items"] = []
        for i, sent in enumerate(s["say"]):
            p = f"{work}/vo_{si}_{i}.wav"; dur = tts(sent, p)
            s["_items"].append((p, t)); t += dur + 0.12
        s["_dur"] = round(t - 0.12 + 0.35, 2)
    total = sum(s["_dur"] for s in scenes)
    # video
    parts = []
    gt0 = 0
    for si, s in enumerate(scenes):
        S = [st for _, st in s["_items"]]; dur = s["_dur"]; n = int(round(dur * FPS))
        f = f"{work}/s{si:02d}.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-vf", f"fade=in:st=0:d=0.25,fade=out:st={dur-0.25}:d=0.25", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                              "-pix_fmt", "yuv420p", f], stdin=subprocess.PIPE)
        for i in range(n):
            t = i / FPS; img = BASE.copy(); d = ImageDraw.Draw(img)
            R[s["type"]](d, t, dur, S, s)
            if s["type"] not in ("hook", "outro"): header(d, gt0 + t, total, spec["header"])
            p.stdin.write(img.tobytes())
        p.stdin.close(); assert p.wait() == 0
        parts.append(f); gt0 += dur
    open(f"{work}/list.txt", "w").write("".join(f"file '{x}'\n" for x in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", f"{work}/v.mp4"], check=True)
    # audio
    sys.path.insert(0, os.path.dirname(__file__)); import mixer
    mixer.mix(scenes, total, f"{work}/a.wav", seed=sum(map(ord, slug)))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/a.wav", "-af",
                    "highpass=f=50,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,loudnorm=I=-14:TP=-1.5:LRA=9",
                    "-ar", "48000", "-ac", "2", f"{work}/a2.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/v.mp4", "-i", f"{work}/a2.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", f"{out}/{slug}.mp4"], check=True)
    json.dump(spec["meta"], open(f"{out}/{slug}.meta.json", "w"), ensure_ascii=False, indent=1)
    # preview stills (for a quick visual check)
    for k, frac in enumerate((0.15, 0.45, 0.8)):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(total * frac), "-i", f"{out}/{slug}.mp4", "-frames:v", "1",
                        "-vf", "scale=360:-1", f"{work}/still{k}.png"], check=True)
    print(json.dumps({"video": f"{out}/{slug}.mp4", "seconds": round(total, 1), "stills": [f"{work}/still{k}.png" for k in range(3)]}))

if __name__ == "__main__":
    main(sys.argv[1])

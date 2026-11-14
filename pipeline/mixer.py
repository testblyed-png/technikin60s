import wave, numpy as np
SR = 44100
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def mix(scenes, TOTAL, outpath, seed=7):
    rng = np.random.default_rng(seed)
    N = int(TOTAL * SR) + SR
    offs = []; o = 0.0
    for s in scenes: offs.append(o); o += s["_dur"]
    def load(f):
        with wave.open(f) as w:
            sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        t_new = np.arange(int(len(x) * SR / sr)) / SR
        return np.interp(t_new, np.arange(len(x)) / sr, x)
    def put(buf, x, t, g=1.0):
        i = int(t * SR); j = min(len(buf), i + len(x))
        if j > i: buf[i:j] += g * x[: j - i]
    voice = np.zeros(N, np.float32)
    for s, off in zip(scenes, offs):
        for f, st, _ in s["_items"]: put(voice, load(f), off + st)
    voice /= max(1e-6, np.abs(voice).max()) / 0.9
    # ---------------- music (Am – F – C – G, 100 bpm)
    bpm = 100; beat = 60 / bpm; bar = 4 * beat
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55, 60], [55, 59, 62]]
    music = np.zeros(N, np.float32)
    tt = np.arange(N) / SR
    # pad
    for ci in range(int(TOTAL / bar) + 2):
        t0 = ci * bar; ch = chords[ci % 4]
        seg = np.arange(int(bar * SR) + int(0.5 * SR)) / SR
        env = np.minimum(1, seg / 0.6) * np.clip((bar + 0.5 - seg) / 0.8, 0, 1)
        tone = np.zeros_like(seg)
        for m in ch:
            f = midi(m)
            for det in (-0.12, 0.12):
                ff = f * 2 ** (det / 12)
                tone += np.sin(2 * np.pi * ff * seg) + 0.25 * np.sin(4 * np.pi * ff * seg)
        put(music, (0.05 * env * tone).astype(np.float32), t0)
        # bass
        bf = midi(ch[0] - 12)
        benv = np.exp(-seg / 1.2) * np.minimum(1, seg / 0.02)
        put(music, (0.22 * benv * np.sin(2 * np.pi * bf * seg)).astype(np.float32), t0)
        put(music, (0.16 * benv * np.sin(2 * np.pi * bf * seg)).astype(np.float32), t0 + 2 * beat)
        # pluck arpeggio, eighth notes
        arp = ch + [ch[1] + 12]
        for k in range(8):
            m = arp[[0, 1, 2, 3, 2, 1, 2, 3][k] % len(arp)] + 12
            ps = np.arange(int(0.5 * SR)) / SR
            pe = np.exp(-ps / 0.16) * np.minimum(1, ps / 0.004)
            put(music, (0.07 * pe * (np.sin(2 * np.pi * midi(m) * ps) + 0.3 * np.sin(4 * np.pi * midi(m) * ps))).astype(np.float32), t0 + k * beat / 2)
        # soft kick + hat
        for b in range(4):
            ks = np.arange(int(0.25 * SR)) / SR
            kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-ks / 0.03)) * ks) * np.exp(-ks / 0.09)
            if b in (0, 2): put(music, (0.32 * kick).astype(np.float32), t0 + b * beat)
            hs = rng.standard_normal(int(0.05 * SR)).astype(np.float32)
            hs = np.diff(hs, prepend=0) * np.exp(-np.arange(len(hs)) / SR / 0.012)
            put(music, 0.05 * hs, t0 + b * beat + beat / 2)
    # fade music in/out
    music *= np.clip(tt / 1.0, 0, 1) * np.clip((TOTAL - tt) / 1.5, 0, 1)
    music /= np.abs(music).max()

    # ducking envelope from voice activity
    act = np.abs(voice) > 0.02
    k = int(0.25 * SR)
    act = np.convolve(act.astype(np.float32), np.ones(k) / k, mode="same") > 0.01
    env = np.convolve(act.astype(np.float32), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
    mgain = 0.30 - 0.20 * env

    # ---------------- sfx
    sfx = np.zeros(N, np.float32)
    def whoosh(dur=0.45):
        n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
        s = np.arange(n) / n
        # moving one-pole lowpass sweep
        y = np.zeros(n, np.float32); a_prev = 0
        cut = 0.02 + 0.25 * np.sin(np.pi * s) ** 2
        for i in range(n): a_prev += cut[i] * (x[i] - a_prev); y[i] = a_prev
        return y * np.sin(np.pi * s) ** 1.5 * 1.6
    def pop(f=880):
        s = np.arange(int(0.12 * SR)) / SR
        return (np.sin(2 * np.pi * f * s * (1 + 0.6 * np.exp(-s / 0.02))) * np.exp(-s / 0.035)).astype(np.float32)
    def boom():
        s = np.arange(int(0.9 * SR)) / SR
        return (np.sin(2 * np.pi * (40 + 70 * np.exp(-s / 0.08)) * s) * np.exp(-s / 0.35)).astype(np.float32)
    def chime():
        s = np.arange(int(1.4 * SR)) / SR; y = np.zeros_like(s)
        for i, m in enumerate([72, 76, 79, 84]):
            d = s - i * 0.09; e = np.where(d > 0, np.exp(-np.clip(d, 0, None) / 0.4), 0)
            y += e * np.sin(2 * np.pi * midi(m) * np.clip(d, 0, None))
        return (0.5 * y).astype(np.float32)

    W = whoosh()
    for off in offs[1:]: put(sfx, W, off - 0.25, 0.35)
    put(sfx, boom(), offs[0] + 0.6, 0.55)
    for s, off in zip(scenes, offs):
        if s["type"] in ("cards", "formula", "compare"):
            for i, (_, st, _) in enumerate(s["_items"][1:]): put(sfx, pop(760 + 110 * i), off + st, 0.22)
    put(sfx, chime(), offs[-1] + 0.1, 0.3)
    mix = voice * 1.0 + music * mgain + sfx
    mix /= np.abs(mix).max() / 0.95
    out = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(outpath, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out[: int(TOTAL * SR)].tobytes())

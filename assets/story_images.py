import math, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H, S = 1600, 900, 2
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
LB = "/usr/share/fonts/truetype/liberation/"
FD = "/usr/share/fonts/truetype/dejavu/"
def F(size, bold=False, mono=False):
    if mono:
        return ImageFont.truetype(FD + ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"), int(size * S))
    return ImageFont.truetype(LB + ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf"), int(size * S))

GOLD, CYAN, RED = (255, 214, 90), (80, 200, 255), (255, 92, 60)
INK, INK2, MUTED = (255, 255, 255), (200, 228, 212), (140, 175, 158)
CARD, CARD_LINE = (12, 40, 30, 235), (255, 255, 255, 40)

def speed_col(v):
    t = max(0.0, min(1.0, v))
    a, b, c = CYAN, GOLD, RED
    if t < 0.5:
        u = t / 0.5; return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
    u = (t - 0.5) / 0.5; return tuple(int(b[i] + (c[i] - b[i]) * u) for i in range(3))

def s(*v):  # scale coordinates
    return [int(x * S) for x in v]

class Slide:
    def __init__(self, num, kicker, title, foot="Out-of-sample results · 2023–25 NFL regular season"):
        self.img = Image.new("RGBA", (W * S, H * S))
        d = ImageDraw.Draw(self.img)
        top, bot = (10, 44, 30), (4, 22, 16)
        for y in range(H * S):
            t = y / (H * S)
            d.line([(0, y), (W * S, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
        lay = self.layer()
        for x in range(80, W, 160):
            lay.line(s(x, 0, x, H), fill=(255, 255, 255, 16), width=2 * S)
        self.flush()
        self.d = ImageDraw.Draw(self.img)
        self.d.rectangle(s(80, 56, 140, 61), fill=GOLD)
        self.d.text(s(80, 74), f"{num:02d} · {kicker.upper()}", font=F(22, True), fill=GOLD)
        self.d.text(s(80, 106), title, font=F(52, True), fill=INK)
        self.d.text(s(80, 852), "NFL Big Data Bowl 2027  ·  Explosiveness Transfers, Smoothness Misleads", font=F(18), fill=MUTED)
        r = foot
        self.d.text((W * S - int(self.d.textlength(r, font=F(18))) - 80 * S, 852 * S), r, font=F(18), fill=MUTED)
        self.num = num

    def layer(self):
        self._lay = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        return ImageDraw.Draw(self._lay)

    def flush(self):
        self.img = Image.alpha_composite(self.img, self._lay)
        self.d = ImageDraw.Draw(self.img)

    def card(self, x0, y0, x1, y1, accent=None):
        lay = self.layer()
        lay.rounded_rectangle(s(x0, y0, x1, y1), radius=18 * S, fill=CARD, outline=CARD_LINE, width=2 * S)
        self.flush()
        if accent:
            self.d.rounded_rectangle(s(x0, y0, x0 + 6, y1), radius=3 * S, fill=accent)

    def text(self, xy, txt, font, fill=INK, maxw=None, lh=1.3):
        x, y = xy
        if maxw is None:
            self.d.text(s(x, y), txt, font=font, fill=fill)
            return y + font.size / S * lh
        words, line = txt.split(), ""
        for w_ in words:
            trial = (line + " " + w_).strip()
            if self.d.textlength(trial, font=font) > maxw * S and line:
                self.d.text(s(x, y), line, font=font, fill=fill); y += font.size / S * lh; line = w_
            else:
                line = trial
        if line:
            self.d.text(s(x, y), line, font=font, fill=fill); y += font.size / S * lh
        return y

    def poly(self, pts, fill, width=3):
        self.d.line([tuple(int(c * S) for c in p) for p in pts], fill=fill, width=width * S, joint="curve")

    def dot(self, x, y, r, fill):
        self.d.ellipse(s(x - r, y - r, x + r, y + r), fill=fill)

    def arrow(self, x0, y0, x1, y1, fill=MUTED, width=3):
        self.poly([(x0, y0), (x1, y1)], fill, width)
        a = math.atan2(y1 - y0, x1 - x0); L = 14
        self.d.polygon([tuple(int(c * S) for c in p) for p in [
            (x1, y1), (x1 - L * math.cos(a - 0.45), y1 - L * math.sin(a - 0.45)),
            (x1 - L * math.cos(a + 0.45), y1 - L * math.sin(a + 0.45))]], fill=fill)

    def save(self, name):
        p = os.path.join(OUT, f"{self.num:02d}_{name}.png")
        self.img.convert("RGB").resize((W, H), Image.LANCZOS).save(p, optimize=True)
        print("saved", p)

# ---------- 01 The problem ----------
sl = Slide(1, "The problem", "Same 40 time. Different athletes.", foot="Illustrative sprint model")
sl.text((80, 180), "A stopwatch reduces a drill to one number. 10 Hz sensor tracking records the whole movement.",
        F(26), INK2, maxw=1400)
# left: stopwatch card
sl.card(80, 250, 520, 800)
sl.text((115, 285), "TRADITIONAL", F(20, True), MUTED)
sl.text((115, 315), "40-yard dash", F(30, True))
cx, cy, R = 300, 520, 130
sl.d.ellipse(s(cx - R, cy - R, cx + R, cy + R), outline=INK2, width=6 * S)
sl.d.rectangle(s(cx - 18, cy - R - 34, cx + 18, cy - R - 12), fill=INK2)
for k in range(12):
    a = k * math.pi / 6
    sl.poly([(cx + (R - 18) * math.sin(a), cy - (R - 18) * math.cos(a)),
             (cx + (R - 6) * math.sin(a), cy - (R - 6) * math.cos(a))], INK2, 3)
txt = "4.45 s"; f = F(54, True)
sl.d.text((int(cx * S - sl.d.textlength(txt, font=f) / 2), int((cy - 34) * S)), txt, font=f, fill=GOLD)
sl.text((115, 690), "Player A = 4.45 s", F(22), INK2)
sl.text((115, 722), "Player B = 4.45 s", F(22), INK2)
sl.text((115, 754), "→ identical on paper", F(22, True), INK)

# right: speed profiles (illustrative exponential sprint model, both cover 40 yd in 4.45 s)
sl.card(560, 250, 1520, 800)
sl.text((595, 285), "TRACKING", F(20, True), MUTED)
sl.text((595, 315), "Speed over the same 40 yards (10 Hz)", F(30, True))
px0, py0, px1, py1 = 640, 400, 1470, 705
T = 4.45
def vmax_for(tau):
    return 40 / (T - tau * (1 - math.exp(-T / tau)))
profiles = [("Player A — explosive start", 0.55, GOLD), ("Player B — slow build, higher top speed", 1.25, CYAN)]
vtop = max(vmax_for(t) for _, t, _ in profiles) * 1.08
for g in range(0, 5):
    yy = py1 - (py1 - py0) * g / 4
    lay = sl.layer(); lay.line(s(px0, yy, px1, yy), fill=(255, 255, 255, 30), width=1 * S); sl.flush()
sl.poly([(px0, py1), (px1, py1)], MUTED, 2)
for tt in range(0, 5):
    xx = px0 + (px1 - px0) * tt / T
    sl.text((xx - 10, py1 + 10), f"{tt}s", F(17), MUTED)
sl.text((px0 - 5, py0 - 34), "speed ↑", F(17), MUTED)
for name, tau, col in profiles:
    vm = vmax_for(tau)
    pts = []
    for i in range(0, 46):
        t = i * T / 45
        v = vm * (1 - math.exp(-t / tau))
        pts.append((px0 + (px1 - px0) * t / T, py1 - (py1 - py0) * v / vtop))
    sl.poly(pts, col, 4)
    for i in range(0, 46, 3):
        sl.dot(*pts[i], 5, col)
# direct labels
sl.text((760, 420), profiles[0][0], F(20, True), INK)
sl.dot(748, 432, 7, GOLD)
sl.text((990, 625), profiles[1][0], F(20, True), INK)
sl.dot(978, 637, 7, CYAN)
sl.text((595, 758), "The curve shows how each player gets there: acceleration, top speed, and timing.", F(19), INK2)
sl.save("problem")


import csv
PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "data/processed/analysis") + "/"
def rows(name):
    with open(PROJ + name) as f:
        return list(csv.DictReader(f))
GOOD, BAD, PART = (12, 163, 12), (208, 59, 59), (250, 178, 25)
NEG = (120, 170, 255)

def plot(sl, box, xs, ys, color, xlabel, ylabel, invert=False):
    """Minimal scatter with dashed least-squares trend inside box=(x0,y0,x1,y1)."""
    x0, y0, x1, y1 = box
    px0, py0, px1, py1 = x0 + 70, y0 + 50, x1 - 30, y1 - 60
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    px_, py_ = (hi_x - lo_x) * 0.04, (hi_y - lo_y) * 0.06
    lo_x, hi_x, lo_y, hi_y = lo_x - px_, hi_x + px_, lo_y - py_, hi_y + py_
    X = lambda v: px0 + (v - lo_x) / (hi_x - lo_x) * (px1 - px0)
    Y = lambda v: (py0 + (v - lo_y) / (hi_y - lo_y) * (py1 - py0)) if invert else (py1 - (v - lo_y) / (hi_y - lo_y) * (py1 - py0))
    lay = sl.layer()
    for k in range(5):
        yy = py0 + (py1 - py0) * k / 4
        lay.line(s(px0, yy, px1, yy), fill=(255, 255, 255, 28), width=1 * S)
    sl.flush()
    for k in range(5):
        val = hi_y - (hi_y - lo_y) * k / 4 if not invert else lo_y + (hi_y - lo_y) * k / 4
        sl.text((x0 + 14, py0 + (py1 - py0) * k / 4 - 10), f"{val:.1f}", F(15), MUTED)
    sl.poly([(px0, py1), (px1, py1)], MUTED, 2)
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    for k in range(0, 40, 2):
        a0 = lo_x + (hi_x - lo_x) * k / 40; a1 = lo_x + (hi_x - lo_x) * (k + 1) / 40
        sl.poly([(X(a0), Y(my + b * (a0 - mx))), (X(a1), Y(my + b * (a1 - mx)))], INK2, 3)
    for a, c in zip(xs, ys):
        sl.dot(X(a), Y(c), 7, color)
    sl.text((px0, py1 + 14), xlabel, F(17), MUTED)
    sl.text((x0 + 14, y0 + 8), ylabel, F(17), MUTED)

def glyph(sl, g, gx0, gy0, gx1, gy1, col):
    if g == "accel":
        sl.poly([(gx0 + (gx1 - gx0) * i / 30, gy1 - (gy1 - gy0) * (1 - math.exp(-i / 6))) for i in range(31)], col, 4)
    elif g == "cod":
        sl.poly([(gx0, gy1 - 20), (gx0 + 120, gy1 - 20), (gx1 - 10, gy0)], col, 4); sl.dot(gx0 + 120, gy1 - 20, 8, INK)
    elif g == "decel":
        sl.poly([(gx0, gy0 + 50), (gx1, gy0 + 50)], MUTED, 3); sl.arrow(gx0, gy0 + 50, gx0 + 150, gy0 + 50, col, 5)
        sl.d.rectangle(s(gx0 + 150, gy0 + 30, gx0 + 158, gy0 + 70), fill=INK)
    elif g == "smooth":
        sl.poly([(gx0 + i * (gx1 - gx0) / 40, gy0 + 30 + 6 * math.sin(i / 3)) for i in range(41)], MUTED, 3)
        sl.poly([(gx0 + i * (gx1 - gx0) / 40, gy0 + 90 + (18 if i % 2 else -18) * (0.5 + 0.5 * math.sin(i))) for i in range(41)], col, 2)
    elif g == "recov":
        pts = [(gx0 + (gx1 - gx0) * i / 30, gy0 + 10 + (gy1 - gy0 - 20) * (1 - abs(i - 12) / 12 if i <= 12 else max(0, 1 - (i - 12) / 6))) for i in range(31)]
        sl.poly(pts, col, 4); sl.dot(*pts[12], 8, INK)

# ---------- 02 MEI v2 ----------
sl = Slide(2, "The metric", "MEI v2: let the data set the weights")
sl.text((80, 180), "Five components from 10 Hz Combine tracking. For defensive linemen, the data rewrote the original weights.", F(26), INK2, maxw=1440)
learned = {r["component"]: float(r["weight"]) for r in rows("learned_weights.csv") if r["position"] == "DL"}
comps = [("Acceleration", "accel_eff", 25, "accel", "Peak speed ÷ time to reach it"),
         ("Deceleration", "decel_ctrl", 20, "decel", "Speed lost ÷ distance used"),
         ("Change of direction", "cod_eff", 25, "cod", "Heading change ÷ time lost"),
         ("Smoothness", "smoothness", 15, "smooth", "Acceleration variation around its trend"),
         ("Recovery", "recovery_acc", 15, "recov", "Speed regained after a cut")]
cw, gap, x = 272, 20, 80
for name, key, orig, g, defin in comps:
    w = learned[key]
    col = GOLD if w >= 0 else NEG
    sl.card(x, 250, x + cw, 740)
    sl.text((x + 24, 270), "LEARNED FOR DL", F(15, True), MUTED)
    sl.text((x + 24, 292), f"{w:+.2f}", F(56, True), col)
    sl.text((x + 24, 362), f"original weight {orig / 100:.2f}", F(17), MUTED)
    sl.text((x + 24, 400), name, F(24, True), INK)
    glyph(sl, g, x + 24, 460, x + cw - 24, 590, col)
    sl.text((x + 24, 620), defin, F(18), INK2, maxw=cw - 48)
    x += cw + gap
sl.card(80, 762, 1520, 832)
sl.text((105, 770), "Learned on two draft classes, tested on the third:", F(19), INK2)
sl.text((105, 798), "DL get-off ρ 0.66 with learned weights vs. ρ 0.36 with the original weights", F(22, True), GOLD)
sl.save("mei")

# ---------- 03 Transfer ----------
sl = Slide(3, "Finding 1", "Explosiveness transfers to the pass rush")
sl.text((80, 180), "A DL index learned from Combine tracking, trained only on get-off, scored on draft classes it never saw.", F(26), INK2, maxw=1440)
t = {r["outcome"]: r for r in rows("transfer.csv")}
stats = [("TRAINED ON", "NFL get-off", f"ρ {-float(t['get_off_eb']['rho']):.2f}", f"95% CI {-float(t['get_off_eb']['hi']):.2f}–{-float(t['get_off_eb']['lo']):.2f}", INK),
         ("NEVER TRAINED ON", "Pressure rate", f"ρ {float(t['pressure_rate_eb']['rho']):.2f}", f"95% CI {float(t['pressure_rate_eb']['lo']):.2f}–{float(t['pressure_rate_eb']['hi']):.2f} · {float(t['pressure_rate_eb']['partial_rho_pick']):.2f} given draft slot", GOLD),
         ("GIVEN DRAFT SLOT", "Snaps per season", f"ρ {float(t['snaps_per_season']['partial_rho_pick']):.2f}", "teams play who they drafted; the index predicts who gets home", INK2)]
y = 250
for tag, what, num, sub, col in stats:
    sl.card(80, y, 660, y + 170, accent=col if col == GOLD else None)
    sl.text((110, y + 20), tag, F(16, True), MUTED)
    sl.text((110, y + 46), what, F(26, True), INK)
    sl.text((420, y + 30), num, F(48, True), col)
    sl.text((110, y + 110), sub, F(17), INK2, maxw=520)
    y += 185
d = [r for r in rows("dl_players.csv") if r["index"] and r["pressure_rate_eb"] and r["n_pressure_rate"] and float(r["n_pressure_rate"]) >= 50]
xs = [float(r["index"]) for r in d]; mu = sum(xs) / len(xs); sd = (sum((v - mu) ** 2 for v in xs) / (len(xs) - 1)) ** 0.5
sl.card(690, 250, 1520, 800)
sl.text((1490 - 420, 268), f"Each dot is a defensive lineman (n = {len(d)})", F(17), INK2)
plot(sl, (700, 260, 1510, 800), [(v - mu) / sd for v in xs], [float(r["pressure_rate_eb"]) * 100 for r in d], ORANGE := (217, 89, 38),
     "Combine Explosiveness Index (out-of-sample, z) →", "NFL pressure rate (%)")
sl.save("transfer")

# ---------- 04 Smoothness ----------
sl = Slide(4, "Finding 2", "The smoothness paradox")
sl.text((80, 180), "We expected smooth movement to signal control. For defensive linemen, the opposite is true.", F(26), INK2, maxw=1440)
d = [r for r in rows("dl_players.csv") if r["smoothness"] and r["pressure_rate_eb"] and r["n_pressure_rate"] and float(r["n_pressure_rate"]) >= 50]
sl.card(80, 250, 910, 800)
sl.text((880 - 420, 268), f"Each dot is a defensive lineman (n = {len(d)})", F(17), INK2)
plot(sl, (90, 260, 900, 800), [float(r["smoothness"]) for r in d], [float(r["pressure_rate_eb"]) * 100 for r in d], GOLD,
     "Combine movement smoothness (smoother →)", "NFL pressure rate (%)")
facts = [("ρ −0.53", "pressure rate vs. smoothness, holding draft slot fixed (q < 0.001)"),
         ("ρ +0.58", "smoother DL are slower off the ball (get-off time, given draft slot)"),
         ("ρ +0.26", "smoother movers also run slower 40s, within position")]
y = 250
for num, txt in facts:
    sl.card(940, y, 1520, y + 150)
    sl.text((970, y + 22), num, F(44, True), GOLD)
    sl.text((970, y + 82), txt, F(18), INK2, maxw=520)
    y += 165
sl.text((940, 752), "Explosive movement is variable movement.", F(22, True), INK)
sl.save("smoothness")

# ---------- 05 Scorecard ----------
sl = Slide(5, "Hypothesis scorecard", "What held up, and what didn't")
sl.text((80, 180), "Every original hypothesis tested out of sample. Refuted results are findings too.", F(26), INK2)
card = [("SUPPORTED", GOOD, "Tracking metrics predict NFL performance", "For DL: get-off, pressure and sacks (permutation p ≤ 0.01)"),
        ("PARTLY", PART, "Position drills carry hidden value", "They cover 100% of players vs. 35% for the three-cone"),
        ("REFUTED", BAD, "Hybrid beats traditional metrics alone", "No significant gain anywhere (DL get-off +0.04 R²)"),
        ("REFUTED", BAD, "Acceleration matters more than top speed", "DL get-off: acceleration ρ −0.62, top speed ρ −0.66"),
        ("REFUTED", BAD, "Deceleration predicts WR separation", "ρ −0.10 holding draft slot fixed"),
        ("REFUTED", BAD, "Movement symmetry predicts availability", "No position above |ρ| 0.14")]
y = 248
for label, col, h, ev in card:
    sl.card(80, y, 1520, y + 86)
    sl.d.rounded_rectangle(s(104, y + 24, 264, y + 62), radius=19 * S, fill=col)
    f = F(17, True); tw = sl.d.textlength(label, font=f)
    sl.d.text((int(184 * S - tw / 2), int((y + 33) * S)), label, font=f, fill=(255, 255, 255) if col == BAD else (10, 30, 22))
    sl.text((290, y + 16), h, F(23, True), INK)
    sl.text((290, y + 50), ev, F(18), INK2)
    y += 96
sl.save("scorecard")

# ---------- 06 Impact ----------
sl = Slide(6, "Football operations impact", "How a front office would use this")
sl.text((80, 180), "Specific, evidence-backed uses, and where not to spend evaluation time.", F(26), INK2)
impact = [("Draft evaluation", "Rank pass rushers within a draft tier with the DL Explosiveness Index. It predicts pressure beyond draft slot."),
          ("Missing workouts", "About one in five DL had no official 40. Tracked drills still measure their explosiveness."),
          ("Scouting language", "Do not reward 'smooth' DL movement. For pass rushers, violent speed changes are the signal."),
          ("Where not to look", "Combine movement did not predict WR separation or OL protection. Spend that time elsewhere.")]
x = 80
for i, (h, b) in enumerate(impact):
    sl.card(x, 250, x + 336, 590)
    sl.d.ellipse(s(x + 30, 280, x + 86, 336), fill=GOLD)
    f = F(28, True); tw = sl.d.textlength(str(i + 1), font=f)
    sl.d.text((int((x + 58) * S - tw / 2), int(290 * S)), str(i + 1), font=f, fill=(10, 30, 22))
    sl.text((x + 30, 360), h, F(27, True))
    sl.text((x + 30, 410), b, F(20), INK2, maxw=280)
    x += 368
sl.card(80, 620, 1520, 800)
sl.text((120, 648), "THE TAKEAWAY", F(18, True), GOLD)
sl.text((120, 684), "Explosiveness transfers.", F(44, True), INK)
sl.text((120, 738), "Smoothness misleads.", F(44, True), GOLD)
sl.save("impact")

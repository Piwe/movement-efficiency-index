import math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, S = 1600, 900, 2  # supersample
w, h = W * S, H * S
FD = "/usr/share/fonts/truetype/dejavu/"
LB = "/usr/share/fonts/truetype/liberation/"
def font(name, size):
    return ImageFont.truetype(name, size * S)

img = Image.new("RGB", (w, h))
px = img.load()
# vertical turf gradient
top, bot = (10, 44, 30), (4, 22, 16)
d = ImageDraw.Draw(img)
for y in range(h):
    t = y / h
    d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

# mowing stripes
stripe = Image.new("RGBA", (w, h), (0, 0, 0, 0))
sd = ImageDraw.Draw(stripe)
step = 160 * S
for i, x in enumerate(range(0, w, step)):
    if i % 2:
        sd.rectangle([x, 0, x + step, h], fill=(255, 255, 255, 7))
# yard lines + hash marks
for i, x in enumerate(range(80 * S, w, step)):
    sd.line([(x, 0), (x, h)], fill=(255, 255, 255, 38), width=3 * S)
    for yy in (int(h * 0.36), int(h * 0.64)):
        for k in range(1, 5):
            hx = x + k * step // 5
            sd.line([(hx, yy - 9 * S), (hx, yy + 9 * S)], fill=(255, 255, 255, 30), width=2 * S)
img = Image.alpha_composite(img.convert("RGBA"), stripe)

# tracking trail: accelerate -> decelerate -> sharp cut -> re-accelerate
pts, x, y, v = [], 760.0, 690.0, 0.0
heading = 0.0
for f in range(60):
    if f < 22:
        v = min(v + 3.2, 56)          # acceleration phase
    elif f < 30:
        v = max(v - 7.5, 10)          # deceleration into the break
    elif f < 33:
        heading -= math.radians(20)   # sharp heading change
        v = 12
    else:
        v = min(v + 5.0, 52)          # recovery acceleration
    x += v * math.cos(heading) * 0.42
    y += v * math.sin(heading) * 0.42
    pts.append((x, y, v))

def speed_col(v):
    t = max(0.0, min(1.0, v / 56))
    a, b, c = (80, 200, 255), (255, 214, 90), (255, 92, 60)
    if t < 0.5:
        u = t / 0.5; return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
    u = (t - 0.5) / 0.5; return tuple(int(b[i] + (c[i] - b[i]) * u) for i in range(3))

glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
trail = Image.new("RGBA", (w, h), (0, 0, 0, 0))
td = ImageDraw.Draw(trail)
P = [(px_ * S, py_ * S, v) for px_, py_, v in pts if px_ < W - 30 and py_ > 40]
for (x0, y0, _), (x1, y1, v) in zip(P, P[1:]):
    td.line([(x0, y0), (x1, y1)], fill=speed_col(v) + (110,), width=3 * S)
for i, (cx, cy, v) in enumerate(P):
    r = (7 if i % 5 else 10) * S
    col = speed_col(v)
    gd.ellipse([cx - r * 2.4, cy - r * 2.4, cx + r * 2.4, cy + r * 2.4], fill=col + (90,))
    td.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (255,))
glow = glow.filter(ImageFilter.GaussianBlur(14 * S))
img = Image.alpha_composite(img, glow)
img = Image.alpha_composite(img, trail)

# annotations along the trail
ad = ImageDraw.Draw(img)
small = font(FD + "DejaVuSansMono.ttf", 19)
def label(idx, text, dx, dy):
    cx, cy, _ = P[idx]
    tx, ty = cx + dx * S, cy + dy * S
    ad.line([(cx, cy), (tx, ty)], fill=(255, 255, 255, 120), width=2 * S)
    ad.text((tx + 6 * S, ty - 12 * S), text, font=small, fill=(225, 238, 230))
label(12, "ACCELERATION", -40, 70)
label(26, "DECELERATION", 30, 70)
label(31, "CHANGE OF DIRECTION", 40, 10)
label(44, "RECOVERY", 40, 0)

# left text panel with fade
panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
pd = ImageDraw.Draw(panel)
for x in range(0, int(w * 0.62)):
    a = int(215 * max(0, 1 - (x / (w * 0.62)) ** 2.2))
    pd.line([(x, 0), (x, h)], fill=(3, 14, 10, a))
img = Image.alpha_composite(img, panel)

d = ImageDraw.Draw(img)
X = 90 * S
d.rectangle([X, 120 * S, X + 70 * S, 126 * S], fill=(255, 214, 90))
d.text((X, 145 * S), "NFL BIG DATA BOWL 2027", font=font(LB + "LiberationSans-Bold.ttf", 28), fill=(255, 214, 90))
title = font(LB + "LiberationSans-Bold.ttf", 78)
d.text((X, 200 * S), "Explosiveness", font=title, fill=(255, 255, 255))
d.text((X, 290 * S), "Transfers.", font=title, fill=(255, 214, 90))
d.text((X, 380 * S), "Smoothness", font=title, fill=(255, 255, 255))
d.text((X, 470 * S), "Misleads.", font=title, fill=(255, 214, 90))
d.text((X, 580 * S), "Rebuilding the Movement Efficiency Index (MEI)", font=font(LB + "LiberationSans-Regular.ttf", 30), fill=(190, 230, 205))

# key results
stat = font(LB + "LiberationSans-Bold.ttf", 44)
lab = font(LB + "LiberationSans-Regular.ttf", 21)
for i, (num, text) in enumerate([("ρ 0.54", "DL pressure rate, predicted\nby an index never trained on it"),
                                 ("ρ −0.53", "smoother Combine movers\nget fewer NFL pressures")]):
    xx = X + i * 330 * S
    d.text((xx, 650 * S), num, font=stat, fill=(255, 214, 90))
    d.multiline_text((xx, 705 * S), text, font=lab, fill=(200, 228, 212), spacing=4 * S)

d.text((X, 805 * S), "510 prospects · 10 Hz Combine tracking → 2023–25 NFL regular season",
       font=font(LB + "LiberationSans-Regular.ttf", 22), fill=(150, 185, 168))

img = img.convert("RGB").resize((W, H), Image.LANCZOS)
img.save(sys.argv[1], optimize=True)
print("saved", sys.argv[1])

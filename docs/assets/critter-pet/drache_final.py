# Critter-Pet Drache (Marks Wahl 11.11.2026): chinesischer Drache, Design 2, etwas dünner, Beine unverändert
import math
from PIL import Image, ImageDraw

W, H = 84, 44
PAL = {
    "K": (40, 8, 10, 255),
    "D": (150, 24, 26, 255),
    "R": (214, 50, 40, 255),
    "L": (246, 112, 80, 255),
    "Y": (246, 196, 82, 255),
    "O": (214, 146, 48, 255),
    "W": (255, 255, 255, 255),
    "B": (17, 17, 17, 255),
    "H": (248, 232, 170, 255),
    "M": (255, 170, 40, 255),   # Mähne goldorange
    "F": (255, 150, 30, 255),
}
KEIN_OUTLINE = {PAL["F"]}


def ell(d, cx, cy, rx, ry, c):
    d.ellipse([round(cx - rx), round(cy - ry), round(cx + rx), round(cy + ry)], fill=PAL[c])


def wirbelsaeule(phase, amp, bob):
    """Punkte vom Schwanz (i=0) zum Hals (i=n-1)."""
    pts = []
    n = 22
    for i in range(n):
        t = i / (n - 1)
        x = 6 + t * 50
        # Welle läuft nach hinten, zum Kopf hin flacher
        a = amp * (1.0 - 0.55 * t)
        y = 26 + bob + math.sin(t * 2.6 * math.pi - phase) * a
        r = 1.5 + 2.8 * min(1.0, t * 1.6)  # Schwanz dünn, dann gleichmäßig
        pts.append((x, y, r, t))
    return pts


def frame(phase=0.0, amp=4.0, bob=0, blink=False, leg=0.0, schnurr=0.0, mund=False, welle=None):
    """`phase` treibt Beine, Mähne, Quaste, Schnurrhaare. `welle` (falls gesetzt)
    bestimmt allein die Körperform — so kann er auf der Stelle tapsen, ohne
    dass eine Welle durch den Körper wandert (Mark: die Figur darf sich in
    ihrem Rahmen nicht fortbewegen, nur der Rahmen wandert über den Schirm)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = wirbelsaeule(phase if welle is None else welle, amp, bob)

    # Beine (hinter dem Körper): zwei Paare
    for idx, ph in ((7, 0.0), (16, math.pi)):
        x, y, r, _ = pts[idx]
        s = math.sin(phase * 2 + ph) * leg
        for off, c in ((-1.5, "D"), (1.5, "R")):
            vorz = 1 if c == "R" else -1
            fx = x + off + s * vorz
            # Fuß hebt sich beim Vorschwingen, steht beim Zurückschieben am Boden.
            hub = max(0.0, math.cos(phase * 2 + ph) * vorz) * leg * 0.7
            fy = y + r + 4 - hub
            d.line([(x + off, y + r - 1), (fx, fy)], fill=PAL[c], width=2)
            d.point((fx + 1, fy), fill=PAL["H"])  # Krallen

    # Mähne entlang des Rückens
    for x, y, r, t in pts[4::2]:
        flatter = math.sin(phase + t * 6) * 1.0
        d.polygon([(x - 2, y - r + 1), (x - 3.5 + flatter, y - r - 3), (x + 1.5, y - r + 1)], fill=PAL["M"])

    # Körper: dunkel, dann rot, dann Bauch
    for x, y, r, t in pts:
        ell(d, x, y + 0.6, r, r, "D")
    for x, y, r, t in pts:
        ell(d, x - 0.2, y - 0.3, max(r - 0.7, 0.6), max(r - 0.7, 0.6), "R")
    for x, y, r, t in pts:
        if r > 2.2:
            ell(d, x, y + r * 0.6, r * 0.45, r * 0.3, "Y")
    for x, y, r, t in pts[6::3]:
        d.point((round(x), round(y + r * 0.55)), fill=PAL["O"])
        d.point((round(x) - 1, round(y - r * 0.4)), fill=PAL["L"])

    # Schwanzquaste
    tx, ty, tr, _ = pts[0]
    flack = math.sin(phase * 1.5) * 1.5
    d.polygon([(tx + 1, ty - 1), (tx - 5, ty - 3 + flack), (tx - 4, ty + 1 + flack), (tx - 5, ty + 4 + flack), (tx + 1, ty + 1)], fill=PAL["F"])

    # Kopf am Ende des Halses
    nx, ny, nr, _ = pts[-1]
    hx, hy = nx + 6, ny - 9
    # Hals-Verbindung
    for k in (0.33, 0.66):
        ell(d, nx + 6 * k, ny - 9 * k + 0.6, 3.5, 3.5, "D")
    for k in (0.33, 0.66):
        ell(d, nx + 6 * k - 0.2, ny - 9 * k, 2.9, 2.9, "R")
    # Geweih-Hörner (nach hinten oben)
    for bx in (hx - 4, hx + 1):
        d.line([(bx, hy - 4), (bx - 4, hy - 11)], fill=PAL["H"], width=2)
        d.line([(bx - 2, hy - 7), (bx - 1, hy - 10)], fill=PAL["H"], width=1)
    # Mähne am Hinterkopf
    for i in range(3):
        my = hy - 2 + i * 3
        d.polygon([(hx - 4, my - 2), (hx - 10 + math.sin(phase + i) * 1.2, my + 0.5), (hx - 4, my + 2)], fill=PAL["M"])
    # Kopf
    ell(d, hx, hy + 0.6, 7.2, 6.2, "D")
    ell(d, hx - 0.3, hy, 6.7, 5.6, "R")
    ell(d, hx - 2, hy - 3, 2.5, 1.2, "L")
    # Schnauze
    ell(d, hx + 7, hy + 2, 4.5, 3, "D")
    ell(d, hx + 6.8, hy + 1.5, 4.1, 2.5, "R")
    d.point((hx + 10, hy), fill=PAL["K"])
    if mund:
        d.line([(hx + 4, hy + 4), (hx + 10, hy + 4)], fill=PAL["K"])
    else:
        d.line([(hx + 5, hy + 3), (hx + 9, hy + 3)], fill=PAL["D"])
    # Bart-Tuft am Kinn
    d.polygon([(hx + 3, hy + 4), (hx + 1 + schnurr, hy + 8), (hx + 6, hy + 5)], fill=PAL["M"])
    # Auge
    if blink:
        d.line([(hx, hy - 1), (hx + 4, hy - 1)], fill=PAL["K"])
    else:
        ell(d, hx + 2, hy - 1.2, 2.2, 2.8, "W")
        d.rectangle([hx + 3, hy - 2, hx + 4, hy], fill=PAL["B"])
        d.point((hx + 3, hy - 2), fill=PAL["W"])
    d.line([(hx - 1, hy - 5), (hx + 5, hy - 4)], fill=PAL["K"])  # Braue
    # Schnurrhaare: lang, geschwungen
    for sy, sgn in ((hy + 1, -1), (hy + 2, 1)):
        p = []
        for k in range(10):
            u = k / 9
            p.append((hx + 10 + u * 10, sy + sgn * (u * 3) + math.sin(u * 4 + phase) * (1 + schnurr) * u))
        d.line(p, fill=PAL["M"], width=1)
    return outline(img)


def outline(img):
    px = img.load()
    out = img.copy()
    po = out.load()
    for y in range(H):
        for x in range(W):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and px[nx, ny][3] and px[nx, ny] not in KEIN_OUTLINE and px[nx, ny] != PAL["M"]:
                        po[x, y] = PAL["K"]
                        break
    return out


def speichern(frames, name, dauer, scale=7):
    gross = []
    for f in frames:
        bg = Image.new("RGBA", (W, H), (24, 26, 38, 255))
        bg.alpha_composite(f)
        gross.append(bg.resize((W * scale, H * scale), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
    gross[0].save(name, save_all=True, append_images=gross[1:], duration=dauer, loop=0, disposal=2)


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    idle = []
    for i in range(20):
        t = i / 20 * 2 * math.pi
        idle.append(frame(phase=t, amp=2.0, bob=round(math.sin(t) * 0.6), blink=i in (14, 15), schnurr=math.sin(t) * 0.5))
    speichern(idle, f"{out}/final_idle.gif", 110)
    lauf = []
    for i in range(10):
        t = i / 10 * 2 * math.pi
        lauf.append(frame(phase=t, amp=4.5, leg=2.0, mund=True, schnurr=1.0))
    speichern(lauf, f"{out}/final_lauf.gif", 80)
    bg = Image.new("RGBA", (W, H), (24, 26, 38, 255)); bg.alpha_composite(lauf[0])
    bg.resize((W * 10, H * 10), Image.NEAREST).save(f"{out}/final_check.png")
    print("ok")

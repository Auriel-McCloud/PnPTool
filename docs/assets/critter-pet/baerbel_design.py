# Bärbel – sprechende Bibel/Zauberbuch (Mark + Frau, 11.11.2026). Drei Gestalten,
# zwischen denen sie sich verwandelt: 1 klassisch, 2 Grimoire (Auge), 3 Gesicht.
from PIL import Image, ImageDraw

FONT = {
    "B": ["110", "101", "110", "101", "110"],
    "A": ["010", "101", "111", "101", "101"],
    "R": ["110", "101", "110", "101", "101"],
    "E": ["111", "100", "110", "100", "111"],
    "L": ["100", "100", "100", "100", "111"],
}

VARIANTEN = {
    "1_klassisch": dict(  # dunkelbraunes Leder, Gold, Kreuz
        K=(30, 16, 10), D=(74, 40, 22), M=(112, 64, 34), H=(150, 92, 50),
        G=(240, 196, 70), g=(176, 126, 36), P=(244, 232, 200), p=(196, 178, 140),
        Band=(170, 30, 40), orn="kreuz", augen=False),
    "2_grimoire": dict(  # violett, Silber, Auge
        K=(22, 10, 32), D=(58, 26, 84), M=(92, 44, 128), H=(130, 74, 170),
        G=(214, 220, 236), g=(140, 146, 170), P=(236, 228, 206), p=(186, 174, 146),
        Band=(60, 200, 170), orn="auge", augen=False),
    "3_gesicht": dict(  # rotes Leder, Gold, Kulleraugen auf dem Deckel
        K=(36, 8, 14), D=(110, 22, 34), M=(160, 36, 46), H=(204, 70, 72),
        G=(246, 200, 80), g=(184, 132, 40), P=(246, 236, 210), p=(198, 182, 150),
        Band=(250, 210, 90), orn="stern", augen=True),
}


def c(v, k):
    return v[k] + (255,)


def text(d, x, y, s, col, dots_col=None):
    for ch in s:
        g = FONT["A" if ch == "Ä" else ch]
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == "1":
                    d.point((x + i, y + j), fill=col)
        if ch == "Ä":
            d.point((x, y - 2), fill=dots_col or col)
            d.point((x + 2, y - 2), fill=dots_col or col)
        x += 4


def outline(img, col):
    w, h = img.size
    px = img.load()
    neu = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 0:
                        neu.append((x, y))
                        break
    for p in neu:
        px[p] = col


def zu(v, lid=0.0, blick=0, band=0, spalt=0, schliesse_auf=False, schreck=False):
    """`spalt` (0..4): Deckel springt an der Vorderkante auf, dunkler Spalt mit
    glühenden Augen (Tentakelmonster). `schliesse_auf`: Schließe baumelt offen.
    `schreck`: Bärbel guckt erschrocken (Gesicht/Auge)."""
    W, H = 52, 58
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Rückdeckel + Seitenblock (3/4-Ansicht nach rechts unten)
    d.rectangle([12, 8, 46, 53], fill=c(v, "D"))
    d.rectangle([11, 7, 44, 51], fill=c(v, "P"))
    for y in range(9, 51, 2):
        d.line([(41, y), (44, y)], fill=c(v, "p"))
    for x in range(13, 44, 3):
        d.line([(x, 48), (x, 51)], fill=c(v, "p"))
    # Lesebändchen hängt unten raus
    # `band` = seitliches Wehen des Endes in Pixeln (-2..2)
    d.line([(30, 50), (30 + band * 0.5, 53), (30 + band, 56)], fill=c(v, "Band"), width=2)
    d.point((round(31 + band), 57), fill=c(v, "Band"))
    # Vorderdeckel
    d.rectangle([6, 3, 40, 47], fill=c(v, "D"))
    d.rectangle([7, 4, 39, 46], fill=c(v, "M"))
    d.line([(8, 4), (38, 4)], fill=c(v, "H"))
    d.line([(39, 5), (39, 45)], fill=c(v, "H"))
    # Buchrücken links mit Bünden
    d.rectangle([4, 4, 10, 46], fill=c(v, "D"))
    d.line([(5, 5), (5, 45)], fill=c(v, "M"))
    for y in (10, 20, 30, 40):
        d.line([(4, y), (10, y)], fill=c(v, "g"))
        d.line([(4, y - 1), (10, y - 1)], fill=c(v, "G"))
    # Goldrahmen (geprägt)
    d.rectangle([13, 8, 36, 42], outline=c(v, "g"))
    # Metall-Ecken
    for (x, y, sx, sy) in ((39, 4, -1, 1), (39, 46, -1, -1), (11, 4, 1, 1), (11, 46, 1, -1)):
        for i in range(5):
            d.line([(x, y + sy * i), (x + sx * (4 - i), y + sy * i)], fill=c(v, "G"))
        d.point((x + sx, y + sy), fill=c(v, "g"))
    # Titelschild
    d.rectangle([14, 10, 35, 18], fill=c(v, "D"))
    text(d, 14, 12, "BÄRBEL", c(v, "G"))
    # Ornament
    o = v["orn"]
    cx, cy = 25, 30
    if o == "kreuz":
        d.rectangle([cx - 1, cy - 8, cx + 1, cy + 9], fill=c(v, "G"))
        d.rectangle([cx - 6, cy - 4, cx + 6, cy - 2], fill=c(v, "G"))
        d.line([(cx + 1, cy - 7), (cx + 1, cy + 9)], fill=c(v, "g"))
        d.line([(cx - 5, cy - 2), (cx + 6, cy - 2)], fill=c(v, "g"))
    elif o == "auge":
        if lid >= 0.95:
            # Geschlossen: nur der Lidbogen mit Wimpern, kein Augenrand
            for x in range(cx - 8, cx + 9):
                dx = (x - cx) / 8
                d.point((x, cy - 1 + round(2 * (1 - dx * dx))), fill=c(v, "G"))
        else:
            d.ellipse([cx - 8, cy - 4, cx + 8, cy + 4], fill=c(v, "G"))
            d.ellipse([cx - 6, cy - 3, cx + 6, cy + 3], fill=c(v, "D"))
            d.ellipse([cx - 3 + blick, cy - 3, cx + 3 + blick, cy + 3], fill=(250, 200, 60, 255))
            if schreck:
                d.point((cx + blick, cy), fill=(10, 10, 10, 255))
            else:
                d.line([(cx + blick, cy - 2), (cx + blick, cy + 2)], fill=(10, 10, 10, 255))
            d.point((cx - 2 + blick, cy - 2), fill=(255, 255, 255, 255))
            if lid > 0:
                ly = round(cy - 4 + lid * 8)
                d.rectangle([cx - 7, cy - 4, cx + 7, ly], fill=c(v, "M"))
                d.ellipse([cx - 8, cy - 4, cx + 8, cy + 4], outline=c(v, "G"))
                d.rectangle([cx - 9, cy - 6, cx + 9, cy - 5], fill=c(v, "M"))
                for x in range(cx - 7, cx + 8):
                    if (x - cx) ** 2 / 64 + (ly - cy) ** 2 / 16 <= 1.05:
                        d.point((x, ly), fill=c(v, "G"))
        for dx in (-6, -2, 2, 6):  # Wimpern/Strahlen
            if lid >= 0.95:
                d.line([(cx + dx, cy + 2 - abs(dx) // 3), (cx + dx * 1.2, cy + 4 - abs(dx) // 3)], fill=c(v, "G"))
            else:
                d.line([(cx + dx, cy - 6), (cx + dx * 0.8, cy - 5)], fill=c(v, "G"))
    if v["augen"]:
        # Stern klein oben, dann Kulleraugen + Mündchen
        for (ex) in (18, 29):
            if lid >= 0.95:
                d.line([(ex - 3, 30), (ex - 2, 31), (ex + 2, 31), (ex + 3, 30)], fill=(20, 10, 10, 255))
            else:
                d.ellipse([ex - 3, 25, ex + 3, 33], fill=(255, 255, 255, 255))
                if schreck:
                    d.rectangle([ex - 1 + blick, 28, ex + blick, 29], fill=(20, 10, 10, 255))
                else:
                    d.ellipse([ex - 2 + blick, 27, ex + 2 + blick, 33], fill=(20, 10, 10, 255))
                    d.point((ex - 1 + blick, 28), fill=(255, 255, 255, 255))
                    d.point((ex + blick, 29), fill=(255, 255, 255, 255))
                if lid > 0:
                    d.rectangle([ex - 3, 24, ex + 3, 24 + round(lid * 8)], fill=c(v, "M"))
                    d.line([(ex - 3, 24 + round(lid * 8)), (ex + 3, 24 + round(lid * 8))], fill=(20, 10, 10, 255))
        d.point((15, 34), fill=c(v, "H"))
        d.point((35, 34), fill=c(v, "H"))
        if schreck:
            d.ellipse([23, 35, 26, 39], fill=c(v, "K"))
        else:
            d.line([(23, 36), (24, 37), (26, 37), (27, 36)], fill=c(v, "K"))
        # Stern
        sx, sy = 25, 41
        d.line([(sx - 2, sy), (sx + 2, sy)], fill=c(v, "G"))
        d.line([(sx, sy - 2), (sx, sy + 2)], fill=c(v, "G"))
    # Spalt an der Vorderkante: Deckel springt auf, drinnen ist es dunkel
    if spalt > 0:
        sp = round(spalt)
        # Keil: an der Vorderkante am weitesten offen, oben/unten schmaler
        d.polygon([(38, 6), (39 + sp, 14), (39 + sp, 38), (38, 46)], fill=(14, 6, 22, 255))
        d.line([(39 + sp, 14), (39 + sp, 38)], fill=(120, 60, 170, 255))
        if spalt >= 2:  # glühende Augen im Dunkeln
            for ey in (21, 27):
                d.rectangle([39, ey, 40, ey], fill=(255, 230, 60, 255))
                d.point((39, ey + 1), fill=(255, 140, 30, 255))
    # Schließe rechts
    if schliesse_auf:
        # baumelt offen nach unten
        d.line([(36, 28), (37, 33)], fill=c(v, "D"), width=3)
        d.rectangle([35, 33, 39, 37], fill=c(v, "G"))
        d.rectangle([36, 34, 38, 36], fill=c(v, "g"))
    else:
        d.rectangle([34, 25, 42, 30], fill=c(v, "K"))
        d.rectangle([35, 26, 42, 29], fill=c(v, "D"))
        d.rectangle([37, 24, 41, 31], fill=c(v, "G"))
        d.rectangle([38, 26, 40, 29], fill=c(v, "g"))
        d.point((38, 25), fill=(255, 255, 255, 255))
    outline(img, c(v, "K"))
    return img


def offen(v, winkel=20.0, nachzug=0.0, band=0.0, lid=0.0, blick=0):
    """Aufgeklappt, Deckel = Flügel. `winkel` in Grad (+ oben, - unten),
    `nachzug` = wie weit die losen Seiten der Bewegung hinterherhängen
    (-1..1), `band` = Phase des wehenden Lesebändchens."""
    import math
    W, H = 76, 76
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    mx, ry = 38, 30          # Rücken oben
    L, hp = 32, 17           # Flügellänge, Seitenhöhe
    w = math.radians(winkel)
    tx = L * math.cos(w)
    ty = -L * math.sin(w) * 0.8
    unten = max(0.0, -math.sin(w))   # wie viel Deckel-Außenseite man sieht
    dicke = 3 + round(unten * 7)
    for s in (-1, 1):
        X = mx + s * tx
        # Deckel (Außenseite unten sichtbar) – etwas länger als die Seiten
        X2 = mx + s * (tx + 3 * math.cos(w))
        d.polygon([(mx, ry + 2), (X2, ry + ty + 1), (X2, ry + ty + hp + dicke + 2), (mx, ry + hp + dicke + 2)], fill=c(v, "D"))
        d.polygon([(mx, ry + hp), (X2, ry + ty + hp), (X2, ry + ty + hp + dicke + 1), (mx, ry + hp + dicke + 1)], fill=c(v, "M"))
        # Goldecken an der Flügelspitze
        for k in range(3):
            d.point((round(X2), round(ry + ty + 1 + k)), fill=c(v, "G"))
            d.point((round(X2), round(ry + ty + hp + dicke + 1 - k)), fill=c(v, "G"))
        # Seitenblock: Schnitt (Dicke) + Oberseite
        d.polygon([(mx, ry), (X, ry + ty), (X, ry + ty + hp + 2), (mx, ry + hp + 2)], fill=c(v, "p"))
        d.polygon([(mx, ry), (X, ry + ty), (X, ry + ty + hp), (mx, ry + hp)], fill=c(v, "P"))
        d.line([(mx + s, ry + 1), (mx + s, ry + hp)], fill=c(v, "p"))
        # lose oberste Seite hängt nach (nur zur Spitze hin)
        if abs(nachzug) > 0.15:
            k0 = 0.45
            x0 = mx + s * tx * k0
            y0 = ry + ty * k0
            nx = mx + s * tx * 0.97
            ny = ry + ty - nachzug * 6
            d.polygon([(x0, y0), (nx, ny), (nx, ny + hp * 0.9), (x0, y0 + hp)], fill=c(v, "P"))
            d.line([(x0, y0), (nx, ny)], fill=c(v, "p"))
        # Textzeilen
        for i in range(5):
            for j in range(4, 28):
                f = j / 30
                if (j + i * 5) % 11 in (3, 7):
                    continue
                xx = mx + s * tx * f
                yy = ry + ty * f + 3 + i * 2.8
                if abs(nachzug) > 0.15 and f > 0.5:
                    yy -= nachzug * 6 * (f - 0.45) / 0.52
                d.point((round(xx), round(yy)), fill=c(v, "g"))
    # Lesebändchen weht unten raus
    pts = []
    for k in range(9):
        pts.append((mx + math.sin(band - k * 0.7) * k * 0.5, ry + hp + 2 + k * 1.6))
    d.line(pts, fill=c(v, "Band"), width=2)
    # Gesicht je Gestalt (auf den Seiten, wie hineingemalt)
    if v["orn"] == "auge":
        cx, cy = mx, ry + 7
        if lid >= 0.95:
            for x in range(cx - 6, cx + 7):
                dx = (x - cx) / 6
                d.point((x, cy + round(1.5 * (1 - dx * dx))), fill=c(v, "D"))
        else:
            d.ellipse([cx - 6, cy - 3, cx + 6, cy + 3], fill=c(v, "D"))
            d.ellipse([cx - 5, cy - 2, cx + 5, cy + 2], fill=(250, 200, 60, 255))
            d.line([(cx + blick, cy - 2), (cx + blick, cy + 2)], fill=(10, 10, 10, 255))
            d.point((cx - 2 + blick, cy - 1), fill=(255, 255, 255, 255))
            if lid > 0:
                d.rectangle([cx - 6, cy - 3, cx + 6, cy - 3 + round(lid * 5)], fill=c(v, "D"))
    if v["augen"]:
        for s in (-1, 1):
            ex = mx + s * 6
            ey = ry + 8 - s * 0
            ey = round(ry + ty * (6 / tx if tx > 1 else 0) + 7) if False else round(ry + 6 * (ty / max(tx, 1)) + 7)
            if lid >= 0.95:
                d.line([(ex - 2, ey + 1), (ex + 2, ey + 1)], fill=(20, 10, 10, 255))
            else:
                d.ellipse([ex - 2, ey - 3, ex + 2, ey + 3], fill=(20, 10, 10, 255))
                d.point((ex - 1 + max(0, blick), ey - 1), fill=(255, 255, 255, 255))
                if lid > 0:
                    d.rectangle([ex - 2, ey - 3, ex + 2, ey - 3 + round(lid * 5)], fill=c(v, "P"))
        d.line([(mx - 1, ry + 13), (mx + 1, ry + 13)], fill=c(v, "D"))
    outline(img, c(v, "K"))
    return img


if __name__ == "__main__":
    import os
    out = os.path.dirname(os.path.abspath(__file__))
    S = 6
    tafeln = []
    for name, v in VARIANTEN.items():
        a = zu(v)
        b = offen(v)
        t = Image.new("RGBA", (a.width + b.width + 8, max(a.height, b.height)), (60, 62, 70, 255))
        t.alpha_composite(a, (0, 0))
        t.alpha_composite(b, (a.width + 8, (t.height - b.height) // 2))
        tafeln.append(t)
        a.resize((a.width * S, a.height * S), Image.NEAREST).save(f"{out}/zu_{name}.png")
    gesamt = Image.new("RGBA", (tafeln[0].width + 8, sum(t.height + 6 for t in tafeln) + 2), (60, 62, 70, 255))
    y = 4
    for t in tafeln:
        gesamt.alpha_composite(t, (4, y))
        y += t.height + 6
    gesamt.resize((gesamt.width * S, gesamt.height * S), Image.NEAREST).save(f"{out}/varianten.png")
    print("ok", gesamt.size)

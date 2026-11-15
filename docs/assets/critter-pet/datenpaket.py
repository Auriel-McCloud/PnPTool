# KI-Futter (Mark, 15.11.2026): leuchtendes Datenpaket, 14×14 → frontend/public/pets/datenpaket.png

from PIL import Image, ImageDraw
img=Image.new("RGBA",(14,14),(0,0,0,0)); d=ImageDraw.Draw(img)
K=(18,40,60,255); C=(60,200,240,255); H=(170,245,255,255); D=(30,120,170,255)
# Würfel in Schrägsicht
d.polygon([(7,1),(13,4),(7,7),(1,4)],fill=H)
d.polygon([(1,4),(7,7),(7,13),(1,10)],fill=C)
d.polygon([(13,4),(7,7),(7,13),(13,10)],fill=D)
for x,y in ((3,6),(4,8),(3,9),(10,6),(9,8),(11,9),(6,3),(8,4)):
    d.point((x,y),fill=(230,255,255,255))
px=img.load(); out=img.copy(); po=out.load()
for y in range(14):
    for x in range(14):
        if px[x,y][3]==0:
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,ny=x+dx,y+dy
                if 0<=nx<14 and 0<=ny<14 and px[nx,ny][3]: po[x,y]=K; break
out.save(r"C:/DEV/PnPTool/frontend/public/pets/datenpaket.png")

# -*- coding: utf-8 -*-
"""Desenha app.ico (ícone do .exe, das janelas e da bandeja): balão de
chat com 'RF' em cores suaves do tema."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "app.ico")
S = 256

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# fundo: quadrado arredondado azul-acinzentado
d.rounded_rectangle((8, 8, S - 8, S - 8), radius=52, fill=(77, 108, 148, 255))
# balão de chat claro com 'cauda'
d.rounded_rectangle((38, 46, S - 38, 178), radius=34, fill=(238, 242, 247, 255))
d.polygon([(78, 170), (70, 216), (120, 172)], fill=(238, 242, 247, 255))
font = None
for name in ("segoeuib.ttf", "arialbd.ttf"):
    try:
        font = ImageFont.truetype(os.path.join(os.environ.get(
            "WINDIR", r"C:\Windows"), "Fonts", name), 92)
        break
    except OSError:
        continue
font = font or ImageFont.load_default()
box = d.textbbox((0, 0), "RF", font=font)
w, h = box[2] - box[0], box[3] - box[1]
d.text(((S - w) / 2 - box[0], 112 - h / 2 - box[1]), "RF", font=font,
       fill=(61, 86, 119, 255))
# ponto verde-salva: 'traduzido'
d.ellipse((182, 178, 236, 232), fill=(91, 148, 121, 255),
          outline=(238, 242, 247, 255), width=6)
img.save(OUT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                     (128, 128), (256, 256)])
print("ícone:", OUT)

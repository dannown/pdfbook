from PIL import Image, ImageDraw, ImageFont
import os

paper_width = 210
paper_height = 297
dpi = 600
square_width_mm = 2.5
square_width = int(square_width_mm / 25.4 * dpi)

font = ImageFont.truetype(
    os.path.join(os.path.dirname(__file__), "../resources/anwb-uu.woff.ttf"), 12)
side = Image.new("RGB",
                 (int(paper_width / 25.4 * dpi), int(paper_height / 25.4 * dpi)),
                 "white")
draw = ImageDraw.Draw(side)
# colors = ["LightGreen", "MediumOrchid", "Pink", "HotPink", "LightPink", "LightBlue", "LemonChiffon"]
colors = ["LightPink", "LightSalmon", "LemonChiffon", "LightGreen", "LightBlue", "Lavender", "Plum"]

for i in range(int(paper_height / square_width_mm) + 1):
    for j in range(int(paper_width / square_width_mm)):
        color = colors[(i + j) % len(colors)]
        draw.rectangle((j * square_width, i * square_width, (j + 1) * square_width, (i + 1) * square_width), color, "black")
        num = i * int(paper_width / square_width_mm) + j
        draw.text((j*square_width, i*square_width), f"{num%100000:05d}", fill="black", font=font)

fp = open("/tmp/test_page.jpg", "wb")
side.save(fp)
fp.close()

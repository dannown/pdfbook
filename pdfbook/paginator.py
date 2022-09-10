from PIL import Image, ImageDraw, ImageFont
import os


class Paginator:
    def __init__(self, num_up: int, pages_per_signature: int, blank: Image = None):
        self.num_up = num_up
        self.pages_per_signature = pages_per_signature
        self.blank = blank
        self.manual_layout = True
        self.paper_width = 21.0
        self.paper_height = 29.7
        self.dpi = 600.0
        self.top_margin = 5  # in mm!
        self.include_last_page_marker = True
        self.register_count = 0

    def signature_page_order(self):
        if self.num_up == 4:
            if self.pages_per_signature == 16:
                return [5, 12, 4, 13,
                        11, 6, 14, 3,
                        7, 10, 2, 15,
                        9, 8, 16, 1]
            if self.pages_per_signature == 8:
                return [3, 6, 2, 7,
                        5, 4, 8, 1]
        if self.num_up == 2:
            if self.pages_per_signature == 12:
                return [12, 1, 2, 11,
                        10, 3, 4, 9,
                        8, 5, 6, 7]
            if self.pages_per_signature == 4:
                return [4, 1, 2, 3]
            if self.pages_per_signature == 8:
                return [8, 1, 2, 7,
                        6, 3, 4, 5]
            if self.pages_per_signature == 16:
                return [16, 1, 2, 15,
                        14, 3, 4, 13,
                        12, 5, 6, 11,
                        10, 7, 8, 9]

    def should_rotate_page(self, page_num):
        if self.num_up == 4:
            if self.pages_per_signature == 16:
                return page_num in [5, 12, 11, 6, 7, 10, 9, 8]
            if self.pages_per_signature == 8:
                return page_num in [3, 6, 5, 4]
        return False

    def write_paginated_images(self, images: list, filename: str):
        print(f"writing out {len(images)} pages.")
        if len(images) % self.pages_per_signature != 0:
            n = self.pages_per_signature - len(images) % self.pages_per_signature
            p = images[0]
            n %= self.num_up * 2
            print(f"adding {n} blank pages to end. There are now "
                  f"{(len(images) + n) % self.pages_per_signature} pages in the last signature.")
            for x in range(n):
                if self.blank is not None:
                    images.append(self.blank)
                else:
                    images.append(Image.new("RGB", (p.width, p.height), "white"))
        paginated_images = []
        offset = 0
        tmp_pps = self.pages_per_signature
        while offset < len(images):
            if len(images) - offset < self.pages_per_signature:
                self.pages_per_signature = len(images) - offset
            for i in self.signature_page_order():
                big_i = offset + i - 1
                page: Image = images[big_i]
                if self.should_rotate_page(i):
                    page = page.rotate(180)
                # print(f"adding page {big_i}")
                paginated_images.append(page)
            offset += self.pages_per_signature
        self.pages_per_signature = tmp_pps
        self.save_images(paginated_images, filename)

    def save_images(self, images: list, filename: str):
        layout = []
        if self.manual_layout and self.num_up == 4:
            num_sheets = int(len(images) / self.num_up)
            num_sheets_per_sig = int(self.pages_per_signature / self.num_up)
            for i in range(num_sheets):
                side = Image.new("RGB",
                                 (int(self.paper_width / 2.54 * self.dpi), int(self.paper_height / 2.54 * self.dpi)),
                                 "white")
                pages = images[i * self.num_up:(i + 1) * self.num_up]
                # we want 5mm on top, on bottom, then repeat.
                top_margin = int(self.top_margin / 25.4 * self.dpi)
                page_height = int((side.height - top_margin * 4) / 2)
                page_width = int(page_height * pages[0].width / pages[0].height)
                left_margin = int((side.width - 2 * page_width) / 2)
                print(f"laying out pages {i * self.num_up + 1} to {(i + 1) * self.num_up}")
                page0 = pages[0].resize((page_width, page_height))
                page1 = pages[1].resize((page_width, page_height))
                page2 = pages[2].resize((page_width, page_height))
                page3 = pages[3].resize((page_width, page_height))
                side.paste(page0,
                           (left_margin,
                            top_margin,
                            left_margin + page_width,
                            top_margin + page_height))
                side.paste(page1,
                           (left_margin + page_width,
                            top_margin,
                            left_margin + 2 * page_width,
                            top_margin + page_height))
                side.paste(page2,
                           (left_margin,
                            top_margin * 3 + page_height,
                            left_margin + page_width,
                            top_margin * 3 + 2 * page_height))
                side.paste(page3,
                           (left_margin + page_width,
                            top_margin * 3 + page_height,
                            left_margin + 2 * page_width,
                            top_margin * 3 + 2 * page_height))
                if (i + 1) % num_sheets_per_sig == 0 or i + 1 == num_sheets:
                    # last sheet for the signature
                    draw = ImageDraw.Draw(side)
                    colors = ["LightGreen", "MediumOrchid", "Pink", "HotPink", "LightPink", "LightBlue"]
                    self.register_count += 1
                    font = ImageFont.truetype(
                        os.path.join(os.path.dirname(__file__), "resources/anwb-uu.woff.ttf"), 30)
                    for box in range(6):
                        draw.rectangle((side.width - (box + 1) * top_margin / 4,
                                        side.height - (box + 1) * top_margin / 4, side.width - box * top_margin / 4,
                                        side.height - box * top_margin / 4),
                                       fill=colors[box], outline="Black")
                    draw.text((side.width - (box + 1) * top_margin / 4,
                               side.height - (box + 1) * top_margin / 4), f"{self.register_count:03d}",
                              font=font,
                              fill="black")

                layout.append(side)
        fp = open(filename, "wb")
        layout[0].save(fp, save_all=True, append_images=layout[1:])
        fp.close()
